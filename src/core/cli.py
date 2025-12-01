"""CLI formatting utilities for pretty output."""


class PrettyFrame:
    """Pretty box-drawing frame for tables and reports."""

    def __init__(self, width: int = 80):
        """Initialize frame with specified width.

        Args:
            width: Total frame width including borders (default: 80)
        """
        self._width = width
        self._content_width = width - 4  # Account for "║ " and " ║"

    def header(self, title: str) -> list[str]:
        """Create frame header with title.

        Args:
            title: Header title text

        Returns:
            List of header lines
        """
        return [
            "",
            "╔" + "═" * (self._width - 2) + "╗",
            "║ " + title.ljust(self._content_width) + " ║",
            "╠" + "═" * (self._width - 2) + "╣",
        ]

    def row(self, content: str) -> str:
        """Create frame row with content.

        Args:
            content: Row content (will be truncated if too long)

        Returns:
            Formatted row string
        """
        truncated = (
            content[: self._content_width] if len(content) > self._content_width else content
        )
        return "║ " + truncated.ljust(self._content_width) + " ║"

    def separator(self) -> str:
        """Create frame separator line.

        Returns:
            Separator line string
        """
        return "╠" + "─" * (self._width - 2) + "╣"

    def footer(self) -> str:
        """Create frame footer.

        Returns:
            Footer line string
        """
        return "╚" + "═" * (self._width - 2) + "╝"

    def build(self, title: str, rows: list[str]) -> str:
        """Build complete framed table.

        Args:
            title: Table title
            rows: List of row contents

        Returns:
            Complete formatted table string
        """
        # Calculate width based on content
        max_len = len(title)
        for row in rows:
            max_len = max(max_len, len(row))
        self._width = max_len + 4  # Add space for "║ " and " ║"
        self._content_width = self._width - 4

        lines = ["", "╔" + "═" * (self._width - 2) + "╗"]
        lines.append("║ " + title.ljust(self._content_width) + " ║")

        if rows:  # Only add separator if there are rows
            lines.append("╠" + "═" * (self._width - 2) + "╣")
            for i, row in enumerate(rows):
                lines.append(self.row(row))
                if i < len(rows) - 1:
                    lines.append(self.separator())

        lines.append("╚" + "═" * (self._width - 2) + "╝")
        total = "\n".join(lines)
        return f"\n{total}\n"
