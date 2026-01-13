# This module is deprecated. Import parsers from:
# - src.core.parser.slx for SLX parsers
# - src.core.parser.sut for SUT parsers

# Re-export for backward compatibility
from src.core.parser.slx import SlxDscParser, SlxEyeParser
from src.core.parser.sut import (
    DmesgEvent,
    DmesgFlapDevice,
    DmesgFlapResult,
    EthtoolModuleDevice,
    MlxlinkDevice,
    MstVersionDevice,
    ParsedDevice,
    SutDmesgFlapParser,
    SutEthtoolModuleParser,
    SutIpmitoolFanNameParser,
    SutIpmitoolFanParser,
    SutMlxlinkAmberParser,
    SutMlxlinkParser,
    SutMstStatusVersionParser,
    SutTimeParser,
    SutTxErrorsParser,
    TxErrorsResult,
    ValueWithUnit,
)

__all__ = [
    "DmesgEvent",
    "DmesgFlapDevice",
    "DmesgFlapResult",
    "EthtoolModuleDevice",
    "MlxlinkDevice",
    "MstVersionDevice",
    "ParsedDevice",
    "SlxDscParser",
    "SlxEyeParser",
    "SutDmesgFlapParser",
    "SutEthtoolModuleParser",
    "SutIpmitoolFanNameParser",
    "SutIpmitoolFanParser",
    "SutMlxlinkAmberParser",
    "SutMlxlinkParser",
    "SutMstStatusVersionParser",
    "SutTimeParser",
    "SutTxErrorsParser",
    "TxErrorsResult",
    "ValueWithUnit",
]
