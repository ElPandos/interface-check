"""MLXConfig CLI tool implementation."""

from dataclasses import dataclass
from typing import Any

from src.mixins.tool import Tool


@dataclass(frozen=True)
class MlxParameter:
    """MLX configuration parameter."""

    name: str
    current_value: str
    default_value: str
    description: str


class MlxconfigTool(Tool):
    """MLXConfig Mellanox adapter configuration tool."""

    @property
    def tool_name(self) -> str:
        return "mlxconfig"

    def get_commands(self) -> dict[str, str]:
        """Get available mlxconfig commands."""
        return {
            "query": "mlxconfig -d {interface} query",
            "query_next": "mlxconfig -d {interface} query_next",
            "backup": "mlxconfig -d {interface} backup",
            "show_confs": "mlxconfig -d {interface} show_confs",
        }

    def parse_output(self, command_name: str, raw_output: str) -> Any:
        """Parse mlxconfig command output."""
        if command_name in ["query", "query_next"]:
            return self._parse_parameters(raw_output)
        if command_name == "show_confs":
            return self._parse_configurations(raw_output)
        return raw_output.strip()

    def _parse_parameters(self, output: str) -> list[MlxParameter]:
        """Parse mlxconfig parameter output."""
        parameters = []
        lines = output.strip().split("\n")

        for line in lines:
            if line.strip().startswith("         "):  # Parameter line
                parts = line.strip().split()
                if len(parts) >= 3:
                    parameters.append(
                        MlxParameter(
                            name=parts[0],
                            current_value=parts[1],
                            default_value=parts[2],
                            description=" ".join(parts[3:]) if len(parts) > 3 else "",
                        )
                    )

        return parameters

    def _parse_configurations(self, output: str) -> dict[str, str]:
        """Parse configuration list."""
        configs = {}
        lines = output.strip().split("\n")

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                configs[key.strip()] = value.strip()

        return configs
