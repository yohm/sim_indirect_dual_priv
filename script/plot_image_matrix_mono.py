#!/usr/bin/env python3
#%%
"""
Monomorphic image matrix for a focal norm.

Usage:
  VSCode Interactive: Run cells sequentially, edit parameters in the parameter cell
"""

#%% Imports and setup
import json
import subprocess
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from pathlib import Path
from utils import figure_path, resolve_build_exe

PRG_EXE = resolve_build_exe("inspect_PrivRepGame")


#%% Helper functions for running C++ simulation
def run_cpp_simulation(
    exe: Path,
    focal: str,
    N: int,
    params: dict,
) -> np.ndarray | None:
    """Run C++ executable and parse image.txt output."""
    json_params = json.dumps(params)
    cmd = [exe, "-j", json_params, focal, str(N), "-g"]
    print(f"[INFO] Running command: {' '.join(cmd)}")
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"[INFO] C++ simulation completed for {focal} (N={N})")
        if res.stdout:
            print(res.stdout)
        
        # Read image.txt (created in the current directory where script is run)
        image_path = Path("image.txt").resolve()
        print(f"[INFO] Reading image from: {image_path}")
        if not image_path.exists():
            print(f"[ERROR] image.txt not found at {image_path}", file=sys.stderr)
            return None
        
        with open(image_path, "r") as f:
            lines = [line.rstrip() for line in f if line.strip()]
        
        # Parse image: 'x' = bad (0), '.' = good (1)
        N_actual = len(lines)
        MEnd = np.zeros((N_actual, N_actual), dtype=int)
        for i, line in enumerate(lines):
            for j, ch in enumerate(line):
                if ch == '.':
                    MEnd[i, j] = 1
                elif ch == 'x':
                    MEnd[i, j] = 0
        
        return MEnd
        
    except FileNotFoundError:
        print(f"[ERROR] Executable not found: {exe}", file=sys.stderr)
        print(f"[INFO] Please build the project first:", file=sys.stderr)
        print(f"  cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release", file=sys.stderr)
        print(f"  cmake --build cmake-build-release -j", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Execution failed with return code {e.returncode}", file=sys.stderr)
        print(f"[ERROR] Command: {' '.join(cmd)}", file=sys.stderr)
        return None


#%% Plotting functions
def show_binary_matrix(MEnd: np.ndarray, good_color: str, outpath: Path | None = None, show: bool = True):
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
    "L1": "#4f6db8", "L1-IS": "#4f6db8",
    "L1v": "#4f6db8", "L1v-IS": "#4f6db8",
    "L2": "#b6483a", "L2-IS": "#b6483a",
    "L2v": "#b6483a", "L2v-IS": "#b6483a",
    "L3": "#86a657", "L3-IS": "#86a657",
    "L4": "#6b5fb9", "L4-IS": "#6b5fb9",
    "L5": "#3d95ad", "L5-IS": "#3d95ad",
    "L6": "#d1781c", "L6-IS": "#d1781c",
    "L7": "#8da4ca", "L7-IS": "#8da4ca",
    "L8": "#c47a9b", "L8-IS": "#c47a9b",
}


#%% Simulation parameters
# Edit these parameters as needed
focal_nm = "L3"

# Parameters for C++ simulation
CPP_PARAMS = {
    "t_init": 1000,
    "t_measure": 1000,
    "q": 1.0,
    "mu_impl": 0.02,
    "mu_percept": 0.0,
    "mu_assess1": 0.02,
    "mu_assess2": 0.02,
    "_seed": 12345678,
}

N = 50
save_figure = True
show_figure = True
output_format = "pdf"  # "png", "pdf", or "svg"


def run_one(focal_norm: str) -> None:
    mend = run_cpp_simulation(PRG_EXE, focal_norm, N, CPP_PARAMS)
    if mend is None:
        print(f"[ERROR] Simulation failed for {focal_norm}.")
        return

    outpath = figure_path(f"image_matrix_mono_{focal_norm}_mono.{output_format}") if save_figure else None
    show_binary_matrix(mend, good_color=default_colors[focal_norm], outpath=outpath, show=show_figure)


def run_all() -> None:
    for focal_norm in ["L1", "L1-IS", "L2", "L2-IS",
                       "L3", "L3-IS", "L4", "L4-IS",
                       "L5", "L5-IS", "L6", "L6-IS",
                       "L7", "L7-IS", "L8", "L8-IS"]:
        run_one(focal_norm)


#%% Run simulation and plot (using C++ implementation)
run_one(focal_nm)

# %%
# Run for multiple norms (using C++ implementation)
run_all()

# %%
