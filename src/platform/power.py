"""Power management module for platform operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any

from src.platform.enums.log import LogName

logger = logging.getLogger(LogName.MAIN.value)


class PowerState(Enum):
    """Power states for system components."""

    ON = "on"
    OFF = "off"
    STANDBY = "standby"
    SUSPEND = "suspend"
    HIBERNATE = "hibernate"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PowerInfo:
    """Power consumption information."""

    component: str
    current_watts: float
    voltage: float
    current_amps: float
    state: PowerState
    temperature: float | None = None


@dataclass(frozen=True)
class BatteryInfo:
    """Battery status information."""

    level: int  # 0-100
    charging: bool
    time_remaining: int | None = None  # minutes
    health: str | None = None


class PowerController(ABC):
    """Abstract interface for power control operations."""

    @abstractmethod
    def set_power_state(self, component: str, state: PowerState) -> bool:
        """Set power state for a component."""

    @abstractmethod
    def get_power_caps(self, component: str) -> dict[str, Any]:
        """Get power capability limits."""


class IpmiPowerController(PowerController):
    """IPMI-based power controller."""

    def __init__(self, connection):
        self._connection = connection

    def set_power_state(self, _component: str, state: PowerState) -> bool:
        """Set power state via IPMI."""
        try:
            cmd = f"ipmitool power {state.value}"
            stdout, stderr = self._connection.exec_command(cmd)
            return not stderr
        except Exception as e:
            logger.exception(f"IPMI power control failed: {e}")
            return False

    def get_power_caps(self, _component: str) -> dict[str, Any]:
        """Get power caps via IPMI."""
        try:
            stdout, _ = self._connection.exec_command("ipmitool dcmi power reading")
            return {"current": self._parse_power_reading(stdout)}
        except Exception:
            return {}

    def _parse_power_reading(self, output: str) -> float:
        """Parse IPMI power reading output."""
        for line in output.split("\n"):
            if "Current Power" in line:
                return float(line.split(":")[1].strip().split()[0])
        return 0.0


class Power:
    """Independent power management system."""

    def __init__(self, connection=None):
        self._connection = connection
        self._controllers: list[PowerController] = []
        if connection:
            self._controllers.append(IpmiPowerController(connection))

    def add_controller(self, controller: PowerController) -> None:
        """Add custom power controller."""
        self._controllers.append(controller)

    def get_power_info(self) -> list[PowerInfo]:
        """Get current power consumption information."""
        info = []

        if not self._connection:
            return info

        try:
            # Get system power via sensors
            stdout, _ = self._connection.exec_command("sensors -A")
            info.extend(self._parse_sensors_power(stdout))

            # Get IPMI power if available
            stdout, stderr = self._connection.exec_command("ipmitool dcmi power reading")
            if not stderr:
                info.extend(self._parse_ipmi_power(stdout))

        except Exception as e:
            logger.exception(f"Power info collection failed: {e}")

        return info

    def get_battery_info(self) -> BatteryInfo | None:
        """Get battery status information."""
        if not self._connection:
            return None

        try:
            stdout, stderr = self._connection.exec_command("acpi -b")
            if stderr:
                return None
            return self._parse_battery_info(stdout)
        except Exception as e:
            logger.exception(f"Battery info failed: {e}")
            return None

    def set_power_policy(self, policy: str) -> bool:
        """Set system power policy."""
        if not self._connection:
            return False

        try:
            cmd = f"cpupower frequency-set -g {policy}"
            _, stderr = self._connection.exec_command(cmd)
            return not stderr
        except Exception as e:
            logger.exception(f"Power policy setting failed: {e}")
            return False

    def get_power_states(self) -> dict[str, PowerState]:
        """Get power states of system components."""
        states = {}

        if not self._connection:
            return states

        try:
            # Check CPU power states
            stdout, _ = self._connection.exec_command("cat /proc/cpuinfo | grep MHz")
            if stdout:
                states["cpu"] = PowerState.ON

            # Check network interfaces
            stdout, _ = self._connection.exec_command("ip link show")
            for line in stdout.split("\n"):
                if "state UP" in line:
                    iface = line.split(":")[1].strip()
                    states[f"net_{iface}"] = PowerState.ON
                elif "state DOWN" in line:
                    iface = line.split(":")[1].strip()
                    states[f"net_{iface}"] = PowerState.OFF

        except Exception as e:
            logger.exception(f"Power state check failed: {e}")

        return states

    def control_component(self, component: str, state: PowerState) -> bool:
        """Control power state of specific component."""
        return any(controller.set_power_state(component, state) for controller in self._controllers)

    def _parse_sensors_power(self, output: str) -> list[PowerInfo]:
        """Parse sensors output for power information."""
        info = []
        current_chip = ""

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.endswith(":"):
                current_chip = line[:-1]
                continue

            if "W" in line and ("power" in line.lower() or "watt" in line.lower()):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        watts = float(parts[1].replace("W", ""))
                        info.append(
                            PowerInfo(
                                component=f"{current_chip}_{parts[0]}",
                                current_watts=watts,
                                voltage=0.0,
                                current_amps=0.0,
                                state=PowerState.ON,
                            )
                        )
                    except ValueError:
                        continue

        return info

    def _parse_ipmi_power(self, output: str) -> list[PowerInfo]:
        """Parse IPMI power reading output."""
        info = []

        for line in output.split("\n"):
            if "Current Power" in line:
                try:
                    watts = float(line.split(":")[1].strip().split()[0])
                    info.append(
                        PowerInfo(
                            component="system",
                            current_watts=watts,
                            voltage=0.0,
                            current_amps=0.0,
                            state=PowerState.ON,
                        )
                    )
                except (ValueError, IndexError):
                    continue

        return info

    def _parse_battery_info(self, output: str) -> BatteryInfo | None:
        """Parse battery information from acpi output."""
        for line in output.split("\n"):
            if "Battery" in line:
                parts = line.split(",")
                if len(parts) >= 2:
                    try:
                        level_str = parts[1].strip()
                        level = int(level_str.replace("%", ""))
                        charging = "Charging" in line
                        return BatteryInfo(level=level, charging=charging)
                    except ValueError:
                        continue
        return None
