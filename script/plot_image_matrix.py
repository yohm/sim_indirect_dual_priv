"""
3-strategy image matrix (focal + ALLC + ALLD), each with 30 players (default).

Usage (from repo root):
  uv venv .venv && source .venv/bin/activate
  uv pip install -r script/requirements.txt

Examples:
  python script/plot_image_matrix.py --focal L3
  python script/plot_image_matrix.py --focal all --mu-assess1 0.01 --mu-assess2 0.01 --mu-impl 0.00 --mu-percept 0.00
  python script/plot_image_matrix.py --focal all --mu-assess1 0.01 --mu-assess2 0.01 --mu-impl 0.00 --mu-percept 0.00 --save --no-show --format pdf
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from pathlib import Path


# ---------------- Assessment rules (donor) ----------------
ASSESS_RULES = {
    "L1": "ggggbgbb",
    "L1v": "ggggbgbb",
    "L2": "gbggbgbb",
    "L2v": "gbggbgbb",
    "L3": "ggggbgbg",
    "L4": "gggbbgbg",
    "L5": "gbggbgbg",
    "L6": "gbgbbgbg",
    "L7": "gggbbgbb",
    "L8": "gbgbbgbb",
    "ALLC": "gggggggg",
    "ALLD": "bbbbbbbb",
}

# ---------------- Action rules ----------------
ACTION_RULES = {
    "L1": "CDCC",
    "L1v": "CDCD",
    "L2": "CDCC",
    "L2v": "CDCD",
    "L3": "CDCD",
    "L4": "CDCD",
    "L5": "CDCD",
    "L6": "CDCD",
    "L7": "CDCD",
    "L8": "CDCD",
    "ALLC": "CCCC",
    "ALLD": "DDDD",
}

FOCAL_ORDER = [
    "L1","L1_IS","L1v","L1v_IS",
    "L2","L2_IS","L2v","L2v_IS",
    "L3","L3_IS","L4","L4_IS",
    "L5","L5_IS","L6","L6_IS",
    "L7","L7_IS","L8","L8_IS",
]

def assrule_for_donor(norm: str) -> np.ndarray:
    raw = ASSESS_RULES[norm]
    if len(raw) != 8 or any(ch not in "gb" for ch in raw):
        raise ValueError(f"{norm}: assessment rule must be 8 chars 'g'/'b'. Got: {raw}")
    sO = np.zeros(8, dtype=int)
    cases = [
        (1, 0, 0),(1, 0, 1),(1, 1, 0),(1, 1, 1),
        (0, 0, 0),(0, 0, 1),(0, 1, 0),(0, 1, 1),
    ]
    for idx, (cp, stD_bad, stR_bad) in enumerate(cases):
        iAs = 4*(cp == 0) + 2*(stD_bad == 1) + 1*(stR_bad == 1)
        sO[iAs] = 1 if raw[idx] == "g" else 0
    return sO

def actrule_from_table(norm: str) -> np.ndarray:
    seq = ACTION_RULES[norm]
    if len(seq) != 4 or any(ch not in "CD" for ch in seq):
        raise ValueError(f"{norm}: action rule must be 4 chars 'C'/'D'. Got: {seq}")
    return np.array([1.0 if ch == "C" else 0.0 for ch in seq], dtype=float)

# ---------------- Mixed-population simulation (focal + ALLC + ALLD) ----------------
def simulate_three_group_MEnd(
    focal: str,
    block_size: int = 30,
    mu_percept: float = 0.05,  # perception error (observer misperceives action)
    q: float = 0.9,
    nIt: int = 20000,
    seed: int = 0,
    recipient_error: bool = True,
    mu_assess1: float = 0.05,  # assessment error 1 (flip assigned reputation)
    mu_assess2: float = 0.0,   # assessment error 2 (independent extra flip)
    mu_impl: float = 0.0,      # implementation error (donor flips intended act)
) -> np.ndarray:

    strategies = [focal, "ALLC", "ALLD"]
    pop_comp   = [block_size, block_size, block_size]
    N = 3 * block_size

    rng = np.random.default_rng(seed)
    rand = rng.random
    randint = lambda lo, hi: int(rng.integers(lo, hi+1))

    def _base_name(s: str) -> str:
        return s.split("_")[0]

    ass_rules = [assrule_for_donor(_base_name(s)) for s in strategies]
    act_rules = [actrule_from_table(_base_name(s)) for s in strategies]
    obs_updates_recipient = [s.upper().endswith("_IS") for s in strategies]

    xP = np.concatenate([np.full(c, i, dtype=int) for i, c in enumerate(pop_comp)])
    MC = np.ones((N, N), dtype=int)

    for _ in range(1, nIt+1):
        Do = randint(0, N-1)
        Re = Do
        while Re == Do:
            Re = randint(0, N-1)

        # donor intention → action
        aD = act_rules[xP[Do]]
        stD = MC[Do, Do]
        stR = MC[Do, Re]
        iA  = (2 if stD == 0 else 0) + (1 if stR == 0 else 0)
        cp_intended = 1 if rand() < aD[iA] else 0  # 1=C, 0=D

        cp = cp_intended
        if rand() < mu_impl:  # implementation error
            cp = 1 - cp

        # observers
        for Obs in range(N):
            if (Obs == Do) or (Obs == Re) or (rand() < q):
                sO = ass_rules[xP[Obs]]
                stD_obs = MC[Obs, Do]
                stR_obs = MC[Obs, Re]

                # perception error on action
                cp_seen = cp if (rand() > mu_percept) else (1 - cp)

                # donor assessment
                iAs = 4*(cp_seen == 0) + 2*(stD_obs == 0) + 1*(stR_obs == 0)
                val = int(sO[iAs])

                # assessment errors
                if rand() < mu_assess1: val = 1 - val
                if rand() < mu_assess2: val = 1 - val
                MC[Obs, Do] = val

                # recipient update for *_IS observers
                if obs_updates_recipient[xP[Obs]]:
                    if recipient_error:
                        cp_seen_rec = cp if (rand() > mu_percept) else (1 - cp)
                        val_r = 1 if cp_seen_rec == 1 else 0
                        if rand() < mu_assess1: val_r = 1 - val_r
                        if rand() < mu_assess2: val_r = 1 - val_r
                        MC[Obs, Re] = val_r
                    else:
                        MC[Obs, Re] = 1 if cp == 1 else 0

    return MC

# ---------------- Plotting ----------------
def _focal_label(name: str) -> str:
    return name.replace("_IS", "-IS")

def show_binary_matrix_with_blocks_and_labels(
    MEnd: np.ndarray,
    focal_name: str,
    good_color: str,
    block_size: int,
    outpath: Path | None = None,
    show: bool = True,
):
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap(["white", good_color])
    norm = BoundaryNorm([-0.5, 0.5, 1.5], 2)

    fig, ax = plt.subplots(figsize=(5.4, 5.4))
    ax.imshow(MEnd, cmap=cmap, norm=norm, interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([])

    for s in ax.spines.values():
        s.set_linewidth(3); s.set_color("black")

    N = MEnd.shape[0]
    for k in range(1, N // block_size):
        ax.axhline(k * block_size - 0.5, linestyle="--", linewidth=2.0, color="black")
        ax.axvline(k * block_size - 0.5, linestyle="--", linewidth=2.0, color="black")

    # external labels
    x_fracs = [1/6, 1/2, 5/6]
    y_fracs_left = [5/6, 1/2, 1/6]
    col_labels = [_focal_label(focal_name), "ALLC", "ALLD"]
    row_labels = [_focal_label(focal_name), "ALLC", "ALLD"]

    fig.subplots_adjust(top=0.88, left=0.22, right=0.98, bottom=0.06)

    for x in range(3):
        ax.text(x_fracs[x], 1.03, col_labels[x],
                transform=ax.transAxes, ha="center", va="bottom",
                fontsize=12, fontweight="bold", clip_on=False)
    for y in range(3):
        ax.text(-0.06, y_fracs_left[y], row_labels[y],
                transform=ax.transAxes, ha="right", va="center",
                fontsize=12, fontweight="bold", rotation=90, clip_on=False)

    if outpath is not None:
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(outpath, bbox_inches="tight")
        print(f"Saved: {outpath}")

    if show:
        plt.show()
    plt.close(fig)

# ---------------- CLI ----------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="3-strategy image matrix: focal + ALLC + ALLD, each block_size players."
    )
    ap.add_argument("--focal", choices=["all"] + FOCAL_ORDER, default="L3",
                    help="Focal strategy (or 'all' to run all focal norms). "
                         "Row/col block order is [focal, ALLC, ALLD].")
    ap.add_argument("--block", type=int, default=30, help="Players per strategy (default: 30)")
    # perception error を一本化
    ap.add_argument("--mu-percept", type=float, default=0.05, help="perception error rate (0..1)")
    # その他の誤り
    ap.add_argument("--mu-assess1", type=float, default=0.05, help="assessment error 1 (0..1)")
    ap.add_argument("--mu-assess2", type=float, default=0.0, help="assessment error 2 (0..1)")
    ap.add_argument("--mu-impl", type=float, default=0.0, help="implementation error (0..1)")
    # 観察確率など
    ap.add_argument("--q", type=float, default=0.9, help="Third-party observation probability (0..1)")
    ap.add_argument("--nIt", type=int, default=20000, help="Number of simulated interactions")
    ap.add_argument("--seed", type=int, default=0, help="RNG seed for reproducibility")
    ap.add_argument("--recipient_no_error", action="store_true",
                    help="Do NOT apply errors to recipient updates in *_IS observers.")
    ap.add_argument("--good_color", type=str, default=None,
                    help="Hex color for 'good' cells (overrides defaults)")
    ap.add_argument("--save", action="store_true",
                    help="Save to figures/image_matrix_<tag>.<format> unless --out is given.")
    ap.add_argument("--format", choices=["png", "pdf", "svg"], default="png",
                    help="Output format when saving without --out")
    ap.add_argument("--no-show", action="store_true", help="Do not open a window.")
    ap.add_argument("--out", type=str, default=None,
                    help="Explicit output path (single run only).")

    args = ap.parse_args()

    default_colors = {
        "L1": "#4f6db8", "L1_IS": "#4f6db8",
        "L1v": "#4f6db8", "L1v_IS": "#4f6db8",
        "L2": "#b6483a", "L2_IS": "#b6483a",
        "L2v": "#b6483a", "L2v_IS": "#b6483a",
        "L3": "#86a657", "L3_IS": "#86a657",
        "L4": "#6b5fb9", "L4_IS": "#6b5fb9",
        "L5": "#3d95ad", "L5_IS": "#3d95ad",
        "L6": "#d1781c", "L6_IS": "#d1781c",
        "L7": "#8da4ca", "L7_IS": "#8da4ca",
        "L8": "#c47a9b", "L8_IS": "#c47a9b",
    }

    def run_one(focal_nm: str):
        MEnd = simulate_three_group_MEnd(
            focal=focal_nm,
            block_size=args.block,
            mu_percept=args.mu_percept,
            q=args.q,
            nIt=args.nIt,
            seed=args.seed,
            recipient_error=not args.recipient_no_error,
            mu_assess1=args.mu_assess1,
            mu_assess2=args.mu_assess2,
            mu_impl=args.mu_impl,
        )
        color = args.good_color or default_colors[focal_nm]
        tag = f"{focal_nm}_ALLC_ALLD_{args.block}x3"

        outpath = None
        if args.out:
            outpath = args.out  # only when a single focal is run
        elif args.save:
            Path("figures").mkdir(exist_ok=True)
            outpath = Path(f"figures/image_matrix_{tag}.{args.format}")

        print(f"{tag}  MEnd shape={MEnd.shape}, good-ratio={MEnd.mean():.3f}")
        print("Block order (rows/cols): [focal, ALLC, ALLD]")
        print(f"params: mu_percept={args.mu_percept}, mu_assess1={args.mu_assess1}, mu_assess2={args.mu_assess2}, mu_impl={args.mu_impl}, q={args.q}")

        show_binary_matrix_with_blocks_and_labels(
            MEnd,
            focal_name=focal_nm,
            good_color=color,
            block_size=args.block,
            outpath=outpath,
            show=(not args.no_show),
        )

    if args.focal == "all":
        if args.out:
            raise ValueError("--out cannot be used with --focal all")
        for nm in FOCAL_ORDER:
            run_one(nm)
    else:
        run_one(args.focal)