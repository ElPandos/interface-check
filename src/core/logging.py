"""Custom logging formatter with dynamic width adjustment."""

import logging

# Standard log format used across all loggers
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class _WidthTracker:
    """Track maximum widths globally."""

    name_width = 0
    level_width = 0


class DynamicWidthFormatter(logging.Formatter):
    """Formatter with dynamic width that grows with longest string seen."""

    def __init__(
        self,
        logger_name: str,
        max_name_width: int | None = None,
        max_level_width: int | None = None,
    ):
        """Initialize formatter with dynamic width tracking.

        Args:
            logger_name: Logger name to determine initial width
            max_name_width: Override name width
            max_level_width: Override level width
        """
        super().__init__(LOG_FORMAT)
        self.name_width = max_name_width if max_name_width is not None else len(logger_name)
        self.level_width = max_level_width if max_level_width is not None else self.name_width

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with dynamic width.

        Args:
            record: Log record to format

        Returns:
            Formatted log string
        """
        # Update global maximums if current values are longer
        _WidthTracker.name_width = max(_WidthTracker.name_width, len(record.name), self.name_width)
        _WidthTracker.level_width = max(
            _WidthTracker.level_width, len(record.levelname), self.level_width
        )

        # Store original values
        original_name = record.name
        original_levelname = record.levelname

        # Pad to global maximum widths (left-aligned)
        record.name = f"{original_name:<{_WidthTracker.name_width}}"
        record.levelname = f"{original_levelname:<{_WidthTracker.level_width}}"

        result = super().format(record)

        # Restore original values
        record.name = original_name
        record.levelname = original_levelname

        return result


def create_formatter(
    logger_name: str, max_name_width: int | None = None, max_level_width: int | None = None
) -> DynamicWidthFormatter:
    """Create formatter for specific logger.

    Args:
        logger_name: Name of logger
        max_name_width: Override name width
        max_level_width: Override level width

    Returns:
        Configured formatter
    """
    return DynamicWidthFormatter(logger_name, max_name_width, max_level_width)
