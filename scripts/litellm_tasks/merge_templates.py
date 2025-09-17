import argparse
import glob
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def load_yaml(file_path: str) -> dict[str, Any]:
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        raise


def merge_yaml_files(generated_folder: str, template_file: str, output_file: str) -> None:
    # Load and validate main template
    template_data = load_yaml(template_file)

    if "include" not in template_data:
        raise ValueError("Main template must contain 'include' keyword")

    # Initialize output data
    output_data = {k: v for k, v in template_data.items() if k != "include"}

    # Process includes
    for pattern in template_data["include"]:
        folder_pattern = f"{generated_folder}/{pattern}"
        try:
            files = glob.glob(folder_pattern)
            if not files:
                print(f"No files found for pattern: {folder_pattern}")
                continue

            latest_file = max(files, key=os.path.getmtime)  # More efficient than sorting

            included_data = load_yaml(latest_file)
            if "model_list" in output_data:
                output_data["model_list"] = output_data.get("model_list", []) + included_data.copy()
                print(f"Merged: {latest_file}")

        except Exception as e:
            print(f"Error processing {pattern}: {str(e)}")

    if not output_data.get("model_list"):
        raise ValueError("No model_list found in any output_data")

    # Write output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        yaml.dump(output_data, f, sort_keys=False, default_flow_style=False)


def verify_generated_folder_exists(folder_path: str) -> None:
    path = Path(folder_path).resolve()
    try:
        if not path.is_dir():
            os.makedirs(path, exist_ok=True)
            print(f"Created folder: {path}")

        # Check for read/write/execute permissions (user, group, others)
        if not os.access(str(path), os.R_OK | os.W_OK | os.X_OK):
            raise PermissionError(f"Insufficient permissions for directory: {path}")

    except OSError as e:
        print(f"Failed to create folder: {folder_path}: {str(e)}")
        raise


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate LLM model templates from provider API's.")
    parser.add_argument(
        "--main-template-file",
        dest="main_template_file",
        type=str,
        required=True,
        help="Main template file containing known LLM provider model templates.",
    )
    parser.add_argument(
        "--output-file",
        dest="output_file",
        type=str,
        required=True,
        help="Output filename for the merged configuration.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    load_dotenv()
    try:
        args = parse_arguments()

        generated_folder = os.getenv("GENERATED_FOLDER_PATH")
        if not generated_folder:
            raise ValueError("GENERATED_FOLDER_PATH environment variable not set.")

        verify_generated_folder_exists(generated_folder)

        output_file = f"{args.output_file}"
        merge_yaml_files(generated_folder, args.main_template_file, output_file)
        print(f"Created configuration file: {output_file}\n")
    except Exception as e:
        print(f"Error: {e}")
