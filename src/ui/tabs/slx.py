import logging
import re
import time
from typing import Any

from nicegui import ui
import plotly.graph_objects as go

from src.core.connect import SshConnection
from src.core.parser import SlxEyeParser
from src.core.screen import MultiScreen
from src.models.config import Config
from src.platform.enums.log import LogName
from src.ui.tabs.base import BasePanel, BaseTab

logger = logging.getLogger(LogName.MAIN.value)

NAME = "slx"
LABEL = "SLX"


class SlxTab(BaseTab):
    ICON_NAME: str = "router"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class SlxPanel(BasePanel, MultiScreen):
    def __init__(
        self,
        build: bool = False,
        cfg: Config = None,
        ssh: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL, SlxTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._cfg = cfg
        self._ssh = ssh
        self._host_handler = host_handler
        self._icon = icon
        self._slx_screens: dict[int, Any] = {}

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base(LABEL)
            if self._host_handler:
                self.set_host_handler(self._host_handler)
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str):
        with ui.card().classes(classes):
            # Card header with route selector
            with ui.row().classes("w-full items-center gap-2 p-4 border-b"):
                ui.icon("computer", size="md").classes("text-blue-600")
                ui.label(f"Host {screen_num}").classes("text-lg font-semibold")

                if screen_num not in self._slx_screens:
                    self._slx_screens[screen_num] = SlxContent(
                        None, self._host_handler, self._cfg, self, screen_num
                    )

                # Buttons next to host label
                slx_content = self._slx_screens[screen_num]
                slx_content.build_buttons()

                # Centered user/password inputs
                slx_content.build_user_inputs()

                ui.space()

                # Route selector in header
                slx_content.build_route_selector()

            # Content area
            with ui.column().classes("w-full p-4"):
                slx_content.build_content(screen_num)


class SlxContent:
    def __init__(
        self,
        ssh: SshConnection | None = None,
        host_handler: Any = None,
        cfg: Config | None = None,
        parent_panel: SlxPanel | None = None,
        screen_num: int = 1,
    ) -> None:
        self._ssh = ssh
        self._host_handler = host_handler
        self._cfg = cfg
        self._parent_panel = parent_panel
        self._screen_num = screen_num
        self._selected_route: int | None = None
        self._slx_results: ui.column | None = None
        self._buttons: dict[str, ui.button] = {}
        self._route_selector: ui.select | None = None
        self._device_chip: ui.chip | None = None
        self._user_input: ui.input | None = None
        self._pass_input: ui.input | None = None
        self._slx_tools_select: ui.select | None = None
        self._interface_select: ui.select | None = None
        self._countdown_timer: ui.timer | None = None
        self._countdown_seconds: int = 0
        self._show_spinner_flag: bool = False

    def build_buttons(self) -> None:
        """Build buttons next to host label."""
        self._buttons["clear"] = ui.button(
            "Clear Results", icon="clear", on_click=self._clear_results
        ).classes("bg-gray-500 hover:bg-gray-600 text-white")

    def build_user_inputs(self) -> None:
        """Build user/password inputs centered in header."""
        with ui.row().classes("items-center gap-2 mx-8"):
            ui.icon("person", size="md").classes("text-gray-600")
            self._user_input = ui.input("User", value="root", placeholder="Enter username").classes(
                "w-28"
            )
            ui.space().classes("w-4")
            ui.icon("lock", size="md").classes("text-gray-600")
            self._pass_input = ui.input(
                "Password", value="fibranne", placeholder="Enter password", password=True
            ).classes("w-28")

    def build_route_selector(self) -> None:
        """Build route selector in card header."""
        self._device_chip = ui.chip("No device", icon="cancel", color="red").classes(
            "text-sm flex items-center justify-center h-10 px-4"
        )
        self._route_selector = (
            ui.select(options=[], value=None, label="Connected Routes")
            .classes("w-96")
            .on_value_change(self._on_route_change)
        )

        ui.timer(0.5, self._update_route_options, active=True)

    def build_content(self, screen_num: int) -> None:
        """Build SLX content area."""
        # SLX Tools selector (initially hidden)
        with ui.row().classes("w-full items-center gap-4 mb-4"):
            self._slx_tools_select = (
                ui.select(options=["Eye Scan"], value=None, label="SLX Tools")
                .classes("w-48")
                .on_value_change(self._on_slx_tool_change)
            )
            self._slx_tools_select.visible = False

            # Interface selector (initially hidden)
            self._interface_select = (
                ui.select(options=[], value=None, label="Interface")
                .classes("w-48")
                .on_value_change(self._on_interface_change)
            )
            self._interface_select.visible = False

            # Spinner for eye scan progress (initially hidden)
            ui.spinner(size="md", color="blue").bind_visibility_from(self, "_show_spinner_flag")
            self._countdown_label = (
                ui.label("30s")
                .classes("text-blue-600 font-bold")
                .bind_visibility_from(self, "_show_spinner_flag")
            )

        self._show_spinner_flag = False

        # Initialize results area below the selectors
        self._slx_results = ui.column().classes("w-full gap-4 mt-4")
        with self._slx_results:
            self._show_empty_state()

        self._update_button_states()

    def _on_route_change(self, e: Any) -> None:
        """
        Handle route selection change and update device status label.

        - Updates the selected route based on the UI selection.
        - Syncs SSH connection and opens shell if necessary.
        - Dynamically updates the device label color to reflect connection status.
        - Ensures UI consistency via NiceGUI's reactive update() mechanism.
        """
        logger.debug(f"Route change event: {getattr(e, 'value', None)}")

        selected_value = getattr(e, "value", None)
        if selected_value is not None:
            # Lookup selected route
            self._selected_route = getattr(self, "_route_value_map", {}).get(selected_value)
            if self._parent_panel:
                self._parent_panel.set_screen_route(self._screen_num, self._selected_route)
            logger.debug(
                f"Selected route label: '{selected_value}' -> route: {self._selected_route}"
            )

            # Check SSH connection state
            connection = (
                self._parent_panel.get_screen_connection(self._screen_num)
                if self._parent_panel
                else None
            )
            if connection:
                is_connected = connection.is_connected()
                logger.debug(f"SSH connection status: {is_connected}")
                if is_connected:
                    try:
                        # Ensure shell is open
                        if not hasattr(connection, "_shell") or connection._shell is None:
                            connection.open_shell()
                            logger.debug("Shell opened for SLX device")
                    except Exception as ex:
                        logger.warning(f"Failed to open shell: {ex}")
                else:
                    logger.debug("SSH connection is not active")
            else:
                logger.debug("No SSH connection found for selected route")
        else:
            # Reset route when selection cleared
            self._selected_route = None
            if self._parent_panel:
                self._parent_panel.set_screen_route(self._screen_num, None)

        self._update_device_chip()
        self._update_slx_tools_visibility()

        # Always update button state last
        self._update_button_states()

    def _update_route_options(self) -> None:
        """Update route selector options."""
        if not (self._parent_panel and self._route_selector):
            return

        connected_routes = self._parent_panel.get_connected_route_options()
        if not connected_routes:
            self._route_selector.options = []
            self._route_selector.update()
            return

        options = [route["label"] for route in connected_routes]
        values = [route["value"] for route in connected_routes]

        self._route_selector.options = options
        self._route_selector.update()
        self._route_value_map = dict(zip(options, values, strict=False))

    def _is_connected(self) -> bool:
        """Check if SSH connection is available."""
        if self._parent_panel and self._selected_route is not None:
            connection = self._parent_panel.get_screen_connection(self._screen_num)
            return connection is not None and connection.is_connected()
        return False

    def _update_button_states(self) -> None:
        """Update button states based on connection status."""
        is_connected = self._is_connected()
        for button_name in ("scan",):
            if button := self._buttons.get(button_name):
                if is_connected:
                    button.enable()
                else:
                    button.disable()

    def update_button_states(self) -> None:
        """Public method to update button states from parent."""
        self._update_button_states()

    def _show_empty_state(self) -> None:
        """Show empty state in results area."""
        if self._slx_results:
            with self._slx_results:
                ui.label("No SLX operations performed yet").classes("text-gray-500 italic")

    def _add_result_card(self, title: str, content: Any, color: str) -> None:
        """Add a result card to the results area."""
        if not self._slx_results:
            return

        # Clear empty state when adding first card
        self._slx_results.clear()

        with self._slx_results, ui.card().classes("w-full max-w-5xl mx-auto p-4"):
            ui.label(title).classes(f"font-bold text-{color}-600")
            if isinstance(content, go.Figure):
                ui.plotly(content)
            else:
                ui.label(str(content)).classes("text-sm text-gray-600")

        # ea(with self._slx_results, ui.card().classes("w-full p-4 border"):
        #     ui.label(title).classes(f"font-bold text-{color}-600")
        #     ui.textar
        #         value=content,
        #     ).classes(
        #         "w-full h-[600px] resize-none bg-black text-green-300 font-mono text-sm border-none rounded-xl p-2 overflow-auto"
        #     )
        # ui.label(content).classes("text-sm text-gray-600")

    def _clear_results(self) -> None:
        """Clear SLX results."""
        if self._slx_results:
            self._slx_results.clear()
            with self._slx_results:
                self._show_empty_state()
        ui.notify("Results cleared", color="info")

    def _update_device_chip(self) -> None:
        connection = (
            self._parent_panel.get_screen_connection(self._screen_num)
            if self._parent_panel
            else None
        )
        if connection and hasattr(connection, "_shell") and connection._shell is not None:
            logger.debug("Shell found - SLX device confirmed")
            self._device_chip.props("icon=router color=green")
            self._device_chip.text = "SLX device"
        else:
            logger.debug("No SLX device detected")
            self._device_chip.props("icon=cancel color=red")
            self._device_chip.text = "No device"

    def _update_slx_tools_visibility(self) -> None:
        """Show/hide SLX tools based on device detection."""
        connection = (
            self._parent_panel.get_screen_connection(self._screen_num)
            if self._parent_panel
            else None
        )
        is_slx = connection and hasattr(connection, "_shell") and connection._shell is not None

        logger.debug(
            f"SLX tools visibility check: is_slx={is_slx}, selector_exists={self._slx_tools_select is not None}"
        )
        if self._slx_tools_select:
            logger.debug(f"Setting SLX tools visibility to: {is_slx}")
            self._slx_tools_select.visible = is_slx
        else:
            logger.warning("SLX tools selector not found")

    def _on_slx_tool_change(self, e: Any) -> None:
        """Handle SLX tool selection."""
        if getattr(e, "value", None) == "Eye Scan":
            self._run_show_interface_status()

    def _on_interface_change(self, e: Any) -> None:
        """Handle interface selection for eye scan."""
        interface = getattr(e, "value", None)
        if interface:
            self._show_spinner()
            if self._user_input and self._pass_input:
                user = self._user_input.value
                password = self._pass_input.value
                if user and password:
                    self._run_eye_scan(interface, user, password)
                else:
                    self._hide_spinner()
                    ui.notify("Please enter username and password", color="negative")
            else:
                self._hide_spinner()

    def _run_show_interface_status(self) -> None:
        """Run show interface status command and populate interface selector."""
        connection = (
            self._parent_panel.get_screen_connection(self._screen_num)
            if self._parent_panel
            else None
        )
        if not connection or not hasattr(connection, "_shell") or connection._shell is None:
            logger.error("No shell connection available")
            ui.notify("No shell connection", color="negative")
            return

        logger.debug("Start show interface status command")
        try:
            # Use execute_shell_command like in main_eye_optimized.py
            logger.debug("Executing command: 'show interface status'")
            result = connection.execute_shell_command("show interface status")
            logger.debug(f"Command result length: {len(result)} characters")
            logger.debug(f"First 200 chars of result: {result[:200]}")
            logger.debug(f"Last 200 chars of result: {result[-200:]}")

            # Parse interface status output
            interfaces = []
            lines = result.split("\n")
            logger.debug(f"Total lines in output: {len(lines)}")

            for i, line in enumerate(lines):
                if line.strip() and line.startswith("Eth "):
                    parts = line.split()
                    if len(parts) >= 2:
                        interface_name = parts[1]
                        interfaces.append(interface_name)
                        logger.debug(f"Found interface: {interface_name} on line {i}")

            logger.debug(f"Total interfaces found: {len(interfaces)}")
            logger.debug(f"Interface list: {interfaces}")

            self._interfaces = interfaces
            if self._interface_select:
                self._interface_select.options = interfaces
                self._interface_select.visible = True
                self._interface_select.update()

            ui.notify(f"Found {len(interfaces)} interfaces", color="positive")

        except Exception as e:
            logger.exception("Failed to get interface status")
            ui.notify(f"Failed to get interfaces: {e}", color="negative")

    def _get_port_id(self, ssh: SshConnection, interface: str) -> str | None:
        """Extract port ID from cmsh output."""
        cmd = f"cmsh -e 'hsl ifm show localdb' | grep {interface}"
        result = ssh.exec_shell_command(cmd)

        pattern = rf"{re.escape(interface)}\s+0x[0-9a-fA-F]+\s+\d+\s+(\d+)"
        match = re.search(pattern, result)
        return match.group(1) if match else None

    def get_interface_name(self, ssh: SshConnection, port_id: str) -> str | None:
        """Find interface name by port ID in fbr-CLI."""
        ssh.exec_shell_command("fbr-CLI")
        ps_result = ssh.exec_shell_command("ps")

        pattern = rf"(\w+)\(\s*{re.escape(port_id)}\)"
        match = re.search(pattern, ps_result)
        return match.group(1) if match else None

    def run_eye_scan(
        self, ssh: SshConnection, interface_name: str, port_id: str
    ) -> tuple[str, bool]:
        """Execute eye scan with interface toggle sequence."""
        try:
            # Run eye scan
            cmd = f"phy diag {interface_name} eyescan"
            logger.info(f"Start eye scan: {cmd}")

            # Send command and wait (like main_eye_optimized.py)
            ssh._shell.send(cmd + "\n")
            eyescan_wait = 20
            logger.info(f"Waiting {eyescan_wait} seconds for eye scan to complete...")
            time.sleep(eyescan_wait)

            # Get results by sending newline and reading available data
            ssh._shell.send("\n")
            time.sleep(2)  # Wait for response

            # Read whatever is available without waiting for prompt
            buffer = b""
            start_time = time.time()
            while time.time() - start_time < 5.0:  # Read for 5 seconds
                if ssh._shell.recv_ready():
                    buffer += ssh._shell.recv(4096)
                else:
                    time.sleep(0.1)

            result = buffer.decode(errors="ignore")
            logger.debug(f"Eye scan completed for: {interface_name}")
            logger.debug("=======================================\n")
            logger.debug(result)
            logger.debug("=======================================\n")

            return result, True
        except Exception as e:
            logger.exception("Failed to eye data")
            ui.notify(f"Failed to get eye: {e}", color="negative")

        return "", False

    def _parse_eyescan_output(self, output: str) -> list[dict[str, str]]:
        """
        Parse SLX OS 'phy diag xe1 eyescan' output into structured rows.

        Each row contains:
            - voltage (in mV)
            - pattern (string of eye diagram symbols)
        """
        rows = []

        # Match lines like: "   128mV : 1111111..."
        pattern = re.compile(r"^\s*([\-]?\d+mV)\s*:\s*([0-9:\-\+\| ]+)$")

        for line in output.splitlines():
            match = pattern.match(line)
            if match:
                voltage, pattern_str = match.groups()
                # Remove extra spaces from pattern for cleaner data
                pattern_str = pattern_str.strip().replace(" ", "")
                rows.append({"voltage": voltage, "pattern": pattern_str})

        return rows

    def _build_rows_string(self, rows: list[dict[str, str]]) -> str:
        """
        Build and return the formatted eyescan table as a single string.
        Efficiently accumulates lines using a string builder pattern.

        :return: Formatted string (identical to original CLI rows)
        """
        if not rows:
            return ""

        # Use list accumulator for efficiency (StringBuilder equivalent)
        buffer: list[str] = []
        for row in rows:
            buffer.append(f"{row['voltage']:>6} : {row['pattern']}")
        return "\n".join(buffer)

    def _run_eye_scan(self, interface: str, user: str, password: str) -> None:
        """Run eye scan commands in shell."""
        connection = (
            self._parent_panel.get_screen_connection(self._screen_num)
            if self._parent_panel
            else None
        )
        if not connection or not hasattr(connection, "_shell") or connection._shell is None:
            ui.notify("No shell connection", color="negative")
            return None

        try:
            # Setup shell environment like main_eye_optimized.py
            connection.execute_shell_command("start-shell")
            connection.execute_shell_command(f"su {user}")
            connection.execute_shell_command(password)

            port_id = self._get_port_id(connection, interface)

            if not port_id:
                logger.error(f"No port ID found for {interface}")
                return False, ""

            interface_name = self.get_interface_name(connection, port_id)
            if not interface_name:
                logger.error(f"No interface found for port {port_id}")
                return False, ""

            result, success = self.run_eye_scan(connection, interface_name, port_id)

            parser = SlxEyeParser(result)
            matrix, voltages, phase_offsets = parser.to_matrix()

            # Build Plotly heatmap
            fig = go.Figure(
                data=go.Heatmap(
                    z=matrix,
                    x=phase_offsets,
                    y=voltages,
                    colorscale="Viridis",
                    colorbar=dict(title="Amplitude / Error Level"),
                    reversescale=True,  # Flip Y so positive voltages on top
                )
            )

            fig.update_layout(
                xaxis_title="Phase Offset",
                yaxis_title="Voltage (mV)",
                yaxis_autorange="reversed",
                height=600,
                margin=dict(l=60, r=40, t=50, b=50),
            )

            # Run complete eye scan workflow
            # success, result = self._scan_interface(connection, interface, port_id)

            connection.execute_shell_command("\x03" + "\r")  # Exit fbr (ctrl+c)
            connection.execute_shell_command("exit" + "\r")  # exit root
            connection.execute_shell_command("exit" + "\r")  # exit shell to #SLX

            # out = self._build_rows_string(self._parse_eyescan_output(result))

            if success:
                self._add_result_card(
                    f"Eye Scan Completed - {interface}",
                    fig,
                    "green",
                )
                ui.notify(f"Eye scan completed for {interface}", color="positive")
            else:
                self._add_result_card(
                    f"Eye Scan Failed - {interface}",
                    f"Failed to complete eye scan for interface {interface}",
                    "red",
                )
                ui.notify(f"Eye scan failed for {interface}", color="negative")

        except Exception as e:
            logger.exception("Failed to run eye scan")
            ui.notify(f"Eye scan failed: {e}", color="negative")
        finally:
            self._hide_spinner()

    def _show_spinner(self) -> None:
        """Show spinner with countdown timer."""
        self._show_spinner_flag = True
        self._countdown_seconds = 30  # Eye scan duration
        self._countdown_label.text = f"{self._countdown_seconds}s"

        # Start countdown timer
        self._countdown_timer = ui.timer(1.0, self._update_countdown, active=True)

    def _hide_spinner(self) -> None:
        """Hide spinner and stop countdown."""
        self._show_spinner_flag = False
        if self._countdown_timer:
            self._countdown_timer.active = False
            self._countdown_timer = None

    def _update_countdown(self) -> None:
        """Update countdown timer."""
        self._countdown_seconds -= 1
        if self._countdown_seconds <= 0:
            self._countdown_label.text = "Finishing..."
            if self._countdown_timer:
                self._countdown_timer.active = False
        else:
            self._countdown_label.text = f"{self._countdown_seconds}s"
