#!/usr/bin/env python3
"""
Plot results from script/sweep_rr.py.

Reads a TSV file produced by sweep_rr.py and plots:
  x-axis: self_coop
  y-axis: eq[0]

Additionally highlights points for specific Rr values:
  - Rr=204 (base norm) in red
  - Rr=170 (IS norm) in blue

Usage:
  python script/plot_rr_sweep.py --in results_tables/rr_sweep_rd128_p2_20250101_120000.tsv \
                                 --out figures/rr_sweep_rd128_p2.png

Options:
  --show   Display the plot window instead of saving (or do both if --out is also given).
"""

import argparse
import json
import os
from typing import List, Tuple

import matplotlib.pyplot as plt


def load_rr_sweep(path: str) -> Tuple[List[float], List[float], List[int], dict]:
  xs: List[float] = []   # self_coop
  ys: List[float] = []   # eq[0]
  rrs: List[int] = []    # rr ids
  meta = {}

  with open(path, "r") as f:
    lines = f.read().splitlines()

  # Parse meta if present on first line
  if lines and lines[0].startswith("# sweep_rr meta:"):
    try:
      meta_json = lines[0].split(":", 1)[1].strip()
      meta = json.loads(meta_json)
    except Exception:
      meta = {}
    # Drop meta line from further parsing
    lines = lines[1:]

  # Ignore lines starting with '#'; fixed column order: rr, eq_coop, self_coop, eq[0], eq[1], eq[2]
  for ln in lines:
    if not ln.strip() or ln.lstrip().startswith("#"):
      continue
    parts = [p.strip() for p in ln.split("\t")]
    if len(parts) < 6:
      continue
    try:
      rr = int(parts[0])
      # eq_coop = float(parts[1])  # not used in this plot
      self_coop = float(parts[2]) if parts[2] not in ("", "None", "null", "nan") else float("nan")
      eq0 = float(parts[3])
    except Exception:
      continue
    if not (self_coop == self_coop and eq0 == eq0):
      continue
    rrs.append(rr)
    xs.append(self_coop)
    ys.append(eq0)

  return xs, ys, rrs, meta


def main():
  ap = argparse.ArgumentParser(description="Plot x=self_coop vs y=eq[0] from sweep_rr output")
  ap.add_argument("--in", dest="inp", required=True, help="Input TSV produced by script/sweep_rr.py")
  ap.add_argument("--out", dest="out", default=None, help="Output image path (PNG/SVG/PDF). If omitted and --show not set, saves next to input with .png")
  ap.add_argument("--show", action="store_true", help="Show the plot window")
  args = ap.parse_args()

  xs, ys, rrs, meta = load_rr_sweep(args.inp)
  if not xs:
    raise SystemExit("No data points could be read from the input file.")

  plt.figure(figsize=(6, 4))
  plt.scatter(xs, ys, s=18, alpha=0.7, edgecolors="none", label="Rr sweep")

  # Highlight specific Rr values if present
  try:
    base_idxs = [i for i, rr in enumerate(rrs) if rr == 204]
    is_idxs = [i for i, rr in enumerate(rrs) if rr == 170]
    if base_idxs:
      bx = [xs[i] for i in base_idxs]
      by = [ys[i] for i in base_idxs]
      plt.scatter(bx, by, s=64, color="red", marker="*", label="Rr=204 (base)")
    if is_idxs:
      ix = [xs[i] for i in is_idxs]
      iy = [ys[i] for i in is_idxs]
      plt.scatter(ix, iy, s=64, color="blue", marker="x", label="Rr=170 (IS)")
  except Exception:
    pass
  plt.xlabel("self_coop")
  plt.ylabel("eq[0]")
  title_bits = []
  if "rd" in meta and "p" in meta:
    title_bits.append(f"rd={meta['rd']}, p={meta['p']}")
  if "base_norm" in meta:
    title_bits.append(f"base={meta['base_norm']}")
  if title_bits:
    plt.title("; ".join(title_bits))
  plt.grid(True, linestyle=":", alpha=0.5)
  plt.legend(frameon=False)
  plt.tight_layout()

  out_path = args.out
  if not out_path and not args.show:
    base, _ = os.path.splitext(args.inp)
    out_path = base + ".png"
  if out_path:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")

  if args.show:
    plt.show()


if __name__ == "__main__":
  main()
