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
def plot_rr_bcs(inp: str, out: Optional[str] = None, show: bool = False, ymax: float = 5.0):
  by_rr, meta = load_rr_bcs(inp)
  if not by_rr:
    raise SystemExit("No data points could be read from the input file.")

  plt.figure(figsize=(6, 4))
  ax = plt.gca()
  # Larger fonts and cleaner frame
  ax.tick_params(axis='both', labelsize=16)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)

  # Draw vertical line segments
  for rr, (x, y0, y1) in by_rr.items():
    y_top = ymax if y1 is None else y1
    # Avoid drawing if y_top < y0 due to bad data
    if y_top < y0:
      continue
    plt.vlines(x, y0, y_top, colors="tab:blue", alpha=0.5, linewidth=1.5)
    # Infinite bc_max is drawn up to ymax without arrowheads

  # Highlight base norm (Rr=KeepRecipient -> 204) and L6-IS (Rr=ImageScoring -> 170)
  base_norm_name = "L6"
  rr_base = 204
  rr_is = 170
  if rr_base in by_rr:
    x, y0, y1 = by_rr[rr_base]
    y_top = ymax if y1 is None else y1
    # Arrow if entire stable segment is above ymax (including infinite top)
    y0_above = (y0 is None) or (y0 > ymax)
    y1_above = (y1 is None) or (y1 > ymax)
    entirely_above = y0_above and y1_above
    if entirely_above:
      # Show an upward arrow near (p_c, 4.0)
      y_head = ymax
      y_tail = y_head - 0.5
      plt.annotate("", xy=(x, y_head), xytext=(x, y_tail),
                   arrowprops=dict(arrowstyle='-|>', color='red', linewidth=1.0))
      y_txt = ymax - 0.75
      plt.text(x, y_txt, base_norm_name, color="red", ha="center", va="bottom", fontsize=18)
    else:
      # Stable range exists (including infinite top). Draw highlight line.
      y0_draw = max(1.0, y0) if (y0 is not None and math.isfinite(y0)) else 1.0
      y_top = ymax if y1 is None else y1
      if y_top >= y0_draw:
        plt.vlines(x, y0_draw, y_top, colors="red", linewidth=3.0)
        # Label near y0
        y_txt = min(ymax - 0.05, max(1.02, y0_draw + 0.02))
        plt.text(x, y_txt, base_norm_name, color="red", ha="center", va="bottom", fontsize=18)
  if rr_is in by_rr:
    x, y0, y1 = by_rr[rr_is]
    y_top = ymax if y1 is None else y1
    if y_top >= y0:
      plt.vlines(x, y0, y_top, colors="tab:orange", linewidth=3.5, zorder=4)
      # Label near y0
      y0_draw = max(1.0, y0) if (y0 is not None and math.isfinite(y0)) else 1.0
      y_txt = min(ymax - 0.05, max(1.02, y0_draw + 0.01))
      plt.text(x+0.04, y_txt, f"{base_norm_name}-IS", color="tab:orange", ha="center", va="bottom", fontsize=18)
    else:
      # No visible segment; annotate near y=4 with small arrow
      y_head = min(4.0, ymax - 0.05)
      y_tail = max(1.05, y_head - 0.2)
      plt.annotate("", xy=(x, y_head), xytext=(x, y_tail),
                   arrowprops=dict(arrowstyle='-|>', color='tab:orange', linewidth=1.3))
      # Label near y0 (clamped into view)
      if y0 is not None and math.isfinite(y0):
        y_txt = y0
      else:
        y_txt = ymax - 0.1
      y_txt = min(ymax - 0.05, max(1.02, y_txt))
      plt.text(x, y_txt, f"{base_norm_name}-IS", color="tab:orange", ha="center", va="bottom", fontsize=18)

  plt.xlabel("self cooperation level", fontsize=18)
  plt.ylabel("$b/c$", fontsize=18)
  plt.xlim(0.48, 1.0)
  plt.yticks([1, 2, 3, 4], fontsize=16)
  plt.xticks(fontsize=16)
  title_bits = []
  if "rd" in meta and "p" in meta:
    title_bits.append(f"rd={meta['rd']}, p={meta['p']}")
  if "base_norm" in meta:
    title_bits.append(f"base={meta['base_norm']}")
  if "N" in meta:
    title_bits.append(f"N={meta['N']}")
  if title_bits:
    plt.title("; ".join(title_bits), fontsize=14)

  # Set y-limits to include [1, ymax]
  plt.ylim(1.0, ymax)
  # plt.grid(True, linestyle=":", alpha=0.5)
  # No legend; direct annotations are used for L6 and L6-IS
  plt.tight_layout()

  out_path = out
  if not out_path and not show:
    base, _ = os.path.splitext(inp)
    out_path = base + "_bcs.png"
  if out_path:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")

  if show:
    plt.show()

#%% Interactive Defaults
# Define defaults only in interactive shells (e.g., VS Code Interactive/Jupyter)
try:
  get_ipython  # type: ignore[name-defined]
  _IN_INTERACTIVE = True
except NameError:
  _IN_INTERACTIVE = False

if _IN_INTERACTIVE:
  # Edit these and then call: plot_rr_bcs(IN_PATH, OUT_PATH, SHOW, YMAX)
  IN_PATH = "../results_tables/rr_bcs_rd153_p10_20250920_170903.tsv"  # change as needed
  OUT_PATH = None  # e.g., "figures/rr_bcs_example.png"
  SHOW = False
  YMAX = 4.0
  plot_rr_bcs(IN_PATH, OUT_PATH, SHOW, YMAX)

#%% CLI Entrypoint
def _main_cli():
  ap = argparse.ArgumentParser(description="Plot x=self_coop vs vertical b/c stability ranges from sweep_rr_bcs output")
  ap.add_argument("--in", dest="inp", required=True, help="Input TSV produced by script/sweep_rr_bcs.py")
  ap.add_argument("--out", dest="out", default=None, help="Output image path (PNG/SVG/PDF). If omitted and --show not set, saves next to input with .png")
  ap.add_argument("--show", action="store_true", help="Show the plot window")
  ap.add_argument("--ymax", type=float, default=4.0, help="Upper y-limit used when bc_max is infinite (None). Default: 4")
  args = ap.parse_args()
  plot_rr_bcs(args.inp, args.out, args.show, args.ymax)

if __name__ == "__main__":
  _main_cli()

# %%
