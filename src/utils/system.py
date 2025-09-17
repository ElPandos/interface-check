import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Union, cast

logger = logging.getLogger(__name__)


def run_command(command: List[str], fail_ok: bool = False) -> str:
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    if result.returncode != 0:
        if fail_ok:
            print(f"[WARN] Command failed but continuing: {' '.join(command)}")
            print(result.stdout)
            return result.stdout
        else:
            raise RuntimeError(f"Command failed: {' '.join(command)}\n{result.stdout}")

    return result.stdout


def set_pythonpath(pythonpath: str, file: str) -> None:
    if pythonpath:
        # Resolve absolute path relative to the reference file's directory
        full_path = os.path.abspath(os.path.join(os.path.dirname(file), pythonpath))
        sys.path.insert(0, full_path)
    else:
        print("[WARN] PYTHONPATH is empty")


def fileExist(path_and_file: str) -> None:
    if Path(path_and_file).exists():
        logger.info(f"File was found: {path_and_file}")
    else:
        raise FileNotFoundError(f"File was not found: {path_and_file}")


def folderExist(path: str) -> None:
    if Path(path).exists():
        logger.info(f"Folder was found: {path}")
    else:
        raise FileNotFoundError(f"Folder was not found: {path}")


def create_folder_if_not_exist(path: str) -> None:
    if not os.path.exists(path):
        logger.info(f"Folder was not found. Creating it: {path}")
        os.makedirs(path)
    else:
        logger.info(f"Folder was found: {path}")


def save_json_to_file(json_data: object, path_and_file: str) -> None:
    with open(path_and_file, "w") as f:
        json.dump(json_data, f)


def load_json_from_file(path_and_file: str) -> Union[Dict[str, Any], List[Any]]:
    if not os.path.exists(path_and_file):
        raise FileNotFoundError(f"File not found: {path_and_file}")
    with open(path_and_file, "r", encoding="utf-8") as f:
        return cast(Union[Dict[str, Any], List[Any]], json.load(f))


def setup_logging(log_obj: logging):
    # Configure logging
    log_obj.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s", handlers=[logging.StreamHandler()]
    )
