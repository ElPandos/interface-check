#!/usr/bin/env python3
"""Optimized SLX eye scan automation."""

from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
import re
import signal
import sys
import time
from zoneinfo import ZoneInfo

from src.core.connect import SshConnection
from src.models.config import Host

# Setup file logging
log_file = Path(__file__).parent / f"eye_scan_{datetime.now(ZoneInfo('localtime')).strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    global running
    logger.info("Ctrl+C pressed. Shutting down gracefully...")
    running = False


signal.signal(signal.SIGINT, signal_handler)


@dataclass(frozen=True)
class Config:
    """Connection configuration."""

    jump_host: str
    jump_user: str
    jump_pass: str

    slx_host: str
    slx_user: str
    slx_pass: str
    slx_root_pass: str
    slx_scan_ports: list[str]
    slx_scan_interval: int
    slx_port_toggle_enabled: int
    slx_port_toggle_wait: int
    slx_port_eyescan_wait: int

    sut_host: str
    sut_user: str
    sut_pass: str
    sut_interface_names: list[str]
    sut_info_dump_level: int

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from nested JSON structure."""
        jump = data["jump"]
        slx = data["slx"]
        sut = data["sut"]

        return cls(
            jump_host=jump["host"],
            jump_user=jump["user"],
            jump_pass=jump["pass"],
            slx_host=slx["host"],
            slx_user=slx["user"],
            slx_pass=slx["pass"],
            slx_root_pass=slx["root_pass"],
            slx_scan_ports=slx["scan_ports"],
            slx_scan_interval=slx["scan_interval"],
            slx_port_toggle_enabled=slx["port_toggling_enabled"],
            slx_port_toggle_wait=slx["port_toggle_wait"],
            slx_port_eyescan_wait=slx["port_eye_scan_wait"],
            sut_host=sut["host"],
            sut_user=sut["user"],
            sut_pass=sut["pass"],
            sut_interface_names=sut["interface_names"],
            sut_info_dump_level=sut["info_dump_level"],
        )


def load_config() -> Config:
    """Load configuration from JSON file."""
    # Handle PyInstaller bundled executable
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        config_file = Path(sys.executable).parent / "main_eye_config.json"
    else:
        # Running as script
        config_file = Path(__file__).parent / "main_eye_config.json"

    try:
        with open(config_file) as f:
            data = json.load(f)
        return Config.from_dict(data)
    except FileNotFoundError:
        logger.exception(f"Config file not found: {config_file}")
        logger.exception("Make sure config.json is in the same directory as the executable")
        raise
    except json.JSONDecodeError as e:
        logger.exception(f"Invalid JSON in config file: {e}")
        raise


@dataclass
class EyeScanResult:
    """Eye scan result data."""

    interface: str
    port_id: str
    result: str


class SLXEyeScanner:
    """SLX eye scan automation."""

    def __init__(self, config: Config):
        self.config = config
        self.ssh: SshConnection | None = None
        self.results: list[EyeScanResult] = []
        self._interface_cache: dict[str, tuple[str, str]] = {}  # interface -> (port_id, interface_name)

    def connect(self) -> bool:
        """Establish SSH connection and setup environment."""
        try:
            host = Host(ip=self.config.jump_host, username=self.config.jump_user, password=self.config.jump_pass)
            self.ssh = SshConnection(
                host=self.config.slx_host,
                username=self.config.slx_user,
                password=self.config.slx_pass,
                jump_hosts=[host],
            )

            if not (self.ssh.connect() and self.ssh.open_shell()):
                return False

            # Setup shell environment on SLX OS
            commands = ["start-shell", "su root", self.config.slx_root_pass]

            for cmd in commands:
                result = self.ssh.execute_shell_command(cmd)
                logger.debug(f"Command '{cmd}': {result}")

            return True

        except Exception:
            logger.exception("Connection failed")
            return False

    def get_port_id(self, interface: str) -> str | None:
        """Extract port ID from cmsh output."""
        cmd = f"cmsh -e 'hsl ifm show localdb' | grep {interface}"
        result = self.ssh.execute_shell_command(cmd)

        pattern = rf"{re.escape(interface)}\s+0x[0-9a-fA-F]+\s+\d+\s+(\d+)"
        match = re.search(pattern, result)
        return match.group(1) if match else None

    def get_interface_name(self, port_id: str) -> str | None:
        """Find interface name by port ID in fbr-CLI."""
        self.ssh.execute_shell_command("fbr-CLI")
        ps_result = self.ssh.execute_shell_command("ps")

        pattern = rf"(\w+)\(\s*{re.escape(port_id)}\)"
        match = re.search(pattern, ps_result)
        return match.group(1) if match else None

    def toggle_interface(self, interface_name: str, enable: bool) -> None:
        """Toggle interface on/off."""
        state = "true" if enable else "false"
        cmd = f"port {interface_name} enable={state}"
        logger.info(f"Toggling interface: {cmd}")
        self.ssh.execute_shell_command(cmd)
        logger.info(f"Waiting {self.config.slx_port_toggle_wait} seconds for interface toggle to take effect...")
        time.sleep(self.config.slx_port_toggle_wait)

    def run_eye_scan(self, interface_name: str, port_id: str) -> None:
        """Execute eye scan with interface toggle sequence."""
        if self.config.slx_port_toggle_enabled:
            # Toggle interface off
            self.toggle_interface(interface_name, False)

            # Toggle interface on
            self.toggle_interface(interface_name, True)

        # Run eye scan
        cmd = f"phy diag {interface_name} eyescan"
        logger.info(f"Starting eye scan: {cmd}")

        # Send command and wait
        self.ssh._shell.send(cmd + "\n")
        logger.info(f"Waiting {self.config.slx_port_eyescan_wait} seconds for eye scan to complete...")
        time.sleep(self.config.slx_port_eyescan_wait)

        # Get results
        self.ssh._shell.send("\n")
        result = self.ssh._read_until_prompt()

        self.results.append(EyeScanResult(interface_name, port_id, result))
        logger.info(f"Eye scan completed for: {interface_name}")
        logger.info("=======================================")
        logger.info(self.results[-1].result)
        logger.info("=======================================")

    def scan_interfaces(self, interfaces: list[str]) -> bool:
        """Complete eye scan workflow for interface."""
        for interface in interfaces:
            # Check cache first
            if interface in self._interface_cache:
                port_id, interface_name = self._interface_cache[interface]
                logger.debug(f"Using cached mapping: {interface} -> {interface_name} (Port {port_id})")
            else:
                # First time lookup
                port_id = self.get_port_id(interface)
                if not port_id:
                    logger.error(f"No port ID found for {interface}")
                    return False

                interface_name = self.get_interface_name(port_id)
                if not interface_name:
                    logger.error(f"No interface found for port {port_id}")
                    return False

                # Cache the mapping
                self._interface_cache[interface] = (port_id, interface_name)
                logger.info(f"Cached mapping: {interface} -> {interface_name} (Port {port_id})")

            self.run_eye_scan(interface_name, port_id)

        return True

    def disconnect(self) -> None:
        """Clean up connection."""
        if self.ssh:
            self.ssh.disconnect()


def main():
    """Main execution with continuous scanning loop."""
    global running

    config = load_config()
    scanner = SLXEyeScanner(config)

    logger.info(f"Starting eye scan automation. Logs saved to: {log_file}")
    logger.info(f"Scanning ports: {config.slx_scan_ports}")
    logger.info("Press Ctrl+C to stop the program")

    try:
        if not scanner.connect():
            logger.error("Failed to connect")
            return

        scan_count = 0
        while running:
            try:
                # Scan first port
                if scanner.scan_interfaces(config.slx_scan_ports):
                    scan_count += 1
                    logger.info(f"Completed scan #{scan_count}")

                    # Log latest result
                    if scanner.results:
                        latest = scanner.results[-1]
                        logger.info(f"Latest: {latest.interface} (Port {latest.port_id})")

                # Wait before next scan (if still running)
                if running:
                    logger.info(f"Waiting {config.slx_scan_interval} seconds before next scan...")
                    for _ in range(config.slx_scan_interval):
                        if not running:
                            break
                        time.sleep(1)

            except Exception:
                logger.exception("Scan iteration failed")
                if running:
                    time.sleep(5)  # Brief pause before retry

    except Exception:
        logger.exception("Main execution failed")
    finally:
        scanner.disconnect()
        logger.info(f"Program stopped. Total scans completed: {len(scanner.results)}")
        logger.info(f"Full log available at: {log_file}")
    return


if __name__ == "__main__":
    main()
