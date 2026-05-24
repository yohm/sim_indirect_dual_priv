#%%
#!/usr/bin/env python3
#%%
"""
Plot results from main_SweepR2.cpp sweep (bc columns).

Reads the TSV written by main_SweepR2 and visualises self_coop vs bc_min(AllD).

Usage:
  VSCode Interactive: Run cells sequentially, edit norm in the parameter cell
"""

#%% Imports and setup
import csv
import math
from typing import Dict, Optional, Tuple
from pathlib import Path

import matplotlib.pyplot as plt
from utils import figure_path, output_path

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

def format_norm_label(norm: str) -> str:
  """Format norm names for display only."""
  if norm.endswith("-IS"):
    return norm[:-3] + "-RIS"
  return norm


def plot_rr_bcs_points(by_rr: Dict[int, Tuple[float, Optional[float], Optional[float]]],
                       norm: str = "",
                       ymax: float = 5.0,
                       xlim: Tuple[float, float] = (0.5, 1.0),
                       show_legend: bool = True,
                       highlights: Optional[list[Tuple[int, str, str, str]]] = None):
  fig, ax = plt.subplots(figsize=(6, 5))
  ax.tick_params(axis='both', labelsize=20)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)

  xs, ys = [], []
  for rr, (self_coop, bc_min, _) in by_rr.items():
    if bc_min is None or not math.isfinite(bc_min):
      continue
    xs.append(self_coop)
    ys.append(bc_min)
  ax.scatter(xs, ys, s=30, color="tab:blue", alpha=1.0, edgecolors="none")

  if highlights is None:
    highlights = [
      (172, "purple", "^", "GDT"),
      (170, "darkorange", "s", "RIS"),
      (204, "navy", "o", "base"),
    ]
  for target_rr, color, marker, label in highlights:
    plotted_in_range = False
    if target_rr in by_rr:
      x, y0, _ = by_rr[target_rr]
      if y0 is not None and math.isfinite(y0):
        if xlim[0] <= x <= xlim[1] and 1.0 <= y0 <= ymax:
          ax.scatter([x], [y0], s=250, color=color, marker=marker, zorder=6, label=label)
          plotted_in_range = True
    if not plotted_in_range:
      # Keep legend entry even when the highlighted point is outside axes.
      ax.scatter([xlim[0] - 1], [ymax + 1], s=250, color=color, marker=marker, label=label, clip_on=True)

  ax.set_xlabel("self cooperation level", fontsize=30)
  ax.set_ylabel("$b/c$", fontsize=30)
  ax.set_xlim(xlim)
  ax.set_ylim(1.0, ymax)
  ax.set_yticks([1, 2, 3, 4])
  ax.grid(True, linestyle=":", alpha=0.5)
  
  if show_legend:
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], frameon=True, fontsize=24, loc="upper right",
              labelspacing=0.3, handletextpad=0.5, borderpad=0.4)
  
  if norm:
    ax.set_title(format_norm_label(norm), fontsize=32, pad=20)
  
  fig.subplots_adjust(left=0.13, right=0.95, top=0.85, bottom=0.17)
  return fig, ax



#%% Parameters
# Edit the norm to plot
norm = "L6"  # L1, L2, L3, L4, L5, L6, L7, L8

save_figure = True
show_figure = True
ymax = 4.0
xlim = (0.5, 1.0)


def run_one(target_norm: str,
            *,
            show_legend: bool,
            show: bool,
            extra_highlights: Optional[list[Tuple[int, str, str, str]]] = None) -> None:
  input_path = output_path(f"R2_sweep_{target_norm}.tsv")
  if not input_path.exists():
    print(f"[ERROR] File not found: {input_path}")
    return

  by_rr = load_rr_bcs(input_path)
  if not by_rr:
    print(f"[ERROR] No valid data rows found in {input_path}")
    return

  print(f"[INFO] Loaded {len(by_rr)} data points from {input_path}")
  base_highlights = [
    (172, "purple", "^", "GDT"),
    (170, "darkorange", "s", "RIS"),
    (204, "navy", "o", "base"),
  ]
  merged_highlights = (extra_highlights or []) + base_highlights
  fig, ax = plot_rr_bcs_points(
    by_rr,
    norm=target_norm,
    ymax=ymax,
    xlim=xlim,
    show_legend=show_legend,
    highlights=merged_highlights,
  )
  if save_figure:
    out = figure_path(f"rr_sweep_bcs_{target_norm}.pdf")
    fig.savefig(out)
    print(f"[INFO] Saved: {out}")
  if show:
    plt.show()
  else:
    plt.close(fig)


def run_all() -> None:
  for target_norm in ["L1", "L1v", "L2", "L2v", "L3", "L4", "L5", "L7", "L8"]:
    input_path = output_path(f"R2_sweep_{target_norm}.tsv")
    if not input_path.exists():
      print(f"[WARNING] File not found: {input_path}, skipping")
      continue
    by_rr = load_rr_bcs(input_path)
    if not by_rr:
      print(f"[WARNING] No valid data for {target_norm}, skipping")
      continue
    print(f"[INFO] Processing {target_norm}: {len(by_rr)} data points")
    fig, ax = plot_rr_bcs_points(by_rr, norm=target_norm, ymax=ymax, xlim=xlim, show_legend=False)
    if save_figure:
      out = figure_path(f"rr_sweep_bcs_{target_norm}.pdf")
      fig.savefig(out)
      print(f"[INFO] Saved: {out}")
    plt.close(fig)
  print("[INFO] All plots completed")


#%% Load data and plot
run_one(norm, show_legend=True, show=show_figure,
# run_one("L5", show_legend=True, show=show_figure,
  extra_highlights=[(255, "crimson", "D", "ALLG")])


#%%
# Plot all norms
run_all()


# %%
# Secondary sixteen example
run_one(
  "S1",
  show_legend=True,
  show=show_figure,
  extra_highlights=[(255, "crimson", "D", "ALLG")],
)


#%%
# Run S2-S16 (S1 is already plotted above)
for i in range(2, 17):
  target_norm = f"S{i}"
  run_one(
    target_norm,
    show_legend=False,
    show=False,
    extra_highlights=[(255, "crimson", "D", "ALLG")],
  )


# %%
