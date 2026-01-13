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

import logging
import signal
import sys
import threading
import time

from src.core.cli import PrettyFrame
from src.core.config import load_scan_config
from src.core.enum.messages import LogMsg
from src.core.log.setup import init_logging
from src.core.scanner import SlxScanner, SutScanner
from src.platform.enums.log import LogName

# ---------------------------------------------------------------------------- #
#                          Graceful shutdown handling                          #
# ---------------------------------------------------------------------------- #

# Global event for coordinating graceful shutdown across all threads
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

loggers = init_logging()

main_logger = loggers[LogName.MAIN.value]
sut_system_info_logger = loggers[LogName.SUT_SYSTEM_INFO.value]
sut_mxlink_logger = loggers[LogName.SUT_MXLINK.value]
sut_mxlink_amber_logger = loggers[LogName.SUT_MXLINK_AMBER.value]
sut_mtemp_logger = loggers[LogName.SUT_MTEMP.value]
sut_ethtool_logger = loggers[LogName.SUT_ETHTOOL.value]
sut_link_flap_logger = loggers[LogName.SUT_LINK_FLAP.value]
sut_tx_errors_logger = loggers[LogName.SUT_TX_ERRORS.value]
sut_ipmitool_fan_logger = loggers[LogName.SUT_IPMITOOL_FAN.value]
slx_eye_logger = loggers[LogName.SLX_EYE.value]
slx_dsc_logger = loggers[LogName.SLX_DSC.value]

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
        cfg = load_scan_config(_logger)
        _logger.debug(f"SLX host: {cfg.slx_host}, SUT host: {cfg.sut_host}")
    except Exception:
        _logger.exception(LogMsg.CONFIG_FAILED.value)
        return

    if not cfg.validate(_logger):
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

    # Print shutdown message after signal detected
    if _shutdown_triggered:
        frame = PrettyFrame()
        msg = frame.build("SHUTDOWN SIGNAL", ["Ctrl+C pressed. Shutting down gracefully..."])
        sys.stderr.write(msg)
        sys.stderr.flush()

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
    _logger.info(frame.build("WORKERS STOPPED", [f"All {total_workers} workers stopped successfully"]))

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

    _logger.info(LogMsg.SHUTDOWN_ALL_COMPLETED.value)
    _logger.info(LogMsg.MAIN_LOGS_SAVED.value)

    stats_summary = sut_scanner.worker_manager.get_statistics_summary()
    _logger.info(stats_summary)


if __name__ == "__main__":
    main()
