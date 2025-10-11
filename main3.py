import re
import subprocess
from typing import Any


class EthtoolParser:
    """
    Fully robust ethtool parser for any network interface.

    Features:
    - Validates interface existence
    - Parses:
        - Module info (-m)
        - Statistics (-S)
        - Ring/buffer params (-g)
        - Offload features (-k)
        - Coalescing params (-c)
    - Graceful handling of unsupported commands or permissions
    - Caches command output for performance
    - Enhanced SFP/QSFP EEPROM parsing for vendor, part number, serial, wavelength, media type
    """

    def __init__(self, interface: str):
        self.interface = interface
        self._cache: dict[str, str | None] = {}

        if not self._interface_exists():
            raise ValueError(f"Interface '{interface}' does not exist")

    # -------------------- Utilities -------------------- #

    def _interface_exists(self) -> bool:
        """Check if the network interface exists."""
        try:
            subprocess.run(["ip", "link", "show", self.interface], capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def _run_command(self, args: list) -> str | None:
        """
        Safely run a system command and cache output.
        Returns None if command fails (unsupported, missing interface, permission issue).
        """
        key = " ".join(args)
        if key in self._cache:
            return self._cache[key]

        try:
            result = subprocess.run(args, capture_output=True, text=True, check=True)
            self._cache[key] = result.stdout
            return result.stdout

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip() if e.stderr else ""
            # Handle permission errors, missing modules, unsupported commands
            if any(
                msg in stderr.lower() for msg in ["operation not permitted", "no device matches name", "not supported"]
            ):
                print(f"Warning: Cannot run {' '.join(args)} - {stderr}")
                self._cache[key] = None
                return None
            print(f"Warning: Command {' '.join(args)} failed - {stderr}")
            self._cache[key] = None
            return None
        except FileNotFoundError:
            print(f"Warning: Command not found: {args[0]}")
            self._cache[key] = None
            return None

    # -------------------- Parsers -------------------- #

    def module_info(self) -> dict[str, Any]:
        """Parse ethtool -m (module EEPROM info) and SFP/QSFP fields."""
        output = self._run_command(["sudo", "ethtool", "-m", self.interface])
        if not output:
            return {}

        data = {}
        # Generic key:value parsing
        for line in output.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()

        # Enhanced parsing for SFP/QSFP modules
        for key in data.copy():
            val = data[key]
            if key.lower() == "vendor name":
                data["vendor"] = val
            elif key.lower() in ["part number", "pn"]:
                data["part_number"] = val
            elif key.lower() in ["serial number", "sn"]:
                data["serial_number"] = val
            elif "wavelength" in key.lower():
                try:
                    data["wavelength_nm"] = int(re.search(r"\d+", val).group())
                except Exception:
                    data["wavelength_nm"] = val
            elif "media" in key.lower() or "type" in key.lower():
                data["media_type"] = val

        return data

    def statistics(self) -> dict[str, int]:
        """Parse ethtool -S (interface statistics)."""
        output = self._run_command(["ethtool", "-S", self.interface])
        if not output:
            return {}
        data = {}
        for line in output.splitlines():
            match = re.match(r"\s*(\S+):\s*(\d+)", line)
            if match:
                key, value = match.groups()
                data[key] = int(value)
        return data

    def ring_params(self) -> dict[str, int | dict[str, int]]:
        """Parse ethtool -g (ring/buffer parameters)."""
        output = self._run_command(["ethtool", "-g", self.interface])
        if not output:
            return {}
        data = {}
        current_block = None
        for line in output.splitlines():
            if line.strip().endswith(":") and not line.startswith(" "):
                current_block = line.strip(":").strip()
                data[current_block] = {}
            elif current_block:
                match = re.match(r"\s*(\S+):\s*(\d+)", line)
                if match:
                    key, value = match.groups()
                    data[current_block][key] = int(value)
        return data

    def features(self) -> dict[str, bool]:
        """Parse ethtool -k (offload features)."""
        output = self._run_command(["ethtool", "-k", self.interface])
        if not output:
            return {}
        data = {}
        for line in output.splitlines():
            match = re.match(r"\s*(\S+):\s*(on|off)", line)
            if match:
                key, value = match.groups()
                data[key] = value.lower() == "on"
        return data

    def coalesce_params(self) -> dict[str, int]:
        """Parse ethtool -c (coalescing parameters)."""
        output = self._run_command(["ethtool", "-c", self.interface])
        if not output:
            return {}
        data = {}
        for line in output.splitlines():
            match = re.match(r"\s*(\S+):\s*(\d+)", line)
            if match:
                key, value = match.groups()
                data[key] = int(value)
        return data

    # -------------------- Unified Output -------------------- #

    def all_info(self) -> dict[str, Any]:
        """Return all parsed ethtool info as a single dictionary."""
        return {
            "module_info": self.module_info(),
            "statistics": self.statistics(),
            "ring_params": self.ring_params(),
            "features": self.features(),
            "coalesce_params": self.coalesce_params(),
        }


# -------------------- Example Usage -------------------- #
if __name__ == "__main__":
    iface = "wlp0s20f3"  # Replace with your interface
    try:
        parser = EthtoolParser(iface)
        info = parser.all_info()
        for section, data in info.items():
            print(f"--- {section} ---")
            print(data)
    except ValueError as e:
        print(e)
