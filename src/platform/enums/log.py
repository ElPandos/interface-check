from enum import Enum


class LogName(Enum):
    """Log names."""

    CORE_MAIN = "main"
    CORE_MEMORY = "memory"

    SLX_EYE = "slx_eye"

    SUT_SYSTEM_INFO = "sut_system_info"
    SUT_MXLINK = "sut_mxlink"
    SUT_MTEMP = "sut_mtemp"
    SUT_LINK_STATUS = "sut_link_status"
