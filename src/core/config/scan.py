"""Configuration for main_scan.py - SLX/SUT scanning."""

from dataclasses import dataclass

from src.core.enum.connect import ConnectType, ShowPartType
from src.core.enum.messages import LogMsg


@dataclass(frozen=True)
class ScanConfig:
    """Application configuration for SLX/SUT scanning.

    Contains all settings for:
    - Jump host connection
    - SLX switch connection and scan settings
    - SUT system connection and monitoring settings

    Attributes:
        jump_host/user/pass: Jump host credentials
        slx_*: SLX switch settings (host, ports, intervals, toggling)
        sut_*: SUT system settings (host, interfaces, packages, intervals)
    """

    log_level: str
    log_rotation_timeout_sec: int

    jump_host: str
    jump_user: str
    jump_pass: str

    slx_host: str
    slx_user: str
    slx_pass: str
    slx_sudo_pass: str
    slx_scan_ports: list[str]
    slx_scan_interval_sec: int
    slx_port_toggle_limit: int
    slx_port_toggle_wait_sec: int
    slx_port_eyescan_wait_sec: int

    sut_host: str
    sut_user: str
    sut_pass: str
    sut_sudo_pass: str
    sut_scan_interfaces: list[str]
    sut_connect_type: ConnectType
    sut_show_parts: list[ShowPartType]
    sut_time_cmd: bool
    sut_reload_driver: bool
    sut_required_software_packages: list[str]
    sut_scan_interval_low_res_ms: int
    sut_scan_interval_high_res_ms: int
    sut_scan_interval_tx_errors_ms: int
    sut_scan_max_log_size_kb: int
    worker_collect: bool

    @classmethod
    def from_dict(cls, data: dict) -> "ScanConfig":
        """Create ScanConfig from nested JSON structure.

        Args:
            data: Dictionary with jump, slx, and sut configuration sections

        Returns:
            ScanConfig instance
        """
        j, slx, sut = data["jump"], data["slx"], data["sut"]
        return cls(
            log_level=data.get("log_level", "info"),
            log_rotation_timeout_sec=data.get("log_rotation_timeout_sec", 300),
            jump_host=j["host"],
            jump_user=j["user"],
            jump_pass=j["pass"],
            slx_host=slx["host"],
            slx_user=slx["user"],
            slx_pass=slx["pass"],
            slx_sudo_pass=slx["sudo_pass"],
            slx_scan_ports=slx["scan_ports"],
            slx_scan_interval_sec=slx["scan_interval_sec"],
            slx_port_toggle_limit=slx["port_toggle_limit"],
            slx_port_toggle_wait_sec=slx["port_toggle_wait_sec"],
            slx_port_eyescan_wait_sec=slx["port_eye_scan_wait_sec"],
            sut_host=sut["host"],
            sut_user=sut["user"],
            sut_pass=sut["pass"],
            sut_sudo_pass=sut["sudo_pass"],
            sut_scan_interfaces=sut["scan_interfaces"],
            sut_connect_type=ConnectType(sut.get("connect_type", ConnectType.LOCAL.value)),
            sut_show_parts=[ShowPartType(p) for p in sut.get("show_parts", [])],
            sut_time_cmd=sut.get("time_cmd", False),
            sut_reload_driver=sut.get("reload_driver", False),
            sut_required_software_packages=sut["required_software_packages"],
            sut_scan_interval_low_res_ms=sut["scan_interval_low_res_ms"],
            sut_scan_interval_high_res_ms=sut["scan_interval_high_res_ms"],
            sut_scan_interval_tx_errors_ms=sut["scan_interval_tx_errors_ms"],
            sut_scan_max_log_size_kb=sut["scan_max_log_size_kb"],
            worker_collect=data.get("worker_collect", False),
        )

    def validate(self, logger) -> bool:
        """Validate configuration values.

        Args:
            logger: Logger instance for error messages

        Returns:
            bool: True if valid, False otherwise
        """
        errors = []

        no_eye = ShowPartType.NO_SLX_EYE in self.sut_show_parts
        no_dsc = ShowPartType.NO_SLX_DSC in self.sut_show_parts

        if not no_eye and not no_dsc:
            errors.append(f"Neither '{ShowPartType.NO_SLX_EYE.value}' or '{ShowPartType.NO_SLX_DSC.value}' is set")
            errors.append("Only one of the SLX scanner can be enabled at a time")

        if self.log_rotation_timeout_sec <= 0:
            errors.append(f"Invalid log_rotation_timeout_sec: {self.log_rotation_timeout_sec} (must be > 0)")

        if self.slx_scan_interval_sec <= 0:
            errors.append(f"Invalid slx_scan_interval_sec: {self.slx_scan_interval_sec} (must be > 0)")

        if not self.slx_scan_ports:
            errors.append("slx_scan_ports cannot be empty")

        if not self.sut_scan_interfaces:
            errors.append("sut_scan_interfaces cannot be empty")

        if self.sut_scan_interval_low_res_ms <= 0:
            errors.append(f"Invalid sut_scan_interval_low_res_ms: {self.sut_scan_interval_low_res_ms} (must be > 0)")

        if self.sut_scan_interval_high_res_ms <= 0:
            errors.append(f"Invalid sut_scan_interval_high_res_ms: {self.sut_scan_interval_high_res_ms} (must be > 0)")

        if self.sut_scan_max_log_size_kb <= 0:
            errors.append(f"Invalid sut_scan_max_log_size_kb: {self.sut_scan_max_log_size_kb} (must be > 0)")

        if errors:
            logger.error(f"{LogMsg.CONFIG_VALIDATION_FAILED.value}:")
            for error in errors:
                logger.error(f"  - {error}")
            return False

        logger.info(LogMsg.CONFIG_VALIDATION_SUCCESS.value)
        return True
