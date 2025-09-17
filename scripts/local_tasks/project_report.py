import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# Predefined excluded directories for faster lookup
EXCLUDED_DIRS = {
    ".git",
    "__git",
    ".venv",
    "__venv",
    ".node_modules",
    "__node_modules",
    ".cache",
    "__cache",
    ".continue",
    "__continue",
    ".vscode",
    "__vscode",
    ".generated",
    "__generated",
    ".init",
    "__init",
    ".pycache",
    "__pycache",
}


def is_excluded_path(path: str) -> bool:
    return any(path.startswith(exclude) for exclude in EXCLUDED_DIRS)


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def collect_files(directory: str) -> List[str]:
    results = []
    for root, dirs, files in os.walk(directory, followlinks=False):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not is_excluded_path(d)]

        # Process files
        for file in files:
            if not (file.startswith(".") or file == "__init__.py" or os.path.islink(os.path.join(root, file))):
                rel_path = _normalize_path(os.path.relpath(os.path.join(root, file), directory))
                results.append(rel_path)

    return results


def collect_directories(directory: str) -> List[str]:
    results = []
    for root, dirs, _ in os.walk(directory, followlinks=False):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not is_excluded_path(d)]

        # Process directories
        for dir_name in dirs:
            if not (dir_name.startswith(".") or os.path.islink(os.path.join(root, dir_name))):
                rel_path = _normalize_path(os.path.relpath(os.path.join(root, dir_name), directory)) + "/"
                results.append(rel_path)

    return results


def generate_report_paths() -> List[str]:
    files = collect_files(".")
    dirs = collect_directories(".")
    return sorted(files + dirs)


def write_json_report(data: List[str], output_path: str) -> None:
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            print(f"Project report generated at: {output_path}")

    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to write report: {e}") from e


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate project structure reports")
    parser.add_argument("--output-file", required=True, help="Output filename")
    return parser.parse_args()


def main() -> None:
    try:
        # Load environment variables
        load_dotenv()

        # Parse command line arguments
        args = parse_arguments()

        # Get configuration from environment
        generated_folder = os.getenv("GENERATED_FOLDER_PATH")
        if not generated_folder:
            raise ValueError("GENERATED_FOLDER_PATH environment variable not set")

        # Validate output file name
        if not args.output_file or not args.output_file.strip():
            raise ValueError("Output filename cannot be empty")

        # Create output directory if needed
        os.makedirs(generated_folder, exist_ok=True)

        # Generate and save report
        output_path = os.path.join(generated_folder, args.output_file)
        paths = generate_report_paths()
        write_json_report(paths, output_path)

    except (ValueError, RuntimeError) as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
