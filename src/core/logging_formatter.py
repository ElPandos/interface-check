"""Custom logging formatter with dynamic width adjustment."""

import logging


class DynamicWidthFormatter(logging.Formatter):
    """Formatter that adjusts logger name and level width to longest seen."""
    
    max_name_len = 0
    max_level_len = 0
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with dynamic width adjustment.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        # Update max length if current name is longer
        current_name_len = len(record.name)
        if current_name_len > DynamicWidthFormatter.max_name_len:
            DynamicWidthFormatter.max_name_len = current_name_len
        
        # Update max length if current level is longer
        current_level_len = len(record.levelname)
        if current_level_len > DynamicWidthFormatter.max_level_len:
            DynamicWidthFormatter.max_level_len = current_level_len
        
        # Pad name and level to current max lengths
        record.name = f"{record.name:<{DynamicWidthFormatter.max_name_len}}"
        record.levelname = f"{record.levelname:<{DynamicWidthFormatter.max_level_len}}"
        
        return super().format(record)
