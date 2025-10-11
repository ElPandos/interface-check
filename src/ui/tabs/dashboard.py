"""Dashboard tab implementation."""

import logging
import platform
import psutil
import socket
from datetime import datetime
from nicegui import ui
from src.models.configurations import AppConfig
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection

NAME = "dashboard"
LABEL = "Dashboard"


class DashboardTab(BaseTab):
    ICON_NAME: str = "dashboard"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class DashboardPanel(BasePanel):
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
        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            with ui.column().classes("w-full h-full p-4"):
                with ui.card().classes("w-full h-full p-6 shadow-lg bg-white border border-gray-200"):
                    with ui.row().classes("w-full items-center gap-3 mb-6"):
                        ui.icon("dashboard", size="lg").classes("text-blue-600")
                        ui.label("System Dashboard").classes("text-2xl font-bold text-gray-800")
                        ui.space()
                        ui.button("Refresh", icon="refresh", on_click=self._refresh_stats).classes(
                            "bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded"
                        )

                    self.stats_container = ui.column().classes("w-full gap-4")
                    with self.stats_container:
                        self._build_system_stats()

    def _refresh_stats(self):
        """Refresh system statistics."""
        self.stats_container.clear()
        with self.stats_container:
            self._build_system_stats()

    def _build_system_stats(self):
        """Build comprehensive system statistics display."""
        try:
            # Row 1: System Identity & Time
            with ui.row().classes("w-full gap-4 mb-4"):
                with ui.card().classes("flex-1 p-4 bg-blue-50 border border-blue-200 h-40"):
                    ui.icon("computer", size="md").classes("text-blue-600 mb-2")
                    ui.label("System Info").classes("font-semibold text-gray-800 mb-2")
                    ui.label(f"OS: {platform.system()} {platform.release()}").classes("text-sm text-gray-600")
                    ui.label(f"Host: {socket.gethostname()}").classes("text-sm text-gray-600")
                    ui.label(f"Arch: {platform.machine()}").classes("text-sm text-gray-600")

                with ui.card().classes("flex-1 p-4 bg-green-50 border border-green-200 h-40"):
                    ui.icon("schedule", size="md").classes("text-green-600 mb-2")
                    ui.label("Uptime").classes("font-semibold text-gray-800 mb-2")
                    boot_time = datetime.fromtimestamp(psutil.boot_time())
                    uptime = datetime.now() - boot_time
                    ui.label(f"Boot: {boot_time.strftime('%m-%d %H:%M')}").classes("text-sm text-gray-600")
                    ui.label(f"Up: {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m").classes("text-sm text-gray-600")
                    ui.label(f"Now: {datetime.now().strftime('%H:%M:%S')}").classes("text-sm text-gray-600")

                with ui.card().classes("flex-1 p-4 bg-purple-50 border border-purple-200 h-40"):
                    ui.icon("list", size="md").classes("text-purple-600 mb-2")
                    ui.label("Processes").classes("font-semibold text-gray-800 mb-2")
                    processes = list(psutil.process_iter(['pid', 'name']))
                    running = sum(1 for p in psutil.process_iter() if p.status() == 'running')
                    ui.label(f"Total: {len(processes)}").classes("text-sm text-gray-600")
                    ui.label(f"Running: {running}").classes("text-sm text-gray-600")
                    ui.label(f"This PID: {psutil.Process().pid}").classes("text-sm text-gray-600")

            # Row 2: Performance Metrics
            with ui.row().classes("w-full gap-4 mb-4"):
                with ui.card().classes("flex-1 p-4 bg-orange-50 border border-orange-200 h-40"):
                    ui.icon("memory", size="md").classes("text-orange-600 mb-2")
                    ui.label("CPU").classes("font-semibold text-gray-800 mb-2")
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    cpu_count = psutil.cpu_count()
                    ui.label(f"Usage: {cpu_percent}%").classes("text-sm text-gray-600")
                    ui.label(f"Cores: {cpu_count}").classes("text-sm text-gray-600")
                    try:
                        load_avg = psutil.getloadavg()
                        ui.label(f"Load: {load_avg[0]:.1f}").classes("text-sm text-gray-600")
                    except AttributeError:
                        ui.label(f"Threads: {psutil.cpu_count(logical=True)}").classes("text-sm text-gray-600")

                with ui.card().classes("flex-1 p-4 bg-red-50 border border-red-200 h-40"):
                    ui.icon("storage", size="md").classes("text-red-600 mb-2")
                    ui.label("Memory").classes("font-semibold text-gray-800 mb-2")
                    memory = psutil.virtual_memory()
                    ui.label(f"Total: {memory.total / (1024**3):.1f} GB").classes("text-sm text-gray-600")
                    ui.label(f"Used: {memory.used / (1024**3):.1f} GB").classes("text-sm text-gray-600")
                    ui.label(f"Usage: {memory.percent}%").classes("text-sm text-gray-600")

                with ui.card().classes("flex-1 p-4 bg-yellow-50 border border-yellow-200 h-40"):
                    ui.icon("hard_drive", size="md").classes("text-yellow-600 mb-2")
                    ui.label("Disk").classes("font-semibold text-gray-800 mb-2")
                    disk = psutil.disk_usage('/')
                    ui.label(f"Total: {disk.total / (1024**3):.0f} GB").classes("text-sm text-gray-600")
                    ui.label(f"Free: {disk.free / (1024**3):.0f} GB").classes("text-sm text-gray-600")
                    ui.label(f"Used: {disk.used/disk.total*100:.0f}%").classes("text-sm text-gray-600")

            # Row 3: Network & Application
            with ui.row().classes("w-full gap-4 mb-4"):
                with ui.card().classes("flex-1 p-4 bg-teal-50 border border-teal-200 h-40"):
                    ui.icon("network_check", size="md").classes("text-teal-600 mb-2")
                    ui.label("Network").classes("font-semibold text-gray-800 mb-2")
                    net_io = psutil.net_io_counters()
                    ui.label(f"Sent: {net_io.bytes_sent / (1024**2):.0f} MB").classes("text-sm text-gray-600")
                    ui.label(f"Recv: {net_io.bytes_recv / (1024**2):.0f} MB").classes("text-sm text-gray-600")
                    ui.label(f"Packets: {(net_io.packets_sent + net_io.packets_recv)/1000:.0f}K").classes("text-sm text-gray-600")

                with ui.card().classes("flex-1 p-4 bg-indigo-50 border border-indigo-200 h-40"):
                    ui.icon("code", size="md").classes("text-indigo-600 mb-2")
                    ui.label("Application").classes("font-semibold text-gray-800 mb-2")
                    current_process = psutil.Process()
                    ui.label(f"Python: {platform.python_version()}").classes("text-sm text-gray-600")
                    ui.label(f"Memory: {current_process.memory_info().rss / (1024**2):.0f} MB").classes("text-sm text-gray-600")
                    ui.label(f"Threads: {current_process.num_threads()}").classes("text-sm text-gray-600")

                with ui.card().classes("flex-1 p-4 bg-gray-50 border border-gray-200 h-40"):
                    ui.icon("info", size="md").classes("text-gray-600 mb-2")
                    ui.label("Status").classes("font-semibold text-gray-800 mb-2")
                    ui.label("Interface Check").classes("text-sm text-gray-600")
                    ui.label("System: Online").classes("text-sm text-green-600")
                    ui.label("Ready").classes("text-sm text-blue-600")

        except Exception as e:
            logging.exception(f"Error building system stats: {e}")
            ui.label(f"Error loading system statistics: {e}").classes("text-red-600")
