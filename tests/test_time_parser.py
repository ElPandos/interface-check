#!/usr/bin/env python3
"""Test TimeCommandParser with both bash and zsh formats."""

from src.core.parser import SutTimeParser

# Test bash format
bash_output = """real\t0m0.002s
user\t0m0.000s
sys\t0m0.002s"""

parser = SutTimeParser()
parser.parse(bash_output)
bash_result = parser.get_result()

print(f"Bash format: {bash_result:.3f} ms (expected: 2.000 ms)")
assert abs(bash_result - 2.0) < 0.001, "Bash parsing failed"

# Test zsh format
zsh_output = """bash -c   0,01s user 0,01s system 75% cpu 0,027 total"""

parser2 = SutTimeParser()
parser2.parse(zsh_output)
zsh_result = parser2.get_result()

print(f"Zsh format: {zsh_result:.3f} ms (expected: 27.000 ms)")
assert abs(zsh_result - 27.0) < 0.001, "Zsh parsing failed"

print("\n✅ Both formats parsed successfully!")
