from dataclasses import dataclass
from datetime import UTC, datetime as dt
import logging
from typing import Any

from src.core.connect import SshConnection
from src.platform.enums.log import LogName

logger = logging.getLogger(LogName.CORE_MAIN.value)


@dataclass(frozen=True)
class TaskResult:
    """Task execution result with command output and status."""

    command: str
    stdout: str
    stderr: str
    success: bool


@dataclass(frozen=True)
class TaskAnalysis:
    """Task analysis result with status, issues, and recommendations."""

    summary: str
    status: str = "unknown"
    issues: list[str] = None
    recommendations: list[str] = None
    metrics: dict[str, Any] = None

    def __post_init__(self) -> None:
        """Initialize default empty collections."""
        if self.issues is None:
            object.__setattr__(self, "issues", [])
        if self.recommendations is None:
            object.__setattr__(self, "recommendations", [])
        if self.metrics is None:
            object.__setattr__(self, "metrics", {})


class Agent:
    """Intelligent network diagnostics agent for automated tasks and network analysis."""

    def __init__(self, ssh_connection: SshConnection) -> None:
        """Initialize agent with SSH connection.

        Args:
            ssh_connection: SSH connection instance
        """
        self._ssh = ssh_connection
        self._running = False

    def is_running(self) -> bool:
        """Check if agent is running.

        Returns:
            True if running
        """
        return self._running

    def start(self) -> bool:
        """Start agent.

        Returns:
            True if started successfully
        """
        if not self._ssh.is_connected():
            logger.error("Cannot start agent: SSH connection not available")
            return False

        self._running = True
        logger.info("Network agent started")
        return True

    def stop(self) -> None:
        """Stop agent."""
        self._running = False
        logger.info("Network agent stopped")

    async def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute diagnostic task with commands and return analysis.

        Args:
            task: Task dictionary with commands

        Returns:
            Task execution result
        """
        if not self._ssh.is_connected():
            return {
                "status": "failed",
                "error": "SSH connection not available",
                "timestamp": dt.now(UTC).isoformat(),
            }

        task_id = task.get("id", "unknown")
        commands = task.get("commands", [])

        logger.info(f"Executing task {task_id} with {len(commands)} commands")

        results = []
        for command in commands:
            try:
                stdout, stderr = self._ssh.exec_command(command, timeout=30)
                results.append(
                    TaskResult(command=command, stdout=stdout, stderr=stderr, success=not stderr)
                )
            except Exception as e:
                logger.exception(f"Command execution failed: {command}")
                results.append(TaskResult(command=command, stdout="", stderr=str(e), success=False))

        analysis = self._analyze_results(task, results)

        return {
            "task_id": task_id,
            "status": "completed",
            "results": [
                {"command": r.command, "stdout": r.stdout, "stderr": r.stderr, "success": r.success}
                for r in results
            ],
            "analysis": analysis.__dict__,
            "timestamp": dt.now(UTC).isoformat(),
        }

    def _analyze_results(self, task: dict[str, Any], results: list[TaskResult]) -> TaskAnalysis:
        """Analyze command results based on task type.

        Args:
            task: Task dictionary
            results: List of task results

        Returns:
            Task analysis
        """
        task_type = task.get("type", "unknown")

        analyzers = {
            "health_check": self._analyze_health_check,
            "performance": self._analyze_performance,
            "diagnostics": self._analyze_diagnostics,
            "backup": self._analyze_backup,
        }

        analyzer = analyzers.get(task_type, self._analyze_generic)
        return analyzer(results)

    def _analyze_health_check(self, results: list[TaskResult]) -> TaskAnalysis:
        """Analyze interface health and link status.

        Args:
            results: List of task results

        Returns:
            Health analysis
        """
        issues = []
        recommendations = []
        status = "healthy"

        for result in results:
            if not result.success:
                status = "warning"
                issues.append(f"Command failed: {result.command}")
                continue

            stdout_lower = result.str_out.lower()

            if "ethtool" in result.command and "eth" in result.command:
                if "link detected: no" in stdout_lower:
                    status = "critical"
                    issues.append("Network link is down")
                    recommendations.append("Check cable connections and switch port")
                elif "speed: unknown" in stdout_lower:
                    status = "warning"
                    issues.append("Interface speed unknown")
                    recommendations.append("Verify interface configuration")

            elif "cat /proc/net/dev" in result.command:
                self._analyze_interface_stats(result.str_out, issues, recommendations)
                if issues and status == "healthy":
                    status = "warning"

        return TaskAnalysis(
            summary="Interface Health Analysis",
            status=status,
            issues=issues,
            recommendations=recommendations,
        )

    def _analyze_performance(self, results: list[TaskResult]) -> TaskAnalysis:
        """Analyze network performance metrics and error rates.

        Args:
            results: List of task results

        Returns:
            Performance analysis
        """
        metrics = {}
        recommendations = []

        for result in results:
            if not result.success:
                continue

            if "ethtool -S" in result.command:
                stats = self._parse_ethtool_stats(result.str_out)
                metrics["interface_stats"] = stats

                # Check for high error rates
                for counter in ["rx_errors", "tx_errors", "rx_dropped", "tx_dropped"]:
                    if counter in stats and stats[counter] > 1000:
                        recommendations.append(
                            f"High {counter}: {stats[counter]} - investigate network issues"
                        )

            elif "sar -n DEV" in result.command:
                metrics["network_activity"] = self._parse_sar_output(result.str_out)

        return TaskAnalysis(
            summary="Performance Analysis", metrics=metrics, recommendations=recommendations
        )

    def _analyze_diagnostics(self, results: list[TaskResult]) -> TaskAnalysis:
        """Analyze link diagnostics and hardware tests.

        Args:
            results: List of task results

        Returns:
            Diagnostics analysis
        """
        link_status = "unknown"
        tests_passed = 0
        tests_failed = 0
        recommendations = []

        for result in results:
            if not result.success:
                tests_failed += 1
                continue

            stdout_lower = result.str_out.lower()

            if "ethtool -t" in result.command:
                if "pass" in stdout_lower:
                    tests_passed += 1
                    link_status = "good"
                elif "fail" in stdout_lower:
                    tests_failed += 1
                    link_status = "failed"
                    recommendations.append("Hardware self-test failed - check NIC and cables")

            elif "mii-tool" in result.command:
                if "link ok" in stdout_lower:
                    link_status = "good"
                elif "no link" in stdout_lower:
                    link_status = "down"
                    recommendations.append("Physical link is down - check connections")

        return TaskAnalysis(
            summary="Link Diagnostics Analysis",
            status=link_status,
            metrics={"tests_passed": tests_passed, "tests_failed": tests_failed},
            recommendations=recommendations,
        )

    def _analyze_backup(self, results: list[TaskResult]) -> TaskAnalysis:
        """Analyze configuration backup completeness.

        Args:
            results: List of task results

        Returns:
            Backup analysis
        """
        configs_captured = 0
        interfaces_found = []
        routes_found = 0

        for result in results:
            if not result.success:
                continue

            if "ip addr show" in result.command:
                configs_captured += 1
                for line in result.str_out.split("\n"):
                    if ": " in line and "state" in line.lower():
                        interface = line.split(":")[1].strip().split("@")[0]
                        if interface not in interfaces_found:
                            interfaces_found.append(interface)

            elif "ip route show" in result.command:
                configs_captured += 1
                routes_found = len([line for line in result.str_out.split("\n") if line.strip()])

        return TaskAnalysis(
            summary="Configuration Backup Analysis",
            metrics={
                "configs_captured": configs_captured,
                "interfaces_found": interfaces_found,
                "routes_found": routes_found,
            },
        )

    def _analyze_generic(self, results: list[TaskResult]) -> TaskAnalysis:
        """Generic task analysis with success rate.

        Args:
            results: List of task results

        Returns:
            Generic analysis
        """
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        success_rate = f"{(successful / len(results) * 100):.1f}%" if results else "0%"

        return TaskAnalysis(
            summary="Task Execution Analysis",
            metrics={
                "commands_executed": len(results),
                "successful": successful,
                "failed": failed,
                "success_rate": success_rate,
            },
        )

    def _parse_ethtool_stats(self, output: str) -> dict[str, int]:
        """Parse ethtool statistics output.

        Args:
            output: Command output

        Returns:
            Statistics dictionary
        """
        stats = {}
        for line in output.split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key, value = key.strip(), value.strip()
                if value.isdigit():
                    stats[key] = int(value)
        return stats

    def _parse_sar_output(self, output: str) -> dict[str, Any]:
        """Parse sar network activity output.

        Args:
            output: Command output

        Returns:
            Network activity dictionary
        """
        interfaces = {}
        for line in output.split("\n"):
            if "eth" in line and "Average:" not in line:
                parts = line.split()
                if len(parts) >= 6:
                    interface = parts[1]
                    interfaces[interface] = {
                        "rxpck/s": parts[2] if parts[2] != "-" else "0",
                        "txpck/s": parts[3] if parts[3] != "-" else "0",
                        "rxkB/s": parts[4] if parts[4] != "-" else "0",
                        "txkB/s": parts[5] if parts[5] != "-" else "0",
                    }
        return {"interfaces": interfaces}

    def _analyze_interface_stats(
        self, stdout: str, issues: list[str], recommendations: list[str]
    ) -> None:
        """Analyze interface statistics from /proc/net/dev.

        Args:
            stdout: Command output
            issues: Issues list to update
            recommendations: Recommendations list to update
        """
        for line in stdout.split("\n"):
            if "eth" in line:
                parts = line.split()
                if len(parts) >= 12:
                    try:
                        rx_errors = int(parts[3]) if parts[3].isdigit() else 0
                        tx_errors = int(parts[11]) if parts[11].isdigit() else 0
                        if rx_errors > 0 or tx_errors > 0:
                            issues.append(
                                f"Interface errors detected: RX={rx_errors}, TX={tx_errors}"
                            )
                            recommendations.append("Investigate error causes and check hardware")
                    except (ValueError, IndexError):
                        continue

    def get_task_recommendations(self, interface: str = "eth0") -> list[dict[str, Any]]:
        """Get task recommendations for interface.

        Args:
            interface: Network interface name

        Returns:
            List of task recommendations
        """
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
