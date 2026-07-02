#!/usr/bin/env python3

"""
Print normalized norm IDs from an exhaustive-search TSV.

Rows displayed with action ID 13 are rewritten by swapping G/B labels, so
the output uses the same interpretation as action_sweep_norm_table.tex.
"""

import argparse
from pathlib import Path


ASSESS_SWAP_MAP = (6, 7, 4, 5, 2, 3, 0, 1)
DEFAULT_TSV = Path("script/output/action_sweep_hits.tsv")


def swap_action_id(action_id: int) -> int:
  """Swap G/B labels for deterministic action rule IDs."""
  swapped = 0
  for bit_idx in range(4):
    if (action_id >> bit_idx) & 1:
      swapped |= 1 << (3 - bit_idx)
  return swapped


def swap_assessment_id(assessment_id: int) -> int:
  """Swap G/B labels for deterministic assessment rule IDs."""
  swapped = 0
  for new_idx, old_idx in enumerate(ASSESS_SWAP_MAP):
    old_bit = (assessment_id >> old_idx) & 1
    new_bit = 0 if old_bit else 1
    if new_bit:
      swapped |= 1 << new_idx
  return swapped


def normalize_ids(r1_id: int, r2_id: int, action_id: int) -> tuple[int, int, int]:
  if action_id == 13:
    return (
      swap_assessment_id(r1_id),
      swap_assessment_id(r2_id),
      swap_action_id(action_id),
    )
  return r1_id, r2_id, action_id


def read_ids(path: Path):
  header = None
  with path.open() as fin:
    for line_number, raw_line in enumerate(fin, start=1):
      line = raw_line.strip()
      if not line:
        continue
      if line.startswith("#"):
        header = line[1:].strip().split("\t")
        continue
      if header is None:
        raise ValueError(f"{path}:{line_number}: missing TSV header")

      cols = line.split("\t")
      row = dict(zip(header, cols))
      r1_id = int(row["rd"])
      r2_id = int(row["rr"])
      action_id = int(row["action"])
      yield normalize_ids(r1_id, r2_id, action_id)


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
    "tsv",
    nargs="?",
    type=Path,
    default=DEFAULT_TSV,
    help=f"input TSV path (default: {DEFAULT_TSV})",
  )
  args = parser.parse_args()

  for r1_id, r2_id, action_id in read_ids(args.tsv):
    print(f"{r1_id}-{r2_id}-{action_id}")

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
