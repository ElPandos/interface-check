"""Log message constants."""

from enum import Enum


class LogMsg(Enum):
    """Log message constants for consistent logging across the application."""

    # === SSH CONNECTION ===
    SSH_CONN_SUCCESS = "SSH connection successful"
    SSH_CONN_FAILED = "SSH connection failed"
    SSH_NO_CONN = "No SSH connection available"
    SSH_ESTABLISHED = "SSH connection established"
    SSH_DISCONNECTED = "SSH connection disconnected"
    SSH_TIMEOUT = "Connection timeout on host"
    SSH_AUTH_FAIL = "Authentication failed for host"
    SSH_PROTOCOL_FAIL = "Protocol error on host"
    SSH_TRANSPORT_INACTIVE = "Connection established but transport is not active"
    SSH_ALREADY_CONNECTED = "Already connected to host"
    SSH_ALREADY_DISCONNECTED = "Already disconnected from host"
    SSH_DISCONNECTING = "Disconnecting from host"
    SSH_DISCONNECT_SUCCESS = "Disconnected from host"
    SSH_RECONNECT = "Attempting to reconnect"
    SSH_RECONNECT_SUCCESS = "Reconnection successful"
    SSH_RECONNECT_FAILED = "Reconnection failed"

    # === SHELL ===
    SHELL_OPEN_FAILED = "Failed to open shell"
    SHELL_OPENED = "Shell opened successfully"
    SHELL_OPEN_SUCCESS = "Shell opened and configured"
    SHELL_CLOSED = "Shell closed"
    SHELL_SKIP = "Skipping shell opening (using exec_cmd instead)"
    SHELL_NOT_CONNECTED = "Cannot open shell: not connected"
    SHELL_ALREADY_OPEN = "Shell already open"
    SHELL_CMD_NO_SHELL = "Cannot execute shell command: shell not opened"
    SHELL_CMD_NO_CON = "Cannot execute shell command: connection lost"

    # === COMMAND EXECUTION ===
    CMD_EXECUTING = "Executing command"
    CMD_RESULT = "Command result"
    CMD_FAILED = "Command execution failed"
    CMD_TIMEOUT = "Command execution timeout"
    CMD_SUCCESS = "Successfully executed command"
    CMD_NO_CONNECTION = "No active connection available"
    CMD_EXEC_FAIL = "Can not execute command"

    # === FBR-CLI ===
    FBR_ENTERING = "Entering fbr-CLI"
    FBR_ENTERED = "Entered fbr-CLI successfully"
    FBR_EXITED = "Exited fbr-CLI"
    FBR_EXIT_CTRL_C = "Sending 'Ctrl+C' to exit fbr-CLI"

    # === INTERFACE LOOKUP ===
    INTERFACE_LOOKUP = "Looking up interface"
    INTERFACE_FOUND = "Interface found"
    INTERFACE_NOT_FOUND = "Interface not found"
    PORT_ID_FOUND = "Port ID found"
    PORT_ID_NOT_FOUND = "Port ID not found"
    PATTERN_SEARCH = "Searching with pattern"

    # === PORT TOGGLE ===
    TOGGLE_ENABLED = "Port toggling enabled"
    TOGGLE_EXECUTING = "Executing toggle"
    TOGGLE_WAITING = "Waiting after toggle"
    TOGGLE_FAILED = "Port toggle failed"

    # === CACHE ===
    CACHE_HIT = "Cache hit"
    CACHE_MISS = "Cache miss"

    # === BUFFER ===
    BUFFER_CLEARING = "Clearing buffer before scan"
    BUFFER_CLEARED = "Buffer cleared"

    # === SCAN OPERATIONS ===
    SCAN_START = "Starting scan"
    SCAN_COMPLETE = "Scan complete"
    SCAN_PROCESSING = "Processing scan"
    SCAN_SKIPPING = "Skipping scan"
    SCAN_NO_INTERFACES = "No interfaces to scan"
    SCAN_ITERATION_FAILED = "Scan iteration failed"

    # === EYE SCAN ===
    EYE_SCAN_START = "Starting eye scan"
    EYE_SCAN_COMPLETE = "Eye scan complete"
    EYE_SCAN_FAILED = "Eye scan failed"
    EYE_SCAN_WAITING = "Waiting for eye scan to complete"

    # === DSC SCAN ===
    DSC_SCAN_START = "Starting DSC scan"
    DSC_SCAN_COMPLETE = "DSC scan complete"
    DSC_SCAN_FAILED = "DSC scan failed"

    # === SOFTWARE MANAGER ===
    SW_MGR_INIT = "Initializing Software Manager"
    SW_MGR_INIT_FAILED = "Failed to initialize software manager"
    SW_MGR_DETECT = "Detecting available package manager"
    SW_MGR_NO_SSH = "No SSH connection available for package manager detection"
    SW_MGR_NO_MANAGER = "No supported package manager detected (APT/YUM)"

    # APT Package Manager
    SW_MGR_APT_CHECK = "Checking for APT package manager"
    SW_MGR_APT_FOUND = "Detected APT package manager (Debian/Ubuntu system)"
    SW_MGR_APT_NOT_FOUND = "APT package manager is not available"
    SW_MGR_APT_INIT = "Initialized APT package manager"

    # YUM Package Manager
    SW_MGR_YUM_CHECK = "Checking for YUM package manager"
    SW_MGR_YUM_FOUND = "Detected YUM package manager (RedHat/CentOS system)"
    SW_MGR_YUM_NOT_FOUND = "YUM package manager is not available"
    SW_MGR_YUM_INIT = "Initialized YUM package manager"

    # Package Operations
    SW_PKG_INSTALL = "Installing package"
    SW_PKG_INSTALL_SUCCESS = "Successfully installed package"
    SW_PKG_INSTALL_FAIL = "Failed to install package"
    SW_PKG_INSTALL_SUMMARY = "All packages installed successfully"
    SW_PKG_INSTALL_PARTIAL = "Installed packages. Failed"
    SW_PKG_NO_PACKAGES = "No packages specified for installation"
    SW_PKG_NO_MANAGER = "Cannot install packages: No package manager available"

    SW_PKG_REMOVE = "Removing package"
    SW_PKG_REMOVE_SUCCESS = "Successfully removed package"
    SW_PKG_REMOVE_FAIL = "Failed to remove package"

    SW_PKG_LIST = "Retrieving list of installed packages"
    SW_PKG_LIST_FAIL = "Failed to retrieve package list"

    SW_PKG_UPDATE = "Updating package index"
    SW_PKG_UPDATE_APT = "Updating APT package index"
    SW_PKG_UPDATE_YUM = "Updating YUM package cache"
    SW_PKG_UPDATE_UNKNOWN = "Unknown package manager type for index update"
    SW_PKG_UPDATE_SUCCESS = "Package index updated successfully"
    SW_PKG_UPDATE_FAIL = "Failed to update package index"

    # Version Management
    SW_PKG_VERSION_PARSE = "Successfully parsed version"
    SW_PKG_VERSION_PARSE_FAIL = "Failed to parse version"
    SW_PKG_VERSION_CHECK = "Verifying installed package versions"
    SW_PKG_VERSION_COMPLETE = "Version verification complete"
    SW_PKG_VALIDATE = "Unsupported packages (no version check available)"

    # Summary and Reporting
    SW_PKG_TABLE_HEADER = "Software Installation Verification Summary"
    SW_PKG_TOTAL = "Total packages verified"
    SW_PKG_SUCCESS = "Successfully installed"
    SW_PKG_FAILED = "Missing or failed"
    SW_PKG_ALL_INSTALLED = "All required packages are properly installed!"
    SW_PKG_MISSING_WARNING = (
        "Some required packages are missing. Consider installing them manually."
    )

    # === SYSTEM INFO ===
    SYS_INFO_LOG = "Logging system information"
    SYS_INFO_FAILED = "Failed to log system information"
    SYS_INFO_START = "Start system information scan"
    SYS_INFO_SKIP = "Skipping system information scan (not in local mode or disabled)"

    # === WORKER MANAGEMENT ===
    WORKER_START = "Starting workers"
    WORKER_FAILED = "Worker startup failed"
    WORKER_STOPPED = "Worker thread stopped unexpectedly"
    WORKER_STOPPED_NAME = "Worker stopped"
    WORKER_JOINED_NAME = "Worker joined"
    WORKER_USER_EXIT = "User pressed 'ctrl+c' - Exiting worker thread"
    WORKER_FOUND = "Found worker"
    WORKER_NOT_FOUND = "Did not find any old worker for interface"
    WORKER_ALREADY_EXISTS = "Worker already exists for command"

    # Worker Pool
    WORKER_POOL_CLEAR = "Clearing workers from pool"
    WORKER_POOL_CLEARED = "Work pool cleared"
    WORKER_POOL_STOP = "Stopping all workers in pool"

    # Worker Operations
    WORKER_EXTRACT = "Extracting worker samples"
    WORKER_SHUTDOWN = "Shutting down workers"
    WORKER_CLEAR_SAMPLES = "Clearing extracted samples"
    WORKER_RESET = "Reset work manager"
    WORKER_RESET_DONE = "Work manager has been resetted"

    # Worker Reconnection
    WORKER_RECONNECT_FAIL = "Reconnect failed"
    WORKER_RECONNECT_SUCCESS = "Reconnect was established successfully"
    WORKER_RECONNECT_ATTEMPT = "Failed to reconnect to host"

    # Worker Logging
    WORKER_LOG_CLEARED = "Cleared log and reset flap flag after one rotation cycle"
    WORKER_LOG_HEADER_FAIL = "Failed to read header from log file"
    WORKER_LOG_CLEAR_FAIL = "Failed to clear log file"

    # === SCANNER - GENERAL ===
    SCANNER_INIT = "Initializing scanners"
    SCANNER_CONN_FAILED = "Scanner connection failed"
    SCANNER_NOT_INIT = "Scanner not initialized"
    SCANNER_START_FAILED = "Failed to start workers"
    SCANNER_WORKERS_CREATED = "Workers created"

    # === SCANNER - SLX ===
    SCANNER_SLX_SKIP = "SLX scanning skipped (both NO_SLX_EYE and NO_SLX_DSC set)"
    SCANNER_SLX_PORTS = "Scanning ports"
    SCANNER_SLX_CONN_HOST = "Connecting to SLX host"

    # SLX Eye Scan
    SCANNER_EYE_START = "Starting eye scan thread"
    SCANNER_EYE_ITER_START = "Start eye scan iteration"
    SCANNER_EYE_ITER_COMPLETE = "Completed eye scan"
    SCANNER_EYE_ITER_FAILED = "Eye scan iteration failed"
    SCANNER_EYE_WAIT = "Waiting before next scan"

    # SLX DSC Scan
    SCANNER_DSC_START = "Starting DSC scan thread"
    SCANNER_DSC_ITER_START = "Start DSC scan iteration"
    SCANNER_DSC_ITER_COMPLETE = "Completed DSC scan"
    SCANNER_DSC_ITER_FAILED = "DSC scan iteration failed"

    # === SCANNER - SUT ===
    SCANNER_SUT_CONN_HOST = "Connecting to SUT host"
    SCANNER_SUT_JUMP_HOST = "Using jump host"
    SCANNER_SUT_TEST_CONN = "Testing connection"
    SCANNER_SUT_CMD_FAILED = "Command failed"
    SCANNER_SUT_SCAN_INTERFACES = "Scanning interfaces"
    SCANNER_SUT_SETUP_INTERFACE = "Setting up workers for interface"
    SCANNER_SUT_PCI_ID = "PCI ID"
    SCANNER_SUT_SHOW_PARTS = "Show parts config"
    SCANNER_SUT_WORKERS_FOR = "Creating workers for interfaces"
    SCANNER_SUT_WORKER_CMD = "Worker command"

    # SUT Software
    SCANNER_SUT_PACKAGES_INSTALL = "Packages to install"
    SCANNER_SUT_PACKAGES_CHECK = "Packages to check"
    SCANNER_SUT_SW_COMPLETE = "Software installation complete"

    # SUT Tools
    SCANNER_SUT_TOOLS_AVAILABLE = "Available tools"
    SCANNER_SUT_TOOL_EXEC = "Executing tool"
    SCANNER_SUT_TOOL_COMPLETE = "Tool completed"

    # === SHUTDOWN ===
    SHUTDOWN_SIGNAL = "Shutdown signal received"
    SHUTDOWN_START = "Starting shutdown"
    SHUTDOWN_COMPLETE = "Shutdown complete"
    SHUTDOWN_TOTAL_COMPLETED = "Shutdown completed"
    SHUTDOWN_SLX_SCANNER = "Shutting SLX scanner"
    SHUTDOWN_SUT_SCANNER = "Shutting SUT scanner"
    SHUTDOWN_EYE_SCANNER = "Shutting down eye scanner"

    # === MAIN APPLICATION ===
    # Configuration
    MAIN_CONFIG_NOT_FOUND = "Config file not found"
    MAIN_CONFIG_SAME_DIR = "Make sure config.json is in the same directory as the executable"
    MAIN_CONFIG_INVALID_JSON = "Invalid JSON in config file"

    # Connection
    MAIN_CONN_FAILED = "Connection failed"
    MAIN_LOCAL_EXEC = "Using local command execution (no SSH)"
    MAIN_LOCAL_CONN_ESTABLISHED = "Local connection established"
    MAIN_SLX_CONN_FAILED = "Failed to connect to SLX eye scanner"

    # Authentication
    MAIN_SUDO_PASSWORD = "Providing sudo password"
    MAIN_PASSWORD_AUTH_RESULT = "Password authentication result"

    # Software Installation
    MAIN_SW_MGR_INIT = "Initializing software manager"
    MAIN_SW_INSTALL_START = "Installing required software packages"
    MAIN_SW_INSTALL_FAILED = "Software installation failed"
    MAIN_SW_INSTALL_WARN = "Failed to install required software, continuing anyway"
    MAIN_SW_VERSION_FAILED = "Failed to log software versions"
    MAIN_SW_VERSION_WARN = "Failed to log installed software versions"

    # Scanning
    MAIN_EYE_SCAN_START = "Start eye scan automation"
    MAIN_SCAN_FAILED_START = "System scanning failed to start"
    MAIN_SCANNER_FAILED = "System scanner failed"
    MAIN_RETRY_WAIT = "Waiting 5 seconds before retry..."

    # Lifecycle
    MAIN_EXIT_PROMPT = "Press Ctrl+C for immediate exit"
    MAIN_EYE_DISCONNECTED = "Eye scanner disconnected"
    MAIN_SCANNER_DISCONNECT = "Disconnecting system scanner"
    MAIN_EXEC_FAILED = "Main execution failed"
    MAIN_LOGS_SAVED = "Logs saved to logs/ directory"

    # === CONFIGURATION ===
    CONFIG_START = "Loading configuration from file"
    CONFIG_LOADED = "Configuration loaded successfully"
    CONFIG_FAILED = "Configuration loading failed"
    CONFIG_CREATED = "Config created"

    # === AGENT ===
    AGENT_NO_SSH = "Cannot start agent: SSH connection not available"
    AGENT_STARTED = "Network agent started"
    AGENT_STOPPED = "Network agent stopped"
    AGENT_TASK_EXEC = "Executing task"
    AGENT_SSH_UNAVAIL = "SSH connection not available"
    AGENT_CMD_FAIL = "Agent command execution failed"

    # === PARSER ===
    PARSER_TIMESTAMP_FAIL = "Failed to parse timestamp"

    # === SAMPLE ===
    SAMPLE_CMD_FAIL = "Sample command execution failed"

    # === KEEPALIVE ===
    ALIVE_THREAD_FAIL = "Keepalive thread encountered an error"
    ALIVE_THREAD_STOP = "Keepalive thread did not stop gracefully"
    ALIVE_NO_ACTIVE = "Keepalive thread did not find any active connections"

    # === STORAGE ===
    STORE_FAIL = "Failed to store results to"

    # === JUMP HOST ===
    CON_JUMP_FAIL = "Failed to establish connection to jump host: "
    CON_JUMP_SUCCESS = "Successfully connected to jump host: "

    # === TARGET CONNECTION ===
    CON_TARGET_SUCCESS = "Successfully connected to target: "
    CON_HOST_SUCCESS = "Successfully connected to host: "
    CON_HOST_FAIL = "Failed to establish connection to host: "
    PRE_HOST_CON = "Already connected to host: "
    POST_HOST_DISCON = "Already disconnected from host: "
    DISCON_HOST = "Disconnecting from host: "
    DISCON_HOST_SUCCESS = "Disconnected from host: "
