#!/usr/bin/env python3
"""SLX Eye Scan Automation with SUT System Monitoring.

This script provides automated eye scan execution on SLX switches while
simultaneously monitoring system metrics on the SUT (System Under Test).

Features:
- Automated eye scans on SLX switch ports with configurable intervals
- Optional port toggling before scans
- Concurrent SUT system monitoring (mlxlink, temperature, etc.)
- Multi-hop SSH connections through jump hosts
- Graceful shutdown on Ctrl+C
- Comprehensive logging to separate log files

Usage:
    python main_scan.py

Configuration:
    Edit main_scan_cfg.json to configure:
    - Jump host and target host credentials
    - SLX scan ports and intervals
    - SUT interfaces and scan intervals
    - Port toggling settings
"""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import signal
import sys
import threading
import time

from src.core.cli import PrettyFrame
from src.core.enums.connect import ConnectType, ShowPartType
from src.core.enums.messages import LogMsg
from src.core.helpers import get_attr_value
from src.core.logging_setup import initialize_logging
from src.core.parser import SutDmesgFlapParser
from src.core.scanner import SlxScanner, SutScanner

# ============================================================================
# Graceful Shutdown Handling
# ============================================================================

# Global event for coordinating graceful shutdown across all threads
shutdown_event = threading.Event()


def signal_handler(_signum, _frame) -> None:
    """Handle Ctrl+C signal for graceful shutdown.

    Sets shutdown event to trigger cleanup in finally block.
    """
    frame = PrettyFrame()
    msg = frame.build("SHUTDOWN SIGNAL", ["Ctrl+C pressed. Shutting down gracefully..."])
    sys.stderr.write(f"\n{msg}\n")
    shutdown_event.set()


# Register signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

# ============================================================================
# Logging Configuration
# ============================================================================

loggers = initialize_logging()
main_logger = loggers["main"]
sut_system_info_logger = loggers["sut_system_info"]
sut_mxlink_logger = loggers["sut_mxlink"]
sut_mxlink_amber_logger = loggers["sut_mxlink_amber"]
sut_mtemp_logger = loggers["sut_mtemp"]
sut_ethtool_logger = loggers["sut_ethtool"]
sut_link_flap_logger = loggers["sut_link_flap"]
slx_eye_logger = loggers["slx_eye"]
slx_dsc_logger = loggers["slx_dsc"]
log_dir = loggers["log_dir"]


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from JSON.

    Contains all settings for:
    - Jump host connection
    - SLX switch connection and scan settings
    - SUT system connection and monitoring settings

    Attributes:
        jump_host/user/pass: Jump host credentials
        slx_*: SLX switch settings (host, ports, intervals, toggling)
        sut_*: SUT system settings (host, interfaces, packages, intervals)
    """

    log_level: str

    jump_host: str
    jump_user: str
    jump_pass: str

    slx_host: str
    slx_user: str
    slx_pass: str
    slx_sudo_pass: str
    slx_scan_ports: list[str]
    slx_scan_interval_sec: int
    slx_port_toggle_enabled: bool
    slx_port_toggle_wait_sec: int
    slx_port_eyescan_wait_sec: int

    sut_host: str
    sut_user: str
    sut_pass: str
    sut_sudo_pass: str
    sut_scan_interfaces: list[str]
    sut_connect_type: ConnectType
    sut_show_parts: list[ShowPartType]
    sut_time_cmd: bool
    sut_required_software_packages: list[str]
    sut_scan_interval_low_res_ms: int
    sut_scan_interval_high_res_ms: int
    sut_scan_max_log_size_kb: int

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from nested JSON structure.

        Args:
            data: Dictionary with jump, slx, and sut configuration sections

        Returns:
            Config: Configured Config instance
        """
        j, slx, sut = data["jump"], data["slx"], data["sut"]
        return cls(
            log_level=data.get("log_level", "info"),
            jump_host=j["host"],
            jump_user=j["user"],
            jump_pass=j["pass"],
            slx_host=slx["host"],
            slx_user=slx["user"],
            slx_pass=slx["pass"],
            slx_sudo_pass=slx["sudo_pass"],
            slx_scan_ports=slx["scan_ports"],
            slx_scan_interval_sec=slx["scan_interval_sec"],
            slx_port_toggle_enabled=slx["port_toggling_enabled"],
            slx_port_toggle_wait_sec=slx["port_toggle_wait_sec"],
            slx_port_eyescan_wait_sec=slx["port_eye_scan_wait_sec"],
            sut_host=sut["host"],
            sut_user=sut["user"],
            sut_pass=sut["pass"],
            sut_sudo_pass=sut["sudo_pass"],
            sut_scan_interfaces=sut["scan_interfaces"],
            sut_connect_type=ConnectType(sut.get("connect_type", "local")),
            sut_show_parts=[ShowPartType(p) for p in sut.get("show_parts", [])],
            sut_time_cmd=sut.get("time_cmd", False),
            sut_required_software_packages=sut["required_software_packages"],
            sut_scan_interval_low_res_ms=sut["scan_interval_low_res_ms"],
            sut_scan_interval_high_res_ms=sut["scan_interval_high_res_ms"],
            sut_scan_max_log_size_kb=sut["scan_max_log_size_kb"],
        )


def load_cfg(logger: logging.Logger) -> Config:
    """Load configuration from JSON file.

    Args:
        logger: Logger instance for error reporting

    Returns:
        Config: Loaded configuration

    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file has invalid JSON
    """
    logger.debug(LogMsg.CONFIG_START)

    cfg_name = "main_scan_cfg.json"
    # Handle PyInstaller bundled executable
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        config_file = Path(sys.executable).parent / cfg_name
    else:
        # Running as script
        config_file = Path(__file__).parent / cfg_name
    try:
        with config_file.open() as f:
            data = json.load(f)

        logger.info(LogMsg.CONFIG_LOADED.value)

        return Config.from_dict(data)
    except FileNotFoundError:
        logger.exception(f"{LogMsg.MAIN_CONFIG_NOT_FOUND.value}: {config_file}")
        logger.exception(LogMsg.MAIN_CONFIG_SAME_DIR.value)
        raise
    except json.JSONDecodeError:
        logger.exception(LogMsg.MAIN_CONFIG_INVALID_JSON.value)
        raise


def check_cfg(cfg: Config, logger: logging.Logger) -> bool:
    """Validate configuration for SLX scanner requirements.

    Args:
        cfg: Configuration to validate
        logger: Logger for error messages

    Returns:
        bool: True if valid, False otherwise
    """
    no_eye = ShowPartType.NO_SLX_EYE in cfg.sut_show_parts
    no_dsc = ShowPartType.NO_SLX_DSC in cfg.sut_show_parts

    if not no_eye and not no_dsc:
        logger.error(
            f"Neither '{ShowPartType.NO_SLX_EYE.value}' or '{ShowPartType.NO_SLX_DSC.value}' is set"
        )
        logger.error("Only one of the SLX scanner can be enabled at a time. Exiting...")
        return False

    return True


def main():  # noqa: PLR0912, PLR0915
    """Main execution orchestrating SUT monitoring and SLX eye scans.

    Execution flow:
    1. Load configuration from JSON
    2. Initialize and connect SUT system scanner
    3. Start SUT metric collection workers
    4. Initialize and connect SLX eye scanner
    5. Run continuous eye scan loop until Ctrl+C
    6. Extract and log collected samples
    7. Graceful shutdown of all components

    The function runs until interrupted by Ctrl+C, at which point it
    performs graceful shutdown of all threads and connections.
    """
    _logger = main_logger

    try:
        cfg = load_cfg(_logger)
        _logger.debug(f"SLX host: {cfg.slx_host}, SUT host: {cfg.sut_host}")
    except Exception:
        _logger.exception(LogMsg.CONFIG_FAILED.value)
        return

    if not check_cfg(cfg, _logger):
        return

    _logger.info(LogMsg.SCANNER_INIT.value)

    slx_scanner = SlxScanner(cfg, main_logger, shutdown_event, loggers)
    sut_scanner = SutScanner(cfg, main_logger, shutdown_event, loggers)

    # ---------------------------------------------------------------------------- #
    #                                  SUT scanner                                 #
    # ---------------------------------------------------------------------------- #

    try:
        sut_scanner.run()
    except Exception:
        _logger.exception(LogMsg.MAIN_SCANNER_FAILED.value)

    # ---------------------------------------------------------------------------- #
    #                                  SLX scanner                                 #
    # ---------------------------------------------------------------------------- #

    try:
        slx_scanner.run()
    except Exception:
        _logger.exception(LogMsg.MAIN_EXEC_FAILED.value)

    # ---------------------------------------------------------------------------- #
    #                                   MAIN loop                                  #
    # ---------------------------------------------------------------------------- #

    _logger.info("Main loop: waiting for shutdown signal...")
    while not shutdown_event.is_set():
        time.sleep(1)

    # ---------------------------------------------------------------------------- #
    #                                   FINISHED                                   #
    # ---------------------------------------------------------------------------- #

    # Log shutdown signal
    _logger.info(LogMsg.SHUTDOWN_SIGNAL.value)

    # Pause logging and show worker shutdown countdown
    logging.disable(logging.CRITICAL)
    sys.stderr.write("\nWaiting for all threads to complete...\n")

    sut_workers = sut_scanner.worker_manager.get_workers_in_pool()
    slx_workers = slx_scanner.worker_manager.get_workers_in_pool()
    all_workers = sut_workers + slx_workers
    total_workers = len(all_workers)
    sys.stderr.write(f"\nStopping {total_workers} workers...\n")

    for idx, w in enumerate(all_workers, 1):
        w.close()
        sys.stderr.write(f"\rWorkers stopped: {idx}/{total_workers}")
        sys.stderr.flush()

    sys.stderr.write("\n\nWaiting for workers to finish...\n")
    for idx, w in enumerate(all_workers, 1):
        w.join()
        sys.stderr.write(f"\rWorkers finished: {idx}/{total_workers}")
        sys.stderr.flush()

    sys.stderr.write("\n")
    logging.disable(logging.NOTSET)

    frame = PrettyFrame()
    shutdown_msg = frame.build("SHUTDOWN", ["Starting shutdown sequence..."])
    _logger.info(f"\n{shutdown_msg}")

    _logger.info(LogMsg.SHUTDOWN_EYE_SCANNER.value)
    slx_scanner.disconnect()
    _logger.debug(LogMsg.MAIN_EYE_DISCONNECTED.value)

    _logger.info(LogMsg.WORKER_EXTRACT.value)
    workers = sut_scanner.worker_manager.get_workers_in_pool()
    _logger.debug(f"Found {len(workers)} workers to extract samples from")
    for w in workers:
        w.extract_all_samples()

    # Build matrix with smallest list determining rows
    all_samples = [w.get_extracted_samples() for w in workers]
    min_rows = min(len(samples) for samples in all_samples) if all_samples else 0

    if min_rows > 0:
        # CSV headers - begin_timestamp first
        headers = [
            "begin_timestamp",
            "temperature",
            "voltage",
            "bias_current",
            "rx_power",
            "tx_power",
            "time_since_last_clear",
            "effective_physical_errors",
            "effective_physical_ber",
            "raw_physical_errors_per_lane",
            "raw_physical_ber",
            "m_temp_nic",
            "link_status",
            "link_status_timestamp",
        ]
        headers_str = [",".join(headers)]

        # mlxlink attributes (excluding begin - we add it first)
        mlxlink_attrs = [
            "temperature",
            "voltage",
            "bias_current",
            "rx_power",
            "tx_power",
            "time_since_last_clear",
            "effective_physical_errors",
            "effective_physical_ber",
            "raw_physical_errors_per_lane",
            "raw_physical_ber",
        ]

        for i in range(min_rows):
            row = []
            for worker_idx, samples in enumerate(all_samples):
                sample = samples[i]
                if worker_idx == 0:  # Worker 1: mlxlink
                    # Add begin timestamp first (from Sample, not snapshot)
                    # Format: YYYY-MM-DD HH:MM:SS.mmm
                    timestamp = (
                        sample.begin.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if sample.begin else ""
                    )
                    row.append(timestamp)
                    # Add all other mlxlink metrics
                    row.extend(get_attr_value(sample.snapshot, attr) for attr in mlxlink_attrs)
                elif worker_idx == 1:  # Worker 2: NIC temp
                    row.append(str(sample.snapshot) if hasattr(sample, "snapshot") else "")
                elif worker_idx == 2:  # Worker 3: dmesg link status
                    dmesg_output = str(sample.snapshot) if hasattr(sample, "snapshot") else ""
                    parser = SutDmesgFlapParser(dmesg_output)
                    link_status, link_ts = parser.get_most_recent_status()
                    row.extend([link_status, link_ts])
            headers_str.append(",".join(row))

    _logger.info(LogMsg.WORKER_SHUTDOWN.value)

    _logger.debug(LogMsg.MAIN_SCANNER_DISCONNECT.value)
    sut_scanner.disconnect()

    stats_summary = sut_scanner.worker_manager.get_statistics_summary()
    _logger.info(f"\n{stats_summary}")

    _logger.info(f"Total eye scans completed: {slx_scanner.scans_collected()}")
    _logger.info(LogMsg.MAIN_SHUTDOWN_COMPLETE.value)
    _logger.info(LogMsg.MAIN_LOGS_SAVED.value)


if __name__ == "__main__":
    main()
