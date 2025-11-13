# ---------------------------------------------------------------------------- #
#                                 Base command                                 #
# ---------------------------------------------------------------------------- #


class Command:
    command_type: Type
    syntax: str

    def __init__(self, command_type: Type) -> None:
        self.command_type = command_type


# ---------------------------------------------------------------------------- #
#                                Modify command                                #
# ---------------------------------------------------------------------------- #


class Modify(Command):
    def __init__(self) -> None:
        super().__init__(Type.MODIFY)

    def to_list(self, data: str) -> list[str]:
        data = data.strip()
        return data.splitlines()


# ---------------------------------------------------------------------------- #
#                             Install python3 libs                             #
# ---------------------------------------------------------------------------- #


class System(Command):
    PYTHON_PSUTIL: str = "sudo apt-get install -y python3-psutil"
    PYTHON_UPGRADE_PIP: str = "pip3 install --upgrade pip"

    def __init__(self) -> None:
        super().__init__(Type.SYSTEM)

    def install_psutil(self) -> Command:
        self.syntax = self.PYTHON_PSUTIL
        return self

    def upgrade_pip(self) -> Command:
        self.syntax = self.PYTHON_UPGRADE_PIP
        return self


# ---------------------------------------------------------------------------- #
#                                    Python                                    #
# ---------------------------------------------------------------------------- #


class Python(Command):
    LICENSES: str = "uv run pip-licenses --format=json"

    def __init__(self) -> None:
        super().__init__(Type.PYTHON)

    def licenses(self) -> Command:
        self.syntax = self.LICENSES
        return self


# ---------------------------------------------------------------------------- #
#                                Common Commands                               #
# ---------------------------------------------------------------------------- #


class Common(Command):
    INTERFACES: str = "import psutil; print('\\n'.join(psutil.net_if_addrs().keys()))"

    def __init__(self) -> None:
        super().__init__(Type.COMMON)

    def get_interfaces(self) -> Command:
        self.syntax = f'python3 -c "{self.INTERFACES}"'
        return self


# ---------------------------------------------------------------------------- #
#                               Ethtool commands                               #
# ---------------------------------------------------------------------------- #


class Ethtool(Command):
    def __init__(self) -> None:
        super().__init__(Type.ETHTOOL)

    def module_info(self, interface: str) -> Command:
        self.syntax = f"sudo ethtool -m {interf}"
        return self

    def stats(self, interface: str) -> Command:
        self.syntax = f"sudo ethtool -S {interf}"
        return self

    def info(self, interface: str) -> Command:
        self.syntax = f"sudo ethtool {interf}"
        return self


# ---------------------------------------------------------------------------- #
#                               Mlxlink commands                               #
# ---------------------------------------------------------------------------- #


class Mlxlink(Command):
    def __init__(self) -> None:
        super().__init__(Type.MLXLINK)

    def serdes_tx(self, interface: str) -> str:
        """Show some MLNX CX-6Lx TX serdes params."""
        return f"sudo mlxlink -d {interf} --show_serdes_tx"

    def rs_fec_err_counters(self, interface: str) -> str:
        """Show MLNX CX-6 Lx RX received signal RS-FEC error counters :"""
        return f"sudo mlxlink -d {interf} --rx_fec_histogram --show_histogram"


# ---------------------------------------------------------------------------- #
#                              Mlxconfig commands                              #
# ---------------------------------------------------------------------------- #


class Mlxconfig(Command):
    def __init__(self) -> None:
        super().__init__(Type.MLXCONFIG)

    def query(self, interface: str) -> Command:
        self.syntax = f"sudo mlxconfig -d {interf} query"
        return self


# ---------------------------------------------------------------------------- #
#                                 MST commands                                 #
# ---------------------------------------------------------------------------- #


class Mst(Command):
    STATUS: str = "sudo mst status -v"
    DEVICES: str = "sudo mst status -v | grep -o '/dev/mst/[^ ]*'"

    def __init__(self) -> None:
        super().__init__(Type.MST)

    def status(self) -> Command:
        self.syntax = self.STATUS
        return self

    def devices(self) -> Command:
        self.syntax = self.DEVICES
        return self


# ---------------------------------------------------------------------------- #
#                                 Git commands                                 #
# ---------------------------------------------------------------------------- #


class Git(Command):
    PATCHSET: str = "git rev-parse --short HEAD"

    def __init__(self) -> None:
        super().__init__(Type.GIT)

    def patchset(self) -> Command:
        self.syntax = self.PATCHSET
        return self
