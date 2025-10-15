"""Dashboard tab implementation."""

from datetime import UTC, datetime
import logging
import platform
import socket

from nicegui import ui
import psutil

from src.core.connect import SshConnection
from src.core.json import Json
from src.models.config import Config
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "local"
LABEL = "Local"


class LocalTab(BaseTab):
    ICON_NAME: str = "dashboard"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class LocalPanel(BasePanel):
    def __init__(
        self,
        build: bool = False,
        config: Config = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        super().__init__(NAME, LABEL, "dashboard")
        self._config = config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._local_content: LocalContent | None = None
        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            if not self._local_content:
                self._local_content = LocalContent(self._ssh_connection, self._host_handler, self._config)
            self._local_content.build()


class LocalContent:
    def __init__(
        self, ssh_connection: SshConnection | None = None, host_handler=None, config: Config | None = None
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._expansion_states = {}
        self._auto_refresh = False
        self._refresh_timer = None
        self._all_expanded = False
        self._expand_button = None
        self._expansions = {}

    def build(self) -> None:
        """Build local system interface."""
        # Add global CSS for left-aligned table cells
        ui.add_head_html("<style>.q-table td, .q-table th { text-align: left !important; }</style>")

        with ui.card().classes("w-full p-4 border"):
            with ui.row().classes("w-full items-center gap-3 mb-6"):
                ui.icon("dashboard", size="lg").classes("text-blue-600")
                ui.label("Local System").classes("text-2xl font-bold text-gray-800")
                ui.space()
                ui.checkbox("Refresh", value=self._auto_refresh, on_change=self._toggle_auto_refresh).classes("mr-4")
                ui.button("Export", icon="upload", on_click=self._export_data).classes(
                    "bg-blue-300 hover:bg-blue-400 text-blue-900 px-4 py-2 rounded ml-2"
                )
                self._expand_button = ui.button(icon="sym_r_expand_all", on_click=self._toggle_all_expansions).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded"
                )

            self.stats_container = ui.column().classes("w-full gap-4")
            with self.stats_container:
                self._build_system_stats()

    def _toggle_all_expansions(self):
        """Toggle all expansion panels and update button icon."""
        self._all_expanded = not self._all_expanded

        # Update all expansion panels directly
        for expansion in self._expansions.values():
            expansion.value = self._all_expanded

        # Update expansion states
        for key in self._expansion_states:
            self._expansion_states[key] = self._all_expanded

        # Update button icon
        if self._expand_button:
            self._expand_button.props(f"icon={'sym_r_collapse_all' if self._all_expanded else 'sym_r_expand_all'}")

    def _refresh_stats(self):
        """Refresh system statistics."""
        self.stats_container.clear()
        with self.stats_container:
            self._build_system_stats()

    def _toggle_auto_refresh(self, enabled: bool):
        """Toggle auto-refresh functionality."""
        self._auto_refresh = enabled
        if enabled:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()

    def _start_auto_refresh(self):
        """Start auto-refresh timer."""
        if self._refresh_timer:
            self._refresh_timer.cancel()
        self._refresh_timer = ui.timer(5.0, self._refresh_stats, active=True)

    def _stop_auto_refresh(self):
        """Stop auto-refresh timer."""
        if self._refresh_timer:
            self._refresh_timer.cancel()
            self._refresh_timer = None

    def _export_data(self):
        """Export all dashboard data to JSON."""
        data = self._collect_all_data()
        Json.export_download(data, "system_dashboard", success_message="System dashboard data exported successfully")

    def _get_system_info(self):
        """Get system information."""
        return {
            "os": f"{platform.system()} {platform.release()}",
            "hostname": socket.gethostname(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        }

    def _get_performance_data(self):
        """Get performance metrics."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_count": psutil.cpu_count(),
            "memory": dict(psutil.virtual_memory()._asdict()),
            "disk_usage": dict(psutil.disk_usage("/")._asdict()),
        }

    def _collect_all_data(self):
        """Collect all system data for export."""
        # Cache process list to avoid multiple iterations
        processes = list(psutil.process_iter(["name", "cpu_percent", "memory_percent", "status"]))

        data = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "system_info": self._get_system_info(),
            "performance": self._get_performance_data(),
            "network": dict(psutil.net_io_counters()._asdict()),
            "processes": {
                "total": len(processes),
                "by_status": {
                    status: sum(1 for p in processes if p.info.get("status") == status)
                    for status in ["running", "sleeping", "zombie", "stopped"]
                },
            },
            "uptime": {
                "boot_time": psutil.boot_time(),
                "uptime_seconds": (
                    datetime.now(tz=UTC) - datetime.fromtimestamp(psutil.boot_time(), tz=UTC)
                ).total_seconds(),
            },
        }

        try:
            # Sort processes once and slice for both CPU and memory
            cpu_sorted = sorted(processes, key=lambda x: x.info.get("cpu_percent") or 0, reverse=True)[:10]
            mem_sorted = sorted(processes, key=lambda x: x.info.get("memory_percent") or 0, reverse=True)[:10]

            data["top_processes"] = {
                "cpu": [{"name": p.info["name"], "cpu_percent": p.info["cpu_percent"]} for p in cpu_sorted],
                "memory": [{"name": p.info["name"], "memory_percent": p.info["memory_percent"]} for p in mem_sorted],
            }
        except Exception:
            data["top_processes"] = {"cpu": [], "memory": []}

        return data

    def _create_table(self, columns, rows):
        """Create optimized table with consistent styling."""
        return (
            ui.table(columns=columns, rows=rows).classes("w-full").style("background-color: white; text-align: left;")
        )

    def _build_system_stats(self):
        """Build comprehensive system statistics display."""
        try:
            # Cache system data to avoid repeated calls
            system_info = self._get_system_info()
            perf_data = self._get_performance_data()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            net_io = psutil.net_io_counters()

            # Row 1: System Overview Tables
            with ui.row().classes("w-full gap-2 mb-2"):
                # System Info Table
                exp1 = ui.expansion(
                    "System Info", icon="computer", value=self._expansion_states.get("system", False)
                ).classes("flex-1 bg-blue-50 border border-blue-200")
                exp1.on_value_change(lambda e: self._expansion_states.update({"system": e.value}))
                self._expansions["system"] = exp1
                with exp1:
                    system_data = [
                        {"Property": "Operating System", "Value": system_info["os"]},
                        {"Property": "Hostname", "Value": system_info["hostname"]},
                        {"Property": "Architecture", "Value": system_info["architecture"]},
                        {"Property": "Python Version", "Value": system_info["python_version"]},
                    ]
                    self._create_table(
                        [
                            {"name": "Property", "label": "Property", "field": "Property"},
                            {"name": "Value", "label": "Value", "field": "Value"},
                        ],
                        system_data,
                    )

                # Performance Table
                exp2 = ui.expansion(
                    "Performance", icon="memory", value=self._expansion_states.get("performance", False)
                ).classes("flex-1 bg-orange-50 border border-orange-200")
                exp2.on_value_change(lambda e: self._expansion_states.update({"performance": e.value}))
                self._expansions["performance"] = exp2
                with exp2:
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage("/")
                    performance_data = [
                        {
                            "Metric": "CPU Usage",
                            "Value": f"{perf_data['cpu_percent']}%",
                            "Details": f"{perf_data['cpu_count']} cores",
                        },
                        {
                            "Metric": "Memory",
                            "Value": f"{memory.percent}%",
                            "Details": f"{memory.used / (1024**3):.1f}/{memory.total / (1024**3):.1f} GB",
                        },
                        {
                            "Metric": "Disk Usage",
                            "Value": f"{disk.used / disk.total * 100:.0f}%",
                            "Details": f"{disk.free / (1024**3):.0f}/{disk.total / (1024**3):.0f} GB",
                        },
                    ]
                    self._create_table(
                        [
                            {"name": "Metric", "label": "Metric", "field": "Metric"},
                            {"name": "Value", "label": "Value", "field": "Value"},
                            {"name": "Details", "label": "Details", "field": "Details"},
                        ],
                        performance_data,
                    )

                # Network Table
                exp3 = ui.expansion(
                    "Network", icon="network_check", value=self._expansion_states.get("network", False)
                ).classes("flex-1 bg-teal-50 border border-teal-200")
                exp3.on_value_change(lambda e: self._expansion_states.update({"network": e.value}))
                self._expansions["network"] = exp3
                with exp3:
                    net_io = psutil.net_io_counters()
                    try:
                        connections = len(psutil.net_connections())
                    except (OSError, psutil.AccessDenied):
                        connections = "N/A"
                    net_data = [
                        {"Metric": "Bytes Sent", "Value": f"{net_io.bytes_sent / (1024**2):.0f} MB"},
                        {"Metric": "Bytes Received", "Value": f"{net_io.bytes_recv / (1024**2):.0f} MB"},
                        {"Metric": "Packets Sent", "Value": f"{net_io.packets_sent:,}"},
                        {"Metric": "Active Connections", "Value": str(connections)},
                    ]
                    self._create_table(
                        [
                            {"name": "Metric", "label": "Metric", "field": "Metric"},
                            {"name": "Value", "label": "Value", "field": "Value"},
                        ],
                        net_data,
                    )

            # Row 2: Process Analysis Tables
            with ui.row().classes("w-full gap-2 mb-2"):
                # Top CPU Processes Table
                exp4 = ui.expansion(
                    "Top CPU Processes", icon="trending_up", value=self._expansion_states.get("top_cpu", False)
                ).classes("flex-1 bg-red-50 border border-red-200")
                exp4.on_value_change(lambda e: self._expansion_states.update({"top_cpu": e.value}))
                self._expansions["top_cpu"] = exp4
                with exp4:
                    try:
                        top_cpu = sorted(
                            psutil.process_iter(["pid", "name", "cpu_percent"]),
                            key=lambda p: p.info["cpu_percent"] or 0,
                            reverse=True,
                        )[:5]
                        cpu_data = [
                            {
                                "PID": p.info["pid"],
                                "Process": p.info["name"][:20],
                                "CPU %": f"{p.info['cpu_percent']:.1f}",
                            }
                            for p in top_cpu
                            if p.info["cpu_percent"]
                        ]
                        self._create_table(
                            [
                                {"name": "PID", "label": "PID", "field": "PID"},
                                {"name": "Process", "label": "Process", "field": "Process"},
                                {"name": "CPU %", "label": "CPU %", "field": "CPU %"},
                            ],
                            cpu_data,
                        )
                    except Exception:
                        ui.label("CPU data unavailable").classes("text-sm text-gray-500")

                # Top Memory Processes Table
                exp5 = ui.expansion(
                    "Top Memory Processes", icon="storage", value=self._expansion_states.get("top_memory", False)
                ).classes("flex-1 bg-purple-50 border border-purple-200")
                exp5.on_value_change(lambda e: self._expansion_states.update({"top_memory": e.value}))
                self._expansions["top_memory"] = exp5
                with exp5:
                    try:
                        top_mem = sorted(
                            psutil.process_iter(["pid", "name", "memory_percent"]),
                            key=lambda p: p.info["memory_percent"] or 0,
                            reverse=True,
                        )[:5]
                        mem_data = [
                            {
                                "PID": p.info["pid"],
                                "Process": p.info["name"][:20],
                                "Memory %": f"{p.info['memory_percent']:.1f}",
                            }
                            for p in top_mem
                            if p.info["memory_percent"]
                        ]
                        self._create_table(
                            [
                                {"name": "PID", "label": "PID", "field": "PID"},
                                {"name": "Process", "label": "Process", "field": "Process"},
                                {"name": "Memory %", "label": "Memory %", "field": "Memory %"},
                            ],
                            mem_data,
                        )
                    except Exception:
                        ui.label("Memory data unavailable").classes("text-sm text-gray-500")

                # Process Health Table
                exp6 = ui.expansion(
                    "Process Health", icon="health_and_safety", value=self._expansion_states.get("health", False)
                ).classes("flex-1 bg-yellow-50 border border-yellow-200")
                exp6.on_value_change(lambda e: self._expansion_states.update({"health": e.value}))
                self._expansions["health"] = exp6
                with exp6:
                    try:
                        status_counts = {}
                        for p in psutil.process_iter():
                            status = p.status()
                            status_counts[status] = status_counts.get(status, 0) + 1

                        health_data = [
                            {
                                "Status": status.title(),
                                "Count": count,
                                "Alert": "⚠️" if status == "zombie" and count > 0 else "",
                            }
                            for status, count in status_counts.items()
                        ]
                        self._create_table(
                            [
                                {"name": "Status", "label": "Status", "field": "Status"},
                                {"name": "Count", "label": "Count", "field": "Count"},
                                {"name": "Alert", "label": "Alert", "field": "Alert"},
                            ],
                            health_data,
                        )
                    except Exception:
                        ui.label("Process data unavailable").classes("text-sm text-gray-500")

            # Row 3: System Resources Tables
            with ui.row().classes("w-full gap-2 mb-2"):
                # Disk I/O Table
                exp7 = ui.expansion(
                    "Disk I/O", icon="storage", value=self._expansion_states.get("disk_io", False)
                ).classes("flex-1 bg-cyan-50 border border-cyan-200")
                exp7.on_value_change(lambda e: self._expansion_states.update({"disk_io": e.value}))
                self._expansions["disk_io"] = exp7
                with exp7:
                    try:
                        disk_io = psutil.disk_io_counters()
                        io_data = [
                            {
                                "Operation": "Read",
                                "Bytes": f"{disk_io.read_bytes / (1024**2):.0f} MB",
                                "Count": f"{disk_io.read_count:,}",
                            },
                            {
                                "Operation": "Write",
                                "Bytes": f"{disk_io.write_bytes / (1024**2):.0f} MB",
                                "Count": f"{disk_io.write_count:,}",
                            },
                            {
                                "Operation": "Total IOPS",
                                "Bytes": "-",
                                "Count": f"{disk_io.read_count + disk_io.write_count:,}",
                            },
                        ]
                        self._create_table(
                            [
                                {"name": "Operation", "label": "Operation", "field": "Operation"},
                                {"name": "Bytes", "label": "Bytes", "field": "Bytes"},
                                {"name": "Count", "label": "Count", "field": "Count"},
                            ],
                            io_data,
                        )
                    except Exception:
                        ui.label("Disk I/O unavailable").classes("text-sm text-gray-500")

                # System Load Table
                exp8 = ui.expansion(
                    "System Load", icon="analytics", value=self._expansion_states.get("load", False)
                ).classes("flex-1 bg-lime-50 border border-lime-200")
                exp8.on_value_change(lambda e: self._expansion_states.update({"load": e.value}))
                self._expansions["load"] = exp8
                with exp8:
                    try:
                        load_avg = psutil.getloadavg()
                        load_data = [
                            {"Period": "1 minute", "Load": f"{load_avg[0]:.2f}"},
                            {"Period": "5 minutes", "Load": f"{load_avg[1]:.2f}"},
                            {"Period": "15 minutes", "Load": f"{load_avg[2]:.2f}"},
                        ]
                    except AttributeError:
                        cpu_times = psutil.cpu_times()
                        load_data = [
                            {"Period": "User Time", "Load": f"{cpu_times.user:.1f}s"},
                            {"Period": "System Time", "Load": f"{cpu_times.system:.1f}s"},
                            {"Period": "Idle Time", "Load": f"{cpu_times.idle:.1f}s"},
                        ]
                    self._create_table(
                        [
                            {"name": "Period", "label": "Period", "field": "Period"},
                            {"name": "Load", "label": "Load", "field": "Load"},
                        ],
                        load_data,
                    )

                # Users Table
                exp9 = ui.expansion(
                    "Active Users", icon="security", value=self._expansion_states.get("security", False)
                ).classes("flex-1 bg-pink-50 border border-pink-200")
                exp9.on_value_change(lambda e: self._expansion_states.update({"security": e.value}))
                self._expansions["security"] = exp9
                with exp9:
                    try:
                        users = psutil.users()
                        current_user = psutil.Process().username()
                        user_data = [{"Type": "Current User", "Name": current_user, "Status": "Active"}]
                        for user in users[-3:]:  # Show last 3 users
                            user_data.append(
                                {"Type": "Session", "Name": user.name, "Status": f"Terminal: {user.terminal or 'N/A'}"}
                            )
                        self._create_table(
                            [
                                {"name": "Type", "label": "Type", "field": "Type"},
                                {"name": "Name", "label": "Name", "field": "Name"},
                                {"name": "Status", "label": "Status", "field": "Status"},
                            ],
                            user_data,
                        )
                    except Exception:
                        ui.label("User data unavailable").classes("text-sm text-gray-500")

            # Row 4: Application & Environment Tables
            with ui.row().classes("w-full gap-2"):
                # Application Stats Table
                exp10 = ui.expansion(
                    "Application Stats", icon="code", value=self._expansion_states.get("application", False)
                ).classes("flex-1 bg-indigo-50 border border-indigo-200")
                exp10.on_value_change(lambda e: self._expansion_states.update({"application": e.value}))
                self._expansions["application"] = exp10
                with exp10:
                    current_process = psutil.Process()
                    app_data = [
                        {"Metric": "Memory Usage", "Value": f"{current_process.memory_info().rss / (1024**2):.0f} MB"},
                        {"Metric": "Thread Count", "Value": str(current_process.num_threads())},
                        {"Metric": "Process ID", "Value": str(current_process.pid)},
                        {"Metric": "Status", "Value": "Online ✅"},
                    ]
                    self._create_table(
                        [
                            {"name": "Metric", "label": "Metric", "field": "Metric"},
                            {"name": "Value", "label": "Value", "field": "Value"},
                        ],
                        app_data,
                    )

                # Sensors Table
                exp11 = ui.expansion(
                    "System Sensors", icon="thermostat", value=self._expansion_states.get("sensors", False)
                ).classes("flex-1 bg-amber-50 border border-amber-200")
                exp11.on_value_change(lambda e: self._expansion_states.update({"sensors": e.value}))
                self._expansions["sensors"] = exp11
                with exp11:
                    try:
                        temps = psutil.sensors_temperatures()
                        sensor_data = []
                        if temps:
                            for name, entries in temps.items():
                                for entry in entries[:3]:  # Max 3 sensors per type
                                    sensor_data.append(
                                        {
                                            "Sensor": f"{name} {entry.label or ''}".strip(),
                                            "Temperature": f"{entry.current:.1f}°C",
                                            "Status": "🔥" if entry.current > 80 else "✅",
                                        }
                                    )
                        if not sensor_data:
                            sensor_data = [{"Sensor": "No sensors detected", "Temperature": "N/A", "Status": "i"}]
                        self._create_table(
                            [
                                {"name": "Sensor", "label": "Sensor", "field": "Sensor"},
                                {"name": "Temperature", "label": "Temperature", "field": "Temperature"},
                                {"name": "Status", "label": "Status", "field": "Status"},
                            ],
                            sensor_data,
                        )
                    except Exception:
                        ui.label("Sensor data unavailable").classes("text-sm text-gray-500")

                # Uptime Table
                exp12 = ui.expansion(
                    "System Uptime", icon="schedule", value=self._expansion_states.get("uptime", False)
                ).classes("flex-1 bg-green-50 border border-green-200")
                exp12.on_value_change(lambda e: self._expansion_states.update({"uptime": e.value}))
                self._expansions["uptime"] = exp12
                with exp12:
                    boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=UTC)
                    uptime = datetime.now(tz=UTC) - boot_time
                    uptime_data = [
                        {"Event": "System Boot", "Time": boot_time.strftime("%Y-%m-%d %H:%M:%S")},
                        {
                            "Event": "Uptime Duration",
                            "Time": f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m",
                        },
                        {"Event": "Current Time", "Time": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")},
                    ]
                    self._create_table(
                        [
                            {"name": "Event", "label": "Event", "field": "Event"},
                            {"name": "Time", "label": "Time", "field": "Time"},
                        ],
                        uptime_data,
                    )

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception("Error building system stats")
            ui.label(f"Error loading system statistics: {e}").classes("text-red-600")
