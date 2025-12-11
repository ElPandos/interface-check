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
from datetime import datetime
import logging
from pathlib import Path
import signal
import sys
import threading
import time

from src.core.cli import PrettyFrame
from src.core.config import load_traffic_config
from src.core.config.traffic import TrafficConfig
from src.core.connect import LocalConnection, SshConnection
from src.core.enum.messages import LogMsg
from src.core.log.setup import init_logging
from src.core.traffic.iperf import IperfClient, IperfServer
from src.models.config import Host
from src.platform.enums.log import LogName

# ---------------------------------------------------------------------------- #
#                          Graceful shutdown handling                          #
# ---------------------------------------------------------------------------- #

shutdown_event = threading.Event()
_shutdown_triggered = False


def signal_handler(_signum, _frame) -> None:
    """Handle Ctrl+C signal for graceful shutdown.

    Sets shutdown event to trigger cleanup. Does not perform I/O
    to avoid reentrant call errors.
    """
    global _shutdown_triggered
    if not _shutdown_triggered:
        _shutdown_triggered = True
        shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)

# ---------------------------------------------------------------------------- #
#                             Logging configuration                            #
# ---------------------------------------------------------------------------- #

loggers = init_logging()
main_logger = loggers[LogName.MAIN.value]
traffic_logger = loggers[LogName.TRAFFIC.value]


# ---------------------------------------------------------------------------- #
#                              Connection Management                           #
# ---------------------------------------------------------------------------- #


def create_connection(
    cfg: TrafficConfig, host_type: str, logger: logging.Logger
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


def write_test_metadata(csv_file: Path, cfg: TrafficConfig, logger: logging.Logger):
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


def setup_connections(cfg: TrafficConfig, logger: logging.Logger) -> tuple | None:
    """Setup and validate connections."""
    logger.info(LogMsg.TRAFFIC_CONN_CREATE.value)
    server_conn = create_connection(cfg, "server", logger)
    client_conn = create_connection(cfg, "client", logger)

    logger.info(LogMsg.CON_CONNECTING.value)
    if not server_conn.connect():
        logger.error(LogMsg.MAIN_CONN_FAILED.value)
        return None

    if not client_conn.connect():
        logger.error(LogMsg.MAIN_CONN_FAILED.value)
        server_conn.disconnect()
        return None

    logger.info(LogMsg.SSH_ESTABLISHED.value)
    return server_conn, client_conn


def setup_iperf(
    cfg: TrafficConfig, server_conn, client_conn, logger: logging.Logger
) -> tuple | None:
    """Setup and validate iperf instances."""
    server = IperfServer(server_conn, logger, cfg.server_port)
    client = IperfClient(client_conn, logger, cfg.server_host, cfg.server_port)

    logger.info(LogMsg.TRAFFIC_CONN_VALIDATE.value)
    if not server.validate_connection() or not client.validate_connection(cfg.server_host):
        logger.error(LogMsg.MAIN_CONN_FAILED.value)
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

    logger.info(LogMsg.TRAFFIC_CONN_VALIDATE_PASS.value)
    return server, client


def run_test_iterations(
    cfg: TrafficConfig, client: IperfClient, csv_file: Path, logger: logging.Logger
) -> tuple:
    """Run test iterations."""
    summaries = []
    successful_tests = 0
    failed_tests = 0
    failed_iterations = []
    consecutive_failures = 0

    for iteration in range(1, cfg.test_iterations + 1):
        if shutdown_event.is_set():
            logger.info(LogMsg.SHUTDOWN_SIGNAL.value)
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
    logger.info(LogMsg.SHUTDOWN_START.value)
    if server:
        try:
            server.stop()
        except Exception:
            logger.exception(LogMsg.TRAFFIC_SERVER_STOP.value)

    try:
        client_conn.disconnect()
    except Exception:
        logger.exception(LogMsg.TRAFFIC_CLIENT_DISCONNECT.value)

    try:
        server_conn.disconnect()
    except Exception:
        logger.exception(LogMsg.TRAFFIC_SERVER_DISCONNECT.value)


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
        msg = frame.build("SHUTDOWN SIGNAL", ["Ctrl+C pressed. Shutting down gracefully..."])
        sys.stderr.write(msg)
        sys.stderr.flush()

    logger.info(PrettyFrame().build("COMPLETE", summary_lines))


# ---------------------------------------------------------------------------- #
#                                MAIN function                                 #
# ---------------------------------------------------------------------------- #


def main():
    """Main execution for iperf traffic testing.

    Execution flow:
    1. Load and validate configuration
    2. Setup SSH connections to server and client
    3. Initialize iperf server and client
    4. Run test iterations with statistics collection
    5. Write results to CSV files
    6. Graceful cleanup and shutdown
    """
    start_time = datetime.now()

    # ---------------------------------------------------------------------------- #
    #                                 Load config                                  #
    # ---------------------------------------------------------------------------- #

    try:
        cfg = load_traffic_config(main_logger)
    except Exception:
        main_logger.exception(LogMsg.CONFIG_FAILED.value)
        return

    main_logger.info(PrettyFrame().build("IPERF TRAFFIC TESTING", ["Starting traffic test..."]))

    if not cfg.validate(main_logger):
        return

    # ---------------------------------------------------------------------------- #
    #                              Setup connections                               #
    # ---------------------------------------------------------------------------- #

    conns = setup_connections(cfg, main_logger)
    if not conns:
        return
    server_conn, client_conn = conns

    # ---------------------------------------------------------------------------- #
    #                               Setup iperf                                    #
    # ---------------------------------------------------------------------------- #

    iperf = setup_iperf(cfg, server_conn, client_conn, main_logger)
    if not iperf:
        server_conn.disconnect()
        client_conn.disconnect()
        return
    server, client = iperf

    # ---------------------------------------------------------------------------- #
    #                              Prepare test files                              #
    # ---------------------------------------------------------------------------- #

    log_dir = Path("logs") / start_time.strftime("%Y%m%d_%H%M%S")
    log_dir.mkdir(parents=True, exist_ok=True)
    csv_file = log_dir / "traffic_stats.csv"
    write_test_metadata(csv_file, cfg, main_logger)

    # ---------------------------------------------------------------------------- #
    #                                Run test loop                                 #
    # ---------------------------------------------------------------------------- #

    summaries = []
    successful_tests = 0
    failed_tests = 0
    failed_iterations = []
    server_started = False

    try:
        main_logger.info(LogMsg.TRAFFIC_SERVER_START.value)
        if not server.start(daemon=True):
            main_logger.error(LogMsg.MAIN_SCAN_FAILED_START.value)
            return
        server_started = True
        main_logger.info(f"Server started on port {cfg.server_port}")
        time.sleep(2)

        if not client.check_port_reachable(cfg.server_host, cfg.server_port):
            main_logger.error(LogMsg.MAIN_CONN_FAILED.value)
            return

        summaries, successful_tests, failed_tests, failed_iterations = run_test_iterations(
            cfg, client, csv_file, main_logger
        )

    finally:
        # ---------------------------------------------------------------------------- #
        #                                   Cleanup                                    #
        # ---------------------------------------------------------------------------- #

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


if __name__ == "__main__":
    main()
