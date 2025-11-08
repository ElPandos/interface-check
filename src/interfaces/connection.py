"""Connection interface for abstracting SSH and other remote connections."""


class CmdResult:
    """Result of a command execution."""

    def __init__(
        self,
        cmd: str = "",
        stdout: str = "",
        stderr: str = "",
        rcode: int = 0,
        exec_time: float = 0.0,
    ):
        self._cmd = cmd
        self._stdout = stdout
        self._stderr = stderr
        self._rcode = rcode
        self._exec_time = exec_time

    @property
    def cmd(self) -> str:
        """Cmd data stripped."""
        return self._cmd.strip()

    @property
    def str_out(self) -> str:
        """Stdout data stripped."""
        return self._stdout.strip()

    @property
    def str_err(self) -> str:
        """Stderr data stripped."""
        return self._stderr.strip()

    @property
    def rcode(self) -> int:
        """Return code."""
        return self._rcode

    @property
    def time(self) -> int:
        """Return execution time."""
        return self._exec_time

    @property
    def success(self) -> bool:
        """Indicates whether the executed command was successful or not."""
        return self._rcode == 0 and not self.str_err

    @staticmethod
    def error(cmd: str, stderr: str, rcode: int = -1) -> "CmdResult":
        """
        Create a default error CmdResult objs for failed or skipped executions.

        Args:
            cmd: The command that failed.
            stderr: Description or error message.
            rcode: Optional custom error code (default: -1).

        Returns:
            CmdResult instance representing a failed command.
        """
        return CmdResult(
            cmd=cmd,
            stdout="",
            stderr=stderr,
            rcode=rcode,
            exec_time=0.0,
        )
