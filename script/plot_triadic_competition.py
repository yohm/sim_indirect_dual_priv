#!/usr/bin/env python3
#%%
"""
Draw a triadic competition diagram for various norms.

Calls the compiled executable `inspect_EvolPrivRepGame` with a single norm string
(e.g., L1, L6-IS, AllD, 0xHEX, or Rd-Rr-P, etc.). The executable must print a single
JSON object that includes:
  - "eq":   array-like, equilibrium shares; we use the first three entries
  - "rhos": 3x3 pairwise transition/intensity matrix (or analogous)

Usage:
  VSCode Interactive: Run cells sequentially, edit norms and params in the parameter cell
"""

#%% Imports and setup
import json
import os
import sys
from pathlib import Path
import subprocess

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

#%% Utils

ROOT = Path(__file__).resolve().parents[1]
EPRG_DEFAULT = ROOT / "cmake-build-release" / "inspect_EvolPrivRepGame"

def parse_json_stdout(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        sys.exit(f"[ERROR] invalid JSON from executable: {e}\n---BEGIN STDOUT---\n{text}\n---END STDOUT---")

def run_and_parse(exe: Path, norm: str, j_arg: str | None):
    cmd = [str(exe)]
    if j_arg:
        cmd += ["-j", j_arg]
    cmd += [norm]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit(f"[ERROR] Executable not found: {exe}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"[ERROR] Execution failed:\n$ {' '.join(cmd)}\n---STDOUT---\n{e.stdout}\n---STDERR---\n{e.stderr}")

    obj = parse_json_stdout(res.stdout)
    eq = obj.get("eq")
    rhos = obj.get("rhos")
    if eq is None or rhos is None:
        sys.exit("[ERROR] JSON must contain keys 'eq' and 'rhos'.")
    return eq[:3], rhos  # use first three eq entries

def fmt_pct1(x):  return f"{x*100:.1f}%"

def fmt_rho(x):
    if isinstance(x, (int, float)):
        return "<0.001" if x < 1e-3 else f"{x:.3f}"
    return "N/A"

#%% Colors for norms

default_colors = {
    "L1": "#4f6db8",
    "L1v": "#4f6db8",
    "L2": "#b6483a",
    "L2v": "#b6483a",
    "L3": "#86a657",
    "L4": "#6b5fb9",
    "L5": "#3d95ad",
    "L6": "#d1781c",
    "L7": "#8da4ca",
    "L8": "#c47a9b",
}

#%% Plot function
def draw_triad(norm_label: str, eq, rhos, outpath: Path | None, show: bool):
    # color for target norm (use base name before "-")
    base_name = norm_label.split('-')[0]
    target_color = default_colors.get(base_name, "black")

    # Node positions
    P_Target = (0.0, 1.0)
    P_ALLD   = (-1.20, -0.9)
    P_ALLC   = (1.20, -0.9)
    R = 0.50

    fig, ax = plt.subplots(figsize=(5.4, 5.0), dpi=150)
    ax.set_aspect("equal")
    ax.set_xlim(-2.05, 2.05)
    ax.set_ylim(-1.80, 1.95)
    ax.axis("off")

    def place_node(name, xy, face, edge, text_color, percent_text, where):
        x, y = xy
        ax.add_patch(
            Circle(
                (x, y), R,
                facecolor=face,
                edgecolor=edge,
                linewidth=1.8,
                zorder=3,
                clip_on=False,
            )
        )
        ax.text(
            x, y, percent_text,
            ha="center", va="center",
            color=text_color,
            fontsize=13,
            fontweight="bold",
            zorder=4,
        )
        if where == "top":
            ax.text(
                x, y + R + 0.08, name,
                ha="center", va="bottom",
                fontsize=18, color="black", zorder=4,
            )
        else:
            ax.text(
                x, y - R - 0.08, name,
                ha="center", va="top",
                fontsize=18, color="black", zorder=4,
            )

    gray = "#bdbdbd"

    place_node(norm_label, P_Target, target_color, target_color, "white", fmt_pct1(eq[0]), "top")
    place_node("ALLD", P_ALLD, gray, gray, "black", fmt_pct1(eq[2]), "bottom")
    place_node("ALLC", P_ALLC, "white", gray, "black", fmt_pct1(eq[1]), "bottom")

    def edge_arrow_with_label(p1, p2, value, rad, text_offset=0.18, ms=18, lw=1.3):
        a = FancyArrowPatch(
            p1, p2,
            connectionstyle=f"arc3,rad={rad}",
            arrowstyle="-|>",
            mutation_scale=ms,
            linewidth=lw,
            color="black",
            shrinkA=37,
            shrinkB=37,
            zorder=4,
        )
        ax.add_patch(a)

        (x1, y1), (x2, y2) = p1, p2
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        dx, dy = x2 - x1, y2 - y1
        nx, ny = -dy, dx
        norm = (nx * nx + ny * ny) ** 0.5 or 1.0
        nx, ny = nx / norm, ny / norm
        sign = 1 if rad >= 0 else -1
        ox, oy = mx + nx * text_offset * sign, my + ny * text_offset * sign

        ax.text(
            ox, oy, fmt_rho(value),
            ha="center", va="center",
            fontsize=11,
            color="black",
            zorder=5,
            bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.9),
        )

    edge_arrow_with_label(P_Target, P_ALLD, rhos[2][0], rad=-0.30)
    edge_arrow_with_label(P_ALLD, P_ALLC, rhos[1][2], rad=-0.18)
    edge_arrow_with_label(P_ALLC, P_Target, rhos[0][1], rad=-0.30)

    edge_arrow_with_label(P_Target, P_ALLC, rhos[1][0], rad=-0.24)
    edge_arrow_with_label(P_ALLC, P_ALLD, rhos[2][1], rad=-0.18)
    edge_arrow_with_label(P_ALLD, P_Target, rhos[0][2], rad=-0.24)

    if outpath is not None:
        outpath.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(outpath, dpi=150, bbox_inches='tight', pad_inches=0.02)
        print(f"Saved: {outpath}")

    if show:
        plt.show()

    plt.close(fig)

#%% Parameters
# Edit these parameters
norms_to_plot = ["L6"]  # Add more norms as needed: ["L1", "L6", "L6-IS", etc.]
build_dir = "cmake-build-release"
params_json = '{"N":50,"benefit":5,"beta":1,"t_init":2000,"t_measure":2000,"q":1.0,"mu_assess1":0.02,"mu_assess2":0.02,"mu_impl":0.02,"mu_percept":0.0,"_seed":123456789}'
save_figure = True
show_figure = True
output_format = "pdf"  # png, pdf, or svg

#%% Check executable
exe = ROOT / build_dir / "inspect_EvolPrivRepGame"
if not exe.exists():
    print(f"[ERROR] executable not found: {exe}")

#%% Run simulations
results = {}
if exe.exists():
    for norm in norms_to_plot:
        print(f"[INFO] Running simulation for {norm}...")
        eq, rhos = run_and_parse(exe, norm, params_json)
        results[norm] = (eq, rhos)
    print(f"[INFO] Completed {len(results)} simulations")

#%% Plot results
for norm, (eq, rhos) in results.items():
    # Add "-base" suffix if norm doesn't contain "-"
    display_name = norm if "-" in norm else f"{norm}-base"
    outpath = (ROOT / "script" / "figures" / f"triad_{norm}.{output_format}") if save_figure else None
    draw_triad(display_name, eq, rhos, outpath=outpath, show=show_figure)

#%% Plot all norms
all_norms = ["L1", "L1-IS", "L1v", "L1v-IS", "L2", "L2-IS", "L2v", "L2v-IS", 
             "L3", "L3-IS", "L4", "L4-IS", "L5", "L5-IS", "L6", "L6-IS", 
             "L7", "L7-IS", "L8", "L8-IS"]

for norm in all_norms:
    try:
        print(f"[INFO] Processing {norm}...")
        eq, rhos = run_and_parse(exe, norm, params_json)
        # Add "-base" suffix if norm doesn't contain "-"
        display_name = norm if "-" in norm else f"{norm}-base"
        outpath = (ROOT / "script" / "figures" / f"triad_{norm}.{output_format}") if save_figure else None
        draw_triad(display_name, eq, rhos, outpath=outpath, show=False)
    except Exception as e:
        print(f"[WARNING] Failed to process {norm}: {e}")

print("[INFO] All plots completed")

# %%
