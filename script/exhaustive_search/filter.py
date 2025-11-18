#!/usr/bin/env python3

import sys

for line in sys.stdin:
    if line.startswith("#") or line.strip() == "":
        continue  # skip header or empty lines

    cols = line.strip().split()
    R1, R2, Action, SelfCoop, bc_min = cols
    SelfCoop = float(SelfCoop)
    bc_min = float(bc_min)

    # if 1 < bc_min:
    #     print(line, end="")
    if SelfCoop > 0.9 and 1 < bc_min < 1.1:
        print(line, end="")
