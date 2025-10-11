import logging
import subprocess

logger = logging.getLogger(__name__)


class ProcessManager:
    __procs: list[subprocess.Popen[str]]

    def __init__(self) -> None:
        self.__procs = []

    def run(self, command: str) -> subprocess.Popen[str]:
        """Start a process and capture stdout/stderr.

        Note: Uses shell=True for command string parsing.
        Ensure command input is validated to prevent injection.
        """
        proc = subprocess.Popen(  # noqa: S602
            command,
            shell=True,  # allows passing the command as a string
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # decode output as string automatically
        )
        self.__procs.append(proc)
        return proc

    def get_output(self, proc: subprocess.Popen[str], timeout: int | None = None) -> tuple[str, str]:
        """Wait for process to finish and get stdout and stderr.

        :param proc: subprocess.Popen instance
        :param timeout: optional timeout in seconds
        :return: tuple (stdout, stderr)
        """
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            logger.debug(f"STDOUT: {stdout}")
            logger.debug(f"STDERR: {stderr}")
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        return stdout, stderr

    def get_procs(self) -> list[subprocess.Popen[str]]:
        return self.__procs

    def terminate_all(self) -> None:
        for proc in self.__procs:
            self.terminate(proc.pid)
        self.__procs = []

    def terminate(self, pid: int) -> None:
        for proc in self.__procs:
            if proc.poll() is None and pid == proc.pid:
                logger.info(f"Killing process: {proc.pid}")
                proc.kill()
                proc.wait()
