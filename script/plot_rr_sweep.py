#%%
#!/usr/bin/env python3
"""
Plot results from main_SweepR2.cpp sweeps.

Reads the TSV written by main_SweepR2 and visualises
  x-axis: self_coop (column 2)
  y-axis: eq0        (column 6)

VS Code Interactive tips:
  - This file uses '#%%' cells for convenient interactive execution.
  - Edit IN_PATH in the "Interactive defaults" cell and run the
    "Quick plot" cell; it will automatically display the figure if
    data was loaded.

CLI usage:
  python script/plot_rr_sweep.py --in R2_sweep.tsv --out figures/rr_sweep.png

Options:
  --out   Optional path for the saved figure.
  --show  Display the plot window (or automatically when no --out).
"""

#%% Imports
import argparse
import csv
import os
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt

#%% Data loading

def load_rr_sweep(path: Path) -> Tuple[List[float], List[float], List[int]]:
  xs: List[float] = []
  ys: List[float] = []
  rrs: List[int] = []

  with path.open("r", newline="") as f:
    reader = csv.reader(f, delimiter="\t")
    for row in reader:
      if not row or row[0].startswith("#"):
        continue
      if len(row) < 6:
        continue
      try:
        rr = int(row[0])
        self_coop = float(row[1])
        eq0 = float(row[5])
      except ValueError:
        continue
      rrs.append(rr)
      xs.append(self_coop)
      ys.append(eq0)
  return xs, ys, rrs

#%% Plotting helper

def plot_rr_sweep(xs: List[float], ys: List[float], rrs: List[int]):
  fig, ax = plt.subplots(figsize=(6, 4))
  ax.scatter(xs, ys, s=18, alpha=0.7, edgecolors="none", label="Rr sweep")

  highlights = [
    (204, "red", "*", "Rr=204 (base)"),
    (170, "blue", "x", "Rr=170 (IS)")
  ]
  for target, color, marker, label in highlights:
    idxs = [i for i, rr in enumerate(rrs) if rr == target]
    if idxs:
      ax.scatter([xs[i] for i in idxs], [ys[i] for i in idxs], s=64,
                 color=color, marker=marker, label=label)

  ax.set_xlabel("self_coop")
  ax.set_ylabel("eq0")
  ax.grid(True, linestyle=":", alpha=0.5)
  ax.legend(frameon=False)
  ax.set_title("Rr sweep (main_SweepR2)")
  fig.tight_layout()
  return fig, ax

#%% Interactive defaults
IN_PATH = Path("../R2_sweep.tsv")  # adjust as needed
xs, ys, rrs = [], [], []
if IN_PATH.exists():
  xs, ys, rrs = load_rr_sweep(IN_PATH)

fig = ax = None
if xs:
  fig, ax = plot_rr_sweep(xs, ys, rrs)
  try:
    display(fig)
  except NameError:
    pass
else:
  print(f"No data loaded from {IN_PATH.resolve()}")

#%% CLI entry point

def main():
  parser = argparse.ArgumentParser(description="Plot self_coop vs eq0 from main_SweepR2 TSV")
  parser.add_argument("--in", dest="inp", required=True, help="Input TSV produced by main_SweepR2")
  parser.add_argument("--out", dest="out", default=None, help="Output image path (PNG/SVG/PDF)")
  parser.add_argument("--show", action="store_true", help="Show the plot window")
  args = parser.parse_args()

  xs, ys, rrs = load_rr_sweep(Path(args.inp))
  if not xs:
    raise SystemExit("No valid data rows found in input file.")

  fig, _ = plot_rr_sweep(xs, ys, rrs)

  out_path = args.out
  if not out_path and not args.show:
    out_path = str(Path(args.inp).with_suffix(".png"))
  if out_path:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")

  if args.show or not out_path:
    plt.show()


if __name__ == "__main__":
  main()
