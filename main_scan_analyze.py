"""Analyze log data and generate visualization graphs."""

import logging

from src.core.analyze import AnalyzeGraphs
from src.core.helpers import get_latest_log_dir
from src.core.log.formatter import create_formatter
from src.platform.enums.log import LogName

main_logger = logging.getLogger(LogName.MAIN.value)
main_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(create_formatter(LogName.MAIN.value))
main_logger.addHandler(console_handler)


def main() -> None:
    """Run log analysis on latest log directory."""
    latest_folder = get_latest_log_dir()
    analyzer = AnalyzeGraphs(latest_folder, main_logger)
    analyzer.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        main_logger.info("Analysis interrupted by user")
    except Exception:
        main_logger.exception("Analysis failed")
