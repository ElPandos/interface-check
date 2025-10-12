"""Centralized JSON handling utility for all JSON operations."""

from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from typing import Any

from nicegui import ui
from pydantic import SecretStr

logger = logging.getLogger(__name__)


class Json:
    """Centralized JSON operations handler with validation, backup, and error handling."""

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Custom JSON serializer for special types."""
        if isinstance(obj, SecretStr):
            return obj.get_secret_value()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    @classmethod
    def save(cls, data: Any, file_path: Path, *, create_backup: bool = False) -> None:
        """Save data to JSON file with optional backup.

        Args:
            data: Data to save
            file_path: Target file path
            create_backup: Whether to backup existing file
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if requested and file exists
            if create_backup and file_path.exists():
                timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f".{timestamp}.bak")
                file_path.rename(backup_path)
                logger.info(f"Backup created: {backup_path}")

            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=cls._json_serializer)

            logger.debug(f"JSON saved to: {file_path}")

        except Exception as e:
            logger.exception(f"Failed to save JSON to {file_path}")
            raise RuntimeError(f"JSON save failed: {e}") from e

    @classmethod
    def load(cls, file_path: Path) -> dict[str, Any] | list[Any]:
        """Load data from JSON file.

        Args:
            file_path: Source file path

        Returns:
            Loaded JSON data
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"JSON file not found: {file_path}")

            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            logger.debug(f"JSON loaded from: {file_path}")
            return data

        except json.JSONDecodeError as e:
            logger.exception(f"Invalid JSON in {file_path}")
            raise ValueError(f"Invalid JSON format: {e}") from e
        except Exception as e:
            logger.exception(f"Failed to load JSON from {file_path}")
            raise RuntimeError(f"JSON load failed: {e}") from e

    @classmethod
    def verify(cls, file_path: Path) -> bool:
        """Verify if file contains valid JSON.

        Args:
            file_path: File to verify

        Returns:
            True if valid JSON, False otherwise
        """
        try:
            cls.load(file_path)
            return True
        except (FileNotFoundError, ValueError, RuntimeError):
            return False

    @classmethod
    def merge_files(cls, *file_paths: Path, output_path: Path) -> None:
        """Merge multiple JSON files into one.

        Args:
            *file_paths: Input JSON files to merge
            output_path: Output file path
        """
        try:
            merged_data = []

            for file_path in file_paths:
                if file_path.exists():
                    data = cls.load(file_path)
                    if isinstance(data, list):
                        merged_data.extend(data)
                    else:
                        merged_data.append(data)

            cls.save(merged_data, output_path)
            logger.info(f"Merged {len(file_paths)} files into {output_path}")

        except Exception as e:
            logger.exception("Failed to merge JSON files")
            raise RuntimeError(f"JSON merge failed: {e}") from e

    @classmethod
    def dump_to_string(cls, data: Any, *, indent: int = 2) -> str:
        """Convert data to JSON string.

        Args:
            data: Data to convert
            indent: JSON indentation

        Returns:
            JSON string
        """
        try:
            return json.dumps(data, indent=indent, ensure_ascii=False, default=cls._json_serializer)
        except Exception as e:
            logger.exception("Failed to dump JSON to string")
            raise ValueError(f"JSON dump failed: {e}") from e

    @classmethod
    def parse_string(cls, json_string: str) -> Any:
        """Parse JSON string to data.

        Args:
            json_string: JSON string to parse

        Returns:
            Parsed data
        """
        try:
            return json.loads(json_string.strip())
        except json.JSONDecodeError as e:
            logger.exception("Failed to parse JSON string")
            raise ValueError(f"Invalid JSON string: {e}") from e

    @classmethod
    def export_download(cls, data: Any, filename_prefix: str, *, success_message: str | None = None) -> None:
        """Export data as downloadable JSON file with timestamp.

        Args:
            data: Data to export
            filename_prefix: Prefix for filename
            success_message: Optional success message
        """
        try:
            json_data = cls.dump_to_string(data)
            timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.json"

            ui.download(json_data.encode("utf-8"), filename)

            message = success_message or f"Data exported to {filename}"
            ui.notify(message, color="positive")

        except Exception as e:
            ui.notify(f"Export failed: {e}", color="negative")
            logger.exception("Failed to export JSON data")

    @classmethod
    def backup_and_save(cls, data: Any, file_path: Path, *, max_backups: int = 5) -> None:
        """Save with automatic backup rotation.

        Args:
            data: Data to save
            file_path: Target file path
            max_backups: Maximum number of backups to keep
        """
        try:
            # Create backup if file exists
            if file_path.exists():
                timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
                backup_path = file_path.with_suffix(f".{timestamp}.bak")
                file_path.rename(backup_path)

                # Clean old backups
                cls._cleanup_backups(file_path, max_backups)

            cls.save(data, file_path)

        except Exception as e:
            logger.exception(f"Failed to backup and save {file_path}")
            raise RuntimeError(f"Backup and save failed: {e}") from e

    @classmethod
    def _cleanup_backups(cls, original_path: Path, max_backups: int) -> None:
        """Clean up old backup files."""
        try:
            backup_pattern = f"{original_path.stem}.*.bak"
            backup_files = list(original_path.parent.glob(backup_pattern))

            if len(backup_files) > max_backups:
                # Sort by modification time, keep newest
                backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                for old_backup in backup_files[max_backups:]:
                    old_backup.unlink()
                    logger.debug(f"Removed old backup: {old_backup}")

        except Exception:
            logger.exception("Failed to cleanup old backups")
