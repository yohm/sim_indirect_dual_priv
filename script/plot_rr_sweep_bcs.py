# %%
#!/usr/bin/env python3
"""
Plot results from script/sweep_rr_bcs.py.

Reads a TSV file produced by sweep_rr_bcs.py and plots:
  x-axis: self_coop
  y-axis: stable b/c range

For each Rr entry, draws a vertical line at x=self_coop from y=bc_min to
  y=bc_max. If bc_max is None/null, treats it as infinity and draws up to --ymax.

Usage:
  python script/plot_rr_sweep_bcs.py --in results_tables/rr_bcs_rd153_p10_20250920_164955.tsv \
                                     --out figures/rr_bcs_rd153_p10.png --ymax 20

Options:
  --show   Display the plot window instead of saving (or do both if --out is also given).
  --ymax   Upper y-limit used to visualize infinite bc_max (default: 10).
"""

import argparse
import json
import os
from typing import List, Tuple, Optional, Dict, Tuple as Tup

import matplotlib.pyplot as plt


def parse_float_or_none(s: str) -> Optional[float]:
  s = s.strip()
  if s in ("", "None", "none", "null", "nan"):
    return None
  try:
    return float(s)
  except Exception:
    return None

# %%

def load_rr_bcs(path: str):
  meta = {}
  by_rr: Dict[int, Tup[float, float, Optional[float]]] = {}

  with open(path, "r") as f:
    lines = f.read().splitlines()

  # Parse meta if present on first line
  if lines and lines[0].startswith("# sweep_rr_bcs meta:"):
    try:
      meta_json = lines[0].split(":", 1)[1].strip()
      meta = json.loads(meta_json)
    except Exception:
      meta = {}
    # Drop meta line from further parsing
    lines = lines[1:]

  # Ignore comment/header lines; expected columns: rr, self_coop, bc_min(AllD), bc_max(AllC)
  for ln in lines:
    if not ln.strip() or ln.lstrip().startswith("#"):
      continue
    parts = [p.strip() for p in ln.split("\t")]
    if len(parts) < 4:
      continue
    try:
      rr = int(parts[0])
      self_coop = parse_float_or_none(parts[1])
      bc_min = parse_float_or_none(parts[2])
      bc_max = parse_float_or_none(parts[3])
    except Exception:
      continue
    if self_coop is None or bc_min is None:
      continue
    by_rr[rr] = (self_coop, bc_min, bc_max)

  return by_rr, meta

# %%
def main():
  ap = argparse.ArgumentParser(description="Plot x=self_coop vs vertical b/c stability ranges from sweep_rr_bcs output")
  ap.add_argument("--in", dest="inp", required=True, help="Input TSV produced by script/sweep_rr_bcs.py")
  ap.add_argument("--out", dest="out", default=None, help="Output image path (PNG/SVG/PDF). If omitted and --show not set, saves next to input with .png")
  ap.add_argument("--show", action="store_true", help="Show the plot window")
  ap.add_argument("--ymax", type=float, default=5.0, help="Upper y-limit used when bc_max is infinite (None). Default: 5")
  args = ap.parse_args()

  by_rr, meta = load_rr_bcs(args.inp)
  if not by_rr:
    raise SystemExit("No data points could be read from the input file.")

  plt.figure(figsize=(6.4, 4.2))

  # Draw vertical line segments
  for rr, (x, y0, y1) in by_rr.items():
    y_top = args.ymax if y1 is None else y1
    # Avoid drawing if y_top < y0 due to bad data
    if y_top < y0:
      continue
    plt.vlines(x, y0, y_top, colors="tab:blue", alpha=0.6, linewidth=1.8)
    # Infinite bc_max is drawn up to ymax without arrowheads

  # Highlight base norm (Rr=KeepRecipient -> 204) and L6-IS (Rr=ImageScoring -> 170)
  rr_base = 204
  rr_is = 170
  if rr_base in by_rr:
    x, y0, y1 = by_rr[rr_base]
    y_top = args.ymax if y1 is None else y1
    if y_top >= y0:
      plt.vlines(x, y0, y_top, colors="red", linewidth=3.0, label="base Rr=204")
  if rr_is in by_rr:
    x, y0, y1 = by_rr[rr_is]
    y_top = args.ymax if y1 is None else y1
    if y_top >= y0:
      plt.vlines(x, y0, y_top, colors="green", linewidth=3.0, label="IS (L6-IS) Rr=170")

  plt.xlabel("self_coop")
  plt.ylabel("stable b/c range")
  plt.xlim(0.48, 1.0)
  plt.yticks([1, 2, 3, 4, 5])
  title_bits = []
  if "rd" in meta and "p" in meta:
    title_bits.append(f"rd={meta['rd']}, p={meta['p']}")
  if "base_norm" in meta:
    title_bits.append(f"base={meta['base_norm']}")
  if "N" in meta:
    title_bits.append(f"N={meta['N']}")
  if title_bits:
    plt.title("; ".join(title_bits))

  # Set y-limits to include [1, ymax]
  plt.ylim(1.0, args.ymax)
  plt.grid(True, linestyle=":", alpha=0.5)
  # Add legend only if we added any labeled highlights
  handles, labels = plt.gca().get_legend_handles_labels()
  if labels:
    plt.legend(frameon=False)
  plt.tight_layout()

  out_path = args.out
  if not out_path and not args.show:
    base, _ = os.path.splitext(args.inp)
    out_path = base + "_bcs.png"
  if out_path:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")

  if args.show:
    plt.show()

# %%

if __name__ == "__main__":
  main()

# %%
