"""
Under construction! 
The layout of figure is not perfect.
Unable to properly create figures for norms other than L1.

Usage (from repo root):
  uv venv .venv && source .venv/bin/activate
  uv pip install -r script/requirements.txt
  cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release && cmake --build cmake-build-release -j
  python script/TriadicCompetition.py L1
  python script/TriadicCompetition.py "1.00 0.00 1.00 1.00 1.00 0.00 1.00 1.00 1.00 0.00 1.00 0.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00"
"""

import subprocess, sys, json, os
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

# Resolve repo root; keep CWD consistent
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
EPRG_EXE = str(ROOT / "cmake-build-release" / "inspect_EvolPrivRepGame")

def parse_json_stdout(text: str) -> dict:
    """Parse stdout that is expected to be a single JSON object."""
    return json.loads(text)

def run_and_parse(norm_arg: str):
    try:
        res = subprocess.run([EPRG_EXE, norm_arg], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit(f"[ERROR] Executable not found: {EPRG_EXE}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"[ERROR] Execution failed: {EPRG_EXE} {norm_arg}\n{e.stdout}\n{e.stderr}")
    obj = parse_json_stdout(res.stdout)
    eq = obj.get("eq")
    rhos = obj.get("rhos")
    if eq is None or rhos is None:
        sys.exit("[ERROR] Could not find 'eq' and/or 'rhos' in program output.")
    return eq[:3], rhos

def fmt_pct1(x):  return f"{x*100:.1f}%"
def fmt_rho(x):
    if isinstance(x, (int, float)):
        return "<0.001" if x < 1e-3 else f"{x:.3f}"
    return "N/A"

def draw_triad(norm_label: str, eq, rhos, save=False, show=True):
    # --- Node positions ---
    P_L1   = (0.0,  1.0)
    P_ALLD = (-1.20, -0.72)
    P_ALLC = ( 1.20, -0.72)
    R = 0.40

    fig, ax = plt.subplots(figsize=(5.4, 5.0), dpi=150)
    ax.set_aspect('equal')
    ax.set_xlim(-2.05, 2.05)
    ax.set_ylim(-1.80, 1.95)
    ax.axis('off')

    # --- Nodes (circle + % + label) ---
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
    place_node("L1",   P_L1,   "#4f6db8", "#4f6db8", "white", fmt_pct1(eq[0]), "top")
    place_node("ALLD", P_ALLD, gray,       gray,      "black", fmt_pct1(eq[2]), "bottom")
    place_node("ALLC", P_ALLC, "white",    gray,      "black", fmt_pct1(eq[1]), "bottom")

    # --- Curved arrows + labels ---
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
    edge_arrow_with_label(P_L1,   P_ALLD, rhos[2][0], rad=outer_left_rad)
    edge_arrow_with_label(P_ALLD, P_ALLC, rhos[1][2], rad=outer_bottom_rad)
    edge_arrow_with_label(P_ALLC, P_L1,   rhos[0][1], rad=outer_right_rad)

    # Inner 3
    edge_arrow_with_label(P_L1,   P_ALLC, rhos[1][0], rad=inner_right_rad)
    edge_arrow_with_label(P_ALLC, P_ALLD, rhos[2][1], rad=inner_bottom_rad)
    edge_arrow_with_label(P_ALLD, P_L1,   rhos[0][2], rad=inner_left_rad)

    if save:
        outdir = ROOT / "figures"
        outdir.mkdir(exist_ok=True)
        fig.savefig(outdir / f"triad_{norm_label}.png", dpi=150)
    if show:
        plt.show()
    plt.close(fig)

def main():
    norm = sys.argv[1] if len(sys.argv) >= 2 else "L1"
    eq, rhos = run_and_parse(norm)
    draw_triad(norm, eq, rhos, save=False, show=True)

if __name__ == "__main__":
    main()
