"""JSON handling utility."""

from datetime import UTC, datetime as dt
import json
import logging
from pathlib import Path
from typing import Any

from pydantic import SecretStr

from src.platform.enums.log import LogName

logger = logging.getLogger(LogName.CORE_MAIN.value)


class Json:
    """JSON operations with backup and error handling."""

    _DEFAULTS = {"indent": 2, "ensure_ascii": False}

    @staticmethod
    def _serializer(obj: Any) -> Any:
        """Serialize special types to JSON-compatible formats.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation
        """
        if isinstance(obj, SecretStr):
            return obj.get_secret_value()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, dt):
            return obj.isoformat()
        raise TypeError(f"{type(obj).__name__} not JSON serializable")

    @classmethod
    def save(cls, data: Any, file_path: Path, *, create_backup: bool = False) -> None:
        """Save data to JSON file with optional backup.

        Args:
            data: Data to save
            file_path: Target file path
            create_backup: Create timestamped backup if file exists
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if create_backup and file_path.exists():
            timestamp = dt.now(UTC).strftime("%Y%m%d_%H%M%S")
            file_path.rename(file_path.with_suffix(f".{timestamp}.bak"))

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, default=cls._serializer, **cls._DEFAULTS)

    @classmethod
    def load(cls, file_path: Path) -> dict[str, Any] | list[Any]:
        """Load data from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Loaded data as dict or list
        """
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def verify(cls, file_path: Path) -> bool:
        """Verify JSON file is valid.

        Args:
            file_path: Path to JSON file

        Returns:
            True if valid JSON, False otherwise
        """
        try:
            cls.load(file_path)
            return True
        except Exception:
            return False

    @classmethod
    def merge_files(cls, *file_paths: Path, output_path: Path) -> None:
        """Merge multiple JSON files into one.

        Args:
            file_paths: Paths to JSON files to merge
            output_path: Output file path
        """
        merged = []
        for path in file_paths:
            if path.exists():
                data = cls.load(path)
                merged.extend(data) if isinstance(data, list) else merged.append(data)
        cls.save(merged, output_path)

    @classmethod
    def dump_to_string(cls, data: Any, *, indent: int = 2) -> str:
        """Convert data to JSON string.

        Args:
            data: Data to convert
            indent: Indentation spaces

        Returns:
            JSON string
        """
        return json.dumps(data, default=cls._serializer, indent=indent, ensure_ascii=False)

    @classmethod
    def parse_string(cls, json_string: str) -> Any:
        """Parse JSON string to data.

        Args:
            json_string: JSON string to parse

        Returns:
            Parsed data
        """
        return json.loads(json_string.strip())



    @classmethod
    def backup_and_save(cls, data: Any, file_path: Path, *, max_backups: int = 5) -> None:
        """Save data with automatic backup rotation.

        Args:
            data: Data to save
            file_path: Target file path
            max_backups: Maximum number of backups to keep
        """
        if file_path.exists():
            timestamp = dt.now(UTC).strftime("%Y%m%d_%H%M%S")
            file_path.rename(file_path.with_suffix(f".{timestamp}.bak"))
            cls._cleanup_backups(file_path, max_backups)
        cls.save(data, file_path)

    @classmethod
    def _cleanup_backups(cls, original_path: Path, max_backups: int) -> None:
        """Remove old backup files exceeding max count.

        Args:
            original_path: Original file path
            max_backups: Maximum backups to retain
        """
        backups = list(original_path.parent.glob(f"{original_path.stem}.*.bak"))
        if len(backups) > max_backups:
            backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for old in backups[max_backups:]:
                old.unlink()
