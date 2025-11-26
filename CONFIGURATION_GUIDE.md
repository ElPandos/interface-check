# Configuration Guide

## Overview

The application uses two independent settings to control behavior:

1. **`connect_type`** - Determines how to connect to the SUT (System Under Test)
2. **`show_parts`** - List of components to SKIP (empty = run everything)

## Connection Type

Controls the connection method to the SUT:

```json
"connect_type": "local"   // Run commands locally on the SUT machine
"connect_type": "remote"  // Run commands via SSH to the SUT
```

### Local Mode
- Runs all workers: mlxlink, mget_temp, dmesg
- Executes commands directly on the local machine
- No SSH connection needed

### Remote Mode
- Runs all workers: mlxlink, mget_temp, dmesg
- Executes commands via SSH to the remote SUT
- Requires MST tools installed on remote machine

## Show Parts (Skip Flags)

An array of components to SKIP. **Empty array = run everything.**

Available skip flags:
- `"no_sys_info"` - Skip system information collection at startup
- `"no_mlxlink"` - Skip mlxlink worker (network metrics)
- `"no_mtemp"` - Skip mget_temp worker (NIC temperature)
- `"no_dmesg"` - Skip dmesg worker (link flap detection)
- `"no_eye_scan"` - Skip SLX eye scan automation

## Configuration Examples

### Run Everything Locally
```json
{
  "sut": {
    "connect_type": "local",
    "show_parts": []
  }
}
```
**Runs:** sys_info + mlxlink + mget_temp + dmesg + eye_scan (all locally)

### Run Locally, Skip Eye Scan
```json
{
  "sut": {
    "connect_type": "local",
    "show_parts": ["no_eye_scan"]
  }
}
```
**Runs:** sys_info + mlxlink + mget_temp + dmesg

### Run Locally, Only Monitor Link Flaps
```json
{
  "sut": {
    "connect_type": "local",
    "show_parts": ["no_sys_info", "no_mlxlink", "no_mtemp", "no_eye_scan"]
  }
}
```
**Runs:** dmesg only

### Run Remotely (SSH)
```json
{
  "sut": {
    "connect_type": "remote",
    "show_parts": []
  }
}
```
**Runs:** sys_info + mlxlink + mget_temp + dmesg + eye_scan (all via SSH)

### Run Remotely, Skip Everything Except Dmesg
```json
{
  "sut": {
    "connect_type": "remote",
    "show_parts": ["no_sys_info", "no_eye_scan"]
  }
}
```
**Runs:** dmesg only

## Port Toggling

Port toggling is controlled by the SLX configuration and only works when eye scanning is enabled:

```json
{
  "slx": {
    "port_toggling_enabled": true,
    "port_toggle_wait_sec": 5
  },
  "sut": {
    "show_parts": []  // Must NOT include "no_eye_scan"
  }
}
```

**Important:** Port toggling requires eye scanning to be active. If `"no_eye_scan"` is in `show_parts`, port toggling will not occur.

## Migration from Old Config

### Old Format (DEPRECATED)
```json
{
  "connect_type": "remote",
  "show_parts": ["remote", "no_eye_scan"]  // ❌ Don't use "remote" or "local" here
}
```

### New Format (CORRECT)
```json
{
  "connect_type": "remote",
  "show_parts": ["no_eye_scan"]  // ✅ Only skip flags
}
```

## Summary

- **`connect_type`** = HOW to execute commands (local vs SSH)
  - Both modes run all workers (mlxlink, mget_temp, dmesg)
  - Remote mode requires MST tools on the remote machine
- **`show_parts`** = WHAT to skip (empty = skip nothing)
- **Port toggling** = Requires eye scan to be enabled (no `"no_eye_scan"` flag)
