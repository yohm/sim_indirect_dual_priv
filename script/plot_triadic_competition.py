#!/usr/bin/env python3
"""
Draw a triadic competition diagram for various norms.

- Calls the compiled executable `inspect_EvolPrivRepGame` with a single norm string
  (e.g., L1, L6-IS, AllD, 0xHEX, or Rd-Rr-P, etc.). The executable must print a single
  JSON object that includes:
    - "eq":   array-like, equilibrium shares; we use the first three entries
    - "rhos": 3x3 pairwise transition/intensity matrix (or analogous)

- Supports forwarding JSON params with -j (either a path to JSON file or inline JSON string),
  and custom build dir (e.g., cmake-build-release).

Usage (from repo root):
  uv venv .venv && source .venv/bin/activate
  uv pip install -r script/requirements.txt

Usage examples:
  # show window for L1
  python script/plot_triadic_competition.py --norms L1

  # multiple norms, save each as figures/triad_<norm>.(png|pdf|svg) without showing windows
  python script/plot_triadic_competition.py --norms L1 L1-IS L1v L1v-IS L2 L2-IS L2v L2v-IS L3 L3-IS L4 L4-IS L5 L5-IS L6 L6-IS L7 L7-IS L8 L8-IS\
      --build-dir cmake-build-release \
      --params '{"N":50,"benefit":5,"beta":1,"t_init":2000,"t_measure":2000,"q":0.9,"mu_assess1":0.01,"mu_assess2":0.01,"mu_impl":0.00,"mu_percept":0.05,"seed":123456789}' \
      --save --format pdf --no-show

  # pass PRG params via JSON file and custom build dir
  python script/plot_triadic_competition.py --norms L1-IS \
      --build-dir cmake-build-release \
      --params '{"N":50,"benefit":5,"beta":1,"t_init":2000,"t_measure":2000,"q":0.9,"mu_assess1":0.05,"mu_assess2":0.0,"mu_impl":0.0,"mu_percept":0.0,"seed":123456789}' \
      --save --format png
"""

import argparse
import json
import os
import sys
from pathlib import Path
import subprocess

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

# ---------- Utils ----------

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

# ---------- Plot ----------

def draw_triad(norm_label: str, eq, rhos, outpath: Path | None, show: bool):
    # Node positions
    P_Target   = (0.0,   1.0)
    P_ALLD = (-1.20, -0.72)
    P_ALLC = ( 1.20, -0.72)
    R = 0.40

    fig, ax = plt.subplots(figsize=(5.4, 5.0), dpi=150)
    ax.set_aspect('equal')
    ax.set_xlim(-2.05, 2.05)
    ax.set_ylim(-1.80, 1.95)
    ax.axis('off')

    # Nodes
    def place_node(name, xy, face, edge, text_color, percent_text, where):
        x, y = xy
        ax.add_patch(Circle((x, y), R, facecolor=face, edgecolor=edge,
                            linewidth=1.8, zorder=3, clip_on=False))
        ax.text(x, y, percent_text, ha="center", va="center", color=text_color,
                fontsize=13, fontweight="bold", zorder=4)
        gap_top = 0.15
        gap_bot = 0.15
        if where == "top":
            ax.text(x, y + R + gap_top, name, ha="center", va="bottom",
                    fontsize=13, color="black", zorder=4)
        else:
            ax.text(x, y - R - gap_bot, name, ha="center", va="top",
                    fontsize=13, color="black", zorder=4)

    gray = "#bdbdbd"
    place_node(f"{norm_label}",   P_Target,   "black", "black", "white", fmt_pct1(eq[0]), "top")
    place_node("ALLD", P_ALLD, gray,       gray,      "black", fmt_pct1(eq[2]), "bottom")
    place_node("ALLC", P_ALLC, "white",    gray,      "black", fmt_pct1(eq[1]), "bottom")

    # Curved arrows + labels
    def edge_arrow_with_label(p1, p2, value, rad, text_offset=0.18, ms=12, lw=1.3):
        a = FancyArrowPatch(p1, p2, connectionstyle=f"arc3,rad={rad}",
                            arrowstyle="-|>", mutation_scale=ms,
                            linewidth=lw, color="black",
                            shrinkA=26, shrinkB=26, zorder=2)
        ax.add_patch(a)
        (x1, y1), (x2, y2) = p1, p2
        mx, my = ((x1+x2)/2.0, (y1+y2)/2.0)
        dx, dy = (x2-x1, y2-y1)
        nx, ny = -dy, dx
        norm = (nx*nx + ny*ny)**0.5 or 1.0
        nx, ny = nx/norm, ny/norm
        sign = 1 if rad >= 0 else -1
        ox, oy = mx + nx*text_offset*sign, my + ny*text_offset*sign
        ax.text(ox, oy, fmt_rho(value), ha="center", va="center",
                fontsize=11, color="black", zorder=5,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.9))

    outer_left_rad   = -0.30
    outer_bottom_rad = -0.18
    outer_right_rad  = -0.30
    inner_right_rad  = -0.24
    inner_bottom_rad = -0.18
    inner_left_rad   = -0.24

    # Outer 3
    edge_arrow_with_label(P_Target,   P_ALLD, rhos[2][0], rad=outer_left_rad)
    edge_arrow_with_label(P_ALLD, P_ALLC, rhos[1][2], rad=outer_bottom_rad)
    edge_arrow_with_label(P_ALLC, P_Target,   rhos[0][1], rad=outer_right_rad)

    # Inner 3
    edge_arrow_with_label(P_Target,   P_ALLC, rhos[1][0], rad=inner_right_rad)
    edge_arrow_with_label(P_ALLC, P_ALLD, rhos[2][1], rad=inner_bottom_rad)
    edge_arrow_with_label(P_ALLD, P_Target,   rhos[0][2], rad=inner_left_rad)

    if outpath is not None:
        outpath.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(outpath, dpi=150)
        print(f"Saved: {outpath}")

    if show:
        plt.show()

    plt.close(fig)

# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="Draw triadic competition diagrams for given norms.")
    parser.add_argument("--norms", nargs="+", required=True,
                        help="Norm strings (e.g., L1, L6-IS, AllD, 0xHEX, or Rd-Rr-P).")
    parser.add_argument("--build-dir", default=str(EPRG_DEFAULT.parent),
                        help="Directory containing inspect_EvolPrivRepGame (default: cmake-build-release).")
    parser.add_argument("--params", default=None,
                        help="JSON string or path to JSON for -j (t_init, t_measure, q, mus, seed...).")
    parser.add_argument("--save", action="store_true", help="Save figures to figures/triad_<norm>.<format>")
    parser.add_argument("--format", choices=["png", "pdf", "svg"], default="png",
                        help="Output image format when --save is set (default: png)")
    parser.add_argument("--no-show", action="store_true", help="Do not open windows")
    args = parser.parse_args()

    # Make cwd stable (repo root)
    os.chdir(ROOT)

    exe = Path(args.build_dir) / "inspect_EvolPrivRepGame"
    if not exe.exists():
        sys.exit(f"[ERROR] executable not found: {exe}")

    # Prepare -j payload (inline JSON string)
    j_arg = None
    if args.params:
        if os.path.exists(args.params):
            with open(args.params) as f:
                j_arg = f.read()
        else:
            j_arg = args.params

    for norm in args.norms:
        eq, rhos = run_and_parse(exe, norm, j_arg)
        outpath = (ROOT / "figures" / f"triad_{norm}.{args.format}") if args.save else None
        draw_triad(norm, eq, rhos, outpath=outpath, show=(not args.no_show))

if __name__ == "__main__":
    main()
