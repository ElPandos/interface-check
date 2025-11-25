#!/usr/bin/env python3
"""Test worker statistics display with all timing metrics."""

from src.core.statistics import WorkerStatistics

stats = WorkerStatistics()
command = "mlxlink -d 31:00.0 -e -m -c"

durations = [
    159.4,
    876.0,
    810.5,
    810.5,
    800.0,
    805.0,
    815.0,
    790.0,
    820.0,
    795.0,
    810.0,
    805.0,
    815.0,
    800.0,
    825.0,
    795.0,
    810.0,
    805.0,
    815.0,
    800.0,
]

for duration in durations:
    stats.record_duration(
        command=command,
        duration_ms=duration,
        send_ms=30.7,
        read_ms=2210.2,
        cycle_ms=duration + 50.0,
        parsed_ms=duration * 0.95,
    )

print(stats.get_summary())
