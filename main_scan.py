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
from src.core.log.setup import init_logging
from src.core.scanner import SlxScanner, SutScanner
from src.platform.enums.log import LogName

# ---------------------------------------------------------------------------- #
#                          Graceful shutdown handling                          #
# ---------------------------------------------------------------------------- #

# Global event for coordinating graceful shutdown across all threads
shutdown_event = threading.Event()


def signal_handler(_signum, _frame) -> None:
    """Handle Ctrl+C signal for graceful shutdown.

    Sets shutdown event to trigger cleanup in finally block.
    """
    frame = PrettyFrame()
    msg = frame.build("SHUTDOWN SIGNAL", ["Ctrl+C pressed. Shutting down gracefully..."])
    sys.stderr.write(msg)
    shutdown_event.set()


# Register signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

# ---------------------------------------------------------------------------- #
#                             Logging configuration                            #
# ---------------------------------------------------------------------------- #

loggers = init_logging()

main_logger = loggers[LogName.MAIN.value]
sut_system_info_logger = loggers[LogName.SUT_SYSTEM_INFO.value]
sut_mxlink_logger = loggers[LogName.SUT_MXLINK.value]
sut_mxlink_amber_logger = loggers[LogName.SUT_MXLINK_AMBER.value]
sut_mtemp_logger = loggers[LogName.SUT_MTEMP.value]
sut_ethtool_logger = loggers[LogName.SUT_ETHTOOL.value]
sut_link_flap_logger = loggers[LogName.SUT_LINK_FLAP.value]
slx_eye_logger = loggers[LogName.SLX_EYE.value]
slx_dsc_logger = loggers[LogName.SLX_DSC.value]

# ---------------------------------------------------------------------------- #
#                                  JSON config                                 #
# ---------------------------------------------------------------------------- #


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
    slx_port_toggle_limit: int
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
    worker_collect: bool

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
            slx_port_toggle_limit=slx["port_toggle_limit"],
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
            worker_collect=data.get("worker_collect", False),
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


# ---------------------------------------------------------------------------- #
#                                MAIN function                                 #
# ---------------------------------------------------------------------------- #


def main():  # noqa: PLR0915
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

    sut_scanner = SutScanner(cfg, main_logger, shutdown_event, loggers)
    slx_scanner = SlxScanner(
        cfg,
        main_logger,
        shutdown_event,
        loggers,
        sut_scanner.worker_manager.get_shared_flap_state(),
    )

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
    #                                 Stop workers                                 #
    # ---------------------------------------------------------------------------- #

    # Log shutdown signal
    _logger.info(LogMsg.SHUTDOWN_SIGNAL.value)

    _logger.info(LogMsg.WORKER_SHUTDOWN.value)

    # Pause logging and show worker shutdown countdown
    sut_workers = sut_scanner.worker_manager.get_workers_in_pool()
    slx_workers = slx_scanner.worker_manager.get_workers_in_pool()
    all_workers = sut_workers + slx_workers
    total_workers = len(all_workers)

    frame = PrettyFrame()
    _logger.info(frame.build("WORKER SHUTDOWN", [f"Total workers: {total_workers}", "---"]))

    logging.disable(logging.CRITICAL)

    for idx, w in enumerate(all_workers, 1):
        w.close()
        sys.stderr.write(f"\rStopping workers: {idx}/{total_workers}")
        sys.stderr.flush()

    sys.stderr.write("\n")
    for idx, w in enumerate(all_workers, 1):
        w.join()
        sys.stderr.write(f"\rWaiting for workers: {idx}/{total_workers}")
        sys.stderr.flush()

    sys.stderr.write("\n")
    logging.disable(logging.NOTSET)

    frame = PrettyFrame()
    _logger.info(
        frame.build("WORKERS STOPPED", [f"All {total_workers} workers stopped successfully"])
    )

    # ---------------------------------------------------------------------------- #
    #                                   Shutdown                                   #
    # ---------------------------------------------------------------------------- #

    frame = PrettyFrame()
    shutdown_msg = frame.build("SHUTDOWN", ["Starting disconnect sequence..."])
    _logger.info(shutdown_msg)

    _logger.info(LogMsg.SHUTDOWN_SLX_SCANNER.value)
    slx_scanner.disconnect()
    _logger.debug(LogMsg.SHUTDOWN_COMPLETE.value)

    _logger.debug(LogMsg.SHUTDOWN_SUT_SCANNER.value)
    sut_scanner.disconnect()
    _logger.debug(LogMsg.SHUTDOWN_COMPLETE.value)

    # ---------------------------------------------------------------------------- #
    #                              Collected Data Summary                          #
    # ---------------------------------------------------------------------------- #

    summary_lines = []

    # SLX Scanner results
    total_scans = slx_scanner.scans_collected()
    if cfg.worker_collect:
        summary_lines.append(f"SLX scans: {total_scans} (~{total_scans * 10}KB)")
    else:
        summary_lines.append("SLX scans: 0 (worker_collect=false)")

    # SUT Worker samples
    total_samples = 0
    for worker in sut_workers:
        sample_count = len(worker.get_extracted_samples())
        total_samples += sample_count
        summary_lines.append(f"{worker.name}: {sample_count} samples")
    summary_lines.append(f"Total SUT: {total_samples} samples (~{total_samples * 5}KB)")

    data_summary = frame.build("COLLECTED DATA", summary_lines)
    _logger.info(data_summary)

    # ---------------------------------------------------------------------------- #
    #                                  Statistics                                  #
    # ---------------------------------------------------------------------------- #

    _logger.info(LogMsg.SHUTDOWN_TOTAL_COMPLETED.value)
    _logger.info(LogMsg.MAIN_LOGS_SAVED.value)

    stats_summary = sut_scanner.worker_manager.get_statistics_summary()
    _logger.info(stats_summary)


if __name__ == "__main__":
    main()
