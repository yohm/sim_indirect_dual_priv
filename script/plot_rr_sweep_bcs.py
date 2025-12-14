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
                       norm: str = "",
                       ymax: float = 5.0,
                       xlim: Tuple[float, float] = (0.5, 1.0),
                       show_legend: bool = True):
  fig, ax = plt.subplots(figsize=(6, 5))
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

  highlights = [
    (172, "green", "^", "good-donor-trusting"),
    (170, "darkorange", "D", "IS"),
    (204, "red", "*", "base")
  ]
  for target_rr, color, marker, label in highlights:
    if target_rr in by_rr:
      x, y0, _ = by_rr[target_rr]
      if y0 is not None and math.isfinite(y0):
        # Plot point even if outside ylim, clip it for display but keep label for legend
        ax.scatter([x], [y0], s=150, color=color, marker=marker, zorder=6, label=label, clip_on=False)
      else:
        # If data is invalid but we want it in legend, plot a dummy point outside the plot area
        ax.scatter([xlim[0] - 1], [ymax + 1], s=150, color=color, marker=marker, label=label, clip_on=True)

  ax.set_xlabel("self cooperation level", fontsize=24)
  ax.set_ylabel("$b/c$", fontsize=24)
  ax.set_xlim(xlim)
  ax.set_ylim(1.0, ymax)
  ax.set_yticks([1, 2, 3, 4])
  ax.grid(True, linestyle=":", alpha=0.5)
  
  if show_legend:
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], frameon=True, fontsize=12)
  
  if norm:
    ax.set_title(norm, fontsize=24)
  
  fig.subplots_adjust(left=0.13, right=0.95, top=0.91, bottom=0.15)
  return fig, ax



#%% Parameters
# Edit the norm to plot
norm = "L6"  # L1, L2, L3, L4, L5, L6, L7, L8

save_figure = True
show_figure = True
ymax = 4.0
xlim = (0.5, 1.0)


#%% Load data and plot
input_path = Path(f"output/R2_sweep_{norm}.tsv")

if not input_path.exists():
  print(f"[ERROR] File not found: {input_path}")
else:
  by_rr = load_rr_bcs(input_path)
  
  if not by_rr:
    print(f"[ERROR] No valid data rows found in {input_path}")
  else:
    print(f"[INFO] Loaded {len(by_rr)} data points from {input_path}")
    
    fig, ax = plot_rr_bcs_points(by_rr, norm=norm, ymax=ymax, xlim=xlim, show_legend=True)
    
    if save_figure:
      Path("figures").mkdir(exist_ok=True)
      output_path = Path(f"figures/rr_sweep_bcs_{norm}.pdf")
      fig.savefig(output_path)
      print(f"[INFO] Saved: {output_path}")
    
    if show_figure:
      plt.show()
    else:
      plt.close(fig)



#%%
# Plot all norms
for norm in ["L1", "L1v", "L2", "L2v", "L3", "L4", "L5", "L7", "L8"]:
  input_path = Path(f"output/R2_sweep_{norm}.tsv")
  
  if not input_path.exists():
    print(f"[WARNING] File not found: {input_path}, skipping")
    continue
  
  by_rr = load_rr_bcs(input_path)
  
  if not by_rr:
    print(f"[WARNING] No valid data for {norm}, skipping")
    continue
  
  print(f"[INFO] Processing {norm}: {len(by_rr)} data points")
  
  fig, ax = plot_rr_bcs_points(by_rr, norm=norm, ymax=ymax, xlim=xlim, show_legend=False)
  
  if save_figure:
    Path("figures").mkdir(exist_ok=True)
    output_path = Path(f"figures/rr_sweep_bcs_{norm}.pdf")
    fig.savefig(output_path)
    print(f"[INFO] Saved: {output_path}")
  
  plt.close(fig)

print("[INFO] All plots completed")


# %%
