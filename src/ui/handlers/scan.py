from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.mixins.tool import Tool


class Scan:
    def __init__(self):
        pass

    def run(self):
        pass


class ScanHandler:
    def __init__(self):
        self._tools: list[Tool] = []

    def run(self):
        pass
