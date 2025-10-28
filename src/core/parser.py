import logging
import re
from typing import ClassVar

import numpy as np

from src.interfaces.component import IParser

# ---------------------------------------------------------------------------- #
#                                   EYE scan                                   #
# ---------------------------------------------------------------------------- #


class EyeScanParser(IParser):
    """Parse SLX 'phy diag xeX eyescan' CLI output into structured data."""

    _row_pattern = re.compile(r"^\s*([\-]?\d+)mV\s*:\s*([0-9:\-\+\| ]+)$")

    # Map pattern characters to numeric levels (you can tune this mapping)
    _char_map: ClassVar[dict[str, int]] = {
        " ": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "+": 10,
        "-": 5,
        "|": 8,
        ":": 2,
    }

    def __init__(self, raw_output: str):
        self._raw_output = raw_output
        self._rows: list[dict[str, str]] = self._parse_rows()

        self.logger = logging.getLogger("main")

    def name(self) -> str:
        return "eye"

    def _parse_rows(self) -> list[dict[str, str]]:
        """Extract voltage/pattern rows from CLI output."""
        rows = []
        for line in self._raw_output.splitlines():
            match = self._row_pattern.match(line)
            if match:
                voltage, pattern = match.groups()
                rows.append(
                    {
                        "voltage": int(voltage.strip()),
                        "pattern": pattern.rstrip(),
                    }
                )
        return rows

    def result(self) -> tuple[np.ndarray, list[int], list[int]]:
        """
        Convert parsed rows into a numeric 2D matrix for plotting.

        Returns:
            matrix (2D np.ndarray): intensity grid
            voltages (List[int]): Y-axis voltage values
            phase_offsets (List[int]): X-axis phase offset values (-31 to +31)
        """
        voltages = [row["voltage"] for row in self._rows]
        patterns = [row["pattern"] for row in self._rows]
        max_len = max(len(p) for p in patterns)

        # Convert pattern characters → numeric grid
        matrix = np.array(
            [[self._char_map.get(ch, 0) for ch in p.ljust(max_len)] for p in patterns]
        )

        # Create phase offset values from -31 to +31
        phase_offsets = list(range(-31, 32))  # -31 to +31 inclusive

        return matrix, voltages, phase_offsets

    def log(self) -> str:
        return ""


# ---------------------------------------------------------------------------- #
#                                      MST                                     #
# ---------------------------------------------------------------------------- #


# class MstStatusParser(IParser):
#     """
#     Parses MST device listings and extracts mappings between PCI IDs and MST device paths.

#     Example use case:
#         parser = MstDeviceParser(raw_output)
#         mst_device = parser.get_mst_by_pci('0000:86:00')
#     """

#     # Regex pattern for capturing /dev/mst/... and corresponding PCI ID
#     _mst_pattern = re.compile(
#         r"(?P<mst_dev>/dev/mst/\S+).*?domain:bus:dev\.fn=(?P<pci_id>[0-9a-fA-F:]+)", re.DOTALL
#     )

#     def __init__(self, raw_output: str):
#         """
#         Initialize the parser with raw MST output (from `mst status` or a file).
#         """
#         self._raw_output = raw_output
#         self._mst_map: dict[str, str] = self._parse()

#         self.logger = logging.getLogger("main")

#     def name(self) -> str:
#         return "mst"

#     def _parse(self) -> dict[str, str]:
#         """
#         Internal method to extract all MST device to PCI ID mappings.

#         Returns:
#             dict: Mapping {pci_id: mst_device}
#         """
#         mapping = {}
#         for match in self._mst_pattern.finditer(self._raw_output):
#             pci_id = match.group("pci_id")
#             mst_dev = match.group("mst_dev")
#             mapping[pci_id] = mst_dev

#         return mapping

#     def get_mst_by_pci(self, pci_id: str) -> str | None:
#         """
#         Retrieve the MST device path for a given PCI ID.

#         Args:
#             pci_id (str): PCI address in format '0000:86:00'

#         Returns:
#             str | None: MST device path if found, else None.
#         """
#         return self._mst_map.get(pci_id)

#     def result(self) -> Any:
#         return self._mst_map

#     def log(self) -> None:
#         for key, value in self._mst_map.items():
#             pass


class MstVersionDevice:
    """
    Represents a single Mellanox/NVIDIA device entry from `mst status -v`.
    Contains all relevant fields for diagnostics and mapping.
    """

    def __init__(
        self,
        device_type: str,
        mst: str,
        pci: str,
        rdma: str | None,
        net: str | None,
        numa: str | None,
    ):
        self.device_type = device_type
        self.mst = mst
        self.pci = pci
        self.rdma = rdma if rdma != "-" else None
        self.net = net.replace("net-", "") if net and net.startswith("net-") else net
        self.numa = numa if numa != "-" else None

        self.logger = logging.getLogger("main")

    def log(self) -> str:
        self.logger.info(
            f"MstDevice(device_type={self.device_type!r}, "
            f"mst={self.mst!r}, pci={self.pci!r}, "
            f"rdma={self.rdma!r}, net={self.net!r}, "
            f"numa={self.numa!r})"
        )


class MstStatusVersionParser(IParser):
    """
    Parser for `mst status -v` output.
    Provides a list of MstDevice objects for easy programmatic use.
    """

    def __init__(self, raw_output: str):
        self._raw_output = raw_output
        self._devices: list[MstVersionDevice] = []

        self._parse()

        self.logger = logging.getLogger("main")

    def name(self) -> str:
        return "mst version"

    def _parse(self) -> None:
        lines = self._raw_output.splitlines()

        # Find header line (starts with DEVICE_TYPE)
        start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("DEVICE_TYPE"):
                start_idx = i + 1
                break
        if start_idx is None:
            return  # No devices found

        # Parse table rows
        for line in lines[start_idx:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 6:
                continue  # skip malformed lines

            # DEVICE_TYPE can contain spaces, so rebuild carefully
            # Assume MST path always starts with "/dev/mst/"
            try:
                mst_index = next(i for i, p in enumerate(parts) if p.startswith("/dev/mst/"))
            except StopIteration:
                continue

            device_type = " ".join(parts[:mst_index])
            mst = parts[mst_index]
            pci = parts[mst_index + 1]
            rdma = parts[mst_index + 2]
            net = parts[mst_index + 3]
            numa = parts[mst_index + 4] if len(parts) > mst_index + 4 else None

            self._devices.append(MstVersionDevice(device_type, mst, pci, rdma, net, numa))

    def result(self) -> list[MstVersionDevice]:
        return self._devices

    def get_mst_by_pci(self, pci_id: str) -> str | None:
        """
        Retrieve the MST device path for a given PCI ID.

        Args:
            pci_id (str): PCI address in format '86:00.0'

        Returns:
            str | None: MST device path if found, else None.
        """
        for mst in self._devices:
            if mst.pci == pci_id:
                return mst.mst

        return None

    def log(self) -> None:
        for device in self._devices:
            device.log()
