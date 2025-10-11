from src.utils.commands import Mst
from src.utils.ssh_connection import SshConnection


class MstDevice:
    """
    Represents a single Mellanox/NVIDIA device entry from `mst status -v`.
    Contains all relevant fields for diagnostics and mapping.
    """

    def __init__(self, device_type: str, mst: str, pci: str, rdma: str | None, net: str | None, numa: str | None):
        self.device_type = device_type
        self.mst = mst
        self.pci = pci
        self.rdma = rdma if rdma != "-" else None
        self.net = net.replace("net-", "") if net and net.startswith("net-") else net
        self.numa = numa if numa != "-" else None

    def __repr__(self):
        return (
            f"MstDevice(device_type={self.device_type!r}, "
            f"mst={self.mst!r}, pci={self.pci!r}, "
            f"rdma={self.rdma!r}, net={self.net!r}, "
            f"numa={self.numa!r})"
        )


class MstStatus:
    """
    Parser for `mst status -v` output.
    Provides a list of MstDevice objects for easy programmatic use.
    """

    def __init__(self, raw_output: str):
        self.raw_output = raw_output
        self.devices: list[MstDevice] = self._parse_output()

    def _parse_output(self) -> list[MstDevice]:
        devices: list[MstDevice] = []
        lines = self.raw_output.splitlines()

        # Find header line (starts with DEVICE_TYPE)
        start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("DEVICE_TYPE"):
                start_idx = i + 1
                break
        if start_idx is None:
            return devices  # no devices found

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

            devices.append(MstDevice(device_type, mst, pci, rdma, net, numa))

        return devices

    def from_system(self, ssh_connection: SshConnection = None) -> "MstStatus":
        out, err = ssh_connection.exec_command(Mst.DEVICES)

        if err:
            raise RuntimeError(f"MST command failed: {err.strip()}")

        return MstStatus(out)

    def print_devices(self) -> None:
        for dev in self.devices:
            print(dev)
