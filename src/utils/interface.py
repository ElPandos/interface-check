import os
from typing import List


class NetworkInterfaces:
    """
    Utility class to list all network interfaces available on the system.
    Uses /sys/class/net for discovery (safe, no root required).
    """

    def __init__(self, include_virtual: bool = True, include_loopback: bool = True):
        """
        :param include_virtual: If False, skip virtual interfaces (veth, docker, etc.)
        :param include_loopback: If False, skip loopback ("lo")
        """
        self.include_virtual = include_virtual
        self.include_loopback = include_loopback
        self.interfaces: List[str] = self._discover_interfaces()

    def _discover_interfaces(self) -> List[str]:
        interfaces = []
        sys_class_net = "/sys/class/net"

        for iface in os.listdir(sys_class_net):
            # Skip loopback if requested
            if not self.include_loopback and iface == "lo":
                continue

            # Skip common virtual interfaces if requested
            if not self.include_virtual and (
                iface.startswith("veth")
                or iface.startswith("docker")
                or iface.startswith("virbr")
                or iface.startswith("br-")
                or iface.startswith("tun")
                or iface.startswith("tap")
            ):
                continue

            interfaces.append(iface)

        return interfaces

    def list(self) -> List[str]:
        """Return all discovered interfaces."""
        return self.interfaces

    def __repr__(self) -> str:
        return f"NetworkInterfaces(count={len(self.interfaces)}, interfaces={self.interfaces})"


# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":
    # Show all interfaces
    all_ifaces = NetworkInterfaces()
    print(all_ifaces.list())

    # Exclude loopback and virtual devices
    physical_ifaces = NetworkInterfaces(include_virtual=False, include_loopback=False)
    print(physical_ifaces.list())
