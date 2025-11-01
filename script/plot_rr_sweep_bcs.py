#%%
#!/usr/bin/env python3
"""
Plot results from main_SweepR2.cpp sweep (bc columns).

Reads the TSV written by main_SweepR2 and visualises the
Rr sweep in two variants:
  - Points: self_coop vs bc_min(AllD)
  - Bars:   vertical range between bc_min and bc_max

VS Code Interactive tips:
  - This file uses '#%%' cells. Edit IN_PATH in the "Interactive defaults"
    cell, then the quick-plot cells will display figures when data is present.

CLI usage:
  python script/plot_rr_sweep_bcs.py --in R2_sweep.tsv --out figures/rr_bcs.png --ymax 6

Options:
  --out   Optional path for the saved figure.
  --show  Display the plot window (or automatically when no --out).
  --ymax  Max y-axis limit for bc values (default: 5.0).
"""

#%% Imports
import argparse
import csv
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import matplotlib.pyplot as plt

#%% Data loading

def parse_optional_float(value: str) -> Optional[float]:
  value = value.strip()
  if value in {"", "None", "null", "nan"}:
    return None
  try:
    return float(value)
  except ValueError:
    return None


def load_rr_bcs(path: Path) -> Dict[int, Tuple[float, Optional[float], Optional[float]]]:
  by_rr: Dict[int, Tuple[float, Optional[float], Optional[float]]] = {}

  with path.open("r", newline="") as f:
    reader = csv.reader(f, delimiter="\t")
    for row in reader:
      if not row or row[0].startswith("#"):
        continue
      if len(row) < 4:
        continue
      try:
        rr = int(row[0])
        self_coop = float(row[1])
        bc_min = parse_optional_float(row[2])
        bc_max = parse_optional_float(row[3])
      except ValueError:
        continue
      by_rr[rr] = (self_coop, bc_min, bc_max)

  return by_rr

#%% Plotting helpers

def plot_rr_bcs_points(by_rr: Dict[int, Tuple[float, Optional[float], Optional[float]]],
                       ymax: float = 5.0,
                       xlim: Tuple[float, float] = (0.5, 1.0),
                       base_norm_name: str = "L6"):
  fig, ax = plt.subplots(figsize=(6, 4))
  ax.tick_params(axis='both', labelsize=16)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)

  xs, ys = [], []
  for rr, (self_coop, bc_min, _) in by_rr.items():
    if bc_min is None or not math.isfinite(bc_min):
      continue
    xs.append(self_coop)
    ys.append(bc_min)
  ax.scatter(xs, ys, s=20, color="tab:blue", alpha=0.6, edgecolors="none")

  highlights = {
    204: ("tab:purple", base_norm_name),
    170: ("tab:orange", f"{base_norm_name}-IS"),
  }
  for target_rr, (color, label) in highlights.items():
    if target_rr in by_rr:
      x, y0, _ = by_rr[target_rr]
      if y0 is not None and math.isfinite(y0):
        ax.scatter([x], [y0], s=110, color=color, zorder=6,
                   edgecolors="white", linewidths=0.8)
        ax.annotate(label, xy=(x, y0), xytext=(3, 3), textcoords='offset points',
                    color=color, fontsize=16, ha="left", va="bottom")

  ax.set_xlabel("self cooperation level", fontsize=18)
  ax.set_ylabel("$b/c$", fontsize=18)
  ax.set_xlim(xlim)
  ax.set_ylim(1.0, ymax)
  ax.grid(True, linestyle=":", alpha=0.4)
  fig.tight_layout()
  return fig, ax


def plot_rr_bcs_bars(by_rr: Dict[int, Tuple[float, Optional[float], Optional[float]]],
                     ymax: float = 5.0,
                     xlim: Tuple[float, float] = (0.5, 1.0),
                     base_norm_name: str = "L6"):
  fig, ax = plt.subplots(figsize=(6, 4))
  ax.tick_params(axis='both', labelsize=16)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)

  for rr, (self_coop, bc_min, bc_max) in by_rr.items():
    if bc_min is None or not math.isfinite(bc_min):
      continue
    y_top = ymax if (bc_max is None or not math.isfinite(bc_max)) else bc_max
    if y_top < bc_min:
      continue
    ax.vlines(self_coop, bc_min, y_top, colors="tab:blue", alpha=0.5, linewidth=1.5)

  highlights = {
    204: ("tab:purple", base_norm_name),
    170: ("tab:orange", f"{base_norm_name}-IS"),
  }
  for target_rr, (color, label) in highlights.items():
    if target_rr in by_rr:
      x, bc_min, bc_max = by_rr[target_rr]
      if bc_min is not None and math.isfinite(bc_min):
        y_top = ymax if (bc_max is None or not math.isfinite(bc_max)) else bc_max
        if y_top >= bc_min:
          ax.vlines(x, bc_min, y_top, colors=color, linewidth=3.0, zorder=6)
          ax.annotate(label, xy=(x, bc_min), xytext=(6, 6), textcoords='offset points',
                      color=color, fontsize=16, ha="left", va="bottom")

  ax.set_xlabel("self cooperation level", fontsize=18)
  ax.set_ylabel("$b/c$", fontsize=18)
  ax.set_xlim(xlim)
  ax.set_ylim(1.0, ymax)
  ax.grid(True, linestyle=":", alpha=0.4)
  fig.tight_layout()
  return fig, ax

#%% Interactive defaults
IN_PATH = Path("../R2_sweep.tsv")  # adjust as needed
YMAX = 5.0
XLIM = (0.5, 1.0)
BASE_NAME = "L6"

by_rr_data = None
if IN_PATH.exists():
  by_rr_data = load_rr_bcs(IN_PATH)

if by_rr_data:
  fig_points, ax_points = plot_rr_bcs_points(by_rr_data, ymax=YMAX, xlim=XLIM, base_norm_name=BASE_NAME)
  try:
    display(fig_points)
  except NameError:
    pass

  fig_bars, ax_bars = plot_rr_bcs_bars(by_rr_data, ymax=YMAX, xlim=XLIM, base_norm_name=BASE_NAME)
  try:
    display(fig_bars)
  except NameError:
    pass
else:
  print(f"No data loaded from {IN_PATH.resolve()}")

#%% CLI entry point

def main():
  parser = argparse.ArgumentParser(description="Plot self_coop vs bc range from main_SweepR2 TSV")
  parser.add_argument("--in", dest="inp", required=True, help="Input TSV produced by main_SweepR2")
  parser.add_argument("--out", dest="out", default=None, help="Output image path (PNG/SVG/PDF)")
  parser.add_argument("--show", action="store_true", help="Show the plot window")
  parser.add_argument("--ymax", dest="ymax", type=float, default=5.0, help="Y-axis upper limit (default: 5)")
  args = parser.parse_args()

  by_rr = load_rr_bcs(Path(args.inp))
  if not by_rr:
    raise SystemExit("No valid data rows found in input file.")

  fig, _ = plot_rr_bcs_points(by_rr, ymax=args.ymax)

  inp_path = Path(args.inp)
  out_path = args.out
  if not out_path and not args.show:
    out_path = str(inp_path.with_name(inp_path.stem + "_bcs.png"))
  if out_path:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")

  if args.show or not out_path:
    plt.show()


if __name__ == "__main__":
  main()
