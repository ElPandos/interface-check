from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pprint
import re
import subprocess
import sys
import tkinter as tk
from typing import Any

import pandas as pd

from src.utils.commands import Git, Python
from src.utils.process_manager import ProcessManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------- #
#                                  Command I/O                                 #
# ---------------------------------------------------------------------------- #


def run_command(command: list[str], *, fail_ok: bool = False) -> str:
    if not command or not all(isinstance(arg, str) for arg in command):
        msg = "Command must be a non-empty list of strings"
        raise ValueError(msg)

    # Input is validated above - command is list of strings, shell=False prevents injection
    result = subprocess.run(  # noqa: S603
        command, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=False
    )

    if result.returncode != 0:
        if fail_ok:
            logger.warning(f"Command failed but will continue: {' '.join(command)}")
        else:
            raise RuntimeError(f"Command failed: {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    logger.info(result.stdout)
    return result.stdout


# ---------------------------------------------------------------------------- #
#                                     PATH                                     #
# ---------------------------------------------------------------------------- #


def set_python_path(full_path: Path) -> None:
    if not full_path or not str(full_path).strip():
        logger.warning("PYTHONPATH is empty - nothing was added to sys.path")
        return

    base_dir = full_path.parent
    target_dir = base_dir.resolve()

    try:
        exist_dir(target_dir)
    except FileNotFoundError:
        logger.exception("PYTHONPATH directory was not found")
        raise

    target_dir_str = str(target_dir)
    if target_dir_str in sys.path:
        logger.debug("PYTHONPATH was found in sys.path. Will not add again")
        return

    sys.path.insert(0, target_dir_str)
    logger.debug(f"Added '{target_dir_str}' to the beginning of sys.path")


# ---------------------------------------------------------------------------- #
#                                     File                                     #
# ---------------------------------------------------------------------------- #


def exist_file(full_path: Path) -> None:
    if full_path.exists():
        logger.debug(f"File was found: {full_path}")
        return
    raise FileNotFoundError(f"File was not found: {full_path}")


# ---------------------------------------------------------------------------- #
#                                   Directory                                  #
# ---------------------------------------------------------------------------- #


def exist_dir(dir_path: Path) -> None:
    if dir_path.exists():
        logger.debug(f"Folder was found: {dir_path}")
    else:
        raise FileNotFoundError(f"Folder was not found: {dir_path}")


def create_dir(dir_path: Path) -> None:
    if not dir_path.exists():
        logger.warning(f"Folder was not found. Creating it: {dir_path}")
        dir_path.mkdir(parents=True, exist_ok=True)
    else:
        logger.debug(f"Folder was found: {dir_path}")


# ---------------------------------------------------------------------------- #
#                                     JSON                                     #
# ---------------------------------------------------------------------------- #


def save_json(config: Any, full_path: Path) -> None:
    # Ensure the parent directory exists
    create_dir(full_path.parent)

    with full_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_json(full_path: Path) -> dict[str, Any] | list[Any]:
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {full_path}")

    with full_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_lists_to_file(list1: list[Any], list2: list[Any], config_path: Path, file_name: str) -> None:
    """
    Safely dump two lists into a JSON file.
    If the file already exists, it is renamed with a timestamp before writing.

    Args:
        list1: First list of data.
        list2: Second list of data.
        config_path: Directory path where the file will be created.
        file_name: Name of the output file.
    """
    try:
        # Ensure parent directories exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        full_path = config_path / file_name

        # Check if file exists and back it up
        if full_path.exists():
            timestamp = datetime.now(tz=datetime.UTC).strftime("%Y%m%d_%H%M%S")
            backup_path = full_path.with_suffix(f".{timestamp}")
            full_path.rename(backup_path)
            logger.info(f"Existing file renamed to backup: {backup_path}")

        # Prepare the data structure
        data = {
            "x": list1,
            "y": list2,
            "created_at": datetime.now(tz=datetime.UTC).isoformat(),
        }

        # Write to JSON file with indentation for readability
        with full_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully wrote data to: {full_path}")

    except Exception as e:
        logger.exception(f"Failed to dump lists to file '{full_path}'")


def merge_lists_from_base_and_backups(base_file: str) -> Path:
    """
    Merge lists from the base JSON file and all its backup files
    (following the .YYYYMMDD_HHMMSS.bak suffix) into a single Excel file.

    Args:
        base_file: Full path to the base JSON file (e.g., interface_data.json).

    Returns:
        Path to the merged Excel file.
    """
    try:
        base_path = Path(base_file)
        merged_entries: list[dict[str, Any]] = []

        if not base_path.exists():
            logger.error(f"Base file does not exist: {base_path}")
            return base_path

        # ------------------------------------------------------------------ #
        # Step 1: Identify base file and backup files
        # ------------------------------------------------------------------ #
        parent_dir = base_path.parent
        base_stem = base_path.stem  # e.g., "interface_data"
        suffix_pattern = re.compile(rf"{re.escape(base_stem)}\.(\d{{8}}_\d{{6}})\.bak")

        files_to_merge = [base_path]  # start with base file

        # Find backup files in same directory
        for f in parent_dir.glob(f"{base_stem}.*.bak*"):
            if suffix_pattern.search(f.name):
                files_to_merge.append(f)

        # Sort files by timestamp (base file first, then backups chronologically)
        def file_sort_key(f: Path):
            match = suffix_pattern.search(f.name)
            if match:
                return datetime.strptime(match.group(1), "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
            return datetime.min.replace(tzinfo=timezone.utc)

        files_to_merge.sort(key=file_sort_key)

        logger.info(f"Merging {len(files_to_merge)} files: {[f.name for f in files_to_merge]}")

        # ------------------------------------------------------------------ #
        # Step 2: Load and append data
        # ------------------------------------------------------------------ #
        for file in files_to_merge:
            try:
                with file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                list1 = data.get("list1", [])
                list2 = data.get("list2", [])
                created_at = data.get("created_at", "unknown")

                max_len = max(len(list1), len(list2))
                for i in range(max_len):
                    merged_entries.append(
                        {
                            "source_file": file.name,
                            "created_at": created_at,
                            "list1_item": list1[i] if i < len(list1) else None,
                            "list2_item": list2[i] if i < len(list2) else None,
                        }
                    )

            except Exception:
                logger.exception(f"Failed to read or parse {file}")

        if not merged_entries:
            logger.warning("No entries found to merge.")
            return base_path

        # ------------------------------------------------------------------ #
        # Step 3: Write merged Excel file
        # ------------------------------------------------------------------ #
        merged_df = pd.DataFrame(merged_entries)
        output_file = base_path.with_name(f"{base_stem}_merged.xlsx")

        if output_file.exists():
            # Backup existing merged file
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_path = output_file.with_name(f"{output_file.stem}.{timestamp}.bak.xlsx")
            output_file.rename(backup_path)
            logger.info(f"Existing merged file backed up: {backup_path}")

        merged_df.to_excel(output_file, index=False)
        logger.info(f"Merged Excel file created: {output_file}")

        return output_file

    except Exception as e:
        logger.exception("Failed to merge files")
        return base_path


# ---------------------------------------------------------------------------- #
#                                    Screen                                    #
# ---------------------------------------------------------------------------- #


def get_screen_size() -> tuple[int, int]:
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    return screen_height, screen_width


# ---------------------------------------------------------------------------- #
#                                      Git                                     #
# ---------------------------------------------------------------------------- #


def get_patchset() -> tuple[str, str]:
    pm = ProcessManager()
    proc = pm.run(Git().patchset().syntax)
    stdout, stderr = pm.get_output(proc)

    return stdout, stderr


# ---------------------------------------------------------------------------- #
#                                    Python                                    #
# ---------------------------------------------------------------------------- #


def run_pip_licenses() -> tuple[str, str]:
    pm = ProcessManager()
    proc = pm.run(Python().syntax)
    stdout, stderr = pm.get_output(proc)

    return stdout, stderr


# ---------------------------------------------------------------------------- #
#                                    Logging                                   #
# ---------------------------------------------------------------------------- #





def log_data(name: str, data, level=logging.DEBUG) -> None:
    """Log data nicely formatted depending on its size."""
    logger = logging.getLogger(__name__)
    if isinstance(data, (list, dict)):
        if len(str(data)) < 300:
            msg = pprint.pformat(data, width=80)
        else:
            msg = json.dumps(data, indent=2)
    else:
        msg = str(data)

    logger.log(level, f"{name}: {msg}")
