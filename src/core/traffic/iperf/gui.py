"""NiceGUI web interface for monitoring iperf processes."""

import asyncio
from collections import deque
from datetime import datetime
import logging
from pathlib import Path
from threading import Thread
import time

from nicegui import ui

from src.interfaces.component import IConnection


class IperfMonitor:
    """Web-based monitoring interface for iperf processes."""

    def __init__(
        self,
        server_conn: IConnection,
        client_conn: IConnection,
        logger: logging.Logger,
        port: int = 8080,
        shutdown_callback=None,
        server_host: str = "Server",
        client_host: str = "Client",
        csv_file: Path | None = None,
    ):
        """Initialize iperf monitor.

        Args:
            server_conn: Server SSH connection
            client_conn: Client SSH connection
            logger: Logger instance
            port: Web service port
            shutdown_callback: Callback to trigger shutdown
            server_host: Server hostname/IP for display
            client_host: Client hostname/IP for display
        """
        self._server_conn = server_conn
        self._client_conn = client_conn
        self._logger = logger
        self._port = port
        self._running = False
        self._thread: Thread | None = None
        self._shutdown_callback = shutdown_callback
        self._server_host = server_host
        self._client_host = client_host
        self._csv_file = csv_file

        self._server_processes: list[dict] = []
        self._client_processes: list[dict] = []
        self._log_messages: deque = deque(maxlen=100)
        self._stats: dict = {"current_gbps": 0.0, "avg_gbps": 0.0, "max_gbps": 0.0, "samples": 0}

    def _get_iperf_processes(self, conn: IConnection, host_ip: str) -> list[dict]:
        """Get running iperf processes from host."""
        try:
            if not conn.is_connected():
                return []

            result = conn.exec_cmd(
                "ps -eo pid,pcpu,pmem,cmd | grep '[i]perf' | head -20", timeout=5
            )
            stdout = result.stdout if hasattr(result, "stdout") else str(result)
            processes = []
            for line in stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.strip().split(None, 3)
                if len(parts) >= 4 and "iperf" in parts[3]:
                    cmd = parts[3][:100]
                    bind_ip = host_ip

                    # Extract bind IP from -B flag or target IP from client command
                    if "-B" in cmd:
                        try:
                            idx = cmd.split().index("-B")
                            bind_ip = cmd.split()[idx + 1]
                        except (ValueError, IndexError):
                            pass
                    elif "-c" in cmd:  # Client process
                        try:
                            idx = cmd.split().index("-c")
                            bind_ip = cmd.split()[idx + 1]
                        except (ValueError, IndexError):
                            pass

                    processes.append(
                        {
                            "ip": bind_ip,
                            "pid": parts[0],
                            "cpu": parts[1],
                            "mem": parts[2],
                            "cmd": cmd,
                            "time": datetime.now().strftime("%H:%M:%S"),
                        }
                    )
            return processes
        except Exception as e:
            self._logger.debug(f"Process fetch error: {e}")
            return []

    def _update_data(self):
        """Update process data from both hosts."""
        if self._server_conn.is_connected():
            self._server_processes = self._get_iperf_processes(self._server_conn, self._server_host)
        if self._client_conn.is_connected():
            self._client_processes = self._get_iperf_processes(self._client_conn, self._client_host)
        self._update_stats()

    def _update_stats(self):
        """Update bandwidth statistics from log files."""
        try:
            if not self._server_conn.is_connected():
                self._logger.warning("Server not connected, skipping stats update")
                return

            bandwidths = []

            # Parse server logs from /tmp
            result = self._server_conn.exec_cmd(
                "ls -lh /tmp/iperf_server_*.log 2>/dev/null", timeout=5
            )
            self._logger.info(
                f"Log files check: rcode={result.rcode}, stdout='{result.stdout.strip()}'"
            )

            if result.rcode == 0 and result.stdout.strip():
                log_files = [line.split()[-1] for line in result.stdout.strip().split("\n") if line]
                self._logger.info(f"Found {len(log_files)} log files: {log_files}")

                for log_file in log_files:
                    if not log_file or not log_file.startswith("/tmp/iperf_server_"):
                        continue

                    result = self._server_conn.exec_cmd(f"tail -100 {log_file}", timeout=5)
                    self._logger.info(
                        f"Reading {log_file}: rcode={result.rcode}, lines={len(result.stdout.split(chr(10)))}"
                    )

                    if result.rcode == 0 and result.stdout:
                        lines_with_data = 0
                        for line in result.stdout.split("\n"):
                            if "Bytes" in line and "bits/sec" in line:
                                lines_with_data += 1
                                parts = line.split()
                                for i, part in enumerate(parts):
                                    if "bits/sec" in part and i > 0:
                                        try:
                                            bw_val = float(parts[i - 1])
                                            if "Gbits/sec" in part:
                                                bandwidths.append(bw_val)
                                            elif "Mbits/sec" in part:
                                                bandwidths.append(bw_val / 1000)
                                            elif "Kbits/sec" in part:
                                                bandwidths.append(bw_val / 1000000)
                                            break
                                        except (ValueError, IndexError) as e:
                                            self._logger.debug(f"Parse error on '{line}': {e}")
                        self._logger.info(
                            f"Parsed {lines_with_data} lines with bandwidth data from {log_file}"
                        )

            if bandwidths:
                bandwidths = bandwidths[-500:]
                self._stats["current_gbps"] = bandwidths[-1]
                self._stats["avg_gbps"] = sum(bandwidths) / len(bandwidths)
                self._stats["max_gbps"] = max(bandwidths)
                self._stats["samples"] = len(bandwidths)
                self._logger.info(
                    f"Stats updated: {len(bandwidths)} samples, current={self._stats['current_gbps']:.2f}, "
                    f"avg={self._stats['avg_gbps']:.2f}, max={self._stats['max_gbps']:.2f} Gbps"
                )
            else:
                self._logger.warning("No bandwidth data found in any log files")
        except Exception as e:
            self._logger.exception(f"Stats update error: {e}")

    def add_log(self, message: str):
        """Add log message to display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"[{timestamp}] {message}"
        self._log_messages.append(msg)
        self._logger.info(f"GUI Log: {msg}")

    def _build_ui(self):
        """Build the monitoring UI."""
        ui.page_title("Iperf Monitor")

        with ui.header().classes("items-center justify-between p-4"):
            ui.label("Iperf Process Monitor").classes("text-h4")
            with ui.row():
                ui.label().bind_text_from(
                    globals(),
                    "current_time",
                    backward=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                self._terminate_btn = ui.button("Terminate Traffic", color="red")
                self._terminate_btn.on_click(lambda: self._terminate_traffic())

        # Statistics card - moved to top
        with ui.card().classes("w-full p-4 mx-4 mb-4"):
            ui.label("Traffic Statistics").classes("text-h6 mb-2 text-center")
            with ui.row().classes("w-full gap-8 justify-center"):
                with ui.column().classes("items-center"):
                    ui.label("Current").classes("text-caption text-gray-600")
                    current_label = ui.label("0.0 Gbps").classes("text-h5 font-bold text-blue-600")
                with ui.column().classes("items-center"):
                    ui.label("Average").classes("text-caption text-gray-600")
                    avg_label = ui.label("0.0 Gbps").classes("text-h5 font-bold text-green-600")
                with ui.column().classes("items-center"):
                    ui.label("Maximum").classes("text-caption text-gray-600")
                    max_label = ui.label("0.0 Gbps").classes("text-h5 font-bold text-orange-600")
                with ui.column().classes("items-center"):
                    ui.label("Samples").classes("text-caption text-gray-600")
                    samples_label = ui.label("0").classes("text-h5 font-bold text-purple-600")

        # Server processes
        with ui.card().classes("w-full p-4 mx-4 mb-4"):
            ui.label("Server Processes").classes("text-h6 mb-2")
            server_table = ui.table(
                columns=[
                    {"name": "ip", "label": "IP", "field": "ip"},
                    {"name": "pid", "label": "PID", "field": "pid"},
                    {"name": "cpu", "label": "CPU%", "field": "cpu"},
                    {"name": "mem", "label": "MEM%", "field": "mem"},
                    {"name": "cmd", "label": "Command", "field": "cmd"},
                    {"name": "time", "label": "Updated", "field": "time"},
                ],
                rows=[],
            ).classes("w-full")

        # Client processes
        with ui.card().classes("w-full p-4 mx-4 mb-4"):
            ui.label("Client Processes").classes("text-h6 mb-2")
            client_table = ui.table(
                columns=[
                    {"name": "ip", "label": "IP", "field": "ip"},
                    {"name": "pid", "label": "PID", "field": "pid"},
                    {"name": "cpu", "label": "CPU%", "field": "cpu"},
                    {"name": "mem", "label": "MEM%", "field": "mem"},
                    {"name": "cmd", "label": "Command", "field": "cmd"},
                    {"name": "time", "label": "Updated", "field": "time"},
                ],
                rows=[],
            ).classes("w-full")

        # Log window
        with ui.card().classes("w-full p-4 mx-4 mb-4"):
            ui.label("Traffic Log").classes("text-h6 mb-2")
            log_area = ui.log().classes("w-full h-64")

            # Store reference for terminate button
            self._log_area = log_area

        # Auto-refresh every 2 seconds
        async def refresh():
            while self._running:
                try:
                    if self._server_conn.is_connected() and self._client_conn.is_connected():
                        self._update_data()
                        server_table.rows = self._server_processes
                        client_table.rows = self._client_processes
                        server_table.update()
                        client_table.update()

                        # Update statistics
                        current_label.set_text(f"{self._stats['current_gbps']:.2f} Gbps")
                        avg_label.set_text(f"{self._stats['avg_gbps']:.2f} Gbps")
                        max_label.set_text(f"{self._stats['max_gbps']:.2f} Gbps")
                        samples_label.set_text(str(self._stats["samples"]))

                    # Update log - copy messages before clearing
                    if self._log_messages:
                        for msg in list(self._log_messages):
                            log_area.push(msg)
                        self._log_messages.clear()
                except Exception as e:
                    self._logger.debug(f"Refresh error: {e}")
                    if not self._running:
                        break

                await asyncio.sleep(2)

        ui.timer(0.1, refresh, once=True)

    def _terminate_traffic(self):
        """Terminate all traffic tests."""
        try:
            self._logger.info("Terminate button clicked in web UI")
            self._terminate_btn.disable()
            self._terminate_btn.set_text("Terminating...")

            # Add log and push immediately
            msg = "Terminating traffic tests..."
            self.add_log(msg)
            if hasattr(self, "_log_area"):
                self._log_area.push(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

            if self._shutdown_callback:
                self._shutdown_callback()
                self._logger.info("Shutdown callback executed")

            ui.notify("Shutdown signal sent", type="positive")
        except Exception as e:
            self._logger.error(f"Terminate button error: {e}")

    def start(self):
        """Start the web monitoring service in background thread."""
        if self._running:
            self._logger.warning("Monitor already running")
            return

        self._running = True
        self._logger.info(f"Starting iperf monitor on port {self._port}")

        # Build UI before starting thread
        self._build_ui()

        def run_server():
            try:
                ui.run(
                    port=self._port,
                    show=False,
                    reload=False,
                    title="Iperf Monitor",
                    reconnect_timeout=30,
                )
            except Exception as e:
                self._logger.error(f"Web server error: {e}")
                self._running = False

        self._thread = Thread(target=run_server, daemon=True, name="IperfMonitor")
        self._thread.start()
        time.sleep(1)  # Give server time to start
        self._logger.info(f"Monitor available at http://localhost:{self._port}")

    def stop(self):
        """Stop the monitoring service."""
        self._logger.info("Stopping iperf monitor")
        self._running = False

    def log(self, message: str):
        """Public method to add log messages."""
        self.add_log(message)
