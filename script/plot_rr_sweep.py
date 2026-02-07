#!/usr/bin/env python3
#%%
"""
Plot results from main_SweepR2.cpp sweeps.

Reads the TSV written by main_SweepR2 and visualises
  x-axis: self_coop (column 2)
  y-axis: eq0        (column 6)

Usage:
  VSCode Interactive: Run cells sequentially, edit norm in the parameter cell
"""

#%% Imports and setup
import csv
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

def plot_rr_sweep(xs: List[float], ys: List[float], rrs: List[int], norm: str = "", show_legend: bool = True):
  fig, ax = plt.subplots(figsize=(6, 5))
  ax.scatter(xs, ys, s=30, alpha=1.0, edgecolors="none")

  highlights = [
    (172, "purple", "^", "GDT"), # "Rr=172 (good-donor-trusting)")
    (170, "darkorange", "s", "IS"), # "Rr=170 (IS)")
    (204, "navy", "o", "base") # "Rr=204 (base)")
  ]
  for target, color, marker, label in highlights:
    idxs = [i for i, rr in enumerate(rrs) if rr == target]
    if idxs:
      ax.scatter([xs[i] for i in idxs], [ys[i] for i in idxs], s=250,
                 color=color, marker=marker, label=label)

  ax.set_xlabel("self-cooperation level", fontsize=30)
  ax.set_ylabel("equilibrium fraction", fontsize=30)
  ax.tick_params(axis='both', labelsize=20)
  ax.grid(True, linestyle=":", alpha=0.5)
  
  # Reverse legend order so base appears first
  if show_legend:
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], frameon=True, fontsize=24, loc="center right",
              labelspacing=0.3, handletextpad=0.5, borderpad=0.4)
  
  # Set title if norm is provided
  if norm:
    ax.set_title(norm, fontsize=32, pad=20)
  
  # Remove top and right spines
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)
  
  fig.subplots_adjust(left=0.18, right=0.97, top=0.85, bottom=0.17)
  return fig, ax

#%% Parameters
# Edit the norm to plot
norm = "L6"  # L1, L2, L3, L4, L5, L6, L7, L8

save_figure = True
show_figure = True


#%% Load data and plot
input_path = Path(f"output/R2_sweep_{norm}.tsv")

if not input_path.exists():
  print(f"[ERROR] File not found: {input_path}")
else:
  xs, ys, rrs = load_rr_sweep(input_path)
  
  if not xs:
    print(f"[ERROR] No valid data rows found in {input_path}")
  else:
    print(f"[INFO] Loaded {len(xs)} data points from {input_path}")
    
    fig, ax = plot_rr_sweep(xs, ys, rrs, norm=norm, show_legend=True)
    
    if save_figure:
      Path("figures").mkdir(exist_ok=True)
      output_path = Path(f"figures/rr_sweep_{norm}.pdf")
      fig.savefig(output_path)
      print(f"[INFO] Saved: {output_path}")
    
    if show_figure:
      plt.show()
    else:
      plt.close(fig)


#%%
# Plot all norms
for norm in ["L1", "L1v", "L2", "L2v", "L3", "L4", "L5", "L7", "L8"]:  # L6 already done
  input_path = Path(f"output/R2_sweep_{norm}.tsv")
  
  if not input_path.exists():
    print(f"[WARNING] File not found: {input_path}, skipping")
    continue
  
  xs, ys, rrs = load_rr_sweep(input_path)
  
  if not xs:
    print(f"[WARNING] No valid data for {norm}, skipping")
    continue
  
  print(f"[INFO] Processing {norm}: {len(xs)} data points")
  
  # Show legend only for L6
  fig, ax = plot_rr_sweep(xs, ys, rrs, norm=norm, show_legend=(norm == "L6"))
  
  if save_figure:
    Path("figures").mkdir(exist_ok=True)
    output_path = Path(f"figures/rr_sweep_{norm}.pdf")
    fig.savefig(output_path)
    print(f"[INFO] Saved: {output_path}")
  
  plt.close(fig)

print("[INFO] All plots completed")

# %%
