#!/usr/bin/env python3
#%%
"""
Plot exhaustive R1/R2 sweep results from main_ExhaustiveSearch.cpp.

Reads script/output/all_norms.tsv and visualises
  1) self_coop vs eq0
  2) self_coop vs bc_min(AllD)

Only points with bc_min(AllD) <= 5 are highlighted in color.
"""

#%% Imports and setup
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from utils import figure_path, output_path


@dataclass(frozen=True)
class AllNormsPoint:
  rd: int
  rr: int
  self_coop: float
  bc_min: Optional[float]
  eq0: float


@dataclass(frozen=True)
class HighlightSpec:
  rd: int
  rr: int
  label: str
  color: str = "darkorange"
  marker: str = "*"
  size: int = 260


BASE_HIGHLIGHTS: tuple[HighlightSpec, ...] = (
  HighlightSpec(153, 170, "L6-RIS"),
)


#%% Data loading

def parse_optional_float(value: str) -> Optional[float]:
  value = value.strip()
  if value in {"", "None", "null", "nan"}:
    return None
  try:
    return float(value)
  except ValueError:
    return None


def load_all_norms(path: Path) -> list[AllNormsPoint]:
  points: list[AllNormsPoint] = []

  with path.open("r", newline="") as f:
    reader = csv.reader(f, delimiter="\t")
    for row in reader:
      if not row or row[0].startswith("#"):
        continue
      if len(row) < 7:
        continue
      try:
        points.append(AllNormsPoint(
          rd=int(row[0]),
          rr=int(row[1]),
          self_coop=float(row[2]),
          bc_min=parse_optional_float(row[3]),
          eq0=float(row[6]),
        ))
      except ValueError:
        continue

  return points


#%% Plotting helpers

def format_axis_tick(value: float, _position: int) -> str:
  if abs(value) < 1e-12:
    value = 0.0
  label = f"{value:.2f}".rstrip("0").rstrip(".")
  if "." not in label:
    label += ".0"
  return label


def has_low_alld_threshold(point: AllNormsPoint, threshold: float) -> bool:
  return point.bc_min is not None and math.isfinite(point.bc_min) and point.bc_min <= threshold


def find_highlight_point(points: list[AllNormsPoint],
                         highlight: HighlightSpec) -> Optional[AllNormsPoint]:
  for point in points:
    if point.rd == highlight.rd and point.rr == highlight.rr:
      return point
  return None


def plot_highlight_eq0(ax,
                       points: list[AllNormsPoint],
                       highlight: HighlightSpec) -> None:
  point = find_highlight_point(points, highlight)
  if point is None:
    return
  ax.scatter(
    [point.self_coop],
    [point.eq0],
    s=highlight.size,
    color=highlight.color,
    marker=highlight.marker,
    edgecolors="black",
    linewidths=0.8,
    label=highlight.label,
    zorder=5,
  )


def plot_highlight_bcs(ax,
                       points: list[AllNormsPoint],
                       highlight: HighlightSpec) -> None:
  point = find_highlight_point(points, highlight)
  if point is None or point.bc_min is None or not math.isfinite(point.bc_min):
    return
  ax.scatter(
    [point.self_coop],
    [point.bc_min],
    s=highlight.size,
    color=highlight.color,
    marker=highlight.marker,
    edgecolors="black",
    linewidths=0.8,
    label=highlight.label,
    zorder=5,
  )


def plot_all_norms(points: list[AllNormsPoint],
                   *,
                   bc_threshold: float = 5.0,
                   xlim: tuple[float, float] | None = None,
                   title: str = "",
                   highlights: tuple[HighlightSpec, ...] = BASE_HIGHLIGHTS):
  fig, ax = plt.subplots(figsize=(6, 5))

  low_bc = [point for point in points if has_low_alld_threshold(point, bc_threshold)]
  other = [point for point in points if not has_low_alld_threshold(point, bc_threshold)]

  ax.scatter(
    [point.self_coop for point in other],
    [point.eq0 for point in other],
    s=10,
    color="lightgray",
    alpha=0.45,
    edgecolors="none",
    label=fr"$b/c_{{min}}(\mathrm{{AllD}}) > {bc_threshold:g}$ or None",
    zorder=1,
  )
  ax.scatter(
    [point.self_coop for point in low_bc],
    [point.eq0 for point in low_bc],
    s=10,
    color="tab:blue",
    alpha=0.75,
    edgecolors="none",
    label=fr"$b/c_{{min}}(\mathrm{{AllD}}) \leq {bc_threshold:g}$",
    zorder=2,
  )

  for highlight in highlights:
    plot_highlight_eq0(ax, points, highlight)

  ax.set_xlabel("self-cooperation level", fontsize=30)
  ax.set_ylabel("equilibrium fraction", fontsize=30)
  if xlim is not None:
    ax.set_xlim(xlim)
  ax.xaxis.set_major_formatter(FuncFormatter(format_axis_tick))
  ax.set_ylim(-0.05, 1.05)
  ax.tick_params(axis="both", labelsize=20)
  ax.grid(True, linestyle=":", alpha=0.5)
  ax.legend(frameon=True, framealpha=0.9, fontsize=14, loc="center right")

  if title:
    ax.set_title(title, fontsize=28, pad=20)

  ax.spines["top"].set_visible(False)
  ax.spines["right"].set_visible(False)

  fig.subplots_adjust(left=0.18, right=0.97, top=0.9, bottom=0.17)
  return fig, ax


def plot_all_norms_bcs(points: list[AllNormsPoint],
                       *,
                       ymax: float = 5.0,
                       xlim: tuple[float, float] = (0.5, 1.0),
                       title: str = "",
                       highlights: tuple[HighlightSpec, ...] = BASE_HIGHLIGHTS):
  fig, ax = plt.subplots(figsize=(6, 5))

  valid_points = [point for point in points if point.bc_min is not None and math.isfinite(point.bc_min)]

  ax.scatter(
    [point.self_coop for point in valid_points],
    [point.bc_min for point in valid_points],
    s=10,
    color="tab:blue",
    alpha=0.75,
    edgecolors="none",
  )

  for highlight in highlights:
    plot_highlight_bcs(ax, points, highlight)

  ax.set_xlabel("self-cooperation level", fontsize=30)
  ax.set_ylabel("$b/c$", fontsize=30)
  ax.set_xlim(xlim)
  ax.set_ylim(1.0, ymax)
  ax.set_yticks([1, 2, 3, 4, 5])
  ax.tick_params(axis="both", labelsize=20)
  ax.grid(True, linestyle=":", alpha=0.5)
  ax.legend(frameon=True, framealpha=0.9, fontsize=18, loc="upper right",
            labelspacing=0.3, handletextpad=0.5, borderpad=0.4)

  if title:
    ax.set_title(title, fontsize=28, pad=20)

  ax.spines["top"].set_visible(False)
  ax.spines["right"].set_visible(False)

  fig.subplots_adjust(left=0.13, right=0.95, top=0.9, bottom=0.17)
  return fig, ax


#%% Parameters
input_path = output_path("all_norms.tsv")
output_filename = "all_norms_rr_sweep.pdf"
output_bcs_filename = "all_norms_rr_sweep_bcs.pdf"

bc_threshold = 5.0
ymax = 5.0
xlim_bcs = (0.5, 1.0)
title = ""

save_figure = True
show_figure = True
save_bcs_figure = True
show_bcs_figure = True


def run_plot(*,
             input_path: Path,
             output_filename: str,
             bc_threshold: float,
             title: str,
             save: bool,
             show: bool) -> None:
  points = load_all_norms(input_path)
  if not points:
    print(f"[ERROR] No valid data rows found in {input_path}")
    return

  low_bc_count = sum(has_low_alld_threshold(point, bc_threshold) for point in points)
  print(f"[INFO] Loaded {len(points)} data points from {input_path}")
  print(f"[INFO] Highlighting {low_bc_count} points with bc_min(AllD) <= {bc_threshold:g}")

  fig, _ax = plot_all_norms(
    points,
    bc_threshold=bc_threshold,
    title=title,
  )
  if save:
    out = figure_path(output_filename)
    fig.savefig(out)
    print(f"[INFO] Saved: {out}")

  if show:
    plt.show()
  else:
    plt.close(fig)


def run_bcs_plot(*,
                 input_path: Path,
                 output_filename: str,
                 ymax: float,
                 xlim: tuple[float, float],
                 title: str,
                 save: bool,
                 show: bool) -> None:
  points = load_all_norms(input_path)
  if not points:
    print(f"[ERROR] No valid data rows found in {input_path}")
    return

  valid_count = sum(point.bc_min is not None and math.isfinite(point.bc_min) for point in points)
  print(f"[INFO] Loaded {len(points)} data points from {input_path}")
  print(f"[INFO] Plotting {valid_count} points with finite bc_min(AllD)")

  fig, _ax = plot_all_norms_bcs(
    points,
    ymax=ymax,
    xlim=xlim,
    title=title,
  )
  if save:
    out = figure_path(output_filename)
    fig.savefig(out)
    print(f"[INFO] Saved: {out}")

  if show:
    plt.show()
  else:
    plt.close(fig)


#%% Load data and plot
run_plot(
  input_path=input_path,
  output_filename=output_filename,
  bc_threshold=bc_threshold,
  title=title,
  save=save_figure,
  show=show_figure,
)

#%% Load data and plot b/c threshold
run_bcs_plot(
  input_path=input_path,
  output_filename=output_bcs_filename,
  ymax=ymax,
  xlim=xlim_bcs,
  title=title,
  save=save_bcs_figure,
  show=show_bcs_figure,
)

# %%
