#!/usr/bin/env python3
"""Test TimeCommandParser."""

from src.core.parser import TimeCommandParser

# Sample output from 'time ls -Fal'
sample_output = """total 100
drwxr-x--- 9 hts  hts   4096 Nov 21 07:15 ./
drwxr-xr-x 3 root root  4096 Oct 16 14:35 ../
-rw------- 1 hts  hts     55 Nov 21 07:15 .Xauthority

real	0m0.002s
user	0m0.000s
sys	0m0.002s"""

parser = TimeCommandParser()
parser.parse(sample_output)
result_ms = parser.get_result()

print(f"Parsed real time: {result_ms:.3f} ms")
print(f"Expected: 2.000 ms")
print(f"Match: {abs(result_ms - 2.0) < 0.001}")
