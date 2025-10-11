"""Toolbox tab implementation."""

import logging

from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.enums.tools import NetworkTool
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection

NAME = "toolbox"
LABEL = "Toolbox"


class ToolboxTab(BaseTab):
    ICON_NAME: str = "build"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class ToolboxPanel(BasePanel):
    def __init__(
        self,
        build: bool = False,
        app_config: AppConfig = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        super().__init__(NAME, LABEL)
        self._app_config = app_config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._selected_tool = None
        self._command_output = ""
        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            with ui.column().classes("w-full h-full p-4"):
                with ui.card().classes("w-full h-full p-6 shadow-lg bg-white border border-gray-200"):
                    with ui.row().classes("w-full items-center gap-3 mb-6"):
                        ui.icon("build", size="lg").classes("text-orange-600")
                        ui.label("Network Toolbox").classes("text-2xl font-bold text-gray-800")
                        ui.space()
                        ui.button("Clear Output", icon="clear", on_click=self._clear_output).classes(
                            "bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded"
                        )

                    with ui.row().classes("w-full gap-4"):
                        # Left panel - Tool selection
                        with ui.card().classes("w-1/3 p-4 bg-gray-50 border border-gray-200"):
                            ui.label("Available Tools").classes("text-lg font-semibold mb-4 text-gray-800")

                            for tool in NetworkTool:
                                with ui.card().classes(
                                    "w-full mb-2 p-3 bg-white border border-gray-300 hover:bg-blue-50 cursor-pointer"
                                ):
                                    with ui.row().classes("w-full items-center gap-3"):
                                        ui.icon(self._get_tool_icon(tool)).classes("text-blue-600")
                                        ui.label(tool.value.upper()).classes("font-medium text-gray-800")
                                        ui.space()
                                        ui.button("Select", on_click=lambda t=tool: self._select_tool(t)).classes(
                                            "bg-blue-300 hover:bg-blue-400 text-blue-900 px-3 py-1 rounded text-sm"
                                        )

                        # Right panel - Tool interface
                        with ui.card().classes("w-2/3 p-4 bg-gray-50 border border-gray-200"):
                            ui.label("Tool Interface").classes("text-lg font-semibold mb-4 text-gray-800")

                            if self._selected_tool:
                                self._build_tool_interface()
                            else:
                                with ui.column().classes("w-full items-center justify-center h-64"):
                                    ui.icon("build_circle", size="xl").classes("text-gray-400 mb-4")
                                    ui.label("Select a tool from the left panel").classes("text-gray-500 text-lg")

                    # Output panel
                    with ui.card().classes("w-full mt-4 p-4 bg-gray-900 border border-gray-700"):
                        ui.label("Command Output").classes("text-lg font-semibold mb-2 text-white")
                        self.output_area = (
                            ui.textarea(value=self._command_output, placeholder="Command output will appear here...")
                            .classes("w-full h-64 bg-black text-green-400 font-mono text-sm border border-gray-600")
                            .props("readonly")
                        )

    def _get_tool_icon(self, tool: NetworkTool) -> str:
        """Get appropriate icon for each tool."""
        icons = {
            NetworkTool.MLXCONFIG: "settings",
            NetworkTool.MLXLINK: "link",
            NetworkTool.IPMITOOL: "computer",
            NetworkTool.ETHTOOL: "network_check",
        }
        return icons.get(tool, "build")

    def _select_tool(self, tool: NetworkTool):
        """Select a tool and update the interface."""
        self._selected_tool = tool
        ui.notify(f"Selected {tool.value.upper()}", color="positive")
        # Rebuild the interface to show the selected tool
        # In a real implementation, you would update the right panel dynamically

    def _build_tool_interface(self):
        """Build the interface for the selected tool."""
        if not self._selected_tool:
            return

        with ui.column().classes("w-full gap-4"):
            ui.label(f"{self._selected_tool.value.upper()} Configuration").classes("text-xl font-bold text-gray-800")

            # Tool-specific interface would go here
            with ui.row().classes("w-full gap-2"):
                ui.input("Command Arguments", placeholder=f"Enter {self._selected_tool.value} arguments").classes(
                    "flex-1"
                )
                ui.button("Execute", icon="play_arrow", on_click=self._execute_command).classes(
                    "bg-green-300 hover:bg-green-400 text-green-900 px-4 py-2 rounded"
                )

    def _execute_command(self):
        """Execute the selected tool command."""
        if not self._selected_tool:
            ui.notify("No tool selected", color="negative")
            return

        try:
            # Placeholder for actual command execution
            output = f"Executing {self._selected_tool.value}...\n"
            output += f"Tool: {self._selected_tool.value}\n"
            output += "Command execution would happen here via SSH connection\n"

            self._command_output = output
            self.output_area.value = self._command_output
            ui.notify(f"{self._selected_tool.value} executed", color="positive")

        except Exception as e:
            logging.exception(f"Error executing {self._selected_tool.value}: {e}")
            ui.notify(f"Execution failed: {e}", color="negative")

    def _clear_output(self):
        """Clear the command output."""
        self._command_output = ""
        self.output_area.value = ""
        ui.notify("Output cleared", color="info")
