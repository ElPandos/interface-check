import logging
import re

# ------------------------------------------------------------------------------
# Configure structured logging for robust debugging
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-8s] [%(name)-30s] %(message)s")


class MstDeviceParser:
    """
    Parses MST device listings and extracts mappings between PCI IDs and MST device paths.

    Example use case:
        parser = MstDeviceParser(mst_output)
        mst_device = parser.get_mst_by_pci('0000:86:00.0')
    """

    # Regex pattern for capturing /dev/mst/... and corresponding PCI ID
    _mst_pattern = re.compile(
        r"(?P<mst_dev>/dev/mst/\S+).*?domain:bus:dev\.fn=(?P<pci_id>[0-9a-fA-F:]+)", re.DOTALL
    )

    def __init__(self, mst_output: str):
        """
        Initialize the parser with raw MST output (from `mst status` or a file).
        """
        self.mst_output = mst_output
        self.mst_map: dict[str, str] = self._parse_mst_output()

    def _parse_mst_output(self) -> dict[str, str]:
        """
        Internal method to extract all MST device to PCI ID mappings.

        Returns:
            dict: Mapping {pci_id: mst_device}
        """
        mapping = {}
        for match in self._mst_pattern.finditer(self.mst_output):
            pci_id = match.group("pci_id")
            mst_dev = match.group("mst_dev")
            mapping[pci_id] = mst_dev
            logging.debug(f"Found mapping: {pci_id} → {mst_dev}")
        logging.info(f"Parsed {len(mapping)} MST devices.")
        return mapping

    def get_mst_by_pci(self, pci_id: str) -> str | None:
        """
        Retrieve the MST device path for a given PCI ID.

        Args:
            pci_id (str): PCI address in format '0000:86:00.0'

        Returns:
            str | None: MST device path if found, else None.
        """
        mst_dev = self.mst_map.get(pci_id)
        if mst_dev:
            logging.info(f"Match found for PCI {pci_id}: {mst_dev}")
        else:
            logging.warning(f"No MST device found for PCI {pci_id}")
        return mst_dev


# ------------------------------------------------------------------------------
# Example usage
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Example mst status output
    mst_output = """
    /dev/mst/mt4119_pciconf0         - PCI configuration cycles access.
                                       domain:bus:dev.fn=0000:86:00.0 addr.reg=88 data.reg=92 cr_bar.gw_offset=-1
                                       Chip revision is: 00
    /dev/mst/mt4119_pciconf1         - PCI configuration cycles access.
                                       domain:bus:dev.fn=0000:af:00.0 addr.reg=88 data.reg=92 cr_bar.gw_offset=-1
                                       Chip revision is: 00
    /dev/mst/mt4127_pciconf0         - PCI configuration cycles access.
                                       domain:bus:dev.fn=0000:12:00.0 addr.reg=88 data.reg=92 cr_bar.gw_offset=-1
                                       Chip revision is: 00
    """

    parser = MstDeviceParser(mst_output)
    pci_to_find = "0000:86:00"
    mst_name = parser.get_mst_by_pci(pci_to_find)
    print(f"MST device for {pci_to_find}: {mst_name}")
