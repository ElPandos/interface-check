import subprocess
from typing import List, Optional, Tuple

from src.ui.tabs.log import logger


class ProcessManager:
    __procs: List[subprocess.Popen]

    def __init__(self) -> None:
        self.__procs = []

    def run(self, command: str) -> subprocess.Popen:
        """Start a process and capture stdout/stderr."""
        proc = subprocess.Popen(
            command,
            shell=True,  # allows passing the command as a string
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # decode output as string automatically
        )
        self.__procs.append(proc)
        return proc

    def get_output(self, proc: subprocess.Popen, timeout: Optional[int] = None) -> Tuple[str, str]:
        """Wait for process to finish and get stdout and stderr.

        :param proc: subprocess.Popen instance
        :param timeout: optional timeout in seconds
        :return: tuple (stdout, stderr)
        """
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            logger.debug(f"Footer: STDOUT: {stdout}")
            logger.debug(f"Footer: STDERR: {stderr}")
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        return stdout, stderr

    def get_procs(self) -> List:
        return self.__procs

    def terminate_all(self) -> None:
        for proc in self.__procs:
            self.terminate(proc.pid)
        self.__procs = []

    def terminate(self, pid: int) -> None:
        for proc in self.__procs:
            if proc.poll() is None and pid == proc.pid:
                logging.info(f"Killing process: {proc.pid}")
                proc.kill()
                proc.wait()
