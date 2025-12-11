#!/usr/bin/env python3
"""Iperf traffic testing with SSH-based remote execution.

This script provides automated iperf traffic testing between remote hosts
with comprehensive logging and statistics collection.

Features:
- Remote iperf server and client management via SSH
- Support for TCP and UDP protocols
- Configurable test parameters (duration, bandwidth, parallel streams)
- CSV logging for easy analysis with plotly
- Multiple test iterations with delays
- Graceful shutdown on Ctrl+C

Usage:
    python main_scan_traffic.py

Configuration:
    Edit main_scan_traffic_cfg.json to configure:
    - Jump host credentials
    - Server and client host credentials
    - Test parameters (protocol, duration, bandwidth, etc.)
"""

import csv
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
import signal
import sys
import threading
import time

from src.core.cli import PrettyFrame
from src.core.connect import LocalConnection, SshConnection
from src.core.log.formatter import create_formatter
from src.core.traffic.iperf import IperfClient, IperfServer
from src.models.config import Host

# ---------------------------------------------------------------------------- #
#                          Graceful shutdown handling                          #
# ---------------------------------------------------------------------------- #

shutdown_event = threading.Event()
_shutdown_triggered = False


def signal_handler(_signum, _frame) -> None:
    """Handle Ctrl+C signal for graceful shutdown."""
    global _shutdown_triggered
    if not _shutdown_triggered:
        _shutdown_triggered = True
        shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)

# ---------------------------------------------------------------------------- #
#                             Logging configuration                            #
# ---------------------------------------------------------------------------- #


def setup_logging(log_dir: Path, log_level: str) -> tuple[logging.Logger, logging.Logger]:
    """Setup logging for traffic testing.

    Args:
        log_dir: Directory for log files
        log_level: Log level string (debug, info, warning, error)

    Returns:
        Tuple of (main_logger, traffic_logger)
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)

    # Main logger
    main_logger = logging.getLogger("main")
    main_logger.setLevel(level)
    main_handler = logging.FileHandler(log_dir / "main.log")
    main_handler.setFormatter(create_formatter("main"))
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(create_formatter("main"))
    main_logger.addHandler(main_handler)
    main_logger.addHandler(console_handler)

    # Traffic logger (CSV format)
    traffic_logger = logging.getLogger("traffic")
    traffic_logger.setLevel(level)
    traffic_logger.propagate = False

    return main_logger, traffic_logger


# ---------------------------------------------------------------------------- #
#                                  Configuration                               #
# ---------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Config:
    """Traffic test configuration."""

    log_level: str
    jump_host: str
    jump_user: str
    jump_pass: str
    server_host: str
    server_user: str
    server_pass: str
    server_sudo_pass: str
    server_port: int
    server_connect_type: str
    client_host: str
    client_user: str
    client_pass: str
    client_sudo_pass: str
    client_connect_type: str
    test_duration_sec: int
    test_protocol: str
    test_bandwidth: str
    test_parallel_streams: int
    test_interval_sec: int
    test_iterations: int
    test_delay_between_tests_sec: int
    test_bidir: bool
    test_reverse: bool

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from JSON dict.

        Args:
            data: Configuration dictionary

        Returns:
            Config instance
        """
        j, srv, cli, test = data["jump"], data["server"], data["client"], data["test"]
        return cls(
            log_level=data.get("log_level", "info"),
            jump_host=j["host"],
            jump_user=j["user"],
            jump_pass=j["pass"],
            server_host=srv["host"],
            server_user=srv["user"],
            server_pass=srv["pass"],
            server_sudo_pass=srv.get("sudo_pass", ""),
            server_port=srv.get("port", 5201),
            server_connect_type=srv.get("connect_type", "remote"),
            client_host=cli["host"],
            client_user=cli["user"],
            client_pass=cli["pass"],
            client_sudo_pass=cli.get("sudo_pass", ""),
            client_connect_type=cli.get("connect_type", "remote"),
            test_duration_sec=test.get("duration_sec", 30),
            test_protocol=test.get("protocol", "tcp"),
            test_bandwidth=test.get("bandwidth", "10G"),
            test_parallel_streams=test.get("parallel_streams", 1),
            test_interval_sec=test.get("interval_sec", 1),
            test_iterations=test.get("iterations", 5),
            test_delay_between_tests_sec=test.get("delay_between_tests_sec", 5),
            test_bidir=test.get("bidir", False),
            test_reverse=test.get("reverse", False),
        )


def validate_config(cfg: Config, logger: logging.Logger) -> bool:
    """Validate configuration values.

    Args:
        cfg: Configuration to validate
        logger: Logger instance

    Returns:
        True if valid
    """
    errors = []

    if cfg.test_duration_sec <= 0:
        errors.append(f"Invalid duration: {cfg.test_duration_sec} (must be > 0)")
    if cfg.test_protocol not in ["tcp", "udp"]:
        errors.append(f"Invalid protocol: {cfg.test_protocol} (must be tcp or udp)")
    if cfg.test_parallel_streams < 1:
        errors.append(f"Invalid parallel streams: {cfg.test_parallel_streams} (must be >= 1)")
    if cfg.test_interval_sec <= 0:
        errors.append(f"Invalid interval: {cfg.test_interval_sec} (must be > 0)")
    if cfg.test_iterations < 1:
        errors.append(f"Invalid iterations: {cfg.test_iterations} (must be >= 1)")
    if cfg.test_bidir and cfg.test_reverse:
        errors.append("Cannot use both bidir and reverse mode simultaneously")
    if cfg.server_port < 1 or cfg.server_port > 65535:
        errors.append(f"Invalid port: {cfg.server_port} (must be 1-65535)")

    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info("Configuration validated successfully")
    return True


# ---------------------------------------------------------------------------- #
#                              Connection Management                           #
# ---------------------------------------------------------------------------- #


def create_connection(
    cfg: Config, host_type: str, logger: logging.Logger
) -> SshConnection | LocalConnection:
    """Create connection based on configuration.

    Args:
        cfg: Configuration
        host_type: "server" or "client"
        logger: Logger instance

    Returns:
        Connection instance
    """
    jump_host = Host(ip=cfg.jump_host, username=cfg.jump_user, password=cfg.jump_pass)

    if host_type == "server":
        connect_type = cfg.server_connect_type
        if connect_type == "local":
            return LocalConnection(cfg.server_host, cfg.server_sudo_pass)
        return SshConnection(
            host=cfg.server_host,
            username=cfg.server_user,
            password=cfg.server_pass,
            jump_hosts=[jump_host],
            sudo_pass=cfg.server_sudo_pass,
        )

    # Client
    connect_type = cfg.client_connect_type
    if connect_type == "local":
        return LocalConnection(cfg.client_host, cfg.client_sudo_pass)
    return SshConnection(
        host=cfg.client_host,
        username=cfg.client_user,
        password=cfg.client_pass,
        jump_hosts=[jump_host],
        sudo_pass=cfg.client_sudo_pass,
    )


# ---------------------------------------------------------------------------- #
#                              Statistics Logging                              #
# ---------------------------------------------------------------------------- #


def write_test_metadata(csv_file: Path, cfg: Config, logger: logging.Logger):
    """Write test configuration metadata to CSV.

    Args:
        csv_file: CSV file path
        cfg: Configuration
        logger: Logger instance
    """
    metadata_file = csv_file.parent / "test_metadata.csv"

    with metadata_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "value"])
        writer.writerow(["protocol", cfg.test_protocol])
        writer.writerow(["duration_sec", cfg.test_duration_sec])
        writer.writerow(["bandwidth", cfg.test_bandwidth])
        writer.writerow(["parallel_streams", cfg.test_parallel_streams])
        writer.writerow(["interval_sec", cfg.test_interval_sec])
        writer.writerow(["iterations", cfg.test_iterations])
        writer.writerow(["bidir", cfg.test_bidir])
        writer.writerow(["reverse", cfg.test_reverse])
        writer.writerow(["server_host", cfg.server_host])
        writer.writerow(["server_port", cfg.server_port])
        writer.writerow(["client_host", cfg.client_host])

    logger.info(f"Test metadata written to {metadata_file}")


def write_stats_to_csv(stats: list, csv_file: Path, iteration: int, logger: logging.Logger):
    """Write statistics to CSV file.

    Args:
        stats: List of IperfStats
        csv_file: CSV file path
        iteration: Test iteration number
        logger: Logger instance
    """
    if not stats:
        logger.warning(f"No statistics to write for iteration {iteration}")
        return

    file_exists = csv_file.exists()

    with csv_file.open("a", newline="") as f:
        fieldnames = [
            "iteration",
            "timestamp",
            "interval",
            "transfer_bytes",
            "bandwidth_bps",
            "bandwidth_mbps",
            "bandwidth_gbps",
            "jitter_ms",
            "lost_packets",
            "total_packets",
            "loss_percent",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for stat in stats:
            writer.writerow(
                {
                    "iteration": iteration,
                    "timestamp": stat.timestamp,
                    "interval": stat.interval,
                    "transfer_bytes": stat.transfer_bytes,
                    "bandwidth_bps": stat.bandwidth_bps,
                    "bandwidth_mbps": stat.bandwidth_bps / 1e6,
                    "bandwidth_gbps": stat.bandwidth_bps / 1e9,
                    "jitter_ms": stat.jitter_ms,
                    "lost_packets": stat.lost_packets,
                    "total_packets": stat.total_packets,
                    "loss_percent": stat.loss_percent,
                }
            )

    logger.info(f"Wrote {len(stats)} statistics to {csv_file}")


def write_summary_stats(summaries: list[dict], csv_file: Path, logger: logging.Logger):
    """Write summary statistics across all iterations.

    Args:
        summaries: List of summary dicts from each iteration
        csv_file: CSV file path
        logger: Logger instance
    """
    if not summaries:
        return

    summary_file = csv_file.parent / "summary_stats.csv"

    with summary_file.open("w", newline="") as f:
        fieldnames = [
            "iteration",
            "bandwidth_min_gbps",
            "bandwidth_max_gbps",
            "bandwidth_avg_gbps",
            "bandwidth_stddev_gbps",
            "transfer_total_gb",
            "sample_count",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, summary in enumerate(summaries, 1):
            writer.writerow(
                {
                    "iteration": i,
                    "bandwidth_min_gbps": summary["bandwidth_min_bps"] / 1e9,
                    "bandwidth_max_gbps": summary["bandwidth_max_bps"] / 1e9,
                    "bandwidth_avg_gbps": summary["bandwidth_avg_bps"] / 1e9,
                    "bandwidth_stddev_gbps": summary["bandwidth_stddev_bps"] / 1e9,
                    "transfer_total_gb": summary["transfer_total_bytes"] / 1e9,
                    "sample_count": summary["sample_count"],
                }
            )

    logger.info(f"Summary statistics written to {summary_file}")


# ---------------------------------------------------------------------------- #
#                              Test Execution                                  #
# ---------------------------------------------------------------------------- #


def setup_connections(cfg: Config, logger: logging.Logger) -> tuple | None:
    """Setup and validate connections."""
    logger.info("Creating connections...")
    server_conn = create_connection(cfg, "server", logger)
    client_conn = create_connection(cfg, "client", logger)

    logger.info("Connecting to hosts...")
    if not server_conn.connect():
        logger.error("Failed to connect to server host")
        return None

    if not client_conn.connect():
        logger.error("Failed to connect to client host")
        server_conn.disconnect()
        return None

    logger.info("Connections established")
    return server_conn, client_conn


def setup_iperf(cfg: Config, server_conn, client_conn, logger: logging.Logger) -> tuple | None:
    """Setup and validate iperf instances."""
    server = IperfServer(server_conn, logger, cfg.server_port)
    client = IperfClient(client_conn, logger, cfg.server_host, cfg.server_port)

    logger.info("Validating connections...")
    if not server.validate_connection() or not client.validate_connection(cfg.server_host):
        logger.error("Connection validation failed")
        return None

    server.configure(use_json=True)
    client.configure(
        duration=cfg.test_duration_sec,
        protocol=cfg.test_protocol,
        bandwidth=cfg.test_bandwidth if cfg.test_protocol == "udp" else None,
        parallel=cfg.test_parallel_streams,
        use_json=True,
        interval=cfg.test_interval_sec,
        bidir=cfg.test_bidir,
        reverse=cfg.test_reverse,
    )

    logger.info("Connection validation passed")
    return server, client


def run_test_iterations(
    cfg: Config, client: IperfClient, csv_file: Path, logger: logging.Logger
) -> tuple:
    """Run test iterations."""
    summaries = []
    successful_tests = 0
    failed_tests = 0
    failed_iterations = []
    consecutive_failures = 0

    for iteration in range(1, cfg.test_iterations + 1):
        if shutdown_event.is_set():
            logger.info("Shutdown signal received, stopping tests")
            break

        logger.info(f"\n{'=' * 60}")
        logger.info(
            f"Test iteration {iteration}/{cfg.test_iterations} (Progress: {iteration * 100 // cfg.test_iterations}%)"
        )
        logger.info(f"{'=' * 60}")

        if client.start():
            stats = client.get_stats()
            logger.info(f"Test completed: {len(stats)} samples collected")

            summary = client.get_stats_summary()
            if summary:
                summaries.append(summary)
                successful_tests += 1
                consecutive_failures = 0

            write_stats_to_csv(stats, csv_file, iteration, logger)
        else:
            logger.error(f"Test iteration {iteration} failed")
            failed_tests += 1
            failed_iterations.append(iteration)
            consecutive_failures += 1

            if consecutive_failures >= 3:
                logger.error("3 consecutive failures detected, aborting tests")
                break

        if iteration < cfg.test_iterations and not shutdown_event.is_set():
            logger.info(f"Waiting {cfg.test_delay_between_tests_sec}s before next test...")
            time.sleep(cfg.test_delay_between_tests_sec)

    return summaries, successful_tests, failed_tests, failed_iterations


def cleanup_resources(server, server_conn, client_conn, logger: logging.Logger):
    """Cleanup all resources."""
    logger.info("\nCleaning up...")
    if server:
        try:
            server.stop()
        except Exception:
            logger.exception("Error stopping server")

    try:
        client_conn.disconnect()
    except Exception:
        logger.exception("Error disconnecting client")

    try:
        server_conn.disconnect()
    except Exception:
        logger.exception("Error disconnecting server")


def print_final_summary(
    start_time: datetime,
    summaries: list,
    successful_tests: int,
    failed_tests: int,
    failed_iterations: list,
    csv_file: Path,
    logger: logging.Logger,
):
    """Print final test summary."""
    end_time = datetime.now()
    duration = end_time - start_time
    summary_lines = [
        f"Duration: {duration.total_seconds():.1f}s",
        f"Total tests: {successful_tests + failed_tests}",
        f"Successful: {successful_tests}",
        f"Failed: {failed_tests}",
    ]
    if failed_iterations:
        summary_lines.append(f"Failed iterations: {failed_iterations}")
    if summaries:
        all_bw = [s["bandwidth_avg_bps"] for s in summaries]
        summary_lines.append(f"Overall avg: {sum(all_bw) / len(all_bw) / 1e9:.2f} Gbps")
    summary_lines.append(f"Results: {csv_file}")

    if _shutdown_triggered:
        frame = PrettyFrame()
        msg = frame.build("SHUTDOWN", ["Traffic testing stopped by user"])
        sys.stderr.write(msg)
        sys.stderr.flush()

    logger.info(PrettyFrame().build("COMPLETE", summary_lines))


# ---------------------------------------------------------------------------- #
#                                MAIN function                                 #
# ---------------------------------------------------------------------------- #


def main() -> int:
    """Main execution for iperf traffic testing.

    Returns:
        Exit code (0=success, 1=failure)
    """
    start_time = datetime.now()
    timestamp = start_time.strftime("%Y%m%d_%H%M%S_traffic")
    log_dir = Path("logs") / timestamp

    # Load config
    try:
        cfg = Config.from_dict(
            json.load(open(Path(__file__).parent / "main_scan_traffic_cfg.json"))
        )
    except FileNotFoundError:
        print("ERROR: Configuration file 'main_scan_traffic_cfg.json' not found")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        return 1

    main_logger, _ = setup_logging(log_dir, cfg.log_level)
    main_logger.info(PrettyFrame().build("IPERF TRAFFIC TESTING", ["Starting traffic test..."]))

    if not validate_config(cfg, main_logger):
        return 1

    # Setup connections
    conns = setup_connections(cfg, main_logger)
    if not conns:
        return 1
    server_conn, client_conn = conns

    # Setup iperf
    iperf = setup_iperf(cfg, server_conn, client_conn, main_logger)
    if not iperf:
        server_conn.disconnect()
        client_conn.disconnect()
        return 1
    server, client = iperf

    # Prepare test
    csv_file = log_dir / "traffic_stats.csv"
    write_test_metadata(csv_file, cfg, main_logger)

    # Initialize test results
    summaries = []
    successful_tests = 0
    failed_tests = 0
    failed_iterations = []
    server_started = False

    try:
        # Start server
        main_logger.info("Starting iperf server...")
        if not server.start(daemon=True):
            main_logger.error("Failed to start server")
            return 1
        server_started = True
        main_logger.info(f"Server started on port {cfg.server_port}")
        time.sleep(2)

        # Validate port reachability
        if not client.check_port_reachable(cfg.server_host, cfg.server_port):
            main_logger.error("Server port not reachable from client")
            return 1

        # Run tests
        summaries, successful_tests, failed_tests, failed_iterations = run_test_iterations(
            cfg, client, csv_file, main_logger
        )

    finally:
        cleanup_resources(server if server_started else None, server_conn, client_conn, main_logger)
        if summaries:
            write_summary_stats(summaries, csv_file, main_logger)
        print_final_summary(
            start_time,
            summaries,
            successful_tests,
            failed_tests,
            failed_iterations,
            csv_file,
            main_logger,
        )

    return 0 if failed_tests == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
