"""Demonstration of the Platform class for SUT management."""

import logging
from typing import Any


# Mock connection for demonstration
class MockConnection:
    def execute_command(self, command: str):
        class Result:
            def __init__(self, stdout: str, success: bool = True):
                self.stdout = stdout
                self.success = success

        # Mock responses for different commands
        responses = {
            "lscpu": "Architecture: x86_64\nCPU(s): 8\nModel name: Intel Core i7",
            "free -h": "Mem: 16Gi 8.0Gi 2.0Gi",
            "which ethtool": "/usr/sbin/ethtool",
            "ethtool --version": "ethtool version 5.16",
            "cat /sys/class/net/eth0/operstate": "up",
            "ping -c 3 8.8.8.8": "3 packets transmitted, 3 received, 0% packet loss",
            "cat /sys/class/thermal/thermal_zone0/temp": "45000",
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'": "15.2%us,",
            "free | grep Mem | awk '{print ($3/$2) * 100.0}'": "65.4",
            "df / | tail -1 | awk '{print $5}' | sed 's/%//'": "42",
        }

        return Result(responses.get(command, "command not found"), command in responses)


# Import after mock to avoid dependency issues
import sys

sys.path.insert(0, "/home/emvekta/projects/interface-check")

try:
    from src.utils.system import Platform, SystemProbe

    # Custom probe example
    class CustomProbe(SystemProbe):
        def probe(self) -> Any:
            return {"custom_metric": 42, "status": "healthy"}

    def demonstrate_platform():
        """Demonstrate Platform class capabilities."""
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("=== Platform Class Demonstration ===")

        # Create platform instance
        connection = MockConnection()
        platform = Platform(connection, "Test-SUT-001")

        logger.info(f"Created platform: {platform}")

        # Hardware information
        logger.info("\n--- Hardware Information ---")
        hw_info = platform.get_hardware_info()
        logger.info(f"CPU Info: {hw_info.get('cpu', {})}")
        logger.info(f"Memory Info: {hw_info.get('memory', 'N/A')}")
        logger.info(f"Interfaces: {hw_info.get('interfaces', [])}")

        # Temperature monitoring
        logger.info("\n--- Temperature Monitoring ---")
        temp = platform.get_temperature("cpu")
        logger.info(f"CPU Temperature: {temp}°C")

        # Power status
        logger.info("\n--- Power Management ---")
        power_status = platform.get_power_status()
        logger.info(f"Power Status: {power_status}")

        # Software management
        logger.info("\n--- Software Management ---")
        ethtool_info = platform.check_software("ethtool")
        logger.info(f"Ethtool: installed={ethtool_info.installed}, version={ethtool_info.version}")

        # Network status
        logger.info("\n--- Network Status ---")
        network_status = platform.get_network_status()
        logger.info(f"Network Interfaces: {network_status}")

        connectivity = platform.test_connectivity()
        logger.info(f"Internet Connectivity: {'OK' if connectivity else 'FAILED'}")

        # Health monitoring
        logger.info("\n--- Health Monitoring ---")
        health = platform.collect_health_metrics()
        logger.info(f"CPU Usage: {health.cpu_usage}%")
        logger.info(f"Memory Usage: {health.memory_usage}%")
        logger.info(f"Disk Usage: {health.disk_usage}%")
        logger.info(f"Temperature: {health.temperature}°C")

        # Custom probes
        logger.info("\n--- Custom Probes ---")
        platform.add_probe("custom_health", CustomProbe())
        probe_results = platform.run_all_probes()
        logger.info(f"Probe Results: {probe_results}")

        # System testing
        logger.info("\n--- System Testing ---")
        platform.log_system_test("connectivity_test", connectivity, "Ping to 8.8.8.8")
        platform.log_system_test("temperature_test", temp < 80, f"CPU temp: {temp}°C")

        logger.info("\n=== Platform Features Demonstrated ===")
        logger.info("✅ Hardware information collection")
        logger.info("✅ Temperature monitoring")
        logger.info("✅ Power management")
        logger.info("✅ Software installation/checking")
        logger.info("✅ Network interface management")
        logger.info("✅ Health monitoring")
        logger.info("✅ Custom probe system")
        logger.info("✅ System test logging")
        logger.info("✅ Manufacturer independent")
        logger.info("✅ Flexible and extensible")

        return True

    if __name__ == "__main__":
        demonstrate_platform()

except ImportError:
    pass
