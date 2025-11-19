from enum import Enum


class LogMsg(Enum):
    """SSH connection and command execution log messages."""

    # Connection messages
    EXEC_CMD_FAIL = "Can not execute command: "
    STORE_FAIL = "Failed to store results to: "
    PRE_HOST_CON = "Already connected to host: "
    POST_HOST_DISCON = "Already disconnected from host: "
    CON_HOST_FAIL = "Failed to establish connection to host: "
    CON_JUMP_FAIL = "Failed to establish connection to jump host: "
    CON_HOST_SUCCESS = "Successfully connected to host: "
    CON_JUMP_SUCCESS = "Successfully connected to jump host: "
    CON_TARGET_SUCCESS = "Successfully connected to target: "
    DISCON_HOST = "Disconnecting from host: "
    DISCON_HOST_SUCCESS = "Disconnected from host: "
    CON_TIMEOUT = "Connection timeout on host: "
    CON_AUTH_FAIL = "Authentication failed for host: "
    CON_PROTOCOL_FAIL = "Protocol error on host: "
    CON_TRANSPORT_INACTIVE = "Connection established but transport is not active"
    ALIVE_THREAD_FAIL = "Keepalive thread encountered an error"
    ALIVE_THREAD_STOP = "Keepalive thread did not stop gracefully"
    ALIVE_NO_ACTIVE = "Keepalive thread did not find any active connections"
    SHELL_NOT_CONNECTED = "Cannot open shell: not connected"
    SHELL_ALREADY_OPEN = "Shell already open"
    SHELL_OPEN_SUCCESS = "Shell opened and configured"
    SHELL_CMD_NO_SHELL = "Cannot execute shell command: shell not opened"
    SHELL_CMD_NO_CON = "Cannot execute shell command: connection lost"
    CMD_CON = "No active connection available"

    # Configuration messages
    CONFIG_START = "Loading configuration from file"
    CONFIG_LOADED = "Configuration loaded successfully"
    CONFIG_FAILED = "Configuration loading failed"
    CONFIG_CREATED = "Config created"

    # Command execution messages
    CMD_EXECUTING = "Executing command"
    CMD_RESULT = "Command result"

    # SSH connection messages
    SSH_CONN_FAILED = "SSH connection failed"
    SSH_CONN_SUCCESS = "SSH connection successful"
    SSH_NO_CONN = "No SSH connection available"

    # Shell messages
    SHELL_OPEN_FAILED = "Failed to open shell"

    # Eye scan messages
    EYE_SCAN_START = "Starting eye scan"
    EYE_SCAN_COMPLETE = "Eye scan complete"
    EYE_SCAN_FAILED = "Eye scan failed"

    # Port ID messages
    PORT_ID_FOUND = "Port ID found"
    PORT_ID_NOT_FOUND = "Port ID not found"

    # Interface messages
    INTERFACE_FOUND = "Interface found"
    INTERFACE_NOT_FOUND = "Interface not found"
    INTERFACE_LOOKUP = "Looking up interface"

    # FBR CLI messages
    FBR_ENTERING = "Entering fbr-CLI"
    FBR_EXITED = "Exited fbr-CLI"

    # Toggle messages
    TOGGLE_EXECUTING = "Executing toggle"
    TOGGLE_WAITING = "Waiting for toggle"
    TOGGLE_ENABLED = "Port toggling enabled"
    TOGGLE_FAILED = "Toggle failed"

    # Scan messages
    SCAN_START = "Starting scan"
    SCAN_COMPLETE = "Scan complete"
    SCAN_PROCESSING = "Processing scan"
    SCAN_SKIPPING = "Skipping scan"
    SCAN_NO_INTERFACES = "No interfaces to scan"

    # Cache messages
    CACHE_HIT = "Cache hit"
    CACHE_MISS = "Cache miss"

    # Software manager messages
    SW_MGR_INIT = "Initializing Software Manager"
    SW_MGR_DETECT = "Detecting available package manager"
    SW_MGR_NO_SSH = "No SSH connection available for package manager detection"
    SW_MGR_APT_CHECK = "Checking for APT package manager"
    SW_MGR_APT_FOUND = "Detected APT package manager (Debian/Ubuntu system)"
    SW_MGR_APT_NOT_FOUND = "APT package manager is not available"
    SW_MGR_YUM_CHECK = "Checking for YUM package manager"
    SW_MGR_YUM_FOUND = "Detected YUM package manager (RedHat/CentOS system)"
    SW_MGR_YUM_NOT_FOUND = "YUM package manager is not available"
    SW_MGR_NO_MANAGER = "No supported package manager detected (APT/YUM)"
    SW_MGR_APT_INIT = "Initialized APT package manager"
    SW_MGR_YUM_INIT = "Initialized YUM package manager"
    SW_PKG_INSTALL = "Installing package"
    SW_PKG_INSTALL_SUCCESS = "Successfully installed package"
    SW_PKG_INSTALL_FAIL = "Failed to install package"
    SW_PKG_REMOVE = "Removing package"
    SW_PKG_REMOVE_SUCCESS = "Successfully removed package"
    SW_PKG_REMOVE_FAIL = "Failed to remove package"
    SW_PKG_LIST = "Retrieving list of installed packages"
    SW_PKG_LIST_FAIL = "Failed to retrieve package list"
    SW_PKG_VERSION_PARSE = "Successfully parsed version"
    SW_PKG_VERSION_PARSE_FAIL = "Failed to parse version"
    SW_PKG_VALIDATE = "Unsupported packages (no version check available)"
    SW_PKG_NO_PACKAGES = "No packages specified for installation"
    SW_PKG_NO_MANAGER = "Cannot install packages: No package manager available"
    SW_PKG_INSTALL_SUMMARY = "All packages installed successfully"
    SW_PKG_INSTALL_PARTIAL = "Installed packages. Failed"
    SW_PKG_VERSION_CHECK = "Verifying installed package versions"
    SW_PKG_VERSION_COMPLETE = "Version verification complete"
    SW_PKG_TABLE_HEADER = "Software Installation Verification Summary"
    SW_PKG_TOTAL = "Total packages verified"
    SW_PKG_SUCCESS = "Successfully installed"
    SW_PKG_FAILED = "Missing or failed"
    SW_PKG_ALL_INSTALLED = "All required packages are properly installed!"
    SW_PKG_MISSING_WARNING = (
        "Some required packages are missing. Consider installing them manually."
    )
    SW_PKG_UPDATE = "Updating package index"
    SW_PKG_UPDATE_APT = "Updating APT package index"
    SW_PKG_UPDATE_YUM = "Updating YUM package cache"
    SW_PKG_UPDATE_UNKNOWN = "Unknown package manager type for index update"
    SW_PKG_UPDATE_SUCCESS = "Package index updated successfully"
    SW_PKG_UPDATE_FAIL = "Failed to update package index"

    # System info messages
    SYS_INFO_LOG = "Logging system information"
    SYS_INFO_FAILED = "Failed to log system information"

    # Worker messages
    WORKER_START = "Starting workers"
    WORKER_FAILED = "Worker startup failed"
    WORKER_EXTRACT = "Extracting worker samples"
    WORKER_SHUTDOWN = "Shutting down workers"
    WORKER_RECONNECT_FAIL = "Reconnect failed"
    WORKER_RECONNECT_SUCCESS = "Reconnect was established successfully"
    WORKER_RECONNECT_ATTEMPT = "Failed to reconnect to host"
    WORKER_STOPPED = "Worker thread stopped unexpectedly"
    WORKER_USER_EXIT = "User pressed 'ctrl+c' - Exiting worker thread"
    WORKER_CLEAR_SAMPLES = "Clearing extracted samples"
    WORKER_LOG_CLEARED = "Cleared log and reset flap flag after one rotation cycle"
    WORKER_LOG_HEADER_FAIL = "Failed to read header from log file"
    WORKER_LOG_CLEAR_FAIL = "Failed to clear log file"
    WORKER_FOUND = "Found worker"
    WORKER_NOT_FOUND = "Did not find any old worker for interface"
    WORKER_ALREADY_EXISTS = "Worker already exists for command"
    WORKER_POOL_CLEAR = "Clearing workers from pool"
    WORKER_POOL_CLEARED = "Work pool cleared"
    WORKER_POOL_STOP = "Stopping all workers in pool"
    WORKER_STOPPED_NAME = "Worker stopped"
    WORKER_JOINED_NAME = "Worker joined"
    WORKER_RESET = "Reset work manager"
    WORKER_RESET_DONE = "Work manager has been resetted"

    # Scanner messages
    SCANNER_INIT = "Initializing scanners"
    SCANNER_CONN_FAILED = "Scanner connection failed"

    # Shutdown messages
    SHUTDOWN_SIGNAL = "Shutdown signal received"
    SHUTDOWN_START = "Starting shutdown"
    SHUTDOWN_EYE_SCANNER = "Shutting down eye scanner"

    # Agent messages
    AGENT_NO_SSH = "Cannot start agent: SSH connection not available"
    AGENT_STARTED = "Network agent started"
    AGENT_STOPPED = "Network agent stopped"
    AGENT_TASK_EXEC = "Executing task"
    AGENT_CMD_FAIL = "Command execution failed"
    AGENT_SSH_UNAVAIL = "SSH connection not available"

    # Parser messages
    PARSER_TIMESTAMP_FAIL = "Failed to parse timestamp"

    # Sample messages
    SAMPLE_CMD_FAIL = "Command execution failed"

    # Tool messages
    TOOL_CMD_SUCCESS = "Succesfully executed command"
