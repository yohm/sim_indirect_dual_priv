"""
Usage (from repo root):
  uv venv .venv && source .venv/bin/activate
  uv pip install -r script/requirements.txt

Usage examples:
  # show window
  python script/plot_image_matrix.py --norm L3 --N 50 --ep 0.05 --q 0.9 --nIt 20000 --seed 0
  python script/plot_image_matrix.py --norm L6_IS
  python script/plot_image_matrix.py --norm all

  # multiple norms, save each as figures/image_matrix_<norm>.(png|pdf|svg) without showing windows
  python script/plot_image_matrix.py --norm all --save --format pdf --no-show
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import os
from pathlib import Path

# ---------------- Assessment rules (donor) ----------------
ASSESS_RULES = {
    "L1": "ggggbgbb",
    "L2": "gbggbgbb",
    "L3": "ggggbgbg",
    "L4": "gggbbgbg",
    "L5": "gbggbgbg",
    "L6": "gbgbbgbg",
    "L7": "gggbbgbb",
    "L8": "gbgbbgbb",
}

# ---------------- Action rules ----------------
ACTION_RULES = {
    "L1": "CDCC",
    "L2": "CDCC",
    "L3": "CDCD",
    "L4": "CDCD",
    "L5": "CDCD",
    "L6": "CDCD",
    "L7": "CDCD",
    "L8": "CDCD",
}

def assrule_for_donor(norm: str) -> np.ndarray:
    """Build donor assessment array sO[0..7] from the 8-row table for a base norm."""
    raw = ASSESS_RULES[norm]
    if len(raw) != 8 or any(ch not in "gb" for ch in raw):
        raise ValueError(f"{norm}: assessment rule must be 8 chars 'g'/'b'. Got: {raw}")
    sO = np.zeros(8, dtype=int)
    # map rows to (cp, stD_bad, stR_bad):
    cases = [
        (1, 0, 0),  # row1
        (1, 0, 1),  # row2
        (1, 1, 0),  # row3
        (1, 1, 1),  # row4
        (0, 0, 0),  # row5
        (0, 0, 1),  # row6
        (0, 1, 0),  # row7
        (0, 1, 1),  # row8
    ]
    for idx, (cp, stD_bad, stR_bad) in enumerate(cases):
        iAs = 4*(cp == 0) + 2*(stD_bad == 1) + 1*(stR_bad == 1)
        sO[iAs] = 1 if raw[idx] == "g" else 0
    return sO

def actrule_from_table(norm: str) -> np.ndarray:
    """Convert 4-char 'C'/'D' action rule to length-4 cooperation probabilities."""
    seq = ACTION_RULES[norm]
    if len(seq) != 4 or any(ch not in "CD" for ch in seq):
        raise ValueError(f"{norm}: action rule must be 4 chars 'C'/'D'. Got: {seq}")
    return np.array([1.0 if ch == "C" else 0.0 for ch in seq], dtype=float)

# ---------------- Simulation ----------------
def simulate_MEnd(norm: str, N=50, ep=0.05, q=0.9, nIt=20000, seed=0, recipient_error=True) -> np.ndarray:
    """
    Return final individual image matrix MEnd (observer × target), values in {0,1}.
    norm ∈ {'L1','L1_IS','L2','L2_IS','L3','L3_IS','L4','L4_IS','L5','L5_IS','L6','L6_IS','L7','L7_IS','L8','L8_IS'}.
    Suffix *_IS: observers also update the RECIPIENT: C→good, D→bad
                 (if recipient_error=True, apply the same perception error ep to that update).
    """
    base = norm.split("_")[0]
    sO = assrule_for_donor(base)
    aD = actrule_from_table(base)

    rng = np.random.default_rng(seed)
    rand = rng.random
    randint = lambda lo, hi: int(rng.integers(lo, hi+1))

    # MC[row=observer, col=target] in {1=good, 0=bad}
    MC = np.ones((N, N), dtype=int)

    for _ in range(1, nIt+1):
        # pick donor & recipient (distinct)
        Do = randint(0, N-1)
        Re = Do
        while Re == Do:
            Re = randint(0, N-1)

        # donor's view -> action
        stD = MC[Do, Do]
        stR = MC[Do, Re]
        iA  = (2 if stD == 0 else 0) + (1 if stR == 0 else 0)
        cp  = 1 if rand() < aD[iA] else 0  # 1=cooperate, 0=defect

        # observers update
        for Obs in range(N):
            if (Obs == Do) or (Obs == Re) or (rand() < q):
                stD_obs = MC[Obs, Do]
                stR_obs = MC[Obs, Re]

                # donor image update with perception error
                if rand() <= 1 - ep:
                    iAs = 4*(cp == 0) + 2*(stD_obs == 0) + 1*(stR_obs == 0)
                else:
                    iAs = 4*(cp == 1) + 2*(stD_obs == 0) + 1*(stR_obs == 0)
                MC[Obs, Do] = int(sO[iAs])

                # recipient image update for *_IS variants
                if norm.upper().endswith("_IS"):
                    if recipient_error:
                        cp_eff = cp if (rand() <= 1 - ep) else (1 - cp)
                    else:
                        cp_eff = cp
                    MC[Obs, Re] = 1 if cp_eff == 1 else 0

    return MC

# ---------------- Plotting ----------------
def show_binary_matrix(MEnd: np.ndarray, title: str, good_color: str,
                       outpath: Path | None = None, show: bool = True):
    # 0 -> white (bad), 1 -> good_color (good)
    cmap = ListedColormap(["white", good_color])
    norm = BoundaryNorm([-0.5, 0.5, 1.5], 2)
    fig, ax = plt.subplots(figsize=(4.0, 4.0))
    ax.imshow(MEnd, cmap=cmap, norm=norm, interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_linewidth(3); s.set_color("black")
    ax.set_title(title)
    fig.tight_layout()

    if outpath is not None:
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(outpath)
        print(f"Saved: {outpath}")

    if show:
        plt.show()
    plt.close(fig)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--norm", choices=[
        "L1","L1_IS","L2","L2_IS","L3","L3_IS","L4","L4_IS","L5","L5_IS","L6","L6_IS","L7","L7_IS","L8","L8_IS","all"
    ], default="L1")
    ap.add_argument("--N", type=int, default=50, help="Population size (matrix will be N×N)")
    ap.add_argument("--ep", type=float, default=0.05, help="Perception error rate (0..1)")
    ap.add_argument("--q", type=float, default=0.9, help="Third-party observation probability (0..1)")
    ap.add_argument("--nIt", type=int, default=20000, help="Number of simulated interactions")
    ap.add_argument("--seed", type=int, default=0, help="RNG seed for reproducibility")
    ap.add_argument("--recipient_no_error", action="store_true",
                    help="Do NOT apply perception error ep to recipient updates in *_IS norms")
    ap.add_argument("--good_color", type=str, default=None,
                    help="Hex color for 'good' cells (overrides defaults)")
    ap.add_argument("--save", action="store_true",
                    help="Save to figures/image_matrix_<norm>.<format> unless --out is given.")
    ap.add_argument("--format", choices=["png", "pdf", "svg"], default="png",
                    help="Output format when saving without --out (default: png)")
    ap.add_argument("--no-show", action="store_true", help="Do not open a window.")
    ap.add_argument("--out", type=str, default=None,
                    help="Explicit output path (used only when a single norm is plotted).")
    args = ap.parse_args()

    # Default palette
    default_colors = {
        "L1": "#4f6db8", "L1_IS": "#4f6db8",
        "L2": "#b6483a", "L2_IS": "#b6483a",
        "L3": "#86a657", "L3_IS": "#86a657",
        "L4": "#6b5fb9", "L4_IS": "#6b5fb9",
        "L5": "#3d95ad", "L5_IS": "#3d95ad",
        "L6": "#d1781c", "L6_IS": "#d1781c",
        "L7": "#8da4ca", "L7_IS": "#8da4ca",
        "L8": "#c47a9b", "L8_IS": "#c47a9b",
    }

    def _default_out(nm: str) -> str:
        return f"figures/image_matrix_{nm}.{args.format}"

    if args.norm != "all":
        MEnd = simulate_MEnd(
            norm=args.norm, N=args.N, ep=args.ep, q=args.q, nIt=args.nIt, seed=args.seed,
            recipient_error=not args.recipient_no_error
        )
        color = args.good_color or default_colors[args.norm]
        print(f"{args.norm}  MEnd shape={MEnd.shape}, good-ratio={MEnd.mean():.3f}")

        outpath = None
        if args.out:
            outpath = args.out
        elif args.save:
            Path("figures").mkdir(exist_ok=True)
            outpath = _default_out(args.norm)

        show_binary_matrix(MEnd, title=args.norm, good_color=color,
                           outpath=outpath, show=(not args.no_show))
    else:
        order = ["L1","L1_IS","L2","L2_IS","L3","L3_IS","L4","L4_IS","L5","L5_IS","L6","L6_IS","L7","L7_IS","L8","L8_IS"]
        for nm in order:
            MEnd = simulate_MEnd(
                norm=nm, N=args.N, ep=args.ep, q=args.q, nIt=args.nIt, seed=args.seed,
                recipient_error=not args.recipient_no_error
            )
            color = args.good_color or default_colors[nm]
            print(f"{nm}  MEnd shape={MEnd.shape}, good-ratio={MEnd.mean():.3f}")

            outpath = None
            if args.save:
                Path("figures").mkdir(exist_ok=True)
                outpath = _default_out(nm)

            show_binary_matrix(MEnd, title=nm, good_color=color,
                               outpath=outpath, show=(not args.no_show))
