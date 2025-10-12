from collections.abc import Generator
from contextlib import contextmanager
import logging
from pathlib import Path
import shlex
import subprocess
import threading
from typing import Any

logger = logging.getLogger(__name__)


class Cli:
    """Robust process manager with security, resource management, and error handling."""

    def __init__(self, *, max_processes: int = 50, default_timeout: int = 30) -> None:
        self._procs: list[subprocess.Popen[str]] = []
        self._lock = threading.Lock()
        self._max_processes = max_processes
        self._default_timeout = default_timeout

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
            msg = "Command must be non-empty list of strings"
            raise ValueError(msg)

        with self._lock:
            self._cleanup_finished()
            if len(self._procs) >= self._max_processes:
                raise RuntimeError(f"Too many processes ({self._max_processes} max)")

            try:
                proc = subprocess.Popen(  # noqa: S603
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=cwd,
                    env=env,
                    shell=False,  # Security: no shell injection
                )
                self._procs.append(proc)
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

    def get_output(self, proc: subprocess.Popen[str], *, timeout: int | None = None) -> tuple[str, str, int]:
        """Get process output with timeout and return code.

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        timeout = timeout or self._default_timeout

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            return_code = proc.returncode

            logger.debug(f"Process {proc.pid} finished with code {return_code}")
            if stdout:
                logger.debug(f"STDOUT: {stdout[:500]}{'...' if len(stdout) > 500 else ''}")
            if stderr:
                logger.debug(f"STDERR: {stderr[:500]}{'...' if len(stderr) > 500 else ''}")

            return stdout, stderr, return_code

        except subprocess.TimeoutExpired:
            logger.warning(f"Process {proc.pid} timed out after {timeout}s")
            proc.kill()
            try:
                stdout, stderr = proc.communicate(timeout=5)
                return stdout, stderr, -1
            except subprocess.TimeoutExpired:
                proc.terminate()
                return "", f"Process killed after timeout ({timeout}s)", -1
        except Exception as e:
            logger.exception(f"Error getting output from process {proc.pid}")
            return "", f"Error: {e}", -1
        finally:
            with self._lock:
                if proc in self._procs:
                    self._procs.remove(proc)

    @contextmanager
    def managed_process(self, command: list[str], **kwargs: Any) -> Generator[subprocess.Popen[str]]:
        """Context manager for automatic process cleanup."""
        proc = self.run_safe(command, **kwargs)
        try:
            yield proc
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()

    def _cleanup_finished(self) -> None:
        """Remove finished processes from tracking."""
        self._procs = [p for p in self._procs if p.poll() is None]

    def get_active_count(self) -> int:
        """Get number of active processes."""
        with self._lock:
            self._cleanup_finished()
            return len(self._procs)

    def terminate_all(self) -> None:
        """Terminate all tracked processes."""
        with self._lock:
            for proc in self._procs[:]:
                self._terminate_process(proc)
            self._procs.clear()

    def terminate_by_pid(self, pid: int) -> bool:
        """Terminate specific process by PID.

        Returns:
            True if process was found and terminated
        """
        with self._lock:
            for proc in self._procs[:]:
                if proc.pid == pid:
                    self._terminate_process(proc)
                    self._procs.remove(proc)
                    return True
            return False

    def _terminate_process(self, proc: subprocess.Popen[str]) -> None:
        """Safely terminate a process."""
        if proc.poll() is not None:
            return  # Already finished

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

    def __enter__(self) -> "Cli":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        self.terminate_all()
