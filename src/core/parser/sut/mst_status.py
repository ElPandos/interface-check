from src.core.parser.sut.common import ParsedDevice
from src.interfaces.component import IParser
from src.platform.enums.log import LogName


class MstVersionDevice(ParsedDevice):
    """Mellanox/NVIDIA device entry from mst status -v."""

    def __init__(
        self,
        device_type: str,
        mst: str,
        pci: str,
        rdma: str | None,
        net: str | None,
        numa: str | None,
    ):
        ParsedDevice.__init__(self, LogName.MAIN.value)
        self.device_type = device_type
        self.mst = mst
        self.pci = pci
        self.rdma = rdma if rdma != "-" else None
        self.net = net.replace("net-", "") if net and net.startswith("net-") else net
        self.numa = numa if numa != "-" else None

    def log(self) -> str:
        self._logger.info(
            f"MstDevice(device_type={self.device_type!r}, "
            f"mst={self.mst!r}, pci={self.pci!r}, "
            f"rdma={self.rdma!r}, net={self.net!r}, "
            f"numa={self.numa!r})"
        )


class SutMstStatusVersionParser(IParser):
    """Parser for mst status -v output."""

    def __init__(self):
        IParser.__init__(self, LogName.MAIN.value)
        self._devices: list[MstVersionDevice] = []
        self._raw_data: str | None = None

    @property
    def name(self) -> str:
        return "mst_version"

    def parse(self, raw_data: str) -> None:
        self._log_parse(raw_data)
        self._raw_data = raw_data
        lines = self._raw_data.splitlines()

        start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("DEVICE_TYPE"):
                start_idx = i + 1
                break
        if start_idx is None:
            return

        for line in lines[start_idx:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 6:
                continue

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

        self._logger.debug(f"[{self.name}] Parsed {len(self._devices)} MST devices")

    def get_result(self) -> list[MstVersionDevice]:
        return self._devices

    def get_mst_by_pci(self, pci_id: str) -> str | None:
        for mst in self._devices:
            if mst.pci == pci_id:
                return mst.mst
        return None

    def log(self) -> None:
        for d in self.get_result():
            d.log()
