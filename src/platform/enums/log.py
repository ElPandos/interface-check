from enum import Enum


class LogName(Enum):
    """Log names."""

    MAIN = "main"
    MEMORY = "memory"

    SUT_SYSTEM_INFO = "sut_system_info"
    SUT_MXLINK = "sut_mxlink"
    SUT_MTEMP = "sut_mtemp"
    SUT_LINK_FLAP = "sut_link_flap"

    SLX_EYE = "slx_eye"
