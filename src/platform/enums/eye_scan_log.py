"""Log message constants for eye scan automation."""

from enum import Enum


class EyeScanLogMsg(str, Enum):
    """Common log messages for eye scan operations."""

    # Connection messages
    SSH_CONN_FAILED = "Failed to establish SSH connection"
    SSH_CONN_SUCCESS = "Connection established successfully"
    SSH_NO_CONN = "No SSH connection available"
    SHELL_OPEN_FAILED = "Failed to open shell"

    # Command execution
    CMD_EXECUTING = "Executing command"
    CMD_RESULT = "Command result"

    # FBR-CLI operations
    FBR_ENTERING = "Entering fbr-CLI"
    FBR_EXITED = "Exited fbr-CLI back to Linux shell"

    # Interface operations
    INTERFACE_LOOKUP = "Looking up interface mapping"
    INTERFACE_FOUND = "Found interface name"
    INTERFACE_NOT_FOUND = "No interface name found for port"
    PORT_ID_FOUND = "Found port ID"
    PORT_ID_NOT_FOUND = "No port ID found for interface"

    # Eye scan operations
    EYE_SCAN_START = "Starting eye scan for interface"
    EYE_SCAN_COMPLETE = "Eye scan completed for"
    EYE_SCAN_FAILED = "Failed to run eye scan"
    EYE_SCAN_WAITING = "Waiting for eye scan to complete"

    # Toggle operations
    TOGGLE_ENABLED = "Port toggling enabled, disabling then enabling interface"
    TOGGLE_EXECUTING = "Toggling interface"
    TOGGLE_WAITING = "Waiting for interface toggle to take effect"
    TOGGLE_FAILED = "Failed to execute toggle command"

    # Cache operations
    CACHE_HIT = "Using cached mapping"
    CACHE_MISS = "Cached mapping"

    # Scan workflow
    SCAN_START = "Start scan for interfaces"
    SCAN_COMPLETE = "Completed scanning interfaces successfully"
    SCAN_NO_INTERFACES = "No interfaces provided for scanning"
    SCAN_PROCESSING = "Processing interface"
    SCAN_SKIPPING = "skipping"

    # Software management
    SW_MGR_INIT = "Software manager initialized"
    SW_MGR_INIT_FAILED = "Failed to initialize software manager"
    SW_INSTALL_START = "Installing required software packages"
    SW_INSTALL_COMPLETE = "Software installation completed"
    SW_INSTALL_FAILED = "Failed to install required software"
    SW_VERSION_LOG = "Logging required software versions"
    SW_VERSION_FAILED = "Failed to log software versions"
    SW_MGR_NOT_INIT = "Software manager not initialized"

    # System info
    SYS_INFO_LOG = "Logging system information"
    SYS_INFO_FAILED = "Failed to log system info"

    # Worker operations
    WORKER_START = "Start scan"
    WORKER_FAILED = "Failed to start scanner"
    WORKER_EXTRACT = "Extracting system value scanner samples"
    WORKER_SHUTDOWN = "Shutting down system value scanner"

    # Main execution
    CONFIG_LOADED = "Configuration loaded successfully"
    CONFIG_FAILED = "Failed to load configuration"
    SCANNER_INIT = "Start system scanner initialization"
    SCANNER_CONN_FAILED = "Failed to connect to system"
    SHUTDOWN_START = "Start graceful shutdown"
    SHUTDOWN_SIGNAL = "Shutdown signal received, stopping scan loop"
    SHUTDOWN_EYE_SCANNER = "Shutting down eye scanner"
