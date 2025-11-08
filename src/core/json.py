"""JSON handling utility."""

from datetime import datetime as dt
import json
import logging
from pathlib import Path
from typing import Any

from nicegui import ui
from pydantic import SecretStr

from src.platform.enums.log import LogName

logger = logging.getLogger(LogName.MAIN.value)


class Json:
    """JSON operations with backup and error handling."""

    _DEFAULTS = {"indent": 2, "ensure_ascii": False}

    @staticmethod
    def _serializer(obj: Any) -> Any:
        if isinstance(obj, SecretStr):
            return obj.get_secret_value()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, dt):
            return obj.isoformat()
        raise TypeError(f"{type(obj).__name__} not JSON serializable")

    @classmethod
    def save(cls, data: Any, file_path: Path, *, create_backup: bool = False) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if create_backup and file_path.exists():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            file_path.rename(file_path.with_suffix(f".{timestamp}.bak"))

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, default=cls._serializer, **cls._DEFAULTS)

    @classmethod
    def load(cls, file_path: Path) -> dict[str, Any] | list[Any]:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def verify(cls, file_path: Path) -> bool:
        try:
            cls.load(file_path)
            return True
        except Exception:
            return False

    @classmethod
    def merge_files(cls, *file_paths: Path, output_path: Path) -> None:
        merged = []
        for path in file_paths:
            if path.exists():
                data = cls.load(path)
                merged.extend(data) if isinstance(data, list) else merged.append(data)
        cls.save(merged, output_path)

    @classmethod
    def dump_to_string(cls, data: Any, *, indent: int = 2) -> str:
        return json.dumps(data, default=cls._serializer, indent=indent, ensure_ascii=False)

    @classmethod
    def parse_string(cls, json_string: str) -> Any:
        return json.loads(json_string.strip())

    @classmethod
    def export_download(
        cls, data: Any, filename_prefix: str, *, success_message: str | None = None
    ) -> None:
        try:
            json_data = cls.dump_to_string(data)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.json"

            ui.download(json_data.encode("utf-8"), filename)
            ui.notify(success_message or f"Exported {filename}", color="positive")
        except Exception as e:
            ui.notify(f"Export failed: {e}", color="negative")

    @classmethod
    def backup_and_save(cls, data: Any, file_path: Path, *, max_backups: int = 5) -> None:
        if file_path.exists():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            file_path.rename(file_path.with_suffix(f".{timestamp}.bak"))
            cls._cleanup_backups(file_path, max_backups)
        cls.save(data, file_path)

    @classmethod
    def _cleanup_backups(cls, original_path: Path, max_backups: int) -> None:
        backups = list(original_path.parent.glob(f"{original_path.stem}.*.bak"))
        if len(backups) > max_backups:
            backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for old in backups[max_backups:]:
                old.unlink()
