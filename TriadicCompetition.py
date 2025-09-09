"""
Under construction! 
The layout of figure is not perfect.
Unable to proeperly create figures for norms other than L1.

Usage:
  cd ~/sim_indirect_dual_priv
  source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install matplotlib
  python TriadicCompetition.py L1
  python TriadicCompetition.py '1.00 0.00 1.00 1.00 1.00 0.00 1.00 1.00 1.00 0.00 1.00 0.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00'
"""

import subprocess, sys, json, os
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

# ---- 実行ファイルパス（このスクリプトの場所から相対で解決） ----
ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)  # 念のため作業ディレクトリ固定
EPRG_EXE = str(ROOT / "cmake-build-release" / "inspect_EvolPrivRepGame")

# --- robust JSON block iterator (handles nested {}) ---
def iter_json_blocks(text: str):
    start = None; depth = 0; in_str = False; esc = False
    for i, ch in enumerate(text):
        if ch == '"' and not esc:
            in_str = not in_str
        esc = (ch == '\\' and not esc) if in_str else False
        if in_str:
            continue
        if ch == '{':
            if depth == 0: start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    chunk = text[start:i+1]
                    try:
                        yield json.loads(chunk)
                    except json.JSONDecodeError:
                        pass
                    start = None

def run_and_parse(norm_arg: str):
    try:
        res = subprocess.run([EPRG_EXE, norm_arg], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit(f"[ERROR] Executable not found: {EPRG_EXE}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"[ERROR] Execution failed: {EPRG_EXE} {norm_arg}\n{e.stdout}\n{e.stderr}")
    eq = rhos = None
    for obj in iter_json_blocks(res.stdout):
        if eq is None and isinstance(obj.get("eq"), list) and len(obj["eq"]) >= 3:
            eq = obj["eq"][:3]
        if rhos is None and isinstance(obj.get("rhos"), list) and len(obj["rhos"]) == 3:
            rhos = obj["rhos"]
    if eq is None or rhos is None:
        sys.exit("[ERROR] Could not find 'eq' and/or 'rhos' in program output.")
    return eq, rhos

def fmt_pct1(x):  return f"{x*100:.1f}%"
def fmt_rho(x):
    if isinstance(x, (int, float)):
        return "<0.001" if x < 1e-3 else f"{x:.3f}"
    return "N/A"

def draw_triad(norm_label: str, eq, rhos, save=False, show=True):
    # --- ノード配置 ---
    P_L1   = (0.0,  1.0)      # 上
    P_ALLD = (-1.20, -0.72)   # 左下（← ALLD を左へ）
    P_ALLC = ( 1.20, -0.72)   # 右下（← ALLC を右へ）
    R = 0.40

    fig, ax = plt.subplots(figsize=(5.4, 5.0), dpi=150)
    ax.set_aspect('equal')
    ax.set_xlim(-2.05, 2.05)
    ax.set_ylim(-1.80, 1.95)
    ax.axis('off')

    # --- ノード（円・%・ラベル） ---
    def place_node(name, xy, face, edge, text_color, percent_text, where):
        x, y = xy
        ax.add_patch(Circle((x, y), R, facecolor=face, edgecolor=edge,
                            linewidth=1.8, zorder=3, clip_on=False))
        ax.text(x, y, percent_text, ha="center", va="center", color=text_color,
                fontsize=13, fontweight="bold", zorder=4)
        # ラベルは円の外側に大きめオフセット
        gap_top = 0.15
        gap_bot = 0.15
        if where == "top":
            ax.text(x, y + R + gap_top, name, ha="center", va="bottom",
                    fontsize=13, color="black", zorder=4)
        else:  # "bottom"
            ax.text(x, y - R - gap_bot, name, ha="center", va="top",
                    fontsize=13, color="black", zorder=4)

    # 色指定：L1 = #4f6db8（縁も塗りも同色）／ ALLD = グレー塗り＋縁グレー ／ ALLC = 白塗り＋縁グレー
    gray = "#bdbdbd"
    place_node("L1",   P_L1,   "#4f6db8", "#4f6db8", "white", fmt_pct1(eq[0]), "top")
    place_node("ALLD", P_ALLD, gray,       gray,      "black", fmt_pct1(eq[2]), "bottom")  # eq[2] = ALLD
    place_node("ALLC", P_ALLC, "white",    gray,      "black", fmt_pct1(eq[1]), "bottom")  # eq[1] = ALLC

    # --- 曲線矢印＋ラベル ---
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

    # ===== 6本の矢印 =====
    # 外側（時計回り）: L1→ALLD（左辺外）、ALLD→ALLC（下辺外）、ALLC→L1（右辺外）
    # 内側（反時計回り）: L1→ALLC（右辺内）、ALLC→ALLD（下辺内）、ALLD→L1（左辺内）
    outer_left_rad   = -0.30
    outer_bottom_rad = -0.18
    outer_right_rad  = -0.30
    inner_right_rad  = -0.24
    inner_bottom_rad = -0.18
    inner_left_rad   = -0.24

    # 外側3本
    edge_arrow_with_label(P_L1,   P_ALLD, rhos[2][0], rad=outer_left_rad)    # L1 <- ALLD
    edge_arrow_with_label(P_ALLD, P_ALLC, rhos[1][2], rad=outer_bottom_rad)  # ALLD <- ALLC
    edge_arrow_with_label(P_ALLC, P_L1,   rhos[0][1], rad=outer_right_rad)   # ALLC <- L1

    # 内側3本
    edge_arrow_with_label(P_L1,   P_ALLC, rhos[1][0], rad=inner_right_rad)   # L1 <- ALLC
    edge_arrow_with_label(P_ALLC, P_ALLD, rhos[2][1], rad=inner_bottom_rad)  # ALLC <- ALLD
    edge_arrow_with_label(P_ALLD, P_L1,   rhos[0][2], rad=inner_left_rad)    # ALLD <- L1

    if save:
        outdir = Path(__file__).resolve().parent / "figures"
        outdir.mkdir(exist_ok=True)
        fig.savefig(outdir / f"triad_{norm_label}.png", dpi=150)
    if show:
        plt.show()
    plt.close(fig)

def main():
    norm = sys.argv[1] if len(sys.argv) >= 2 else "L1"
    eq, rhos = run_and_parse(norm)
    draw_triad(norm, eq, rhos, save=False, show=True)  # 表示のみ

if __name__ == "__main__":
    main()
