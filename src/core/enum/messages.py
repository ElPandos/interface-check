"""Log message constants."""

from enum import Enum


class LogMsg(Enum):
    """Log message constants for consistent logging across the application."""

    # ---------------------------------------------------------------------------- #
    #                         CConnections local or remote                         #
    # ---------------------------------------------------------------------------- #

    # Connection
    CONN_ALREADY_CONNECTED = "Already connected to host"
    CONN_ALREADY_DISCONNECTED = "Already disconnected from host"
    CONN_DISCONNECTING = "Disconnecting from host"
    CONN_DISCONNECT_FAILED = "Failed disconnecting from host"
    CONN_DISCONNECTED = "Disconnected from host"
    CONN_RECONNECT = "Attempting to reconnect"
    CONN_RECONNECT_SUCCESS = "Reconnection successful"
    CONN_RECONNECT_FAILED = "Reconnection failed"
    CONN_NONE_AVAILABLE = "No connection available"
    CONN_PROTOCOL_ERROR = "Protocol error on host"
    CONN_AUTH_FAILED = "Authentication failed for host"
    CONN_TIMEOUT = "Connection timeout on host"
    CONN_TARGET_SUCCESS = "Successfully connected to target"
    CONN_HOST_SUCCESS = "Successfully connected to host"
    CONN_HOST_FAILED = "Failed to establish connection to host: "
    CONN_FAILED = "Connection failed"
    CONN_LOCAL_ESTABLISHED = "Local connection established"

    # Connection
    CONN_SLX_FAILED = "Failed to connect to SLX"

    # Jump Host
    CONN_JUMP_FAILED = "Failed to establish connection to jump host"
    CONN_JUMP_SUCCESS = "Successfully connected to jump host"

    # Target Connection
    CONN_CONNECTING = "Connecting to hosts..."
    CONN_ESTABLISHED = "Connection established to hosts..."
    CONN_TRANSPORT_INACTIVE = "Connection established but transport is not active"

    # SSH Connection
    SSH_CONN_SUCCESS = "SSH connection successful"
    SSH_CONN_FAILED = "SSH connection failed"
    SSH_CONN_NOT_AVAILABLE = "SSH connection not available"
    SSH_CONN_ESTABLISHED = "SSH connection established"
    SSH_CONN_DISCONNECTED = "SSH connection disconnected"
    SSH_CONN_TIMEOUT = "SSH connection timeout"
    SSH_CONN_AUTH_FAILED = "SSH authentication failed"
    SSH_CONN_PROTOCOL_FAILED = "SSH protocol failed"
    SSH_CONN_TRANSPORT_INACTIVE = "SSH connection established but transport is inactive"

    # Shell
    SHELL_OPEN_FAILED = "Failed to open shell"
    SHELL_OPENED_SUCCESS = "Shell opened successfully"
    SHELL_OPENED_CONFIGURED = "Shell opened and configured"
    SHELL_CLOSED = "Shell closed"
    SHELL_CLOSING = "Closing shell"
    SHELL_CLOSED_SUCCESS = "Shell closed successfully"
    SHELL_SKIP = "Skipping shell opening (using exec_cmd instead)"
    SHELL_NOT_CONNECTED = "Cannot open shell: Not connected"
    SHELL_NOT_OPENED = "Shell not opened"
    SHELL_ALREADY_OPENED = "Shell already opened"
    SHELL_ALREADY_CLOSED = "Shell already closed or have not been opened"
    SHELL_INVOKED_BANNER = "Shell invoked, waiting for banner"
    SHELL_STOPPING_THREAD = "Stopping keepalive thread"

    # Command Execution
    CMD_EXEC = "Executing command"
    CMD_EXEC_FAILED = "Command execution failed"
    CMD_EXEC_TIMEOUT = "Command execution timeout"
    CMD_EXEC_FAIL = "Failed to execute command"
    CMD_EXEC_SUCCESS = "Successfully executed command"
    CMD_EXEC_RESULT = "Command execution result"
    CMD_LOCAL_EXEC_USED = "Using local command execution (no SSH)"

    # FBR-CLI
    FBR_CLI_ENTERING = "Entering fbr-CLI"
    FBR_CLI_ENTERED = "Entered fbr-CLI successfully"
    FBR_CLI_EXITED = "Exited fbr-CLI"
    FBR_CLI_EXIT_CTRL_C = "Exiting fbr-CLI, sending 'Ctrl+C' to exit"

    # Interface Lookup
    INTERFACE_LOOKUP = "Looking up interface"
    INTERFACE_FOUND = "Interface found"
    INTERFACE_NOT_FOUND = "Interface not found"

    # Port ID
    PORT_ID_FOUND = "Port ID found"
    PORT_ID_NOT_FOUND = "Port ID not found"

    # Pattern
    PATTERN_SEARCH = "Searching with pattern"

    # Port Toggle
    PORT_TOGGLE_ENABLED = "Port toggling enabled"
    PORT_TOGGLE_FAILED = "Port toggle failed"
    PORT_TOGGLE_EXECUTING = "Executing toggle"
    PORT_TOGGLE_WAITING = "Waiting after toggle"

    # Cache
    CACHE_HIT = "Cache hit"
    CACHE_MISS = "Cache miss"

    # Buffer
    BUFFER_CLEARING = "Clearing buffer"
    BUFFER_CLEARED = "Buffer cleared"
    BUFFER_CLEAR_FAILED = "Buffer clear failed, continuing anyway"

    # ---------------------------------------------------------------------------- #
    #                                      SLX                                     #
    # ---------------------------------------------------------------------------- #

    # Scan Operations
    SLX_SCAN_START = "Starting SLX scan"
    SLX_SCAN_COMPLETE = "SLX scan complete"
    SLX_SCAN_PROCESSING = "Processing SLX scan"
    SLX_SCAN_SKIPPING = "Skipping SLX scan"
    SLX_SCAN_NO_INTERFACES = "No SLX interfaces to scan"
    SLX_SCAN_ITERATION_FAILED = "SLX scan iteration failed"

    # SLX Eye Scan
    SLX_EYE_SCAN_START = "Starting SLX eye scan"
    SLX_EYE_SCAN_COMPLETE = "SLX eye scan complete"
    SLX_EYE_SCAN_FAILED = "SLX eye scan failed"
    SLX_EYE_SCAN_WAITING = "Waiting for eye scan to complete"

    # DSLX Dsc Scan
    SLX_DSC_SCAN_STARTING = "Starting DSC scan"
    SLX_DSC_SCAN_COMPLETE = "DSC scan complete"
    SLX_DSC_SCAN_FAILED = "DSC scan failed"

    # ---------------------------------------------------------------------------- #
    #                                      SUT                                     #
    # ---------------------------------------------------------------------------- #

    # Software Manager
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

    # System Info
    SYS_INFO_LOG = "Logging system information"
    SYS_INFO_FAILED = "Failed to log system information"
    SYS_INFO_START = "Start system information scan"
    SYS_INFO_SKIP = "Skipping system information scan (not in local mode or disabled)"

    # Worker Management
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
    WORKER_POOL_CLEARING = "Clearing worker pool"
    WORKER_POOL_CLEARED = "Work pool cleared"
    WORKER_POOL_STOP = "Stopping workers in pool"

    # Worker
    WORKER_EXTRACT_SAMPLE = "Extracting worker samples"
    WORKER_SHUTDOWN = "Shutting down worker(s)"
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

    # Scanner - General
    SCANNER_INIT = "Initializing scanners"
    SCANNER_CONN_FAILED = "Scanner connection failed"
    SCANNER_NOT_INIT = "Scanner not initialized"
    SCANNER_START_FAILED = "Failed to start workers"
    SCANNER_WORKERS_CREATED = "Workers created"

    # Scanner - SLX
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

    # Scanner - SUT
    SCANNER_SUT_CONN_HOST = "Connecting to SUT host"
    SCANNER_SUT_JUMP_HOST = "Using jump host"
    SCANNER_SUT_TEST_CONN = "Testing connection"
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

    # Shutdown
    SHUTDOWN_SIGNAL = "Shutdown signal received"
    SHUTDOWN_START = "Starting shutdown"
    SHUTDOWN_COMPLETE = "Shutdown complete"
    SHUTDOWN_GRACEFUL = "Ctrl+C pressed. Shutting down gracefully..."
    SHUTDOWN_ALL_COMPLETED = "Shutdown all completed"
    SHUTDOWN_SLX_SCANNER = "Shutting SLX scanner"
    SHUTDOWN_SUT_SCANNER = "Shutting SUT scanner"

    # Command
    COMMAND_EXEC_FAILED = "Command execution failed"
    COMMAND_NO_SHELL = "Cannot execute shell command: shell not opened"
    COMMAND_NO_CONNNECT = "Cannot execute shell command: connection lost"
    # ------------------- COMMAND_TIMEOUT< = "Command timeout" ------------------- #

    # Local Connection
    LOCAL_EXEC = "Using local command execution (no SSH)"
    LOCAL_CLOSED = "Local connection closed"
    LOCAL_CMD_EXEC = "Executing local command"
    LOCAL_CMD_STDERR = "Command stderr"

    # ---------------------------------------------------------------------------- #
    #                               Main Application                               #
    # ---------------------------------------------------------------------------- #

    # Configuration
    MAIN_CONFIG_NOT_FOUND = "Config file not found"
    MAIN_CONFIG_SAME_DIR = "Make sure config.json is in the same directory as the executable"
    MAIN_CONFIG_INVALID_JSON = "Config file has an invalid JSON"

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

    # Configuration
    CONFIG_START = "Loading configuration from file"
    CONFIG_LOADED = "Configuration loaded successfully"
    CONFIG_FAILED = "Configuration loading failed"
    CONFIG_CREATED = "Config created"
    CONFIG_VALIDATION_FAILED = "Configuration validation failed"
    CONFIG_VALIDATION_SUCCESS = "Configuration validated successfully"

    # Agent
    AGENT_NO_SSH = "Cannot start agent: SSH connection not available"
    AGENT_STARTED = "Network agent started"
    AGENT_STOPPED = "Network agent stopped"
    AGENT_TASK_EXEC = "Executing task"
    AGENT_SSH_UNAVAIL = "SSH connection not available"
    AGENT_CMD_FAIL = "Agent command execution failed"

    # Traffic Testing
    TRAFFIC_CONN_CREATE = "Creating connections..."
    TRAFFIC_CONN_VALIDATE = "Validating connections..."
    TRAFFIC_CONN_VALIDATE_PASS = "Connection validation passed"
    TRAFFIC_CONN_VALIDATE_LOCAL = "Validating local connection..."
    TRAFFIC_CONN_VALIDATED = "Connection validated"
    TRAFFIC_CONN_LOCAL_VALIDATED = "Local connection validated"

    TRAFFIC_SERVER_START = "Starting iperf server on port"
    TRAFFIC_SERVER_STOP = "Iperf server stopped"

    TRAFFIC_CLIENT_DISCONNECT = "Error disconnecting client"
    TRAFFIC_SERVER_DISCONNECT = "Error disconnecting server"

    TRAFFIC_TEST_START = "Starting traffic test..."
    TRAFFIC_TEST_COMPLETE = "Test completed"
    TRAFFIC_TEST_FAILED = "Test iteration failed"
    TRAFFIC_TEST_ABORT = "3 consecutive failures detected, aborting tests"
    TRAFFIC_TEST_WAIT = "Waiting before next test..."

    TRAFFIC_METADATA_START = "Start writing metadata to file"
    TRAFFIC_METADATA_STOPP = "Metadata written to file"
    TRAFFIC_METADATA_NONE = "No metadata to write"

    TRAFFIC_STATS_START = "Start writing stats to file"
    TRAFFIC_STATS_STOP = "Stats written to file"
    TRAFFIC_STATS_NONE = "No statistics to write"

    TRAFFIC_SUMMARY_START = "Start writing summary to file"
    TRAFFIC_SUMMARY_STOP = "Summary written to file"
    TRAFFIC_SUMMARY_NONE = "No summary to write for iteration"

    TRAFFIC_JSON_PARSE_FAIL = "Failed to parse JSON output"
    TRAFFIC_IPERF_CHECK = "Checking for existing iperf processes..."
    TRAFFIC_IPERF_KILLED = "Killed existing iperf processes"
    TRAFFIC_SW_CHECK = "Checking required software..."
    TRAFFIC_SW_MISSING = "not found"
    TRAFFIC_SW_INSTALLED = "All required software is installed"
    TRAFFIC_SW_INSTALL_START = "Installing missing software"
    TRAFFIC_SW_INSTALL_FAIL = "Failed to install"
    TRAFFIC_SW_VERIFY = "Verifying installations..."
    TRAFFIC_SW_VERIFY_FAIL = "verification failed"
    TRAFFIC_SW_VERIFY_SUCCESS = "All required software installed and verified"
    TRAFFIC_SW_VERIFIED = "verified"
    TRAFFIC_SW_INSTALLING = "Installing"
    TRAFFIC_SW_INSTALL_SUCCESS_APT = "installed successfully via apt"
    TRAFFIC_SW_INSTALL_SUCCESS_YUM = "installed successfully via yum"
    TRAFFIC_SW_INSTALL_FAIL_APT = "Failed to install via apt"
    TRAFFIC_SW_INSTALL_FAIL_YUM = "Failed to install via yum"
    TRAFFIC_SW_NO_PKG_MGR = "No supported package manager found (apt/yum)"
    TRAFFIC_CMD_EXEC = "Executing"
    TRAFFIC_CMD_FAIL = "Command failed"
    TRAFFIC_PORT_CHECK = "Checking port"
    TRAFFIC_PORT_REACHABLE = "is reachable"
    TRAFFIC_PORT_UNREACHABLE = "is not reachable (firewall/network issue?)"
    TRAFFIC_PROCESS_STOP = "Stopping process"
    TRAFFIC_PROCESS_STOPPED = "Process stopped"
    TRAFFIC_PROCESS_STOP_FAIL = "Failed to stop process"
    TRAFFIC_PROCESS_KILL = "Force killing process"
    TRAFFIC_PROCESS_STARTED = "Process started with PID"
    TRAFFIC_PROCESS_NO_PID = "Failed to get process PID"
    TRAFFIC_PID_NONE = "No PID found"

    # Parser
    PARSER_TIMESTAMP_FAIL = "Failed to parse timestamp"

    # Sample
    SAMPLE_CMD_FAIL = "Sample command execution failed"

    # Keepalive
    ALIVE_THREAD_START = "Keepalive thread started"
    ALIVE_THREAD_FAIL = "Keepalive thread encountered an error"
    ALIVE_THREAD_STOP = "Keepalive thread did not stop gracefully"
    ALIVE_THREAD_STOPPING = "Stopping keepalive thread"
    ALIVE_NO_ACTIVE = "Keepalive thread did not find any active connections"
    ALIVE_LOOP_STOP = "Keepalive loop stopped"

    # Storage
    STORE_FAIL = "Failed to store results to"
