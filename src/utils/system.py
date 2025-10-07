import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.utils.process_manager import ProcessManager
from src.utils.commands import Git, Python

# ---------------------------------------------------------------------------- #
#                                  Command I/O                                 #
# ---------------------------------------------------------------------------- #


def run_command(command: list[str], fail_ok: bool = False) -> str:
    result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    if result.returncode != 0:
        if fail_ok:
            logging.warning(f"Command failed but will continue: {' '.join(command)}")
        else:
            raise RuntimeError(f"Command failed: {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    logging.info(result.stdout)
    return result.stdout


# ---------------------------------------------------------------------------- #
#                                     PATH                                     #
# ---------------------------------------------------------------------------- #


def set_python_path(full_path: Path) -> None:
    if not full_path or not str(full_path).strip():
        logging.warning("PYTHONPATH is empty - nothing was added to sys.path")
        return

    base_dir = full_path.parent
    target_dir = base_dir.resolve()

    try:
        exist_dir(target_dir)
    except FileNotFoundError:
        logging.exception("PYTHONPATH directory was not found")
        raise

    target_dir_str = str(target_dir)
    if target_dir_str in sys.path:
        logging.debug("PYTHONPATH was found in sys.path. Will not add again")
        return

    sys.path.insert(0, target_dir_str)
    logging.debug(f"Added '{target_dir_str}' to the beginning of sys.path")


# ---------------------------------------------------------------------------- #
#                                     File                                     #
# ---------------------------------------------------------------------------- #


def exist_file(full_path: Path) -> None:
    if full_path.exists():
        logging.debug(f"File was found: {full_path}")
        return
    raise FileNotFoundError(f"File was not found: {full_path}")


# ---------------------------------------------------------------------------- #
#                                   Directory                                  #
# ---------------------------------------------------------------------------- #


def exist_dir(dir_path: Path) -> None:
    if dir_path.exists():
        logging.debug(f"Folder was found: {dir_path}")
    else:
        raise FileNotFoundError(f"Folder was not found: {dir_path}")


def create_dir(dir_path: Path) -> None:
    if not dir_path.exists():
        logging.warning(f"Folder was not found. Creating it: {dir_path}")
        dir_path.mkdir(parents=True, exist_ok=True)
    else:
        logging.debug(f"Folder was found: {dir_path}")


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


# ---------------------------------------------------------------------------- #
#                                    Screen                                    #
# ---------------------------------------------------------------------------- #


def get_screen_size() -> tuple[int, int]:
    import tkinter as tk

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


def setup_logging(level: int) -> None:
    logging.basicConfig(
        level=level, format="[%(asctime)s] %(levelname)s: %(message)s", handlers=[logging.StreamHandler()]
    )
