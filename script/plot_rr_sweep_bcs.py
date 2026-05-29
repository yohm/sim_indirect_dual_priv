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
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from pathlib import Path

import matplotlib.pyplot as plt
from utils import figure_path, output_path

DEFAULT_HIGHLIGHT_SIZE = 250


@dataclass(frozen=True)
class RrBcsPoint:
  self_coop: float
  bc_min: Optional[float]
  bc_max: Optional[float]


@dataclass(frozen=True)
class HighlightSpec:
  rr: int
  color: str
  marker: str
  label: str
  size: int = DEFAULT_HIGHLIGHT_SIZE


BASE_HIGHLIGHTS: list[HighlightSpec] = [
  HighlightSpec(204, "navy", "o", "base"),
  HighlightSpec(170, "darkorange", "s", "RIS"),
  HighlightSpec(172, "purple", "^", "GDT"),
  HighlightSpec(255, "#009E73", "D", "ALLG", size=130)
]
# ALLG_HIGHLIGHT = HighlightSpec(255, "#009E73", "D", "ALLG", size=130)

#%% Data loading

def parse_optional_float(value: str) -> Optional[float]:
  value = value.strip()
  if value in {"", "None", "null", "nan"}:
    return None
  try:
    return float(value)
  except ValueError:
    return None


def load_rr_bcs(path: Path) -> Dict[int, RrBcsPoint]:
  by_rr: Dict[int, RrBcsPoint] = {}

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
      by_rr[rr] = RrBcsPoint(self_coop, bc_min, bc_max)

  return by_rr

#%% Plotting helpers

def format_norm_label(norm: str) -> str:
  """Format norm names for display only."""
  if norm.endswith("-IS"):
    return norm[:-3] + "-RIS"
  return norm


def plot_highlight(ax,
                   by_rr: Dict[int, RrBcsPoint],
                   highlight: HighlightSpec,
                   xlim: Tuple[float, float],
                   ymax: float) -> None:
  is_point_in_axes = False
  if highlight.rr in by_rr:
    point = by_rr[highlight.rr]
    if point.bc_min is not None and math.isfinite(point.bc_min):
      if xlim[0] <= point.self_coop <= xlim[1] and 1.0 <= point.bc_min <= ymax:
        ax.scatter([point.self_coop], [point.bc_min], s=highlight.size, color=highlight.color,
                   marker=highlight.marker, zorder=6, label=highlight.label,
                   clip_on=False)
        is_point_in_axes = True
  if not is_point_in_axes:
    # Keep legend entry even when the highlighted point is outside axes.
    ax.scatter([xlim[0] - 1], [ymax + 1], s=highlight.size,
               color=highlight.color, marker=highlight.marker,
               label=highlight.label, clip_on=True)


def plot_rr_bcs_points(by_rr: Dict[int, RrBcsPoint],
                       norm: str = "",
                       ymax: float = 5.0,
                       xlim: Tuple[float, float] = (0.5, 1.0),
                       show_legend: bool = True,
                       highlights: Optional[list[HighlightSpec]] = None):
  fig, ax = plt.subplots(figsize=(6, 5))
  ax.tick_params(axis='both', labelsize=20)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)

  xs, ys = [], []
  for point in by_rr.values():
    if point.bc_min is None or not math.isfinite(point.bc_min):
      continue
    xs.append(point.self_coop)
    ys.append(point.bc_min)
  ax.scatter(xs, ys, s=30, color="tab:blue", alpha=1.0, edgecolors="none")

  if highlights is None:
    highlights = BASE_HIGHLIGHTS
  for highlight in highlights:
    plot_highlight(ax, by_rr, highlight, xlim, ymax)

  ax.set_xlabel("self-cooperation level", fontsize=30)
  ax.set_ylabel("$b/c$", fontsize=30)
  ax.set_xlim(xlim)
  ax.set_ylim(1.0, ymax)
  ax.set_yticks([1, 2, 3, 4])
  ax.grid(True, linestyle=":", alpha=0.5)
  
  if show_legend:
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, frameon=True, fontsize=24, loc="upper right",
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
            extra_highlights: Optional[list[HighlightSpec]] = None) -> None:
  input_path = output_path(f"R2_sweep_{target_norm}.tsv")
  if not input_path.exists():
    print(f"[ERROR] File not found: {input_path}")
    return

  by_rr = load_rr_bcs(input_path)
  if not by_rr:
    print(f"[ERROR] No valid data rows found in {input_path}")
    return

  print(f"[INFO] Loaded {len(by_rr)} data points from {input_path}")
  merged_highlights = BASE_HIGHLIGHTS + (extra_highlights or [])
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


#%% Load data and plot
run_one(norm, show_legend=True, show=show_figure,
  extra_highlights=[])


#%%
# Plot all norms
for target_norm in ["L1", "L1v", "L2", "L2v", "L3", "L4", "L5", "L7", "L8"]:
  run_one(target_norm, show_legend=False, show=False, extra_highlights=[])
print("[INFO] All plots completed")


# %%
# Secondary sixteen example
run_one(
  "S1",
  show_legend=True,
  show=show_figure,
  extra_highlights=[],
)


#%%
# Run S2-S16 (S1 is already plotted above)
for i in range(2, 17):
  target_norm = f"S{i}"
  run_one(
    target_norm,
    show_legend=False,
    show=False,
    extra_highlights=[],
  )


# %%
# Secondary sixteen variants example
run_one(
  "S1v",
  show_legend=True,
  show=show_figure,
  extra_highlights=[],
)


#%%
# Run S2v-S16v (S1v is already plotted above)
for i in range(2, 17):
  target_norm = f"S{i}v"
  run_one(
    target_norm,
    show_legend=False,
    show=False,
    extra_highlights=[],
  )


# %%
