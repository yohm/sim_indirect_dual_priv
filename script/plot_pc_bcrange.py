#!/usr/bin/env python3
#%%
"""
Run simulations on the fly and create individual plots comparing two norms.

Creates two separate plots:
  1) Bar chart of self cooperation level
  2) Vertical range bars [bc_min, bc_max]

Usage:
  VSCode Interactive: Run cells sequentially, edit parameters in cell 4
"""

#%% Imports and setup
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt

# Resolve repo root and executables
ROOT = Path(__file__).resolve().parents[1]
PRG_EXE = str(ROOT / "cmake-build-release" / "inspect_PrivRepGame")


#%% Helper functions for running simulations
def run_simulation(exe: str, args: list[str]) -> Optional[dict]:
    """Run C++ executable and return parsed JSON output."""
    try:
        res = subprocess.run([exe] + args, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except FileNotFoundError:
        print(f"[ERROR] Executable not found: {exe}", file=sys.stderr)
        print(f"[INFO] Please build the project first:", file=sys.stderr)
        print(f"  cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release", file=sys.stderr)
        print(f"  cmake --build cmake-build-release -j", file=sys.stderr)
        return None
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Execution failed: {exe} {args}", file=sys.stderr)
        print(f"{e.stdout}\n{e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON output: {e}", file=sys.stderr)
        return None


def get_self_cooperation(norm: str, params: dict, N: int) -> Optional[float]:
    """Get self cooperation level for a monomorphic population."""
    print(f"[INFO] Running simulation for {norm} monomorphic population (N={N})...")
    json_params = json.dumps(params)
    result = run_simulation(PRG_EXE, ["-j", json_params, norm, str(N)])
    if result:
        return result.get("SystemWideCooperationLevel")
    return None


def get_bc_range(norm: str, params: dict, N: int, mutant_size: int = 1) -> Tuple[Optional[float], Optional[float]]:
    """Get b/c range where norm is stable against both AllD and AllC mutant invasions."""
    resident_size = N - mutant_size
    json_params = json.dumps(params)

    # Invasion vs AllD (lower bound)
    print(f"[INFO] Running invasion analysis for {norm} vs AllD (N={resident_size}+{mutant_size})...")
    print(f"[INFO] command: {PRG_EXE} -j '{json_params}' {norm} {resident_size} AllD {mutant_size}")
    result_alld = run_simulation(PRG_EXE, ["-j", json_params, norm, str(resident_size), "AllD", str(mutant_size)])
    bc_min_alld = None
    bc_max_alld = None
    if result_alld:
        invasion = result_alld.get("Invasion", {})
        bc_min_alld = invasion.get("bc_min")
        bc_max_alld = invasion.get("bc_max")

    # Invasion vs AllC (upper bound)
    print(f"[INFO] Running invasion analysis for {norm} vs AllC (N={resident_size}+{mutant_size})...")
    print(f"[INFO] command: {PRG_EXE} -j '{json_params}' {norm} {resident_size} AllC {mutant_size}")
    result_allc = run_simulation(PRG_EXE, ["-j", json_params, norm, str(resident_size), "AllC", str(mutant_size)])
    bc_min_allc = None
    bc_max_allc = None
    if result_allc:
        invasion = result_allc.get("Invasion", {})
        bc_min_allc = invasion.get("bc_min")
        bc_max_allc = invasion.get("bc_max")

    # Combine results: use AllD bc_min (lower limit) and AllC bc_max (upper limit)
    bc_min = bc_min_alld
    bc_max = bc_max_allc

    return bc_min, bc_max


#%% Plotting functions
def _style_axes(ax, remove_top_right=True):
    """Style axes for cleaner appearance."""
    if remove_top_right:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    ax.tick_params(axis='y', labelsize=16)
    ax.tick_params(axis='x', labelsize=24)


def plot_cooperation_level(norm1: str, norm2: str,
                           val1: Optional[float], val2: Optional[float],
                           colors=("tab:purple", "tab:orange")):
    """Create individual plot for self cooperation level comparison."""
    fig, ax = plt.subplots(figsize=(6, 5))

    xs = [0, 1]
    ys = [val1 if val1 is not None else 0.0,
          val2 if val2 is not None else 0.0]

    bar_width = 0.6
    ax.bar(xs, ys, width=bar_width, color=colors, alpha=0.9)
    
    # Display values on top of bars (2 decimal places)
    for x, y in zip(xs, ys):
        ax.text(x, y, f'{y:.2f}', ha='center', va='bottom', fontsize=16)
    
    ax.set_xticks(xs)
    ax.set_xticklabels([norm1, norm2])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("self cooperation level", fontsize=24)

    _style_axes(ax)
    fig.subplots_adjust(left=0.18, right=0.97, top=0.97, bottom=0.13)
    return fig, ax

def plot_bc_range(norm1: str, norm2: str,
                  range1: Tuple[Optional[float], Optional[float]],
                  range2: Tuple[Optional[float], Optional[float]],
                  colors=("tab:purple", "tab:orange")):
    """Create individual plot for b/c range comparison."""
    fig, ax = plt.subplots(figsize=(6, 5))

    xs = [0, 1]
    bottoms = []
    tops = []

    for bc in (range1, range2):
        y0, y1 = bc
        y0p = 100.0 if y0 is None else max(1.0, y0)  # treat None as infinite
        y1p = 100.0 if y1 is None else min(4.0, y1)
        bottoms.append(y0p)
        tops.append(y1p)

    bar_width = 0.6
    for x, orig_bc, y0p, y1p, c in zip(xs, (range1, range2), bottoms, tops, colors):
        if y1p >= y0p:
            ax.bar(x, y1p - y0p, bottom=y0p, width=bar_width,
                  color=c, alpha=0.9, align='center', edgecolor='none')
            # Add boundary markers
            ax.scatter([x], [y0p], s=24, color=c, edgecolors='white', zorder=3)
            _, y1_orig = orig_bc
            if y1_orig is not None and y1_orig <= 4.0:
                ax.scatter([x], [y1p], s=24, color=c, edgecolors='white', zorder=3)

    ax.set_xticks(xs)
    ax.set_xticklabels([norm1, norm2])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(1.0, 4.0)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_ylabel("$b/c$", fontsize=24)
    # ax.set_title(f"Stable b/c Range: {norm1} vs {norm2}", fontsize=16)

    _style_axes(ax)
    fig.subplots_adjust(left=0.18, right=0.97, top=0.97, bottom=0.13)
    return fig, ax


# %%
def run_compare(norm1: str, norm2: str, params: dict):
    print(f"\n[INFO] Comparing {norm1} vs {norm2} with parameters: {params}\n")
    print(f"[INFO] Parameters: {params}")
    print(f"[INFO] t_init={params['t_init']}, t_measure={params['t_measure']}\n")

    # Build params dict for C++ executable (exclude N and mutant_size)
    sim_params = {k: v for k, v in params.items() if k not in ["N", "mutant_size"]}

    # Get self cooperation levels
    coop1 = get_self_cooperation(norm1, sim_params, params["N"])
    coop2 = get_self_cooperation(norm2, sim_params, params["N"])
    # Get b/c ranges
    bc_range1 = get_bc_range(norm1, sim_params, params["N"], params["mutant_size"])
    bc_range2 = get_bc_range(norm2, sim_params, params["N"], params["mutant_size"])

    # Print results
    print(f"\n[RESULTS]")
    coop1_str = f"{coop1:.3f}" if coop1 is not None else "N/A"
    bc1_min_str = f"{bc_range1[0]:.3f}" if bc_range1[0] is not None else "N/A"
    bc1_max_str = f"{bc_range1[1]:.3f}" if bc_range1[1] is not None else "N/A"
    print(f"  {norm1}: cooperation = {coop1_str}, b/c range = [{bc1_min_str}, {bc1_max_str}]")

    coop2_str = f"{coop2:.3f}" if coop2 is not None else "N/A"
    bc2_min_str = f"{bc_range2[0]:.3f}" if bc_range2[0] is not None else "N/A"
    bc2_max_str = f"{bc_range2[1]:.3f}" if bc_range2[1] is not None else "N/A"
    print(f"  {norm2}: cooperation = {coop2_str}, b/c range = [{bc2_min_str}, {bc2_max_str}]\n")

    return coop1, coop2, bc_range1, bc_range2

# %%
# Simulation parameters
PARAMS = {
    "N": 50,                # Population size
    "t_init": 5000,         # Initialization steps
    "t_measure": 5000,      # Measurement steps
    "q": 1.0,               # Observation probability
    "mu_impl": 0.02,         # Implementation error
    "mu_percept": 0.0,      # Perception error
    "mu_assess1": 0.02,     # Assessment error 1
    "mu_assess2": 0.02,      # Assessment error 2
    "seed": 123456789,      # RNG seed
    "mutant_size": 1,       # Mutant size for invasion analysis
}

# Norms to compare (EDIT HERE)
norm1 = "L3"
norm2 = "L3-IS"
# Run comparison
coop1, coop2, bc_range1, bc_range2 = run_compare(norm1, norm2, PARAMS)

#%% Plot 1: Self cooperation level
print(f"[INFO] Creating self cooperation level plot...")
fig, ax = plot_cooperation_level(norm1, norm2, coop1, coop2)
fig.savefig(f"pc_{norm1}_vs_{norm2}.pdf")


#%% Plot 2: b/c range
print(f"[INFO] Creating b/c range plot...")
fig,ax = plot_bc_range(norm1, norm2, bc_range1, bc_range2)
fig.savefig(f"bc_range_{norm1}_vs_{norm2}.pdf")

# %%
def run_and_plot_all(norm1: str, norm2: str, params: dict, fig: plt.Figure = plt.figure()):
    coop1, coop2, bc_range1, bc_range2 = run_compare(norm1, norm2, params)

    fig.clf()
    print(f"[INFO] Creating self cooperation level plot...")
    fig, ax = plot_cooperation_level(norm1, norm2, coop1, coop2)
    fig.savefig(f"pc_{norm1}_vs_{norm2}.pdf")

    fig.clf()
    print(f"[INFO] Creating b/c range plot...")
    fig,ax = plot_bc_range(norm1, norm2, bc_range1, bc_range2)
    fig.savefig(f"bc_range_{norm1}_vs_{norm2}.pdf")

# %%
run_and_plot_all("L1", "L1-IS", PARAMS)
# %%
run_and_plot_all("L1v", "L1v-IS", PARAMS)
# %%
run_and_plot_all("L2", "L2-IS", PARAMS)
# %%
run_and_plot_all("L2v", "L2v-IS", PARAMS)
# %%
run_and_plot_all("L4", "L4-IS", PARAMS)
# %%
run_and_plot_all("L5", "L5-IS", PARAMS)
# %%
run_and_plot_all("L6", "L6-IS", PARAMS)
# %%
run_and_plot_all("L7", "L7-IS", PARAMS)
# %%
run_and_plot_all("L8", "L8-IS", PARAMS)
# %%
