"""Improved process executor with better resource management and independence."""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
import logging
from pathlib import Path
import shlex
import subprocess
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExecutionResult:
    """Result of command execution."""

    command: str
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    success: bool

    @classmethod
    def from_process(cls, command: str, proc: subprocess.Popen[str], execution_time: float) -> "ExecutionResult":
        """Create result from completed process."""
        return cls(
            command=command,
            stdout=proc.stdout.read() if proc.stdout else "",
            stderr=proc.stderr.read() if proc.stderr else "",
            return_code=proc.returncode or 0,
            execution_time=execution_time,
            success=(proc.returncode or 0) == 0,
        )


class ProcessManager:
    """Manages process lifecycle with automatic cleanup."""

    def __init__(self, max_processes: int = 50, default_timeout: int = 30):
        self._processes: dict[int, subprocess.Popen[str]] = {}
        self._lock = threading.Lock()
        self._max_processes = max_processes
        self._default_timeout = default_timeout

    def execute(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> ExecutionResult:
        """Execute command and return result."""
        if not command or not all(isinstance(arg, str) for arg in command):
            msg = "Command must be non-empty list of strings"
            raise ValueError(msg)

        timeout = timeout or self._default_timeout
        cmd_str = " ".join(command)

        with self._managed_process(command, cwd=cwd, env=env) as proc:
            start_time = time.perf_counter()

            try:
                proc.wait(timeout=timeout)
                execution_time = time.perf_counter() - start_time

                return ExecutionResult(
                    command=cmd_str,
                    stdout=proc.stdout.read() if proc.stdout else "",
                    stderr=proc.stderr.read() if proc.stderr else "",
                    return_code=proc.returncode or 0,
                    execution_time=execution_time,
                    success=(proc.returncode or 0) == 0,
                )

            except subprocess.TimeoutExpired:
                execution_time = time.perf_counter() - start_time
                logger.warning(f"Process {proc.pid} timed out after {timeout}s")

                proc.kill()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.terminate()

                return ExecutionResult(
                    command=cmd_str,
                    stdout="",
                    stderr=f"Process killed after timeout ({timeout}s)",
                    return_code=-1,
                    execution_time=execution_time,
                    success=False,
                )

    def execute_shell(self, command: str, **kwargs) -> ExecutionResult:
        """Execute shell command safely."""
        try:
            parsed_cmd = shlex.split(command)
            return self.execute(parsed_cmd, **kwargs)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {command}") from e

    @contextmanager
    def _managed_process(self, command: list[str], **kwargs) -> Generator[subprocess.Popen[str]]:
        """Context manager for process lifecycle."""
        with self._lock:
            self._cleanup_finished()
            if len(self._processes) >= self._max_processes:
                raise RuntimeError(f"Too many processes ({self._max_processes} max)")

        proc = None
        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,  # Security: no shell injection
                **kwargs,
            )

            with self._lock:
                self._processes[proc.pid] = proc

            logger.debug(f"Started process {proc.pid}: {' '.join(command)}")
            yield proc

        except Exception as e:
            logger.exception(f"Failed to start process: {' '.join(command)}")
            raise RuntimeError(f"Process start failed: {e}") from e
        finally:
            if proc:
                with self._lock:
                    self._processes.pop(proc.pid, None)

                if proc.poll() is None:
                    self._terminate_process(proc)

    def _cleanup_finished(self) -> None:
        """Remove finished processes from tracking."""
        finished = [pid for pid, proc in self._processes.items() if proc.poll() is not None]
        for pid in finished:
            self._processes.pop(pid, None)

    def _terminate_process(self, proc: subprocess.Popen[str]) -> None:
        """Safely terminate a process."""
        if proc.poll() is not None:
            return

        try:
            logger.info(f"Terminating process {proc.pid}")
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning(f"Force killing process {proc.pid}")
            proc.kill()
            proc.wait()
        except Exception:
            logger.exception(f"Error terminating process {proc.pid}")

    def get_active_count(self) -> int:
        """Get number of active processes."""
        with self._lock:
            self._cleanup_finished()
            return len(self._processes)

    def terminate_all(self) -> None:
        """Terminate all tracked processes."""
        with self._lock:
            processes = list(self._processes.values())
            self._processes.clear()

        for proc in processes:
            self._terminate_process(proc)

    def __enter__(self) -> "ProcessManager":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.terminate_all()


# Global process manager instance
_process_manager = ProcessManager()


def get_process_manager() -> ProcessManager:
    """Get global process manager instance."""
    return _process_manager
