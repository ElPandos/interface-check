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
        """Initialize command result.

        Args:
            cmd: Command that was executed
            stdout: Standard output
            stderr: Standard error
            rcode: Return code
            exec_time: Execution time in seconds
        """
        self._cmd = cmd
        self._stdout = stdout
        self._stderr = stderr
        self._rcode = rcode
        self._exec_time = exec_time

    @property
    def cmd(self) -> str:
        """Cmd data stripped.

        Returns:
            Command string
        """
        return self._cmd.strip()

    @property
    def stdout(self) -> str:
        """Stdout data stripped.

        Returns:
            Standard output
        """
        return self._stdout.strip()

    @property
    def stderr(self) -> str:
        """Stderr data stripped.

        Returns:
            Standard error
        """
        return self._stderr.strip()

    @property
    def rcode(self) -> int:
        """Return code.

        Returns:
            Return code
        """
        return self._rcode

    @property
    def time(self) -> int:
        """Return execution time.

        Returns:
            Execution time
        """
        return self._exec_time

    @property
    def success(self) -> bool:
        """Indicates whether the executed command was successful or not.

        Returns:
            True if successful
        """
        return self._rcode == 0

    @staticmethod
    def error(cmd: str, stderr: str, rcode: int = -1) -> "CmdResult":
        """Create error CmdResult for failed executions.

        Args:
            cmd: Command that failed
            stderr: Error message
            rcode: Error code

        Returns:
            CmdResult instance
        """
        return CmdResult(
            cmd=cmd,
            stdout="",
            stderr=stderr,
            rcode=rcode,
            exec_time=0.0,
        )
