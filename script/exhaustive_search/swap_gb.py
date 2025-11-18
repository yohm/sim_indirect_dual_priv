#!/usr/bin/env python3

"""
Swap the IDs of the donor/recipient assessment rules and action rule
whenever the (G,G) entry of the action rule is defection.

The script expects tab/space-delimited rows where the first three columns
are Rd ID, Rr ID, and action ID (as produced by main_ExhaustiveSearch).
Lines starting with "#" or blank lines are passed through unchanged.
"""

import sys

ASSESS_SWAP_MAP = (6, 7, 4, 5, 2, 3, 0, 1)


def swap_action_id(action_id: int) -> int:
  """Swap G/B labels for deterministic action rule IDs (4-bit values)."""
  if not 0 <= action_id <= 0xF:
    raise ValueError(f"action ID must be between 0 and 15 (got {action_id})")
  swapped = 0
  for bit_idx in range(4):
    if (action_id >> bit_idx) & 1:
      swapped |= 1 << (3 - bit_idx)
  return swapped


def swap_assessment_id(assess_id: int) -> int:
  """Swap G/B labels for deterministic assessment rule IDs (8-bit values)."""
  if not 0 <= assess_id <= 0xFF:
    raise ValueError(f"assessment ID must be between 0 and 255 (got {assess_id})")
  swapped = 0
  for new_idx, old_idx in enumerate(ASSESS_SWAP_MAP):
    old_bit = (assess_id >> old_idx) & 1
    new_bit = 0 if old_bit else 1  # invert because swapping flips reputations
    if new_bit:
      swapped |= 1 << new_idx
  return swapped


def needs_swap(action_id: int) -> bool:
  """Return True if the (G,G) action is defection."""
  return ((action_id >> 3) & 1) == 0


def main() -> int:
  for raw_line in sys.stdin:
    if raw_line.lstrip().startswith("#") or raw_line.strip() == "":
      sys.stdout.write(raw_line)
      continue

    cols = raw_line.strip().split()
    if len(cols) < 3:
      sys.stderr.write(f"[warn] skipping line with fewer than 3 columns: {raw_line}")
      continue

    try:
      r1 = int(cols[0])
      r2 = int(cols[1])
      action = int(cols[2])
    except ValueError as exc:
      raise SystemExit(f"failed to parse IDs from line: {raw_line}") from exc

    if needs_swap(action):
      r1 = swap_assessment_id(r1)
      r2 = swap_assessment_id(r2)
      action = swap_action_id(action)

    updated_cols = [str(r1), str(r2), str(action)] + cols[3:]
    sys.stdout.write("\t".join(updated_cols) + "\n")

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
