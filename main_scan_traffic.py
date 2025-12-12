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
from src.core.enum.connect import ConnectType, IperfHostType
from src.core.enum.messages import LogMsg
from src.core.log.setup import init_logging
from src.core.traffic.iperf import IperfClient, IperfServer
from src.interfaces.component import IConnection
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


# Register signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

# ---------------------------------------------------------------------------- #
#                             Logging configuration                            #
# ---------------------------------------------------------------------------- #

# Note: Logging is initialized in main() to use same timestamp as CSV files
traffic_logger = None

# ---------------------------------------------------------------------------- #
#                              Connection Management                           #
# ---------------------------------------------------------------------------- #


def create_connection(
    cfg: TrafficConfig, host_type: IperfHostType
) -> SshConnection | LocalConnection:
    """Create connection based on configuration.

    Args:
        cfg: Configuration
        host_type: Server or client host type

    Returns:
        Connection instance
    """
    # Create jump host configuration for SSH tunneling
    jump_host = Host(ip=cfg.jump_host, username=cfg.jump_user, password=cfg.jump_pass)
    traffic_logger.debug(f"Creating {host_type.value} connection via jump host {cfg.jump_host}")

    if host_type == IperfHostType.SERVER:
        connect_type = cfg.server_connect_type
        traffic_logger.debug(f"Server connection type: {connect_type}")

        # Use local execution if server is on same machine
        if connect_type == ConnectType.LOCAL.value:
            traffic_logger.debug(f"Creating local connection to {cfg.server_host}")
            return LocalConnection(cfg.server_host, cfg.server_sudo_pass)

        # Create SSH connection through jump host
        traffic_logger.debug(f"Creating SSH connection to server {cfg.server_host}")
        return SshConnection(
            host=cfg.server_host,
            username=cfg.server_user,
            password=cfg.server_pass,
            jump_hosts=[jump_host],
            sudo_pass=cfg.server_sudo_pass,
        )

    # Client connection setup
    connect_type = cfg.client_connect_type
    traffic_logger.debug(f"Client connection type: {connect_type}")

    # Use local execution if client is on same machine
    if connect_type == ConnectType.LOCAL.value:
        traffic_logger.debug(f"Creating local connection to {cfg.client_host}")
        return LocalConnection(cfg.client_host, cfg.client_sudo_pass)

    # Create SSH connection through jump host
    traffic_logger.debug(f"Creating SSH connection to client {cfg.client_host}")
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


def write_metadata_to_csv(csv_file: Path, cfg: TrafficConfig, logger: logging.Logger):
    """Write test configuration metadata to CSV.

    Args:
        csv_file: CSV file path
        cfg: Configuration
        logger: Logger instance
    """
    if not cfg:
        logger.warning(f"{LogMsg.TRAFFIC_METADATA_NONE.value}")
        return

    logger.info(f"{LogMsg.TRAFFIC_METADATA_START.value}: {csv_file}")

    with csv_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["server_ip", cfg.server_ip])
        writer.writerow(["server_port", cfg.server_port])
        writer.writerow(["parameter", "value"])
        writer.writerow(["duration_sec", cfg.test_duration_sec])
        writer.writerow(["protocol", cfg.test_protocol])
        writer.writerow(["bandwidth", cfg.test_bandwidth])
        writer.writerow(["parallel_streams", cfg.test_parallel_streams])
        writer.writerow(["interval_sec", cfg.test_interval_sec])
        writer.writerow(["iterations", cfg.test_iterations])
        writer.writerow(["delay_between_tests_sec", cfg.test_delay_between_tests_sec])
        writer.writerow(["server_host", cfg.server_host])
        writer.writerow(["client_host", cfg.client_host])

    logger.info(f"{LogMsg.TRAFFIC_METADATA_STOPP.value}")


def write_stats_to_csv(stats: list, csv_file: Path, iteration: int, logger: logging.Logger):
    """Write statistics to CSV file.

    Args:
        stats: List of IperfStats
        csv_file: CSV file path
        iteration: Test iteration number
        logger: Logger instance
    """
    if not stats:
        logger.warning(f"{LogMsg.TRAFFIC_STATS_NONE.value} {iteration}")
        return

    # Check if file exists BEFORE opening to determine if header is needed
    write_header = not csv_file.exists()

    with csv_file.open("a", newline="") as f:
        fieldnames = [
            "begin_timestamp",
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
            "iteration",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        logger.info(f"{LogMsg.TRAFFIC_STATS_START.value}: {csv_file}")

        begin_ts = datetime.now()
        for stat in stats:
            writer.writerow(
                {
                    "begin_timestamp": begin_ts,
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
                    "iteration": iteration,
                }
            )

    logger.info(f"{LogMsg.TRAFFIC_STATS_STOP.value}: {len(stats)} samples")


def write_summary_to_csv(summaries: list[dict], csv_file: Path, logger: logging.Logger):
    """Write summary statistics across all iterations.

    Args:
        summaries: List of summary dicts from each iteration
        csv_file: CSV file path
        logger: Logger instance
    """
    if not summaries:
        logger.warning(f"{LogMsg.TRAFFIC_SUMMARY_NONE.value}")
        return

    with csv_file.open("w", newline="") as f:
        fieldnames = [
            "begin_timestamp",
            "bandwidth_min_gbps",
            "bandwidth_max_gbps",
            "bandwidth_avg_gbps",
            "bandwidth_stddev_gbps",
            "transfer_total_gb",
            "sample_count",
            "iteration",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        logger.info(f"{LogMsg.TRAFFIC_SUMMARY_START.value}: {csv_file}")

        begin_ts = datetime.now()
        for i, summary in enumerate(summaries, 1):
            writer.writerow(
                {
                    "begin_timestamp": begin_ts,
                    "bandwidth_min_gbps": summary["bandwidth_min_bps"] / 1e9,
                    "bandwidth_max_gbps": summary["bandwidth_max_bps"] / 1e9,
                    "bandwidth_avg_gbps": summary["bandwidth_avg_bps"] / 1e9,
                    "bandwidth_stddev_gbps": summary["bandwidth_stddev_bps"] / 1e9,
                    "transfer_total_gb": summary["transfer_total_bytes"] / 1e9,
                    "sample_count": summary["sample_count"],
                    "iteration": i,
                }
            )

    logger.info(f"{LogMsg.TRAFFIC_SUMMARY_STOP.value}: {len(summaries)} samples")


# ---------------------------------------------------------------------------- #
#                              Test Execution                                  #
# ---------------------------------------------------------------------------- #


def setup_connections(cfg: TrafficConfig, logger: logging.Logger) -> tuple | None:
    """Setup and validate connections to server and client hosts.

    Creates SSH/local connections and validates connectivity before proceeding.

    Returns:
        Tuple of (server_conn, client_conn) or None on failure
    """
    logger.info(LogMsg.TRAFFIC_CONN_CREATE.value)
    logger.debug(f"Server: {cfg.server_host}, Client: {cfg.client_host}")

    # Create connection objects (doesn't establish connection yet)
    server_conn = create_connection(cfg, IperfHostType.SERVER)
    client_conn = create_connection(cfg, IperfHostType.CLIENT)
    logger.debug("Connection objects created successfully")

    logger.info(LogMsg.CONN_CONNECTING.value)

    # Establish server connection first
    logger.debug(f"Connecting to server {cfg.server_host}...")
    if not server_conn.connect():
        logger.error(f"Failed to connect to server {cfg.server_host}")
        logger.error(LogMsg.CONN_FAILED.value)
        return None
    logger.debug(f"Server connection established: {cfg.server_host}")

    # Establish client connection
    logger.debug(f"Connecting to client {cfg.client_host}...")
    if not client_conn.connect():
        logger.error(f"Failed to connect to client {cfg.client_host}")
        logger.error(LogMsg.CONN_FAILED.value)
        # Clean up server connection before returning
        logger.debug("Disconnecting server due to client connection failure")
        server_conn.disconnect()
        return None
    logger.debug(f"Client connection established: {cfg.client_host}")

    logger.info(LogMsg.CONN_ESTABLISHED.value)
    logger.debug("Both connections ready for iperf testing")

    return server_conn, client_conn


def setup_iperf(
    cfg: TrafficConfig, server_conn: IConnection, client_conn: IConnection, logger: logging.Logger
) -> tuple | None:
    """Setup and validate iperf server and client instances.

    Creates iperf instances, validates connectivity, and configures test parameters.

    Returns:
        Tuple of (server, client) or None on failure
    """
    # Create iperf server and client instances
    logger.debug(f"Creating iperf server on port {cfg.server_port}")
    server = IperfServer(server_conn, logger, cfg.server_port)

    logger.debug(f"Creating iperf client targeting: {cfg.server_ip}:{cfg.server_port}")
    client = IperfClient(client_conn, logger, cfg.server_ip, cfg.server_port)

    # Validate that iperf is installed and connections work
    logger.info(LogMsg.TRAFFIC_CONN_VALIDATE.value)
    logger.debug("Validating server connection and iperf availability...")

    if not server.validate_connection():
        logger.error("Server validation failed - iperf may not be installed")
        logger.error(LogMsg.CONN_FAILED.value)
        return None
    logger.debug("Server validation passed")

    logger.debug(f"Validating client connection to: {cfg.server_ip}...")
    if not client.validate_connection(cfg.server_ip):
        logger.error(f"Client validation failed - cannot reach {cfg.server_ip}")
        logger.error(LogMsg.CONN_FAILED.value)
        return None
    logger.debug("Client validation passed")

    # Configure server (minimal config, no JSON output)
    logger.debug("Configuring iperf server...")
    server.configure(use_json=False)

    # Configure client with test parameters
    logger.debug(
        f"Configuring iperf client: protocol={cfg.test_protocol}, duration={cfg.test_duration_sec}s"
    )
    logger.debug(
        f"  bandwidth={cfg.test_bandwidth}, parallel={cfg.test_parallel_streams}, interval={cfg.test_interval_sec}s"
    )
    client.configure(
        duration=cfg.test_duration_sec,
        protocol=cfg.test_protocol,
        bandwidth=cfg.test_bandwidth if cfg.test_protocol == "udp" else None,  # Only for UDP
        parallel=cfg.test_parallel_streams,
        use_json=False,  # Use text output for iperf2 compatibility
        interval=cfg.test_interval_sec,
    )

    logger.info(LogMsg.TRAFFIC_CONN_VALIDATE_PASS.value)
    logger.debug("Iperf setup complete and ready for testing")
    return server, client


def update_timer(
    duration: int,
    logger: logging.Logger,
    stop_event: threading.Event,
    csv_file: Path,
    cfg: TrafficConfig,
):
    """Display countdown in terminal with single line updates."""
    remaining = duration

    while remaining > 0 and not stop_event.is_set():
        # Read last line from CSV for live bandwidth stats
        bw_str = ""
        try:
            if csv_file.exists():
                with csv_file.open("r") as f:
                    lines = f.readlines()
                    if len(lines) > 1:  # Skip header
                        last = lines[-1].strip()
                        parts = last.split(",")
                        if len(parts) > 5 and parts[5]:
                            bw_str = f" @ {float(parts[5]):.1f} Gbps"
        except Exception:
            pass

        msg = f"{cfg.client_host} -> {cfg.server_ip}:{cfg.server_port}{bw_str} | Time: {remaining}s"
        sys.stderr.write(f"\r{msg}" + " " * 20)
        sys.stderr.flush()
        time.sleep(1)
        remaining -= 1

    sys.stderr.write("\r" + " " * 100 + "\nTraffic test(s) completed!\n")
    sys.stderr.flush()


def display_iteration_frame(iteration: int, cfg: TrafficConfig, infinite_mode: bool):
    """Display iteration progress frame."""
    if infinite_mode:
        frame = PrettyFrame().build(
            "TRAFFIC",
            ["Mode: Infinit", "To quit use: Ctrl+C"],
        )
    else:
        frame = PrettyFrame().build(
            f"ITERATION {iteration}/{cfg.test_iterations}",
            [
                f"Progress: {iteration * 100 // cfg.test_iterations}%",
                f"Test duration: {cfg.test_duration_sec}s",
            ],
        )
    sys.stderr.write(frame)
    sys.stderr.flush()


def run_single_test(
    client: IperfClient, stats_csv_file: Path, iteration: int, logger: logging.Logger
) -> tuple[list, dict | None]:
    """Run single test iteration and return stats."""
    if not client.start():
        return [], None

    stats = client.get_stats()
    logger.info(f"{LogMsg.TRAFFIC_TEST_COMPLETE.value}: {len(stats)} samples collected")
    summary = client.get_stats_summary()
    write_stats_to_csv(stats, stats_csv_file, iteration, logger)
    return stats, summary


def wait_between_tests(delay_sec: int, logger: logging.Logger):
    """Wait between test iterations with shutdown check."""
    logger.info(f"{LogMsg.TRAFFIC_TEST_WAIT.value} {delay_sec}s...")
    for _ in range(delay_sec):
        if shutdown_event.is_set():
            break
        time.sleep(1)


def run_test_iterations(
    cfg: TrafficConfig, client: IperfClient, stats_csv_file: Path, logger: logging.Logger
) -> tuple:
    """Run iperf test iterations with progress tracking and error handling.

    Executes multiple test iterations, collecting statistics and handling failures.
    Supports both finite and infinite iteration modes.

    Returns:
        Tuple of (summaries, successful_tests, failed_tests, failed_iterations)
    """
    # Initialize tracking variables
    summaries = []
    successful_tests = 0
    failed_tests = 0
    failed_iterations = []
    consecutive_failures = 0

    iteration = 0
    # Infinite mode: iterations=0 means run continuously until manuel, ctrl+c
    infinite_iterations = cfg.test_iterations == 0
    max_iterations = None if infinite_iterations else cfg.test_iterations

    logger.debug(
        f"Starting test loop: infinite={infinite_iterations}, max_iterations={max_iterations}"
    )

    gen_frame = True
    # Main test loop - continues until max iterations or shutdown
    while not shutdown_event.is_set():  # Fixed: was checking is_set() instead of not is_set()
        iteration += 1
        logger.debug(f"Starting iteration {iteration}")

        # Check for shutdown signal
        if shutdown_event.is_set():
            logger.info(LogMsg.SHUTDOWN_SIGNAL.value)
            logger.debug(f"Shutdown requested at iteration {iteration}")
            break

        # Check if we've reached max iterations (finite mode only)
        if max_iterations and iteration > max_iterations:
            logger.debug(f"Reached max iterations: {max_iterations}")
            break

        if gen_frame:
            gen_frame = False
            display_iteration_frame(iteration, cfg, infinite_iterations)

        if not infinite_iterations:
            # Start countdown timer thread for live progress updates
            logger.debug(f"Starting countdown timer for {cfg.test_duration_sec}s")
            timer_stop = threading.Event()
            timer_thread = threading.Thread(
                target=update_timer,
                args=(cfg.test_duration_sec, logger, timer_stop, stats_csv_file, cfg),
                daemon=True,
            )
            timer_thread.start()
        else:
            timer_stop = None

        # Execute the actual iperf test
        logger.debug(f"Running test iteration {iteration}")
        stats, summary = run_single_test(client, stats_csv_file, iteration, logger)

        # Process test results
        if stats:
            # Test succeeded - stop timer and record results
            if timer_stop:
                timer_stop.set()
            logger.debug(f"Test {iteration} succeeded with {len(stats)} samples")

            if summary:
                summaries.append(summary)
                successful_tests += 1
                consecutive_failures = 0  # Reset failure counter
                logger.debug(
                    f"Summary recorded: avg_bw={summary['bandwidth_avg_bps'] / 1e9:.2f} Gbps"
                )
        else:
            # Test failed - track failure and check abort condition
            logger.error(f"{LogMsg.TRAFFIC_TEST_FAILED.value} {iteration}")
            logger.debug(f"Test {iteration} failed - no stats collected")
            failed_tests += 1
            failed_iterations.append(iteration)
            consecutive_failures += 1

            # Abort after 3 consecutive failures to prevent infinite retry
            if consecutive_failures >= 3:
                logger.error(LogMsg.TRAFFIC_TEST_ABORT.value)
                logger.debug(f"Aborting after {consecutive_failures} consecutive failures")
                break

        # Wait between tests if not shutting down and more tests remain (skip in infinite mode)
        if not shutdown_event.is_set() and not infinite_iterations and iteration < max_iterations:
            logger.debug(f"Waiting {cfg.test_delay_between_tests_sec}s before next test")
            wait_between_tests(cfg.test_delay_between_tests_sec, logger)

    logger.debug(f"Test loop complete: {successful_tests} passed, {failed_tests} failed")
    return summaries, successful_tests, failed_tests, failed_iterations


def kill_iperf_processes(conn, host_type: IperfHostType, logger: logging.Logger):
    """Kill all iperf processes on a host."""
    try:
        logger.info(f"Cleaning up iperf processes on {host_type}...")
        conn.exec_cmd("pkill -9 iperf", timeout=5)
    except Exception:
        logger.exception(f"Failed to cleanup {host_type} iperf processes")


def cleanup_resources(server, server_conn, client_conn, logger: logging.Logger):
    """Cleanup all resources."""
    logger.info(LogMsg.SHUTDOWN_START.value)

    kill_iperf_processes(server_conn, IperfHostType.SERVER, logger)
    kill_iperf_processes(client_conn, IperfHostType.CLIENT, logger)

    if server:
        try:
            server.stop()
        except Exception:
            logger.exception(LogMsg.TRAFFIC_SERVER_STOPP.value)

    try:
        client_conn.disconnect()
    except Exception:
        logger.exception(LogMsg.TRAFFIC_CLIENT_DISCONNECT.value)

    try:
        server_conn.disconnect()
    except Exception:
        logger.exception(LogMsg.TRAFFIC_SERVER_DISCONNECT.value)


def build_summary_lines(
    start_time: datetime,
    summaries: list,
    successful_tests: int,
    failed_tests: int,
    failed_iterations: list,
    stats_csv_file: Path,
    summary_csv_file: Path,
) -> list[str]:
    """Build summary lines for final report."""
    duration = datetime.now() - start_time
    lines = [f"Duration: {duration.total_seconds():.1f}s"]

    total_tests = successful_tests + failed_tests
    if total_tests > 0:
        lines.extend(
            [
                f"Total tests: {total_tests}",
                f"Successful: {successful_tests}",
                f"Failed: {failed_tests}",
            ]
        )
        if failed_iterations:
            lines.append(f"Failed iterations: {failed_iterations}")

    if summaries:
        avg_bw = sum(s["bandwidth_avg_bps"] for s in summaries) / len(summaries) / 1e9
        lines.append(f"Overall avg: {avg_bw:.2f}Gbps")
    lines.append(f"Statistics: {stats_csv_file}")
    lines.append(f"Summary: {summary_csv_file}")
    return lines


def print_final_summary(
    start_time: datetime,
    summaries: list,
    successful_tests: int,
    failed_tests: int,
    failed_iterations: list,
    stats_csv_file: Path,
    summary_csv_file: Path,
    logger: logging.Logger,
):
    """Print final test summary."""
    if _shutdown_triggered:
        msg = PrettyFrame().build("SHUTDOWN SIGNAL", [LogMsg.SHUTDOWN_GRACEFUL.value])
        sys.stderr.write(msg)
        sys.stderr.flush()

    summary_lines = build_summary_lines(
        start_time,
        summaries,
        successful_tests,
        failed_tests,
        failed_iterations,
        stats_csv_file,
        summary_csv_file,
    )
    summary_frame = PrettyFrame().build("TRAFFIC COMPLETED", summary_lines)
    logger.info(summary_frame)
    sys.stderr.write(summary_frame)
    sys.stderr.flush()


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
    # ---------------------------------------------------------------------------- #
    #                          Initialize logging and config                       #
    # ---------------------------------------------------------------------------- #

    # Create timestamped log directory first
    start_time = datetime.now()
    log_dir = Path("logs") / start_time.strftime("%Y%m%d_%H%M%S")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Initialize logging to use the same directory
    global traffic_logger
    loggers = init_logging("main_scan_traffic_cfg.json")
    traffic_logger = loggers[LogName.TRAFFIC.value]

    try:
        cfg = load_traffic_config(traffic_logger)
    except Exception:
        traffic_logger.exception(LogMsg.CONFIG_FAILED.value)
        return

    traffic_logger.info(PrettyFrame().build("IPERF TRAFFIC", [LogMsg.TRAFFIC_TEST_START.value]))

    if not cfg.validate(traffic_logger):
        return

    # ---------------------------------------------------------------------------- #
    #                              Setup connections                               #
    # ---------------------------------------------------------------------------- #

    conns = setup_connections(cfg, traffic_logger)
    if not conns:
        return
    server_conn, client_conn = conns

    # ---------------------------------------------------------------------------- #
    #                               Setup iperf                                    #
    # ---------------------------------------------------------------------------- #

    iperf = setup_iperf(cfg, server_conn, client_conn, traffic_logger)
    if not iperf:
        server_conn.disconnect()
        client_conn.disconnect()
        return
    server, client = iperf

    # ---------------------------------------------------------------------------- #
    #                              Prepare CSV files                               #
    # ---------------------------------------------------------------------------- #

    stats_csv_file = log_dir / "traffic_stats.csv"
    metadata_csv_file = log_dir / "traffic_metadata.csv"
    summary_csv_file = log_dir / "traffic_summary.csv"

    write_metadata_to_csv(metadata_csv_file, cfg, traffic_logger)

    # ---------------------------------------------------------------------------- #
    #                                   MAIN loop                                  #
    # ---------------------------------------------------------------------------- #

    summaries = []
    successful_tests = 0
    failed_tests = 0
    failed_iterations = []
    server_started = False

    try:
        traffic_logger.info(f"{LogMsg.TRAFFIC_SERVER_START.value}: {cfg.server_port}")

        if not server.start(daemon=True):
            traffic_logger.error(LogMsg.MAIN_SCAN_FAILED_START.value)
            return
        server_started = True
        time.sleep(2)

        if not client.check_port_reachable(cfg.server_ip, cfg.server_port):
            traffic_logger.error(LogMsg.CONN_FAILED.value)
            return

        summaries, successful_tests, failed_tests, failed_iterations = run_test_iterations(
            cfg, client, stats_csv_file, traffic_logger
        )

    finally:
        # ---------------------------------------------------------------------------- #
        #                                   Cleanup                                    #
        # ---------------------------------------------------------------------------- #

        cleanup_resources(
            server if server_started else None, server_conn, client_conn, traffic_logger
        )

        traffic_logger.info(f"{LogMsg.TRAFFIC_SERVER_STOP.value}")

        if summaries:
            write_summary_to_csv(summaries, summary_csv_file, traffic_logger)

        print_final_summary(
            start_time,
            summaries,
            successful_tests,
            failed_tests,
            failed_iterations,
            stats_csv_file,
            summary_csv_file,
            traffic_logger,
        )


if __name__ == "__main__":
    main()
