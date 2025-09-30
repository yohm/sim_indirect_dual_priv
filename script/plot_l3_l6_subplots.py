#!/usr/bin/env python3
#%%
"""
Create a 1x4 subplot figure comparing L3/L3-IS and L6/L6-IS.

Inputs: TSV files produced by script/sweep_rr_bcs.py for L3 and L6 respectively.

Layout (left -> right):
  1) Bar chart of self cooperation level for L3 vs L3-IS
  2) Vertical range bars [bc_min, bc_max] for L3 vs L3-IS
  3) Bar chart of self cooperation level for L6 vs L6-IS
  4) Vertical range bars [bc_min, bc_max] for L6 vs L6-IS

Example (CLI):
  python script/plot_l3_l6_subplots.py \
    --in-l3 results_tables/rr_bcs_rd187_p10_20250920_221515.tsv \
    --in-l6 results_tables/rr_bcs_rd153_p10_20250920_170903.tsv \
    --out figures/l3_l6_subplots.png

VS Code Interactive:
  - Run cells top-to-bottom; edit IN_L3/IN_L6; then run
    plot_l3_l6_subplots(IN_L3, IN_L6, OUT_PATH)
"""

#%% Imports
import argparse
import json
import os
from typing import Optional, Dict, Tuple

import matplotlib.pyplot as plt


#%% Helpers
def parse_float_or_none(s: str) -> Optional[float]:
  s = s.strip()
  if s in ("", "None", "none", "null", "nan"):
    return None
  try:
    return float(s)
  except Exception:
    return None


def load_rr_bcs(path: str) -> Dict[int, Tuple[Optional[float], Optional[float], Optional[float]]]:
  """Return mapping rr_id -> (self_coop, bc_min, bc_max)."""
  by_rr: Dict[int, Tuple[Optional[float], Optional[float], Optional[float]]] = {}
  with open(path, "r") as f:
    lines = f.read().splitlines()
  if lines and lines[0].startswith("# sweep_rr_bcs meta:"):
    lines = lines[1:]
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
    by_rr[rr] = (self_coop, bc_min, bc_max)
  return by_rr


#%% Plotting core
def _style_axes(ax, remove_top_right=True):
  if remove_top_right:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
  ax.tick_params(axis='both', labelsize=14)


def _bar_two(ax, val_base: Optional[float], val_is: Optional[float], labels=("L3", "L3-IS"), colors=("tab:purple", "tab:orange")):
  xs = [0, 1]
  ys = [val_base if val_base is not None else 0.0,
        val_is if val_is is not None else 0.0]
  ax.bar(xs, ys, color=colors, alpha=0.9)
  ax.set_xticks(xs, labels)
  ax.set_ylim(0.0, 1.0)
  ax.set_ylabel("self cooperation level", fontsize=18)
  for x, y in zip(xs, ys):
    if y is not None:
      ax.text(x, min(1.0 - 0.02, y + 0.02), f"{y:.3f}", ha='center', va='bottom', fontsize=12)


def _range_two(ax, base: Tuple[Optional[float], Optional[float]], isv: Tuple[Optional[float], Optional[float]], labels=("L3", "L3-IS"), colors=("tab:purple", "tab:orange")):
  # base = (bc_min, bc_max)
  # isv = (bc_min, bc_max)
  xs = [0, 1]
  bottoms = []
  tops = []
  for bc in (base, isv):
    y0, y1 = bc
    y0p = 1.0 if y0 is None else max(1.0, y0)
    y1p = 4.0 if y1 is None else min(4.0, y1)
    bottoms.append(y0p)
    tops.append(y1p)
  # Draw thick "range bars" using bar() for visual consistency with bar charts
  bar_width = 0.6
  for x, (orig_bc), y0p, y1p, c in zip(xs, (base, isv), bottoms, tops, colors):
    if y1p >= y0p:
      ax.bar(x, y1p - y0p, bottom=y0p, width=bar_width, color=c, alpha=0.6, align='center', edgecolor='none')
      # Add boundary markers: always bottom; top only if not clipped above ymax
      ax.scatter([x], [y0p], s=24, color=c, edgecolors='white', zorder=3)
      _, y1_orig = orig_bc
      if y1_orig is not None and y1_orig <= 4.0:
        ax.scatter([x], [y1p], s=24, color=c, edgecolors='white', zorder=3)
  ax.set_xticks(xs, labels)
  # Ensure x-limits always include tick positions even if nothing is drawn
  ax.set_xlim(-0.5, 1.5)
  ax.set_ylim(1.0, 4.0)
  ax.set_yticks([1, 2, 3, 4])
  ax.set_ylabel("$b/c$", fontsize=18)


def plot_l3_l6_subplots(in_l3: str,
                        in_l6: str,
                        out: Optional[str] = None):
  data_l3 = load_rr_bcs(in_l3)
  data_l6 = load_rr_bcs(in_l6)
  # rr ids
  RR_BASE = 204
  RR_IS = 170
  sc_l3_base, bcmin_l3_base, bcmax_l3_base = data_l3.get(RR_BASE, (None, None, None))
  sc_l3_is,   bcmin_l3_is,   bcmax_l3_is   = data_l3.get(RR_IS,   (None, None, None))
  sc_l6_base, bcmin_l6_base, bcmax_l6_base = data_l6.get(RR_BASE, (None, None, None))
  sc_l6_is,   bcmin_l6_is,   bcmax_l6_is   = data_l6.get(RR_IS,   (None, None, None))

  fig, axes = plt.subplots(1, 4, figsize=(12.5, 3.6), constrained_layout=True)

  # L3 self coop
  ax = axes[0]
  _style_axes(ax)
  _bar_two(ax, sc_l3_base, sc_l3_is, labels=("L3", "L3-IS"), colors=("tab:purple", "tab:orange"))

  # L3 bc range
  ax = axes[1]
  _style_axes(ax)
  _range_two(ax, (bcmin_l3_base, bcmax_l3_base), (bcmin_l3_is, bcmax_l3_is), labels=("L3", "L3-IS"), colors=("tab:purple", "tab:orange"))

  # L6 self coop
  ax = axes[2]
  _style_axes(ax)
  _bar_two(ax, sc_l6_base, sc_l6_is, labels=("L6", "L6-IS"), colors=("tab:purple", "tab:orange"))

  # L6 bc range
  ax = axes[3]
  _style_axes(ax)
  _range_two(ax, (bcmin_l6_base, bcmax_l6_base), (bcmin_l6_is, bcmax_l6_is), labels=("L6", "L6-IS"), colors=("tab:purple", "tab:orange"))

  if out:
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
  else:
    plt.show()


#%% Interactive defaults
IN_L3 = "../results_tables/rr_bcs_rd187_p10_20250920_221515.tsv"
IN_L6 = "../results_tables/rr_bcs_rd153_p10_20250920_170903.tsv"
OUT_PATH = "../figures/l3_l6_subplots.pdf"
plot_l3_l6_subplots(IN_L3, IN_L6, OUT_PATH)


# CLI entrypoint intentionally omitted; this module is intended for VS Code Interactive use.

# %%
