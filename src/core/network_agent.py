from datetime import UTC, datetime
import logging
from typing import Any

from src.core.connect import SshConnection

logger = logging.getLogger(__name__)


class NetworkAgent:
    """
    Intelligent network diagnostics agent that can execute automated tasks
    and provide insights based on network interface analysis.
    """

    def __init__(self, ssh_connection: SshConnection):
        self._ssh_connection = ssh_connection
        self._running = False
        self._tasks: list[dict[str, Any]] = []
        self._results: list[dict[str, Any]] = []

    def is_running(self) -> bool:
        """Check if the agent is currently running."""
        return self._running

    def start(self) -> bool:
        """Start the network agent."""
        if not self._ssh.is_connected():
            logger.error("Cannot start agent: SSH connection not available")
            return False

        self._running = True
        logger.info("Network agent started")
        return True

    def stop(self) -> None:
        """Stop the network agent."""
        self._running = False
        logger.info("Network agent stopped")

    async def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a network diagnostic task."""
        if not self._ssh.is_connected():
            return {
                "status": "failed",
                "error": "SSH connection not available",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        task_id = task.get("id", "unknown")
        commands = task.get("commands", [])

        logger.info(f"Executing task {task_id} with {len(commands)} commands")

        results = []
        for command in commands:
            try:
                stdout, stderr = self._ssh.exec_command(command, timeout=30)
                results.append(
                    {
                        "command": command,
                        "stdout": stdout,
                        "stderr": stderr,
                        "success": len(stderr) == 0,
                    }
                )
            except Exception as e:
                logger.exception(f"Command execution failed: {command}")
                results.append(
                    {
                        "command": command,
                        "stdout": "",
                        "stderr": str(e),
                        "success": False,
                    }
                )

        # Analyze results and provide insights
        analysis = self._analyze_results(task, results)

        return {
            "task_id": task_id,
            "status": "completed",
            "results": results,
            "analysis": analysis,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _analyze_results(self, task: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze command results and provide intelligent insights."""
        task_type = task.get("type", "unknown")

        if task_type == "health_check":
            return self._analyze_health_check(results)
        if task_type == "performance":
            return self._analyze_performance(results)
        if task_type == "diagnostics":
            return self._analyze_diagnostics(results)
        if task_type == "backup":
            return self._analyze_backup(results)
        return self._analyze_generic(results)

    def _analyze_health_check(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze interface health check results."""
        analysis = {
            "summary": "Interface Health Analysis",
            "status": "healthy",
            "issues": [],
            "recommendations": [],
        }

        for result in results:
            if not result["success"]:
                analysis["status"] = "warning"
                analysis["issues"].append(f"Command failed: {result['command']}")
                continue

            stdout = result["stdout"].lower()
            command = result["command"]

            # Analyze ethtool output
            if "ethtool" in command and "eth" in command:
                if "link detected: no" in stdout:
                    analysis["status"] = "critical"
                    analysis["issues"].append("Network link is down")
                    analysis["recommendations"].append("Check cable connections and switch port")

                if "speed: unknown" in stdout:
                    analysis["status"] = "warning"
                    analysis["issues"].append("Interface speed unknown")
                    analysis["recommendations"].append("Verify interface configuration")

            # Analyze interface statistics
            if "cat /proc/net/dev" in command:
                lines = result["stdout"].split("\n")
                for line in lines:
                    if "eth" in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            rx_errors = int(parts[3]) if parts[3].isdigit() else 0
                            tx_errors = int(parts[11]) if len(parts) > 11 and parts[11].isdigit() else 0

                            if rx_errors > 0 or tx_errors > 0:
                                analysis["status"] = "warning"
                                analysis["issues"].append(f"Interface errors detected: RX={rx_errors}, TX={tx_errors}")
                                analysis["recommendations"].append("Investigate error causes and check hardware")

        return analysis

    def _analyze_performance(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze performance monitoring results."""
        analysis = {
            "summary": "Performance Analysis",
            "metrics": {},
            "trends": [],
            "recommendations": [],
        }

        for result in results:
            if not result["success"]:
                continue

            command = result["command"]
            stdout = result["stdout"]

            # Analyze ethtool statistics
            if "ethtool -S" in command:
                stats = self._parse_ethtool_stats(stdout)
                analysis["metrics"]["interface_stats"] = stats

                # Check for high error rates
                error_counters = ["rx_errors", "tx_errors", "rx_dropped", "tx_dropped"]
                for counter in error_counters:
                    if counter in stats and stats[counter] > 1000:
                        analysis["recommendations"].append(
                            f"High {counter}: {stats[counter]} - investigate network issues"
                        )

            # Analyze network activity
            if "sar -n DEV" in command:
                network_activity = self._parse_sar_output(stdout)
                analysis["metrics"]["network_activity"] = network_activity

        return analysis

    def _analyze_diagnostics(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze link diagnostics results."""
        analysis = {
            "summary": "Link Diagnostics Analysis",
            "link_status": "unknown",
            "tests_passed": 0,
            "tests_failed": 0,
            "recommendations": [],
        }

        for result in results:
            if not result["success"]:
                analysis["tests_failed"] += 1
                continue

            command = result["command"]
            stdout = result["stdout"].lower()

            # Analyze self-test results
            if "ethtool -t" in command:
                if "pass" in stdout:
                    analysis["tests_passed"] += 1
                    analysis["link_status"] = "good"
                elif "fail" in stdout:
                    analysis["tests_failed"] += 1
                    analysis["link_status"] = "failed"
                    analysis["recommendations"].append("Hardware self-test failed - check NIC and cables")

            # Analyze MII tool output
            if "mii-tool" in command:
                if "link ok" in stdout:
                    analysis["link_status"] = "good"
                elif "no link" in stdout:
                    analysis["link_status"] = "down"
                    analysis["recommendations"].append("Physical link is down - check connections")

        return analysis

    def _analyze_backup(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze configuration backup results."""
        analysis = {
            "summary": "Configuration Backup Analysis",
            "configs_captured": 0,
            "interfaces_found": [],
            "routes_found": 0,
        }

        for result in results:
            if not result["success"]:
                continue

            command = result["command"]
            stdout = result["stdout"]

            if "ip addr show" in command:
                analysis["configs_captured"] += 1
                # Extract interface names
                lines = stdout.split("\n")
                for line in lines:
                    if ": " in line and "state" in line.lower():
                        interface = line.split(":")[1].strip().split("@")[0]
                        if interface not in analysis["interfaces_found"]:
                            analysis["interfaces_found"].append(interface)

            elif "ip route show" in command:
                analysis["configs_captured"] += 1
                analysis["routes_found"] = len([line for line in stdout.split("\n") if line.strip()])

        return analysis

    def _analyze_generic(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Generic analysis for custom tasks."""
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        return {
            "summary": "Task Execution Analysis",
            "commands_executed": len(results),
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful / len(results) * 100):.1f}%" if results else "0%",
        }

    def _parse_ethtool_stats(self, output: str) -> dict[str, int]:
        """Parse ethtool statistics output."""
        stats = {}
        lines = output.split("\n")

        for line in lines:
            if ":" in line:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if value.isdigit():
                        stats[key] = int(value)

        return stats

    def _parse_sar_output(self, output: str) -> dict[str, Any]:
        """Parse sar network activity output."""
        activity = {"interfaces": {}, "summary": {}}
        lines = output.split("\n")

        for line in lines:
            if "eth" in line and "Average:" not in line:
                parts = line.split()
                if len(parts) >= 6:
                    interface = parts[1]
                    activity["interfaces"][interface] = {
                        "rxpck/s": parts[2] if parts[2] != "-" else "0",
                        "txpck/s": parts[3] if parts[3] != "-" else "0",
                        "rxkB/s": parts[4] if parts[4] != "-" else "0",
                        "txkB/s": parts[5] if parts[5] != "-" else "0",
                    }

        return activity

    def get_task_recommendations(self, interface: str = "eth0") -> list[dict[str, Any]]:
        """Get intelligent task recommendations based on current system state."""
        recommendations = [
            {
                "name": "Quick Health Check",
                "description": f"Verify {interface} is operational and configured correctly",
                "commands": [f"ethtool {interface}", f"ip link show {interface}"],
                "priority": "high",
                "estimated_time": "30 seconds",
            },
            {
                "name": "Performance Baseline",
                "description": f"Establish performance baseline for {interface}",
                "commands": [f"ethtool -S {interface}", "sar -n DEV 1 3"],
                "priority": "medium",
                "estimated_time": "1 minute",
            },
            {
                "name": "Comprehensive Diagnostics",
                "description": f"Run full diagnostic suite on {interface}",
                "commands": [
                    f"ethtool -t {interface}",
                    f"ethtool --show-ring {interface}",
                    f"ethtool --show-coalesce {interface}",
                ],
                "priority": "low",
                "estimated_time": "2 minutes",
            },
        ]

        return recommendations
