"""Network diagnostic tool implementations."""

import json
import logging
import time
from typing import Any

from src.interfaces.connection import IConnection
from src.interfaces.tool import ITool, IToolFactory, ToolResult

logger = logging.getLogger(__name__)

"""

SUPPORTED_PACKAGES: list[str] = {
    "pciutils",  # PCI utilities for hardware info
    "ethtool",  # Ethernet tool for NIC management
    "rdma-core",  # RDMA/InfiniBand tools
    "lshw",  # Hardware lister
    "lm-sensors",  # Hardware monitoring sensors
    "python3-pip",  # Python package installer
    "mstflint",  # Mellanox firmware tools
    "mlnx-tools",  # Mellanox configuration tools
}

System dump

sudo apt update
sudo apt install -y pciutils ethtool rdma-core lshw lm-sensors python3-pip mstflint mlnx-tools ethtool inxi

ip -br link
rdma dev show
mst start
mst status
mst stop
*ibv_devinfo
*ibstat
ethtool <ifname>
ethtool -v -s <ifname>
ethtool -i <ifname>
ethtool -S <ifname> # statistics
ethtool -m <ifname> # Temp, volt ect
*mlxfwmanager --query
*mlnx_qos -i <ifname> # not supported on system
mlxlink -d /dev/mst/mtXXXX
mlxconfig -d /dev/mst/mtXXXX query # Port and module link status
lspci -v -s <PCI_ID>
lshw -C network
lsmod
lsb_release -a





dmesg | egrep -i 'mlx|mellanox|sfp|qsfp|phy|eth|port' | tail -n 200
dmesg | egrep -i 'mlx|sfp|qsfp|phy'
dmesg | egrep -i 'mlx|mellanox|sfp|qsfp|phy|port'

journalctl -k -u NetworkManager --since "1 hour ago" | egrep -i 'mlx|mellanox|sfp|qsfp'

ls -l /sys/class/net/<ifname>/device/
cat /sys/class/net/<ifname>/device/uevent
cat /sys/class/net/<ifname>/device/vendor
cat /sys/class/net/<ifname>/device/device
cat /sys/class/net/<ifname>/phys_port_name 2>/dev/null
cat /etc/os-release

uname -a



lspci -nn | egrep -i 'mellanox|mlx'
lspci -v
lspci -nn | grep -i mellanox
lspci -vvv | grep -A20 Mellanox



sudo hwinfo --network | grep -A20 Mellanox  # optional, if hwinfo installed


"""


class NetworkTool(ITool):
    """Base class for network diagnostic tools."""

    def __init__(self, connection: IConnection, interface: str | None = None):
        self._connection = connection
        self._interface = interface

    def execute(self, command: str, **_kwargs) -> ToolResult:
        """Execute tool command."""
        commands = self.get_commands()
        if command not in commands:
            return ToolResult(
                command=command, data=None, success=False, error=f"Unknown command: {command}"
            )

        cmd_template = commands[command]
        if self._interface:
            cmd_template = cmd_template.format(interface=self._interface)

        start_time = time.perf_counter()
        result = self._connection.execute_command(cmd_template)
        execution_time = time.perf_counter() - start_time

        if result.success:
            try:
                parsed_data = self.parse_output(command, result.stdout)
                return ToolResult(
                    command=cmd_template,
                    data=parsed_data,
                    success=True,
                    execution_time=execution_time,
                )
            except Exception as e:
                logger.exception(f"Failed to parse output for {command}")
                return ToolResult(
                    command=cmd_template,
                    data=None,
                    success=False,
                    error=f"Parse error: {e}",
                    execution_time=execution_time,
                )
        else:
            return ToolResult(
                command=cmd_template,
                data=None,
                success=False,
                error=result.stderr,
                execution_time=execution_time,
            )


class EthtoolImpl(NetworkTool):
    """Ethtool implementation."""

    @property
    def name(self) -> str:
        return "ethtool"

    def get_commands(self) -> dict[str, str]:
        return {
            "info": "ethtool {interface}",
            "statistics": "ethtool -S {interface}",
            "driver": "ethtool -i {interface}",
            "module": "ethtool -m {interface}",
            "features": "ethtool -k {interface}",
            "ring": "ethtool -g {interface}",
            "coalesce": "ethtool -c {interface}",
        }

    def parse_output(self, command: str, output: str) -> Any:
        """Parse ethtool output."""
        if command == "info":
            return self._parse_key_value(output)
        if command == "statistics":
            return self._parse_numeric_key_value(output)
        if command == "features":
            return self._parse_features(output)
        return self._parse_key_value(output)

    def _parse_key_value(self, output: str) -> dict[str, str]:
        """Parse key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
        return result

    def _parse_numeric_key_value(self, output: str) -> dict[str, int]:
        """Parse numeric key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                try:
                    result[key.strip()] = int(value.strip())
                except ValueError:
                    result[key.strip()] = value.strip()
        return result

    def _parse_features(self, output: str) -> dict[str, bool]:
        """Parse features output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip().lower() == "on"
        return result


class MlxconfigImpl(NetworkTool):
    """Mlxconfig implementation."""

    @property
    def name(self) -> str:
        return "mlxconfig"

    def get_commands(self) -> dict[str, str]:
        return {
            "query": "mlxconfig -d {interface} q",
            "backup": "mlxconfig -d {interface} backup",
        }

    def parse_output(self, _command: str, output: str) -> Any:
        """Parse mlxconfig output."""
        return self._parse_key_value(output)

    def _parse_key_value(self, output: str) -> dict[str, str]:
        """Parse key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip()
        return result


class NetworkToolFactory(IToolFactory):
    """Factory for creating network diagnostic tools."""

    def __init__(self, connection: IConnection):
        self._connection = connection
        self._tools = {
            "ethtool": EthtoolImpl,
            "mlxconfig": MlxconfigImpl,
        }

    def create_tool(self, tool_name: str, **kwargs) -> ITool:
        """Create tool instance."""
        if tool_name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise ValueError(f"Unknown tool '{tool_name}'. Available: {available}")

        tool_class = self._tools[tool_name]
        interface = kwargs.get("interface")
        return tool_class(self._connection, interface)

    def get_available_tools(self) -> list[str]:
        """Get list of available tools."""
        return list(self._tools.keys())


# ---------------------------------------------------------------------------
# Base executor interface (the actual SSH or subprocess logic is external)
# ---------------------------------------------------------------------------
class CLIExecutor:
    """Abstract base for command execution (local or remote)."""

    async def run(self, command: str) -> str:
        """Execute command and return raw stdout."""
        raise NotImplementedError("Executor.run() must be implemented by subclass.")


# ---------------------------------------------------------------------------
# Base class for Mellanox CLI tools
# ---------------------------------------------------------------------------
class MellanoxToolBase:
    """Common functionality for all Mellanox diagnostic tools."""

    def __init__(self, executor: CLIExecutor, logger: logging.Logger | None = None):
        self.executor = executor
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    async def _execute(self, command: str) -> str:
        """Safely execute a command and return its output."""
        self.logger.debug(f"Executing command: {command}")
        try:
            output = await self.executor.run(command)
            self.logger.debug(f"Command output:\n{output}")
            return output
        except Exception as e:
            self.logger.exception(f"Command execution failed: {e}")
            raise RuntimeError(f"Command failed: {command}") from e

    @staticmethod
    def _safe_json_parse(data: dict[str, Any]) -> str:
        """Safely convert parsed data to formatted JSON."""
        try:
            return json.dumps(data, indent=2)
        except Exception as e:
            logging.getLogger("MellanoxToolBase").error(f"JSON serialization error: {e}")
            return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# ETHtool wrapper
# ---------------------------------------------------------------------------
class EthtoolTool(MellanoxToolBase):
    """Encapsulates 'ethtool' commands for network interface diagnostics."""

    async def show_interface(self, interface: str) -> str:
        """Display interface details."""
        output = await self._execute(f"ethtool {interface}")
        parsed = self._parse_show_interface(output)
        return self._safe_json_parse(parsed)

    def _parse_show_interface(self, output: str) -> dict[str, Any]:
        """Parse ethtool output into a structured JSON-like dict."""
        data = {}
        for line in output.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()
        return data

    async def show_module_info(self, interface: str) -> str:
        """Show SFP/QSFP module details."""
        output = await self._execute(f"ethtool -m {interface}")
        parsed = self._parse_module_info(output)
        return self._safe_json_parse(parsed)

    def _parse_module_info(self, output: str) -> dict[str, Any]:
        """Parse ethtool -m (module info) output."""
        data = {}
        for line in output.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()
        return data


# ---------------------------------------------------------------------------
# MLXLINK
# ---------------------------------------------------------------------------
class MlxlinkTool(MellanoxToolBase):
    """Wrapper for mlxlink tool (link diagnostics)."""

    async def get_link_info(self, interface: str) -> str:
        """Retrieve link diagnostics info."""
        output = await self._execute(f"mlxlink -d {interface}")
        return self._safe_json_parse(self._parse_link_info(output))

    def _parse_link_info(self, output: str) -> dict[str, Any]:
        """Parse mlxlink diagnostics output."""
        data = {}
        for line in output.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip()
        return data


# ---------------------------------------------------------------------------
# MLXCONFIG
# ---------------------------------------------------------------------------
class MlxconfigTool(MellanoxToolBase):
    """Handles mlxconfig commands for device configuration."""

    async def show_config(self, device: str) -> str:
        """Show current configuration for given device."""
        output = await self._execute(f"mlxconfig -d {device} query")
        return self._safe_json_parse(self._parse_config(output))

    def _parse_config(self, output: str) -> dict[str, Any]:
        """Parse mlxconfig query output."""
        data = {}
        for line in output.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()
        return data


# ---------------------------------------------------------------------------
# MSTTOOL
# ---------------------------------------------------------------------------
class MstTool(MellanoxToolBase):
    """Handles mst devices enumeration."""

    async def list_devices(self) -> str:
        """List all available MST devices."""
        output = await self._execute("mst status")
        return self._safe_json_parse(self._parse_mst_status(output))

    def _parse_mst_status(self, output: str) -> dict[str, Any]:
        """Parse mst status output."""
        devices = []
        for line in output.splitlines():
            if "MST" in line or "/dev/mst" in line:
                devices.append(line.strip())
        return {"devices": devices}


# ---------------------------------------------------------------------------
# LSPCI TOOL
# ---------------------------------------------------------------------------
class LspciTool(MellanoxToolBase):
    """Provides PCI-level details about Mellanox NICs."""

    async def show_nic_info(self) -> str:
        """Get Mellanox PCI device info."""
        output = await self._execute("lspci -nn | grep -i mellanox")
        return self._safe_json_parse({"devices": output.splitlines()})


# ---------------------------------------------------------------------------
# IP TOOL
# ---------------------------------------------------------------------------
class IpTool(MellanoxToolBase):
    """Wrapper for Linux 'ip' commands."""

    async def show_interfaces(self) -> str:
        """List interfaces and their states."""
        output = await self._execute("ip -br addr")
        interfaces = [line.split() for line in output.splitlines()]
        return self._safe_json_parse({"interfaces": interfaces})


# ---------------------------------------------------------------------------
# HWMGMT TOOL
# ---------------------------------------------------------------------------
class HwMgmtTool(MellanoxToolBase):
    """Handles hardware management queries (mlxreg, sensors, etc.)."""

    async def show_temperature(self) -> str:
        """Get device temperature sensors."""
        output = await self._execute("sensors | grep -i mlx")
        temps = [line.strip() for line in output.splitlines()]
        return self._safe_json_parse({"mlx_temperatures": temps})
