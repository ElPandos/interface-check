import logging
from typing import Any


class MellanoxSoftwareInstaller:
    """Handles the installation and verification of Mellanox-related packages on a remote device via SSH.

    This class assumes that a CLI execution object (e.g., an SSH client wrapper) is provided which can
    execute commands remotely. The class will not handle the SSH logic itself — it will only call the
    provided interface.
    """


def __init__(self, cli_executor: Any):
    """Initialize the installer with a CLI execution object.

    Args:
        cli_executor: Object responsible for executing commands on the remote device.
    """
    self.cli = cli_executor
    self.logger = logging.getLogger(self.__class__.__name__)
    self.logger.setLevel(logging.DEBUG)


async def update_package_index(self) -> bool:
    """Run 'sudo apt update' to refresh package metadata on the target device."""
    try:
        self.logger.info("Updating package index (sudo apt update)...")
        result = await self.cli.run("sudo apt update -y")
        if result.returncode == 0:
            self.logger.info("Package index updated successfully.")
            return True
        self.logger.error(f"apt update failed: {result.stderr}")
        return False
    except Exception as e:
        self.logger.exception(f"Unexpected error during apt update: {e}")
        return False


async def install_required_packages(self) -> bool:
    """Install all required Mellanox-related software packages."""
    packages = [
        "pciutils",
        "ethtool",
        "rdma-core",
        "lshw",
        "lm-sensors",
        "python3-pip",
        "mstflint",
        "mlnx-tools",
    ]

    try:
        self.logger.info(f"Installing packages: {' '.join(packages)}")
        cmd = f"sudo apt install -y {' '.join(packages)}"
        result = await self.cli.run(cmd)

        if result.returncode == 0:
            self.logger.info("All packages installed successfully.")
            return True
        self.logger.error(f"Package installation failed: {result.stderr}")
        return False
    except Exception as e:
        self.logger.exception(f"Error installing packages: {e}")
        return False


async def verify_installed_versions(self) -> dict[str, str]:
    """Verify installed package versions and return a summary in JSON format."""
    version_info = {}
    commands = {
        "pciutils": "lspci -v | head -n 3",
        "ethtool": "ethtool --version",
        "rdma-core": "rdma link show",
        "lshw": "lshw -version",
        "lm-sensors": "sensors -v",
        "python3-pip": "pip3 --version",
        "mstflint": "mstflint --version",
        "mlnx-tools": "mlxconfig --version || true",
    }

    self.logger.info("Verifying installed versions of all required packages...")

    for pkg, cmd in commands.items():
        try:
            result = await self.cli.run(cmd)
            if result.returncode == 0 and result.stdout:
                version_info[pkg] = result.stdout.strip().split("\n")[0]
                self.logger.debug(f"{pkg} version: {version_info[pkg]}")
            else:
                version_info[pkg] = "Not found or error"
                self.logger.warning(f"{pkg} appears missing or failed to return version.")
        except Exception as e:
            self.logger.exception(f"Error while checking version for {pkg}: {e}")
            version_info[pkg] = "Error"

    return version_info


async def summarize_installation(self) -> None:
    """Run full installation workflow and print summary of versions in a readable format."""
    self.logger.info("Starting Mellanox installation workflow...")

    if not await self.update_package_index():
        self.logger.error("Failed to update package index — aborting installation.")
        return

    if not await self.install_required_packages():
        self.logger.error("Failed to install one or more packages — aborting.")
        return

    summary = await self.verify_installed_versions()

    # Print formatted summary
    print("\n\033[1m=== Mellanox Software Installation Summary ===\033[0m")
    for pkg, version in summary.items():
        print(f"{pkg:<15} : {version}")
    print("\033[1m==============================================\033[0m\n")

    self.logger.info("Installation verification complete.")
