#!/usr/bin/env python
"""
Applying a threshold and an aggregate limit to a column of numbers.

Usage: cat input | python compute.py <threshold> <limit>

Each input is reduced by the threshold. Outputs are capped so
their running total never exceeds the limit. The last line is the total. 
In reinsurance terms this is an excess-of-loss layer.

Submitted by Jak Linstaedt
"""
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

MAX_VALUE = Decimal("1000000000")
TENTH = Decimal("0.1")

# parse a number and check it is within the allowed range
def parse_amount(text, name="value"):
    try:
        value = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError("invalid {}: {!r}".format(name, text.strip()))
    if not value.is_finite() or value < 0 or value > MAX_VALUE:
        raise ValueError("{} out of range: {!r}".format(name, text.strip()))
    # round anything smaller than one decimal place to get exact totals
    return value.quantize(TENTH, rounding=ROUND_HALF_UP)

# apply the threshold and limit to each value in order
def apply_layer(values, threshold, limit):
    remaining = limit
    for value in values:
        out = min(max(value - threshold, Decimal(0)), remaining)
        remaining -= out
        yield out

# format a value to one decimal place
def format_amount(value):
    return "{:.1f}".format(value)

# parse each non-blank line from the input
def read_values(lines):
    for line in lines:
        if line.strip():  # skip blank lines
            yield parse_amount(line)

# read args and stdin, write the results to stdout
def main(argv=None, stdin=None, stdout=None, stderr=None):
    argv = sys.argv[1:] if argv is None else argv
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    # check for exactly two args and validate them, exit code 2 on bad args
    if len(argv) != 2:
        stderr.write("usage: compute <threshold> <limit>\n")
        return 2
    try:
        threshold = parse_amount(argv[0], "threshold")
        limit = parse_amount(argv[1], "limit")
    except ValueError as e:
        stderr.write("error: {}\n".format(e))
        return 2

    # read all input before writing anything to avoid partial output on bad lines
    try:
        values = list(read_values(stdin))
    except ValueError as e:
        stderr.write("error: {}\n".format(e))
        return 1

    # write each output, then the total as the last line
    total = Decimal(0)
    for out in apply_layer(values, threshold, limit):
        total += out
        stdout.write(format_amount(out) + "\n")
    stdout.write(format_amount(total) + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())