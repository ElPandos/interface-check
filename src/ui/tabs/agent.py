import asyncio
from datetime import datetime
from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.network_agent import NetworkAgent
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "agent"
LABEL = "Agent"


class AgentTab(BaseTab):
    ICON_NAME: str = "psychology"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()


class AgentPanel(BasePanel, MultiScreen):
    def __init__(
        self,
        *,
        build: bool = False,
        config: Config = None,
        ssh_connection: SshConnection = None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL, AgentTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._config = config
        self._ssh_connection = ssh_connection
        self._icon = icon
        self._agent_screens: dict[int, Any] = {}

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base("Network Agent")
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes):
        with (
            ui.card().classes(classes),
            ui.expansion(f"Network Agent {screen_num}", icon="psychology", value=True).classes("w-full"),
        ):
            if screen_num not in self._agent_screens:
                self._agent_screens[screen_num] = AgentContent(self._ssh_connection)

            agent = self._agent_screens[screen_num]
            agent.build(screen_num)


class AgentContent:
    def __init__(self, ssh_connection: SshConnection | None = None) -> None:
        self._ssh_connection = ssh_connection
        self._tasks: list[dict[str, Any]] = []
        self._running_tasks: set[str] = set()
        self._agent = NetworkAgent(ssh_connection) if ssh_connection else None

        # UI components
        self._status_badge: ui.badge | None = None
        self._task_container: ui.column | None = None
        self._results_container: ui.column | None = None
        self._recommendations_container: ui.column | None = None
        self._task_name: ui.input | None = None
        self._task_command: ui.input | None = None
        self._task_interval: ui.number | None = None
        self._task_repeat: ui.number | None = None
        self._buttons: dict[str, ui.button] = {}

        # Task configurations cache
        self._task_configs = {
            "health_check": {
                "name": "Interface Health Check",
                "commands": ["ethtool eth0", "ip link show", "cat /proc/net/dev"],
                "description": "Check interface status and basic health metrics",
            },
            "performance": {
                "name": "Performance Monitor",
                "commands": ["ethtool -S eth0", "sar -n DEV 1 5", "ss -i"],
                "description": "Monitor interface performance and statistics",
            },
            "diagnostics": {
                "name": "Link Diagnostics",
                "commands": ["ethtool -t eth0", "mii-tool eth0", "ethtool --show-ring eth0"],
                "description": "Run comprehensive link diagnostics",
            },
            "backup": {
                "name": "Config Backup",
                "commands": ["ip addr show", "ip route show", "cat /etc/network/interfaces"],
                "description": "Backup current network configuration",
            },
        }

    def build(self, screen_num: int) -> None:
        """Build the network agent automation interface."""
        with ui.column().classes("w-full h-full gap-4"):
            # Agent status and controls
            with ui.row().classes("w-full items-center gap-4 mb-4"):
                self._status_badge = ui.badge("Ready", color="positive").classes("text-sm")
                self._buttons["start"] = ui.button(
                    "Start Agent", icon="play_arrow", on_click=self._start_agent
                ).classes("bg-green-500 hover:bg-green-600 text-white")
                self._buttons["stop"] = ui.button("Stop Agent", icon="stop", on_click=self._stop_agent).classes(
                    "bg-red-500 hover:bg-red-600 text-white"
                )
                self._buttons["clear"] = ui.button("Clear Tasks", icon="clear_all", on_click=self._clear_tasks).classes(
                    "bg-gray-500 hover:bg-gray-600 text-white"
                )

            self._update_button_states()

            # Quick automation tasks
            with ui.expansion("Quick Tasks", icon="flash_on", value=True).classes("w-full"):
                with ui.row().classes("w-full gap-2 flex-wrap"):
                    ui.button(
                        "Interface Health Check",
                        icon="health_and_safety",
                        on_click=lambda: self._add_task(screen_num, "health_check"),
                    ).classes("bg-blue-500 hover:bg-blue-600 text-white")

                    ui.button(
                        "Performance Monitor",
                        icon="speed",
                        on_click=lambda: self._add_task(screen_num, "performance"),
                    ).classes("bg-purple-500 hover:bg-purple-600 text-white")

                    ui.button(
                        "Link Diagnostics",
                        icon="cable",
                        on_click=lambda: self._add_task(screen_num, "diagnostics"),
                    ).classes("bg-orange-500 hover:bg-orange-600 text-white")

                    ui.button(
                        "Config Backup",
                        icon="backup",
                        on_click=lambda: self._add_task(screen_num, "backup"),
                    ).classes("bg-teal-500 hover:bg-teal-600 text-white")

            # Task queue and results
            with ui.row().classes("w-full gap-4"):
                # Task queue
                with ui.column().classes("flex-1"):
                    ui.label("Task Queue").classes("text-lg font-bold mb-2")
                    with ui.scroll_area().classes("h-64 border border-gray-300 rounded p-2 bg-gray-50"):
                        self._task_container = ui.column().classes("w-full gap-2")
                        self._update_task_display()

                # Results panel
                with ui.column().classes("flex-1"):
                    ui.label("Results").classes("text-lg font-bold mb-2")
                    with ui.scroll_area().classes("h-64 border border-gray-300 rounded p-2 bg-gray-50"):
                        self._results_container = ui.column().classes("w-full gap-2")

            # Intelligent recommendations
            with ui.expansion("Smart Recommendations", icon="psychology", value=True).classes("w-full"):
                with ui.column().classes("w-full gap-2"):
                    ui.label("AI-powered task recommendations based on your network setup:").classes(
                        "text-sm text-gray-600"
                    )

                    with ui.row().classes("w-full gap-2 flex-wrap"):
                        ui.button(
                            "Get Recommendations",
                            icon="auto_awesome",
                            on_click=lambda: self._show_recommendations(screen_num),
                        ).classes("bg-purple-500 hover:bg-purple-600 text-white")

                        ui.button(
                            "Auto-Schedule Tasks",
                            icon="schedule",
                            on_click=lambda: self._auto_schedule_tasks(screen_num),
                        ).classes("bg-cyan-500 hover:bg-cyan-600 text-white")

                    # Recommendations display area
                    self._recommendations_container = ui.column().classes("w-full gap-2 mt-2")

            # Custom task builder
            with ui.expansion("Custom Task Builder", icon="build").classes("w-full"):
                with ui.column().classes("w-full gap-2"):
                    with ui.row().classes("w-full gap-2"):
                        self._task_name = ui.input("Task Name", placeholder="Enter task name").classes("flex-1")
                        self._task_command = ui.input("Command", placeholder="ethtool eth0").classes("flex-1")

                    with ui.row().classes("w-full gap-2"):
                        self._task_interval = ui.number("Interval (seconds)", value=60, min=1).classes("w-32")
                        self._task_repeat = ui.number("Repeat Count", value=1, min=1).classes("w-32")
                        ui.button(
                            "Add Custom Task",
                            icon="add_task",
                            on_click=lambda: self._add_custom_task(screen_num),
                        ).classes("bg-indigo-500 hover:bg-indigo-600 text-white")

    def _is_connected(self) -> bool:
        """Check if SSH connection is available."""
        return self._ssh_connection is not None and self._ssh_connection.is_connected()

    def _update_button_states(self) -> None:
        """Update button states based on connection status."""
        is_connected = self._is_connected()
        for button_name in ("start", "stop"):
            if button := self._buttons.get(button_name):
                if is_connected:
                    button.enable()
                else:
                    button.disable()

    def _create_task(
        self, task_id: str, name: str, commands: list[str], description: str, task_type: str, **kwargs
    ) -> dict[str, Any]:
        """Create a standardized task dictionary."""
        return {
            "id": task_id,
            "name": name,
            "commands": commands,
            "description": description,
            "status": "queued",
            "created": datetime.now().strftime("%H:%M:%S"),
            "type": task_type,
            **kwargs,
        }

    def _start_agent(self):
        """Start the network agent."""
        if not self._agent or not self._is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        if self._agent.start():
            if self._status_badge:
                self._status_badge.text = "Running"
                self._status_badge.color = "info"
            ui.notify("Network agent started", color="positive")
        else:
            ui.notify("Failed to start agent", color="negative")

    def _stop_agent(self):
        """Stop the network agent."""
        if self._agent:
            self._agent.stop()
        self._running_tasks.clear()
        if self._status_badge:
            self._status_badge.text = "Stopped"
            self._status_badge.color = "negative"
        ui.notify("Network agent stopped", color="warning")

    def _clear_tasks(self):
        """Clear all tasks."""
        self._tasks.clear()
        self._running_tasks.clear()
        self._update_task_display()
        if self._results_container:
            self._results_container.clear()
        ui.notify("Tasks cleared", color="info")
        ui.notify("Tasks cleared", color="info")

    def _add_task(self, screen_num: int, task_type: str):
        """Add a predefined task to the queue."""
        config = self._task_configs.get(task_type)
        if not config:
            return

        task = self._create_task(
            f"{task_type}_{len(self._tasks)}", config["name"], config["commands"], config["description"], task_type
        )

        self._tasks.append(task)
        self._update_task_display()
        ui.notify(f"Added task: {config['name']}", color="positive")

    def _add_custom_task(self, screen_num: int):
        """Add a custom task to the queue."""
        if not self._task_name or not self._task_command or not self._task_name.value or not self._task_command.value:
            ui.notify("Task name and command are required", color="negative")
            return

        task = self._create_task(
            f"custom_{len(self._tasks)}",
            self._task_name.value,
            [self._task_command.value],
            f"Custom task: {self._task_command.value}",
            "custom",
            interval=self._task_interval.value if self._task_interval else 60,
            repeat=self._task_repeat.value if self._task_repeat else 1,
        )

        self._tasks.append(task)
        self._update_task_display()

        # Clear inputs
        if self._task_name:
            self._task_name.value = ""
        if self._task_command:
            self._task_command.value = ""

        ui.notify(f"Added custom task: {task['name']}", color="positive")

    def _update_task_display(self):
        """Update the task queue display."""
        if not self._task_container:
            return

        self._task_container.clear()

        if not self._tasks:
            with self._task_container:
                ui.label("No tasks in queue").classes("text-gray-500 italic")
            return

        with self._task_container:
            for task in self._tasks:
                with ui.card().classes("w-full p-2 border"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column().classes("flex-1"):
                            ui.label(task["name"]).classes("font-bold")
                            ui.label(task["description"]).classes("text-sm text-gray-600")
                            ui.label(f"Created: {task['created']}").classes("text-xs text-gray-500")

                        with ui.column().classes("items-end gap-1"):
                            status_color = {
                                "queued": "gray",
                                "running": "blue",
                                "completed": "green",
                                "failed": "red",
                            }.get(task["status"], "gray")

                            ui.badge(task["status"].title(), color=status_color)

                            with ui.row().classes("gap-1"):
                                ui.button(
                                    icon="play_arrow",
                                    on_click=lambda t=task: self._run_task(t),
                                ).props("size=sm flat").classes("text-green-600")

                                ui.button(
                                    icon="delete",
                                    on_click=lambda t=task: self._remove_task(t),
                                ).props("size=sm flat").classes("text-red-600")

    def _run_task(self, task: dict[str, Any]):
        """Execute a task."""
        if not self._agent or not self._ssh_connection or not self._ssh_connection.is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        if task["id"] in self._running_tasks:
            ui.notify("Task already running", color="warning")
            return

        task["status"] = "running"
        self._running_tasks.add(task["id"])
        self._update_task_display()
        ui.notify(f"Running task: {task['name']}", color="info")

        # Execute task asynchronously
        asyncio.create_task(self._execute_task_async(task))

    async def _execute_task_async(self, task: dict[str, Any]):
        """Execute task asynchronously and handle results."""
        try:
            result = await self._agent.execute_task(task)
            self._handle_task_result(task, result)
        except Exception as e:
            self._handle_task_error(task, str(e))

    def _handle_task_result(self, task: dict[str, Any], result: dict[str, Any]):
        """Handle successful task completion."""
        task["status"] = "completed"
        self._running_tasks.discard(task["id"])
        self._update_task_display()

        # Add result to results panel
        if not self._results_container:
            return

        with self._results_container:
            status_color = "green" if result["status"] == "completed" else "red"
            border_class = f"border-l-4 border-{status_color}-500"

            with ui.card().classes(f"w-full p-3 {border_class}"):
                with ui.row().classes("w-full items-center justify-between"):
                    status_icon = "✅" if result["status"] == "completed" else "❌"
                    ui.label(f"{status_icon} {task['name']}").classes(f"font-bold text-{status_color}-700")
                    ui.label(datetime.now().strftime("%H:%M:%S")).classes("text-xs text-gray-500")

                # Show analysis if available
                if "analysis" in result:
                    analysis = result["analysis"]
                    ui.label(analysis.get("summary", "Analysis completed")).classes("text-sm text-gray-600")

                    # Show issues and recommendations
                    if analysis.get("issues"):
                        with ui.expansion("Issues Found", icon="warning").classes("w-full mt-2"):
                            for issue in analysis["issues"]:
                                ui.label(f"⚠️ {issue}").classes("text-sm text-orange-600")

                    if analysis.get("recommendations"):
                        with ui.expansion("Recommendations", icon="lightbulb").classes("w-full mt-2"):
                            for rec in analysis["recommendations"]:
                                ui.label(f"💡 {rec}").classes("text-sm text-blue-600")

                # Show command results
                if "results" in result:
                    with ui.expansion("Command Output", icon="terminal").classes("w-full mt-2"):
                        for cmd_result in result["results"]:
                            cmd_status = "✅" if cmd_result["success"] else "❌"
                            ui.label(f"{cmd_status} {cmd_result['command']}").classes("font-mono text-sm")
                            if cmd_result["stdout"]:
                                ui.code(
                                    cmd_result["stdout"][:500] + ("..." if len(cmd_result["stdout"]) > 500 else "")
                                ).classes("text-xs mt-1")
                            if cmd_result["stderr"]:
                                ui.code(f"ERROR: {cmd_result['stderr']}").classes("text-xs text-red-600 mt-1")

        ui.notify(f"Task completed: {task['name']}", color="positive")

    def _handle_task_error(self, task: dict[str, Any], error: str):
        """Handle task execution error."""
        task["status"] = "failed"
        self._running_tasks.discard(task["id"])
        self._update_task_display()

        # Add error to results panel
        if not self._results_container:
            return

        with self._results_container, ui.card().classes("w-full p-3 border-l-4 border-red-500"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(f"❌ {task['name']}").classes("font-bold text-red-700")
                ui.label(datetime.now().strftime("%H:%M:%S")).classes("text-xs text-gray-500")

            ui.label(f"Task failed: {error}").classes("text-sm text-red-600")

        ui.notify(f"Task failed: {task['name']}", color="negative")

    def _remove_task(self, task: dict[str, Any]):
        """Remove a task from the queue."""
        if task["id"] in self._running_tasks:
            ui.notify("Cannot remove running task", color="negative")
            return

        self._tasks = [t for t in self._tasks if t["id"] != task["id"]]
        self._update_task_display()
        ui.notify(f"Removed task: {task['name']}", color="info")

    def _show_recommendations(self, screen_num: int):
        """Display intelligent task recommendations."""
        if not self._agent:
            ui.notify("Agent not available", color="negative")
            return

        recommendations = self._agent.get_task_recommendations()
        if not self._recommendations_container:
            return

        self._recommendations_container.clear()

        if not recommendations:
            with self._recommendations_container:
                ui.label("No recommendations available").classes("text-gray-500 italic")
            return

        with self._recommendations_container:
            ui.label("Recommended Tasks:").classes("font-bold text-sm mb-2")

            for rec in recommendations:
                with ui.card().classes("w-full p-3 border border-gray-200"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column().classes("flex-1"):
                            ui.label(rec["name"]).classes("font-bold")
                            ui.label(rec["description"]).classes("text-sm text-gray-600")

                            with ui.row().classes("gap-2 mt-1"):
                                priority_color = {"high": "red", "medium": "orange", "low": "green"}.get(
                                    rec["priority"], "gray"
                                )

                                ui.badge(rec["priority"].title(), color=priority_color).classes("text-xs")
                                ui.label(f"~{rec['estimated_time']}").classes("text-xs text-gray-500")

                        ui.button(
                            "Add Task",
                            icon="add",
                            on_click=lambda r=rec: self._add_recommended_task(screen_num, r),
                        ).props("size=sm").classes("bg-blue-500 hover:bg-blue-600 text-white")

        ui.notify("Recommendations loaded", color="positive")

    def _add_recommended_task(self, screen_num: int, recommendation: dict[str, Any]):
        """Add a recommended task to the queue."""
        task = {
            "id": f"rec_{len(self._tasks)}",
            "name": recommendation["name"],
            "commands": recommendation["commands"],
            "description": recommendation["description"],
            "status": "queued",
            "created": datetime.now().strftime("%H:%M:%S"),
            "type": "recommended",
            "priority": recommendation["priority"],
        }

        self._tasks.append(task)
        self._update_task_display()
        ui.notify(f"Added recommended task: {task['name']}", color="positive")

    def _auto_schedule_tasks(self, screen_num: int):
        """Automatically schedule high-priority recommended tasks."""
        if not self._agent:
            ui.notify("Agent not available", color="negative")
            return

        recommendations = self._agent.get_task_recommendations()
        high_priority_tasks = [r for r in recommendations if r["priority"] == "high"]

        if not high_priority_tasks:
            ui.notify("No high-priority tasks to schedule", color="info")
            return

        for rec in high_priority_tasks:
            self._add_recommended_task(screen_num, rec)

        ui.notify(f"Auto-scheduled {len(high_priority_tasks)} high-priority tasks", color="positive")
