"""NiceGUI web interface for monitoring iperf processes."""

import asyncio
from collections import deque
import csv
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
        summary_csv_file: Path | None = None,
        poll_rate_ms: int = 2000,
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
        self._summary_csv_file = summary_csv_file
        self._poll_rate_ms = poll_rate_ms

        self._server_processes: list[dict] = []
        self._client_processes: list[dict] = []
        self._log_messages: deque = deque(maxlen=100)
        self._stats: dict = {"current_gbps": 0.0, "avg_gbps": 0.0, "max_gbps": 0.0, "samples": 0}
        self._interface_stats: dict[str, list[float]] = {}  # Track per-interface bandwidth
        self._last_csv_write = time.time()

    def _get_iperf_processes(self, conn: IConnection, host_ip: str) -> list[dict]:
        """Get running iperf processes from host."""
        try:
            if not conn.is_connected():
                return []

            result = conn.exec_cmd("ps -eo pid,pcpu,pmem,cmd | grep '[i]perf' | head -20", timeout=5)
            stdout = result.stdout if hasattr(result, "stdout") else str(result)
            processes = []
            for line in stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.strip().split(None, 3)
                if len(parts) >= 4 and "iperf" in parts[3]:
                    cmd = parts[3][:100]
                    # Skip sudo/nohup wrapper processes
                    if "sudo -S" in cmd or ("nohup" in cmd and "iperf" not in cmd.split("nohup")[1].split()[0]):
                        continue
                    bind_ip = host_ip

                    # Extract bind IP and interface from command
                    interface = "-"
                    if "-B" in cmd:
                        try:
                            idx = cmd.split().index("-B")
                            bind_ip = cmd.split()[idx + 1]
                            interface = bind_ip.split(".")[-1] if "." in bind_ip else bind_ip
                        except (ValueError, IndexError):
                            pass
                    elif "-c" in cmd:  # Client process
                        try:
                            idx = cmd.split().index("-c")
                            bind_ip = cmd.split()[idx + 1]
                            interface = bind_ip.split(".")[-1] if "." in bind_ip else bind_ip
                        except (ValueError, IndexError):
                            pass

                    processes.append(
                        {
                            "ip": bind_ip,
                            "interface": interface,
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
            result = self._server_conn.exec_cmd("ls -lh /tmp/iperf_server_*.log 2>/dev/null", timeout=5)
            self._logger.info(f"Log files check: rcode={result.rcode}, stdout='{result.stdout.strip()}'")

            if result.rcode == 0 and result.stdout.strip():
                log_files = [line.split()[-1] for line in result.stdout.strip().split("\n") if line]
                self._logger.info(f"Found {len(log_files)} log files: {log_files}")

                for log_file in log_files:
                    if not log_file or not log_file.startswith("/tmp/iperf_server_"):
                        continue

                    # Extract port from filename for interface tracking
                    port = log_file.split("_")[-1].replace(".log", "")
                    interface_bw = []

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
                                                bw_gbps = bw_val
                                            elif "Mbits/sec" in part:
                                                bw_gbps = bw_val / 1000
                                            elif "Kbits/sec" in part:
                                                bw_gbps = bw_val / 1000000
                                            else:
                                                continue
                                            bandwidths.append(bw_gbps)
                                            interface_bw.append(bw_gbps)
                                            break
                                        except (ValueError, IndexError) as e:
                                            self._logger.debug(f"Parse error on '{line}': {e}")
                        self._logger.info(f"Parsed {lines_with_data} lines with bandwidth data from {log_file}")
                        if interface_bw:
                            self._interface_stats[port] = interface_bw[-10:]  # Keep last 10 samples per interface

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
                self._write_stats_to_csv()
                self._write_summary_to_csv()
            else:
                self._logger.warning("No bandwidth data found in any log files")
        except Exception as e:
            self._logger.exception(f"Stats update error: {e}")

    def _write_stats_to_csv(self):
        """Write current statistics to CSV file."""
        if not self._csv_file:
            return

        # Write every 5 seconds to avoid excessive I/O
        now = time.time()
        if now - self._last_csv_write < 5:
            return
        self._last_csv_write = now

        try:
            write_header = not self._csv_file.exists()
            with self._csv_file.open("a", newline="") as f:
                # Build fieldnames with per-interface columns
                fieldnames = [
                    "timestamp",
                    "total_current_gbps",
                    "total_avg_gbps",
                    "total_max_gbps",
                    "samples",
                ]
                # Add per-interface columns
                for port in sorted(self._interface_stats.keys()):
                    fieldnames.append(f"port_{port}_gbps")

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()

                row = {
                    "timestamp": datetime.now().isoformat(),
                    "total_current_gbps": f"{self._stats['current_gbps']:.2f}",
                    "total_avg_gbps": f"{self._stats['avg_gbps']:.2f}",
                    "total_max_gbps": f"{self._stats['max_gbps']:.2f}",
                    "samples": self._stats["samples"],
                }
                # Add per-interface bandwidth
                for port, bw_list in self._interface_stats.items():
                    if bw_list:
                        row[f"port_{port}_gbps"] = f"{bw_list[-1]:.2f}"

                writer.writerow(row)
        except Exception as e:
            self._logger.error(f"Failed to write stats to CSV: {e}")

    def _write_summary_to_csv(self):
        """Write summary statistics to CSV file."""
        if not self._summary_csv_file:
            return

        try:
            # Overwrite summary file each time with latest stats
            with self._summary_csv_file.open("w", newline="") as f:
                fieldnames = [
                    "timestamp",
                    "total_avg_gbps",
                    "total_max_gbps",
                    "total_min_gbps",
                    "samples",
                    "duration_seconds",
                ]
                # Add per-interface summary columns
                for port in sorted(self._interface_stats.keys()):
                    fieldnames.extend([f"port_{port}_avg_gbps", f"port_{port}_max_gbps"])

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                # Calculate duration from first write
                duration = time.time() - (self._last_csv_write - 5)  # Approximate start time

                row = {
                    "timestamp": datetime.now().isoformat(),
                    "total_avg_gbps": f"{self._stats['avg_gbps']:.2f}",
                    "total_max_gbps": f"{self._stats['max_gbps']:.2f}",
                    "total_min_gbps": f"{min(self._stats['avg_gbps'], self._stats['current_gbps']):.2f}",
                    "samples": self._stats["samples"],
                    "duration_seconds": int(duration),
                }
                # Add per-interface summary
                for port, bw_list in self._interface_stats.items():
                    if bw_list:
                        row[f"port_{port}_avg_gbps"] = f"{sum(bw_list) / len(bw_list):.2f}"
                        row[f"port_{port}_max_gbps"] = f"{max(bw_list):.2f}"

                writer.writerow(row)
        except Exception as e:
            self._logger.error(f"Failed to write summary to CSV: {e}")

    def add_log(self, message: str):
        """Add log message to display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"[{timestamp}] {message}"
        self._log_messages.append(msg)
        self._logger.info(f"GUI Log: {msg}")

    def _build_ui(self):
        """Build the monitoring UI."""
        ui.page_title("IPM")

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
        with ui.card().classes("w-full p-4 ml-4 mr-4 mb-4"):
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
        with ui.card().classes("w-full p-4 ml-4 mr-4 mb-4"):
            ui.label("Server Processes").classes("text-h6 mb-2")
            server_table = ui.table(
                columns=[
                    {"name": "ip", "label": "IP", "field": "ip"},
                    {"name": "interface", "label": "Interface", "field": "interface"},
                    {"name": "pid", "label": "PID", "field": "pid"},
                    {"name": "cpu", "label": "CPU%", "field": "cpu"},
                    {"name": "mem", "label": "MEM%", "field": "mem"},
                    {"name": "cmd", "label": "Command", "field": "cmd"},
                    {"name": "time", "label": "Updated", "field": "time"},
                ],
                rows=[],
            ).classes("w-full")

        # Client processes
        with ui.card().classes("w-full p-4 ml-4 mr-4 mb-4"):
            ui.label("Client Processes").classes("text-h6 mb-2")
            client_table = ui.table(
                columns=[
                    {"name": "ip", "label": "IP", "field": "ip"},
                    {"name": "interface", "label": "Interface", "field": "interface"},
                    {"name": "pid", "label": "PID", "field": "pid"},
                    {"name": "cpu", "label": "CPU%", "field": "cpu"},
                    {"name": "mem", "label": "MEM%", "field": "mem"},
                    {"name": "cmd", "label": "Command", "field": "cmd"},
                    {"name": "time", "label": "Updated", "field": "time"},
                ],
                rows=[],
            ).classes("w-full")

        # Log window
        with ui.card().classes("w-full p-4 ml-4 mr-4 mb-4"):
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

                await asyncio.sleep(self._poll_rate_ms / 1000)

        ui.timer(0.1, refresh, once=True)

    def _terminate_traffic(self):
        """Terminate all traffic tests."""
        try:
            self._logger.info("Terminate button clicked in Web UI")
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

            ui.notify("Shutdown signal sent. Closing window in 2 seconds...", type="positive")

            # Close browser tab after 2 seconds
            ui.timer(2.0, lambda: ui.run_javascript("window.close();"), once=True)
        except Exception:
            self._logger.exception("Terminate button error")

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
                    show=True,
                    reload=False,
                    title="IPM",
                    reconnect_timeout=30,
                )
            except Exception:
                self._logger.exception("Web server error")
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
