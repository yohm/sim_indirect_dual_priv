#%%
#!/usr/bin/env python3
"""
Plot results from script/sweep_rr_bcs.py.

Reads a TSV file produced by sweep_rr_bcs.py and plots:
  - x-axis: self_coop
  - y-axis: stable b/c range

For each Rr entry, draws a vertical line at x=self_coop from y=bc_min to
  y=bc_max. If bc_max is None/null, treats it as infinity and draws up to a
  configurable y-limit.

VS Code Interactive tips:
  - This file is structured with '#%%' cells for stepwise execution.
  - Run the "Interactive Defaults" cell and then the "Plot Function" invocation.

CLI usage:
  python script/plot_rr_sweep_bcs.py --in results_tables/rr_bcs_rd153_p10_20250920_164955.tsv \
                                     --out figures/rr_bcs_rd153_p10.png --ymax 20

Options:
  --show   Display the plot window instead of saving (or do both if --out is also given).
  --ymax   Upper y-limit used to visualize infinite bc_max (default: 5).
"""

import argparse
import json
import os
from typing import Optional, Dict, Tuple as Tup

import matplotlib.pyplot as plt
import math


def parse_float_or_none(s: str) -> Optional[float]:
  s = s.strip()
  if s in ("", "None", "none", "null", "nan"):
    return None
  try:
    return float(s)
  except Exception:
    return None

#%% Helpers

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

#%% Plotting
def plot_rr_bcs(inp: str, out: Optional[str] = None, ymax: float = 4.0, xlim: Tup[float, float]=(0.48, 1.0), base_norm_name: str="L6"):
  by_rr, meta = load_rr_bcs(inp)
  if not by_rr:
    raise SystemExit("No data points could be read from the input file.")

  plt.figure(figsize=(6, 4))
  ax = plt.gca()
  # Larger fonts and cleaner frame
  ax.tick_params(axis='both', labelsize=16)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)

  # Plot points (self_coop, bc_min); ignore bc_max entirely
  xs, ys = [], []
  for rr, (x, y0, _y1) in by_rr.items():
    if y0 is None or not math.isfinite(y0):
      continue
    xs.append(x)
    ys.append(y0)
  plt.scatter(xs, ys, s=20, color="tab:blue", alpha=0.6, edgecolors="none")

  # Highlight base norm (Rr=KeepRecipient -> 204) and L6-IS (Rr=ImageScoring -> 170)
  rr_base = 204
  rr_is = 170
  if rr_base in by_rr:
    x, y0, _y1 = by_rr[rr_base]
    if y0 is not None and math.isfinite(y0):
      if y0 <= ymax:
        # Visible point
        plt.scatter([x], [y0], s=90, color="tab:purple", zorder=5, edgecolors="white", linewidths=0.8)
        y_txt = min(ymax - 0.05, max(1.02, y0 + 0.02))
        plt.annotate(f"{base_norm_name}", xy=(x, y0), xytext=(-3, 3), textcoords='offset points',
                     color="tab:purple", fontsize=18, ha="right", va="bottom")
      else:
        # Above ymax: show vertical arrow at top to indicate off-plot point
        y_head = ymax
        y_tail = max(1.05, y_head - 0.5)
        plt.annotate("", xy=(x, y_head), xytext=(x, y_tail),
                     arrowprops=dict(arrowstyle='-|>', color='tab:purple', linewidth=1.2))
        y_txt = ymax - 0.75
        plt.text(x, y_txt, base_norm_name, color="tab:purple", ha="center", va="bottom", fontsize=18)
  if rr_is in by_rr:
    x, y0, _y1 = by_rr[rr_is]
    if y0 is not None and math.isfinite(y0):
      plt.scatter([x], [y0], s=110, color="tab:orange", zorder=6, edgecolors="white", linewidths=0.8)
      # Place label with a fixed screen-space offset so it stays near the point regardless of x-scale
      plt.annotate(f"{base_norm_name}-IS", xy=(x, y0), xytext=(3, 3), textcoords='offset points',
                   color="tab:orange", fontsize=18, ha="left", va="bottom")

  plt.xlabel("self cooperation level", fontsize=18)
  plt.ylabel("$b/c$", fontsize=18)
  plt.xlim(xlim)
  plt.yticks([1, 2, 3, 4], fontsize=16)
  plt.xticks(fontsize=16)

  # Set y-limits to include [1, ymax]
  plt.ylim(1.0, ymax)
  plt.tight_layout()

  if out:
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")

#%% Plotting (vertical bars using bc_min and bc_max)
def plot_rr_bcs_bars(inp: str, out: Optional[str] = None, ymax: float = 4.0, xlim: Tup[float, float]=(0.48, 1.0), base_norm_name: str="L6"):
  by_rr, meta = load_rr_bcs(inp)
  if not by_rr:
    raise SystemExit("No data points could be read from the input file.")

  plt.figure(figsize=(6, 4))
  ax = plt.gca()
  ax.tick_params(axis='both', labelsize=16)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)

  # Draw vertical bars from bc_min to bc_max (None => ymax)
  for rr, (x, y0, y1) in by_rr.items():
    if y0 is None or not math.isfinite(y0):
      continue
    y_top = ymax if (y1 is None or not math.isfinite(y1)) else y1
    if y_top < y0:
      continue
    plt.vlines(x, y0, y_top, colors="tab:blue", alpha=0.5, linewidth=1.5)

  # Highlight base and IS bars
  rr_base = 204
  rr_is = 170
  if rr_base in by_rr:
    x, y0, y1 = by_rr[rr_base]
    if y0 is not None and math.isfinite(y0):
      y_top = ymax if (y1 is None or not math.isfinite(y1)) else y1
      if y_top >= y0:
        plt.vlines(x, y0, y_top, colors="tab:purple", linewidth=3.0, zorder=5)
        plt.annotate(base_norm_name, xy=(x, y0), xytext=(6, 6), textcoords='offset points',
                     color="tab:purple", fontsize=18, ha="left", va="bottom")

  if rr_is in by_rr:
    x, y0, y1 = by_rr[rr_is]
    if y0 is not None and math.isfinite(y0):
      y_top = ymax if (y1 is None or not math.isfinite(y1)) else y1
      if y_top >= y0:
        plt.vlines(x, y0, y_top, colors="tab:orange", linewidth=3.5, zorder=6)
        plt.annotate(f"{base_norm_name}-IS", xy=(x, y0), xytext=(8, 8), textcoords='offset points',
                     color="tab:orange", fontsize=18, ha="left", va="bottom")

  plt.xlabel("self cooperation level", fontsize=18)
  plt.ylabel("$b/c$", fontsize=18)
  plt.xlim(xlim)
  plt.yticks([1, 2, 3, 4], fontsize=16)
  plt.xticks(fontsize=16)
  plt.ylim(1.0, ymax)
  plt.tight_layout()

  if out:
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")

#%% Interactive Defaults
in_path = "../results_tables/rr_bcs_rd153_p10_20250920_170903.tsv"  # change as needed
out_path = "../results_tables/rr_bcs_rd153_p10_20250920_170903.pdf"
plot_rr_bcs(inp=in_path, out=out_path, ymax=4.0, xlim=(0.48, 1.0), base_norm_name="L6")

# %%
in_path = "../results_tables/rr_bcs_rd187_p10_20250920_221515.tsv"  # change as needed
plot_rr_bcs_bars(inp=in_path, out=None, ymax=4.0, xlim=(0.940, 0.98), base_norm_name="L3")
# %%
in_path = "../results_tables/rr_bcs_rd187_p10_20250920_221515.tsv"  # change as needed
out_path = "../results_tables/rr_bcs_rd187_p10_20250920_221515.pdf"
# out_path = None
plot_rr_bcs(inp=in_path, out=out_path, ymax=4.0, xlim=(0.7, 1.0), base_norm_name="L3")

# %%
# find the data whose bc_min < 1.1 and sort by bc_max in descending order
in_path = "../results_tables/rr_bcs_rd187_p10_20250920_221515.tsv"  # change as needed
by_rr, meta = load_rr_bcs(in_path)
filtered = [(rr, vals) for rr, vals in by_rr.items() if vals[1] < 1.1]
sorted_filtered = sorted(filtered, key=lambda item: (item[1][2] if item[1][2] is not None else float('inf')), reverse=True)
for rr, (self_coop, bc_min, bc_max) in sorted_filtered:
  print(f"Rr={rr}: self_coop={self_coop:.4f}, bc_min={bc_min:.4f}, bc_max={bc_max}")

# %%
