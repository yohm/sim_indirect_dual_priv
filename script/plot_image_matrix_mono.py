#!/usr/bin/env python3
#%%
"""
Monomorphic image matrix for a focal norm.

Usage:
  VSCode Interactive: Run cells sequentially, edit parameters in the parameter cell
"""

#%% Imports and setup
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from pathlib import Path


#%% Assessment and action rules
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


#%% Helper functions for rules
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


#%% Monomorphic simulation
def simulate_monomorphic_MEnd(
    focal: str,
    N: int,
    mu_percept: float,
    q: float,
    nIt: int,
    seed: int,
    recipient_error: bool,
    mu_assess1: float,
    mu_assess2: float,
    mu_impl: float,
) -> np.ndarray:

    rng = np.random.default_rng(seed)
    rand = rng.random
    randint = lambda lo, hi: int(rng.integers(lo, hi+1))

    def _base_name(s: str) -> str:
        return s.split("_")[0]

    ass_rule = assrule_for_donor(_base_name(focal))
    act_rule = actrule_from_table(_base_name(focal))
    updates_recipient = focal.upper().endswith("_IS")

    MC = np.ones((N, N), dtype=int)

    for _ in range(1, nIt+1):
        Do = randint(0, N-1)
        Re = Do
        while Re == Do:
            Re = randint(0, N-1)

        stD = MC[Do, Do]
        stR = MC[Do, Re]
        iA = (2 if stD == 0 else 0) + (1 if stR == 0 else 0)
        cp_intended = 1 if rand() < act_rule[iA] else 0

        cp = cp_intended
        if rand() < mu_impl:
            cp = 1 - cp

        for Obs in range(N):
            if (Obs == Do) or (Obs == Re) or (rand() < q):
                stD_obs = MC[Obs, Do]
                stR_obs = MC[Obs, Re]

                cp_seen = cp if (rand() > mu_percept) else (1 - cp)

                iAs = 4*(cp_seen == 0) + 2*(stD_obs == 0) + 1*(stR_obs == 0)
                val = int(ass_rule[iAs])

                if rand() < mu_assess1: val = 1 - val
                if rand() < mu_assess2: val = 1 - val
                MC[Obs, Do] = val

                if updates_recipient:
                    if recipient_error:
                        cp_seen_rec = cp if (rand() > mu_percept) else (1 - cp)
                        val_r = 1 if cp_seen_rec == 1 else 0
                        if rand() < mu_assess1: val_r = 1 - val_r
                        if rand() < mu_assess2: val_r = 1 - val_r
                        MC[Obs, Re] = val_r
                    else:
                        MC[Obs, Re] = 1 if cp == 1 else 0

    return MC


#%% Plotting functions
def _focal_label(name: str) -> str:
    return name.replace("_IS", "-IS")


def show_binary_matrix(
    MEnd: np.ndarray,
    focal_name: str,
    good_color: str,
    outpath: Path | None = None,
    show: bool = True,
):
    cmap = ListedColormap(["white", good_color])
    norm = BoundaryNorm([-0.5, 0.5, 1.5], 2)

    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.imshow(MEnd, cmap=cmap, norm=norm, interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([])

    for s in ax.spines.values():
        s.set_linewidth(3); s.set_color("black")

    fig.subplots_adjust(top=0.95, left=0.06, right=0.98, bottom=0.06)

    if outpath is not None:
        outpath = Path(outpath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(outpath, bbox_inches="tight")
        print(f"Saved: {outpath}")

    if show:
        plt.show()
    plt.close(fig)


#%% Default colors for each norm
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


#%% Simulation parameters
# Edit these parameters as needed
focal_nm = "L3"  # or "L3_IS", "L5", etc.

PARAMS = {
    "N": 50,
    "mu_percept": 0.0,
    "mu_assess1": 0.02,
    "mu_assess2": 0.02,
    "mu_impl": 0.02,
    "q": 1.0,
    "nIt": 20000,
    "seed": 0,
    "recipient_error": True,
}

save_figure = True
show_figure = True
output_format = "pdf"  # "png", "pdf", or "svg"


#%% Run simulation and plot
MEnd = simulate_monomorphic_MEnd(focal=focal_nm, **PARAMS)

color = default_colors[focal_nm]
tag = f"{focal_nm}_mono"

outpath = None
if save_figure:
    Path("figures").mkdir(exist_ok=True)
    outpath = Path(f"figures/image_matrix_mono_{tag}.{output_format}")

print(f"{tag}  MEnd shape={MEnd.shape}, good-ratio={MEnd.mean():.3f}")
print(f"params: mu_percept={PARAMS['mu_percept']}, mu_assess1={PARAMS['mu_assess1']}, mu_assess2={PARAMS['mu_assess2']}, mu_impl={PARAMS['mu_impl']}, q={PARAMS['q']}")

show_binary_matrix(
    MEnd,
    focal_name=focal_nm,
    good_color=color,
    outpath=outpath,
    show=show_figure,
)


# %%
# Run for multiple norms
for focal_nm in ["L3", "L3_IS", "L5", "L5_IS"]:
    MEnd = simulate_monomorphic_MEnd(focal=focal_nm, **PARAMS)
    
    color = default_colors[focal_nm]
    tag = f"{focal_nm}_mono"
    
    outpath = None
    if save_figure:
        Path("figures").mkdir(exist_ok=True)
        outpath = Path(f"figures/image_matrix_mono_{tag}.{output_format}")
    
    print(f"{tag}  MEnd shape={MEnd.shape}, good-ratio={MEnd.mean():.3f}")
    
    show_binary_matrix(
        MEnd,
        focal_name=focal_nm,
        good_color=color,
        outpath=outpath,
        show=show_figure,
    )

# %%
