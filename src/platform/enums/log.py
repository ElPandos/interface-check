from enum import Enum


class LogName(Enum):
    """Log names."""

    MAIN = "main"

    SLX_EYE_SCANNER = "slx_eye_scanner"
    SUT_SYSTEM_INFO = "sut_system_info"
    SUT_VALUE_SCANNER = "sut_value_scanner"
