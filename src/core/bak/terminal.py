from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
import logging
from pathlib import Path
import shlex
import subprocess
import threading
from typing import Any
import weakref

logger = logging.getLogger(LogName.MAIN.value)


@dataclass(frozen=True)
class ProcessResult:
    """Structured process execution result."""

    stdout: str
    stderr: str
    return_code: int

    @property
    def success(self) -> bool:
        """Check if process completed successfully."""
        return self.return_code == 0


@dataclass(frozen=True)
class ProcessConfig:
    """Process execution configuration."""

    max_processes: int = 50
    default_timeout: int = 30
    cleanup_timeout: int = 5


class Cli:
    """Robust process manager with security, resource management, and error handling."""

    def __init__(self, *, max_processes: int = 50, default_timeout: int = 30) -> None:
        self._cfg = ProcessConfig(max_processes, default_timeout)
        self._procs: weakref.WeakSet[subprocess.Popen[str]] = weakref.WeakSet()
        self._lock = threading.RLock()

    def run_safe(
        self, command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None
    ) -> subprocess.Popen[str]:
        """Run command safely without shell injection risks.

        Args:
            command: Command as list of strings
            cwd: Working directory
            env: Environment variables
        """
        if not command or not all(isinstance(arg, str) for arg in command):
            raise ValueError("Command must be non-empty list of strings")

        with self._lock:
            if len(self._procs) >= self._cfg.max_processes:
                raise RuntimeError(f"Too many processes ({self._cfg.max_processes} max)")

            try:
                proc = subprocess.Popen(  # noqa: S603
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=cwd,
                    env=env,
                    shell=False,
                )
                self._procs.add(proc)
                logger.debug(f"Started process {proc.pid}: {' '.join(command)}")
                return proc
            except Exception as e:
                logger.exception(f"Failed to start process: {' '.join(command)}")
                raise RuntimeError(f"Process start failed: {e}") from e

    def run(self, command: str, *, cwd: Path | None = None) -> subprocess.Popen[str]:
        """Legacy method - parses shell command safely."""
        try:
            parsed_cmd = shlex.split(command)
            return self.run_safe(parsed_cmd, cwd=cwd)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {command}") from e

    def get_output(self, proc: subprocess.Popen[str], *, timeout: int | None = None) -> ProcessResult:
        """Get process output with timeout and return code."""
        timeout = timeout or self._cfg.default_timeout

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            stdout = stdout.strip()
            stderr = stderr.strip()
            return_code = proc.returncode or 0

            logger.debug(f"Process {proc.pid} finished with return code: {return_code}")
            if stdout:
                logger.debug(f"STDOUT: {stdout[:500]}{'...' if len(stdout) > 500 else ''}")
            if stderr:
                logger.debug(f"STDERR: {stderr[:500]}{'...' if len(stderr) > 500 else ''}")

            return ProcessResult(stdout.strip(), stderr.strip(), return_code)

        except subprocess.TimeoutExpired:
            logger.warning(f"Process {proc.pid} timed out after {timeout}s")
            self._force_terminate(proc)
            return ProcessResult("", f"Process killed after timeout ({timeout}s)", -1)
        except Exception as e:
            logger.exception(f"Error getting output from process {proc.pid}")
            return ProcessResult("", f"Error: {e}", -1)

    def run_and_get_output(self, command: list[str], *, timeout: int | None = None, **kwargs: Any) -> ProcessResult:
        """Run command and get output in one call."""
        proc = self.run_safe(command, **kwargs)
        return self.get_output(proc, timeout=timeout)

    @contextmanager
    def managed_process(self, command: list[str], **kwargs: Any) -> Generator[subprocess.Popen[str]]:
        """Context manager for automatic process cleanup."""
        proc = self.run_safe(command, **kwargs)
        try:
            yield proc
        finally:
            self._safe_terminate(proc)

    def _safe_terminate(self, proc: subprocess.Popen[str]) -> None:
        """Safely terminate a single process."""
        if proc.poll() is not None:
            return

        try:
            proc.terminate()
            proc.wait(timeout=self._cfg.cleanup_timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        except Exception:
            logger.exception(f"Error terminating process {proc.pid}")

    def _force_terminate(self, proc: subprocess.Popen[str]) -> None:
        """Force terminate process after timeout."""
        try:
            proc.kill()
            proc.communicate(timeout=self._cfg.cleanup_timeout)
        except subprocess.TimeoutExpired:
            proc.terminate()
        except Exception:
            logger.exception(f"Error force terminating process {proc.pid}")

    def get_active_count(self) -> int:
        """Get number of active processes."""
        with self._lock:
            return len([p for p in self._procs if p.poll() is None])

    def terminate_all(self) -> None:
        """Terminate all tracked processes."""
        with self._lock:
            procs_to_terminate = list(self._procs)

        for proc in procs_to_terminate:
            self._safe_terminate(proc)

    def terminate_by_pid(self, pid: int) -> bool:
        """Terminate specific process by PID.

        Returns:
            True if process was found and terminated
        """
        with self._lock:
            for proc in list(self._procs):
                if proc.pid == pid:
                    self._safe_terminate(proc)
                    return True
            return False

    def get_process_list(self) -> list[int]:
        """Get list of active process PIDs."""
        with self._lock:
            return [p.pid for p in self._procs if p.poll() is None]

    def __enter__(self) -> "Cli":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        self.terminate_all()

    def __len__(self) -> int:
        """Get number of active processes."""
        return self.get_active_count()
