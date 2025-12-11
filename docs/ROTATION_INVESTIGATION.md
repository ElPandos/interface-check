# Log Rotation Investigation - 2025-12-11

## Issue Report
User observed that `sut_ethtool.log` did not rotate despite flaps being detected.

## Investigation Results

### Log Folder: `20251211_201516`

**File Sizes:**
- `sut_ethtool.log`: 11KB (below 20KB limit)
- `slx_eye.log`: 25KB (rotated)
- `slx_eye_1.log`: 23KB (rotated)
- `slx_eye_2.log`: 15KB (rotated)
- `sut_link_flap.log`: 932 bytes (5 flaps detected)

**Flaps Detected:**
1. 20:15:57 - ens3f0np0 (11.7s duration)
2. 20:16:47 - ens3f0np0 (11.7s duration)
3. 20:17:47 - ens3f0np0 (11.2s duration)
4. 20:18:46 - ens3f0np0 (10.6s duration)
5. 20:19:36 - ens3f0np0 (9.5s duration)

**Rotation Events:**
- 20:18:04 - `slx_eye` rotated to `_1` (flap_marked=True)
- 20:20:37 - `slx_eye` rotated to `_2` (flap_marked=True)
- 20:22:43 - `slx_eye` cleared (flap_marked=False)

### Root Cause

**`sut_ethtool.log` did NOT rotate because it never reached the 20KB size limit.**

The rotation logic works as follows:
1. **Size check first**: Only check rotation if file >= max_size_kb
2. **Flap marking**: When flap detected, mark ALL active loggers for rotation
3. **Rotation decision**: When size limit reached, check if logger was marked
   - If marked: Rotate to new file (preserve data)
   - If not marked: Clear file (reuse)

**Why `sut_ethtool` didn't rotate:**
- File was only 11KB (55% of 20KB limit)
- Even though it was marked for rotation during flaps, the size check prevented rotation
- The marking is "pending" until the file reaches size limit

**Why `slx_eye` rotated:**
- File reached 25KB (exceeded 20KB limit)
- Was marked for rotation during flaps
- Rotated to preserve data instead of clearing

## Behavior Analysis

### Expected Behavior
The current logic is **CORRECT**:
- Logs only rotate when they reach size limit
- Flap marking ensures data preservation when rotation happens
- Small logs (like `sut_ethtool` at 11KB) don't need rotation yet

### Rotation Flow
```
Flap Detected
    ↓
Mark ALL active loggers for rotation
    ↓
Each logger continues collecting data
    ↓
When logger reaches size limit:
    - If marked: Rotate to new file
    - If not marked: Clear and reuse
```

## Improvements Added

### Enhanced Logging

1. **Registration Logging** (DEBUG level):
   - When workers register as active loggers
   - When SLX loggers register as active loggers

2. **Flap Detection Logging** (INFO level):
   - Number of active loggers being marked
   - Interface where flap occurred

3. **Marking Logging** (DEBUG level):
   - Each logger being marked for rotation

4. **Rotation Check Logging** (DEBUG level):
   - File size, limit, should_rotate flag, flap_marked flag
   - Helps understand why rotation did/didn't happen

5. **Rotation Action Logging** (INFO level):
   - File size included in rotation messages
   - Clear distinction between rotate vs clear actions

### Log Output Examples

**Registration:**
```
DEBUG - Registered sut_ethtool as active logger for flap rotation
DEBUG - Registered slx_eye as active logger for flap rotation
```

**Flap Detection:**
```
INFO - Flap detected on ens3f0np0, marking 6 active loggers for rotation
DEBUG - Rotation: Marked sut_ethtool for rotation (flap detected)
DEBUG - Rotation: Marked slx_eye for rotation (flap detected)
```

**Rotation Check:**
```
DEBUG - Rotation check: sut_ethtool size=11.0KB limit=20KB should_rotate=False flap_marked=True
DEBUG - Rotation check: slx_eye size=25.3KB limit=20KB should_rotate=True flap_marked=True
```

**Rotation Action:**
```
INFO - Rotation: slx_eye rotating to _1 (size=25.3KB, flap_marked=True)
INFO - Rotation: slx_eye clearing file (size=21.5KB, flap_marked=False)
```

## Conclusion

**No bug found.** The system is working as designed:
- `sut_ethtool.log` was correctly marked for rotation during flaps
- It will rotate (not clear) when it reaches 20KB
- Until then, it continues collecting data with the flap marking preserved

The enhanced logging will make it easier to track rotation state and understand why logs rotate or don't rotate.
