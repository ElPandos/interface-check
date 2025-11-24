"""Command execution result data structure."""


class CmdResult:
    """Result of a command execution."""

    def __init__(
        self,
        cmd: str = "",
        stdout: str = "",
        stderr: str = "",
        rcode: int = 0,
        exec_time: float = 0.0,
        send_ms: float = 0.0,
        read_ms: float = 0.0,
        parsed_ms: float = 0.0,
    ):
        """Initialize command result.

        Args:
            cmd: Command that was executed
            stdout: Standard output
            stderr: Standard error
            rcode: Return code
            exec_time: Execution time in seconds
            send_ms: Time to send command in milliseconds
            read_ms: Time to read response in milliseconds
            parsed_ms: Parsed execution time from time command in milliseconds
        """
        self._cmd = cmd
        self._stdout = stdout
        self._stderr = stderr
        self._rcode = rcode
        self._exec_time = exec_time
        self._send_ms = send_ms
        self._read_ms = read_ms
        self._parsed_ms = parsed_ms

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
    def send_ms(self) -> float:
        """Return send time in milliseconds.

        Returns:
            Send time
        """
        return self._send_ms

    @property
    def read_ms(self) -> float:
        """Return read time in milliseconds.

        Returns:
            Read time
        """
        return self._read_ms

    @property
    def parsed_ms(self) -> float:
        """Return parsed time in milliseconds.

        Returns:
            Parsed time
        """
        return self._parsed_ms

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
