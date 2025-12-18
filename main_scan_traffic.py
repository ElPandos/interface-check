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

import argparse
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
from src.core.traffic.iperf.base import IperfBase
from src.core.traffic.iperf.gui import IperfMonitor
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
#                              Connection Management                           #
# ---------------------------------------------------------------------------- #


def _get_host_credentials(cfg: TrafficConfig, is_server: bool) -> tuple[str, str, str, str, str]:
    """Extract host credentials from config.

    Returns:
        Tuple of (host, user, password, sudo_pass, connect_type)
    """
    if is_server:
        return (
            cfg.server_host,
            cfg.server_user,
            cfg.server_pass,
            cfg.server_sudo_pass,
            cfg.server_connect_type,
        )
    return (
        cfg.client_host,
        cfg.client_user,
        cfg.client_pass,
        cfg.client_sudo_pass,
        cfg.client_connect_type,
    )


def create_connection(
    cfg: TrafficConfig, host_type: IperfHostType, logger: logging.Logger
) -> SshConnection | LocalConnection:
    """Create connection based on configuration.

    Args:
        cfg: Configuration
        host_type: Server or client host type
        logger: Logger instance

    Returns:
        Connection instance
    """
    is_server = host_type == IperfHostType.SERVER
    host, user, password, sudo_pass, connect_type = _get_host_credentials(cfg, is_server)

    logger.debug(f"Creating {host_type.value} connection to {host} ({connect_type})")

    if connect_type == ConnectType.LOCAL.value:
        return LocalConnection(host, sudo_pass)

    jump_host = Host(ip=cfg.jump_host, username=cfg.jump_user, password=cfg.jump_pass)
    return SshConnection(
        host=host,
        username=user,
        password=password,
        jump_hosts=[jump_host],
        sudo_pass=sudo_pass,
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
        writer.writerow(["server_ips", ",".join(cfg.client_server_ips)])
        if cfg.server_server_ips:
            writer.writerow(["server_reverse_ips", ",".join(cfg.server_server_ips)])
        writer.writerow(["start_port", cfg.client_start_port])
        writer.writerow(["parameter", "value"])
        writer.writerow(["traffic_duration_sec", cfg.setup_traffic_duration_sec])
        writer.writerow(["protocol", cfg.setup_protocol])
        writer.writerow(["bandwidth", cfg.setup_bandwidth])
        writer.writerow(["parallel_streams", cfg.setup_parallel_streams])
        writer.writerow(["stats_poll_sec", cfg.setup_stats_poll_sec])
        writer.writerow(["server_host", cfg.server_host])
        writer.writerow(["client_host", cfg.client_host])

    logger.info(f"{LogMsg.TRAFFIC_METADATA_STOP.value}")


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


def _connect_to_host(
    conn: IConnection, host: str, host_type: IperfHostType, logger: logging.Logger
) -> bool:
    """Establish connection to a single host.

    Returns:
        True if connection successful, False otherwise
    """
    logger.debug(f"Connecting to {host_type.value} {host}...")
    if not conn.connect():
        logger.error(f"Failed to connect to {host_type.value} {host}")
        logger.error(LogMsg.CONN_FAILED.value)
        return False
    logger.debug(f"{host_type.value.capitalize()} connection established: {host}")
    return True


def setup_connections(
    cfg: TrafficConfig, logger: logging.Logger
) -> tuple[IConnection, IConnection] | None:
    """Setup and validate connections to server and client hosts.

    Creates SSH/local connections and validates connectivity before proceeding.

    Returns:
        Tuple of (server_conn, client_conn) or None on failure
    """
    logger.info(LogMsg.TRAFFIC_CONN_CREATE.value)
    logger.debug(f"Server: {cfg.server_host}, Client: {cfg.client_host}")

    server_conn = create_connection(cfg, IperfHostType.SERVER, logger)
    client_conn = create_connection(cfg, IperfHostType.CLIENT, logger)
    logger.debug("Connection objects created successfully")

    logger.info(LogMsg.CONN_CONNECTING.value)

    if not _connect_to_host(server_conn, cfg.server_host, IperfHostType.SERVER, logger):
        return None

    if not _connect_to_host(client_conn, cfg.client_host, IperfHostType.CLIENT, logger):
        logger.debug("Disconnecting server due to client connection failure")
        server_conn.disconnect()
        return None

    logger.info(LogMsg.CONN_ESTABLISHED.value)
    logger.debug("Both connections ready for iperf testing")

    return server_conn, client_conn


def _create_iperf_pair(
    server_conn: IConnection,
    client_conn: IConnection,
    server_ip: str,
    port: int,
    cfg: TrafficConfig,
    logger: logging.Logger,
    log_dir: Path,
) -> tuple[IperfServer, IperfClient] | None:
    """Create and configure iperf server/client pair.

    Returns:
        Tuple of (server, client) or None on failure
    """
    server = IperfServer(server_conn, logger, port, server_ip)
    client = IperfClient(client_conn, logger, port, server_ip)
    client.configure(
        duration=cfg.setup_traffic_duration_sec,
        protocol=cfg.setup_protocol,
        bandwidth=cfg.setup_bandwidth if cfg.setup_protocol == "udp" else None,
        parallel=cfg.setup_parallel_streams,
        interval=cfg.setup_stats_poll_sec,
    )

    if not IperfClient.validate_pair(server, client, server_ip, port, logger):
        return None

    return server, client


def _setup_forward_iperf(
    cfg: TrafficConfig,
    server_conn: IConnection,
    client_conn: IConnection,
    logger: logging.Logger,
    log_dir: Path,
) -> tuple[list[IperfServer], list[IperfClient]] | None:
    """Setup forward direction iperf instances (client -> server).

    Returns:
        Tuple of (servers, clients) or None on failure
    """
    servers, clients = [], []

    for idx, server_ip in enumerate(cfg.client_server_ips):
        port = cfg.client_start_port + idx
        logger.debug(f"Creating forward iperf on {server_ip}:{port}")

        pair = _create_iperf_pair(server_conn, client_conn, server_ip, port, cfg, logger, log_dir)
        if not pair:
            logger.error(LogMsg.CONN_FAILED.value)
            return None

        servers.append(pair[0])
        clients.append(pair[1])
        logger.debug(f"Forward setup complete for {server_ip}:{port}")

    return servers, clients


def _setup_reverse_iperf(
    cfg: TrafficConfig,
    server_conn: IConnection,
    client_conn: IConnection,
    num_forward: int,
    logger: logging.Logger,
    log_dir: Path,
) -> tuple[list[IperfServer], list[IperfClient]] | None:
    """Setup reverse direction iperf instances (server -> client).

    Returns:
        Tuple of (reverse_servers, reverse_clients) or None on failure
    """
    reverse_servers, reverse_clients = [], []

    for idx, reverse_ip in enumerate(cfg.server_server_ips):
        port = cfg.client_start_port + num_forward + idx
        logger.debug(f"Creating reverse iperf on {reverse_ip}:{port}")

        pair = _create_iperf_pair(client_conn, server_conn, reverse_ip, port, cfg, logger, log_dir)
        if not pair:
            logger.error(LogMsg.CONN_FAILED.value)
            return None

        reverse_servers.append(pair[0])
        reverse_clients.append(pair[1])
        logger.debug(f"Reverse setup complete for {reverse_ip}:{port}")

    return reverse_servers, reverse_clients


def setup_iperf(
    cfg: TrafficConfig,
    server_conn: IConnection,
    client_conn: IConnection,
    logger: logging.Logger,
    log_dir: Path,
) -> tuple[list[IperfServer], list[IperfClient], list[IperfServer], list[IperfClient]] | None:
    """Setup and validate iperf server and client instances.

    Creates multiple iperf instances for parallel testing across all server IPs.
    If reverse IPs configured, creates bidirectional traffic setup.

    Returns:
        Tuple of (servers, clients, reverse_servers, reverse_clients) or None on failure
    """
    logger.info(LogMsg.TRAFFIC_CONN_VALIDATE.value)

    forward = _setup_forward_iperf(cfg, server_conn, client_conn, logger, log_dir)
    if not forward:
        return None
    servers, clients = forward

    reverse_servers, reverse_clients = [], []
    if cfg.server_server_ips:
        reverse = _setup_reverse_iperf(cfg, server_conn, client_conn, len(servers), logger, log_dir)
        if not reverse:
            return None
        reverse_servers, reverse_clients = reverse

    logger.info(LogMsg.TRAFFIC_CONN_VALIDATE_PASS.value)
    return servers, clients, reverse_servers, reverse_clients


def kill_iperf_processes(conn, host_type: IperfHostType, logger: logging.Logger):
    """Kill all iperf processes on a host."""
    logger.info(f"Cleaning up iperf processes on {host_type}...")
    IperfBase.kill_all_processes(conn, logger)


def _stop_servers(servers: list[IperfServer], logger: logging.Logger) -> None:
    """Stop all iperf servers."""
    for server in servers:
        try:
            server.stop()
        except Exception as e:
            logger.exception(f"{LogMsg.TRAFFIC_SERVER_STOPP.value}: {e}")


def _disconnect_connection(conn: IConnection, conn_type: str, logger: logging.Logger) -> None:
    """Disconnect a single connection with error handling."""
    try:
        conn.disconnect()
    except Exception as e:
        msg = (
            LogMsg.TRAFFIC_CLIENT_DISCONNECT.value
            if conn_type == "client"
            else LogMsg.TRAFFIC_SERVER_DISCONNECT.value
        )
        logger.exception(f"{msg}: {e}")


def cleanup_resources(
    servers: list[IperfServer] | None,
    reverse_servers: list[IperfServer] | None,
    server_conn: IConnection,
    client_conn: IConnection,
    logger: logging.Logger,
) -> None:
    """Cleanup all resources."""
    logger.info(LogMsg.SHUTDOWN_START.value)

    kill_iperf_processes(server_conn, IperfHostType.SERVER, logger)
    kill_iperf_processes(client_conn, IperfHostType.CLIENT, logger)

    all_servers = (servers or []) + (reverse_servers or [])
    if all_servers:
        _stop_servers(all_servers, logger)

    _disconnect_connection(client_conn, "client", logger)
    _disconnect_connection(server_conn, "server", logger)


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
        total_bw = sum(s["bandwidth_avg_bps"] for s in summaries) / 1e9
        lines.append(f"Overall avg: {total_bw:.2f}Gbps")
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


def _parse_arguments() -> str:
    """Parse command line arguments.

    Returns:
        Config file path
    """
    parser = argparse.ArgumentParser(description="Iperf traffic testing with SSH")
    parser.add_argument(
        "--json",
        type=str,
        metavar="CONFIG",
        help="Config file (default: main_scan_traffic_cfg.json)",
    )
    args = parser.parse_args()
    return args.json or "main_scan_traffic_cfg.json"


def _initialize_logging(
    config_file: str, logger_name: str = LogName.TRAFFIC.value
) -> tuple[Path, datetime, logging.Logger]:
    """Initialize logging and create log directory.

    Returns:
        Tuple of (log_dir, start_time)
    """
    start_time = datetime.now()
    log_dir = Path("logs") / start_time.strftime("%Y%m%d_%H%M%S")
    log_dir.mkdir(parents=True, exist_ok=True)

    loggers = init_logging(config_file)
    logger = loggers[logger_name]

    return log_dir, start_time, logger


def _load_and_validate_config(logger: logging.Logger) -> TrafficConfig | None:
    """Load and validate configuration.

    Returns:
        Config object or None on failure
    """
    try:
        cfg = load_traffic_config(logger)
    except Exception:
        logger.exception(LogMsg.CONFIG_FAILED.value)
        return None

    logger.info(PrettyFrame().build("IPERF TRAFFIC", [LogMsg.TRAFFIC_TEST_START.value]))

    if not cfg.validate(logger):
        return None

    return cfg


def _prepare_csv_files(
    log_dir: Path, cfg: TrafficConfig, logger: logging.Logger
) -> tuple[Path, Path, Path]:
    """Prepare CSV files for statistics and metadata.

    Returns:
        Tuple of (stats_csv_file, metadata_csv_file, summary_csv_file)
    """
    stats_csv_file = log_dir / "traffic_stats.csv"
    metadata_csv_file = log_dir / "traffic_metadata.csv"
    summary_csv_file = log_dir / "traffic_summary.csv"

    write_metadata_to_csv(metadata_csv_file, cfg, logger)

    return stats_csv_file, metadata_csv_file, summary_csv_file


def _start_web_monitor(
    cfg: TrafficConfig,
    server_conn: IConnection,
    client_conn: IConnection,
    logger: logging.Logger,
    csv_file: Path,
    summary_csv_file: Path,
) -> IperfMonitor | None:
    """Start web monitor if enabled.

    Returns:
        Monitor instance or None if disabled
    """
    if not cfg.web_enabled:
        return None

    monitor = IperfMonitor(
        server_conn,
        client_conn,
        logger,
        cfg.web_port,
        shutdown_callback=lambda: shutdown_event.set(),
        server_host=cfg.server_host,
        client_host=cfg.client_host,
        csv_file=csv_file,
        summary_csv_file=summary_csv_file,
        poll_rate_ms=cfg.web_poll_rate_ms,
    )
    monitor.start()
    monitor.log("Iperf monitor started")
    return monitor


def _check_software_and_cleanup(
    servers: list,
    reverse_servers: list,
    server_conn: IConnection,
    client_conn: IConnection,
    logger: logging.Logger,
) -> bool:
    """Check required software and cleanup existing processes.

    Returns:
        True if successful, False otherwise
    """
    logger.info("Checking required software on server host...")
    if not servers[0].ensure_required_sw():
        logger.error("Required software not available on server host")
        return False
    logger.info("Cleaning up existing iperf processes on server host...")
    kill_iperf_processes(server_conn, IperfHostType.SERVER, logger)

    if reverse_servers:
        logger.info("Checking required software on client host...")
        if not reverse_servers[0].ensure_required_sw():
            logger.error("Required software not available on client host")
            return False
        logger.info("Cleaning up existing iperf processes on client host...")
        kill_iperf_processes(client_conn, IperfHostType.CLIENT, logger)

    return True


def _start_single_server(
    server: IperfServer,
    server_ip: str,
    direction: str,
    monitor: IperfMonitor | None,
) -> bool:
    """Start a single iperf server.

    Returns:
        True if started successfully, False otherwise
    """
    return server.start_with_logging(server_ip, direction, monitor)


def _start_iperf_servers(
    servers: list,
    reverse_servers: list,
    cfg: TrafficConfig,
    logger: logging.Logger,
    monitor: IperfMonitor | None,
) -> bool:
    """Start all iperf servers (forward and reverse).

    Returns:
        True if all servers started successfully, False otherwise
    """
    for idx, server in enumerate(servers):
        server_ip = cfg.client_server_ips[idx]
        if not _start_single_server(server, server_ip, "forward", monitor):
            return False

    if reverse_servers:
        for idx, server in enumerate(reverse_servers):
            reverse_ip = cfg.server_server_ips[idx]
            if not _start_single_server(server, reverse_ip, "reverse", monitor):
                return False

    time.sleep(2)
    logger.info("Servers verified listening via netstat - starting tests")
    return True


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
    config_file = _parse_arguments()
    log_dir, start_time, logger = _initialize_logging(config_file)

    cfg = _load_and_validate_config(logger)
    if not cfg:
        return

    conns = setup_connections(cfg, logger)
    if not conns:
        return
    server_conn, client_conn = conns

    iperf = setup_iperf(cfg, server_conn, client_conn, logger, log_dir)
    if not iperf:
        server_conn.disconnect()
        client_conn.disconnect()
        return
    servers, clients, reverse_servers, reverse_clients = iperf

    stats_csv_file, metadata_csv_file, summary_csv_file = _prepare_csv_files(log_dir, cfg, logger)

    monitor = _start_web_monitor(cfg, server_conn, client_conn, logger, stats_csv_file, summary_csv_file)

    summaries = []
    successful_tests = 0
    failed_tests = 0
    failed_iterations = []
    server_started = False

    try:
        if not _check_software_and_cleanup(
            servers, reverse_servers, server_conn, client_conn, logger
        ):
            return

        if not _start_iperf_servers(servers, reverse_servers, cfg, logger, monitor):
            return

        server_started = True

        # Start all clients once in background for infinite duration
        if monitor:
            monitor.log("Starting traffic clients...")
        for client in clients + reverse_clients:
            if shutdown_event.is_set():
                break
            client.start()

        logger.info("All clients started, traffic running...")
        if monitor:
            monitor.log("Traffic running - Monitor will show live process stats")

        # Wait until shutdown
        while not shutdown_event.is_set():
            time.sleep(1)

        summaries, successful_tests, failed_tests, failed_iterations = [], 0, 0, []

    finally:
        msg = LogMsg.TRAFFIC_SERVER_STOP.value
        logger.info(msg)
        if monitor:
            monitor.log(msg)
            monitor.log("Traffic testing completed")
            monitor.stop()
            time.sleep(1)

        cleanup_resources(
            servers if server_started else None,
            reverse_servers if server_started else None,
            server_conn,
            client_conn,
            logger,
        )

        if summaries:
            write_summary_to_csv(summaries, summary_csv_file, logger)

        print_final_summary(
            start_time,
            summaries,
            successful_tests,
            failed_tests,
            failed_iterations,
            stats_csv_file,
            summary_csv_file,
            logger,
        )


if __name__ == "__main__":
    main()
