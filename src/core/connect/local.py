"""Local command execution without SSH overhead."""

import logging
import subprocess
import time

from src.core.enum.messages import LogMsg
from src.core.parser import SutTimeParser
from src.core.result import CmdResult
from src.interfaces.component import IConnection
from src.platform.enums.log import LogName


def _log_exec_time(
    exec_time: float,
    exit_code: int,
    send_time: float | None = None,
    read_time: float | None = None,
    time_cmd_ms: float | None = None,
    logger: logging.Logger | None = None,
) -> None:
    """Log command execution time.

    Args:
        exec_time: Total execution time in seconds
        exit_code: Command exit code
        send_time: Optional send time in milliseconds
        read_time: Optional read time in milliseconds
        time_cmd_ms: Optional parsed time from time command in milliseconds
        logger: Logger instance
    """
    exec_ms = exec_time * 1000
    if send_time is not None and read_time is not None:
        time_str = f", time={time_cmd_ms:.1f} ms" if time_cmd_ms else ""
        logger.debug(
            f"Command execution times (send={send_time:.1f} ms, read={read_time:.1f} ms{time_str}, exit:{exit_code})"
        )
    else:
        logger.debug(f"Command completed in {exec_ms:.1f} ms with exit status: {exit_code}")


class LocalConnection(IConnection):
    """Local command execution without SSH overhead.

    Executes commands directly on the local system using subprocess.
    """

    __slots__ = ("_host", "_logger", "_sudo_pass")

    def __init__(self, host: str = "localhost", sudo_pass: str = ""):
        """Initialize local connection.

        Args:
            host: Host identifier for logging (default: localhost)
            sudo_pass: Optional sudo password for privileged commands
        """
        self._host = host
        self._sudo_pass = sudo_pass

        self._logger = logging.getLogger(f"{LogName.MAIN.value}.{host}")

    def __enter__(self) -> "LocalConnection":
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.disconnect()

    def connect(self) -> bool:
        """Establish local connection (always succeeds).

        Returns:
            True
        """
        self._logger.debug(LogMsg.LOCAL_EXEC.value)
        return True

    def disconnect(self) -> None:
        """Disconnect (no-op for local execution)."""
        self._logger.debug(LogMsg.LOCAL_CLOSED.value)

    def is_connected(self) -> bool:
        """Check if connection is active.

        Returns:
            True (always connected for local execution)
        """
        return True

    def exec_cmd(
        self,
        cmd: str,
        timeout: int | None = 20,
        use_time_cmd: bool = False,
        logger: logging.Logger | None = None,
    ) -> CmdResult:
        """Execute command locally.

        Args:
            cmd: Command to execute
            timeout: Timeout in seconds (default: 20)
            use_time_cmd: Wrap command with 'time' for execution timing
            logger: Optional logger to use instead of default

        Returns:
            Command execution result
        """
        exec_cmd = cmd
        log = logger or self._logger

        # Wrap with time command if requested
        if use_time_cmd:
            if self._sudo_pass:
                escaped_cmd = cmd.replace("'", "'\"'\"'")
                exec_cmd = f"time bash -c 'echo \"{self._sudo_pass}\" | sudo -S {escaped_cmd}'"
            else:
                escaped_cmd = cmd.replace("'", "'\"'\"'")
                exec_cmd = f"time bash -c '{escaped_cmd}'"
        elif self._sudo_pass and not cmd.startswith("sudo"):
            exec_cmd = f"sudo -S {cmd}"

        log.debug(f"{LogMsg.LOCAL_CMD_EXEC.value}: '{exec_cmd}' (timeout: {timeout} s)")

        try:
            # Pass sudo password via stdin if needed (only when not using time_cmd)
            use_sudo = self._sudo_pass and not cmd.startswith("sudo") and not use_time_cmd
            stdin_input = f"{self._sudo_pass}\n" if use_sudo else None

            # For local execution, we measure total time as both send and read
            exec_start = time.perf_counter()
            result = subprocess.run(  # noqa: S602
                exec_cmd,
                shell=True,
                capture_output=True,
                text=True,
                input=stdin_input,
                timeout=timeout,
                check=False,
            )
            exec_time = time.perf_counter() - exec_start

            # Parse time command output if present in stderr
            parsed_ms = 0.0
            if result.stderr and ("real" in result.stderr or "elapsed" in result.stderr):
                time_parser = SutTimeParser(log.name)
                time_parser.parse(result.stderr)
                parsed_ms = time_parser.get_result()

            # For local execution, no network send/read times
            _log_exec_time(
                exec_time,
                result.returncode,
                0.0,
                0.0,
                parsed_ms if parsed_ms > 0 else None,
                log,
            )

            if result.returncode != 0:
                log.warning(f"{LogMsg.LOCAL_CMD_STDERR.value}: {result.stderr[:200]}")

            return CmdResult(
                cmd=exec_cmd,
                stdout=result.stdout,
                stderr=result.stderr,
                exec_time=exec_time / 1000,
                rcode=result.returncode,
                send_ms=0.0,
                read_ms=0.0,
                parsed_ms=parsed_ms,
            )

        except subprocess.TimeoutExpired:
            log.exception(f"{LogMsg.LOCAL_CMD_TIMEOUT.value}: {cmd}")
            return CmdResult(exec_cmd, "", "Timeout", -1)
        except Exception as e:
            log.exception(f"{LogMsg.LOCAL_CMD_FAILED.value}: {cmd}")
            return CmdResult(exec_cmd, "", f"Error: {e}", -1)
