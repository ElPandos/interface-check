"""Process executor with resource management."""

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

logger = logging.getLogger(LogName.MAIN.value)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    command: str
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    success: bool


class ProcessManager:
    """Manages process lifecycle with automatic cleanup."""

    __slots__ = ("_default_timeout", "_lock", "_max_processes", "_processes")

    def __init__(self, max_processes: int = 50, default_timeout: int = 30):
        self._processes = {}
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
        if not command:
            raise ValueError("Command cannot be empty")

        timeout = timeout or self._default_timeout
        cmd_str = " ".join(command)

        with self._managed_process(command, cwd=cwd, env=env) as proc:
            start = time.perf_counter()

            try:
                proc.wait(timeout=timeout)
                exec_time = time.perf_counter() - start
                rc = proc.returncode or 0

                return ExecutionResult(
                    cmd_str,
                    proc.stdout.read() if proc.stdout else "",
                    proc.stderr.read() if proc.stderr else "",
                    rc,
                    exec_time,
                    rc == 0,
                )

            except subprocess.TimeoutExpired:
                exec_time = time.perf_counter() - start
                proc.kill()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.terminate()

                return ExecutionResult(
                    cmd_str, "", f"Timeout after {timeout} s", -1, exec_time, False
                )

    def execute_shell(self, command: str, **kwargs) -> ExecutionResult:
        return self.execute(shlex.split(command), **kwargs)

    @contextmanager
    def _managed_process(self, command: list[str], **kwargs) -> Generator[subprocess.Popen[str]]:
        with self._lock:
            self._cleanup_finished()
            if len(self._processes) >= self._max_processes:
                raise RuntimeError(f"Too many processes ({self._max_processes} max)")

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            **kwargs,
        )

        with self._lock:
            self._processes[proc.pid] = proc

        try:
            yield proc
        finally:
            with self._lock:
                self._processes.pop(proc.pid, None)
            if proc.poll() is None:
                self._terminate_process(proc)

    def _cleanup_finished(self) -> None:
        finished = [pid for pid, proc in self._processes.items() if proc.poll() is not None]
        for pid in finished:
            del self._processes[pid]

    def _terminate_process(self, proc: subprocess.Popen[str]) -> None:
        if proc.poll() is not None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        except Exception:
            logger.exception(f"Error terminating {proc.pid}")

    def get_active_count(self) -> int:
        with self._lock:
            self._cleanup_finished()
            return len(self._processes)

    def terminate_all(self) -> None:
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
