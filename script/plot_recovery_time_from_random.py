#!/usr/bin/env python3
# %%
"""Monte Carlo test of random-configuration recovery under L6-RIS.

The simulation uses the aggregated transition probabilities from the SI table
for the state (n_G, n_B, n_M).

Example:
  # run cell-by-cell inside VSCode
  # (adjust configuration values in the CONFIG cell)
"""

# %%
from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass
from statistics import mean, stdev
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from utils import figure_path


# %%
@dataclass(frozen=True)
class Result:
    n: int
    reps: int
    mean_time: float
    sd_time: float
    se_time: float
    harmonic: float
    lower_bound: float
    upper_bound: float
    ratio_n_log_n: float


def harmonic_number(n: int) -> float:
    return sum(1.0 / k for k in range(1, n + 1))


def simulate_once(n: int, rng: random.Random) -> int:
    """Return recovery time from (0, 0, n) to (n, 0, 0)."""
    g = 0
    b = 0
    m = n
    steps = 0
    denom = 2 * n * (n - 1)

    while g != n:
        # Aggregated transition weights, multiplied by 2 to keep integers.
        w_same = 2 * g * (g - 1) + 2 * g * b + g * m + b * m
        w_g_up_b_down = 2 * g * b + 2 * b * (b - 1) + b * m
        w_g_up_m_down = 2 * g * m + 2 * b * m + m * (m - 1)
        w_g_down_b_up = g * m
        # The remaining weight is w_b_up_m_down = m * (m - 1).

        r = rng.randrange(denom)
        if r < w_same:
            pass
        elif r < w_same + w_g_up_b_down:
            g += 1
            b -= 1
        elif r < w_same + w_g_up_b_down + w_g_up_m_down:
            g += 1
            m -= 1
        elif r < w_same + w_g_up_b_down + w_g_up_m_down + w_g_down_b_up:
            g -= 1
            b += 1
        else:
            b += 1
            m -= 1
        steps += 1

    return steps


def simulate(n: int, reps: int, rng: random.Random) -> Result:
    times = [simulate_once(n, rng) for _ in range(reps)]
    avg = mean(times)
    sd = stdev(times) if reps > 1 else 0.0
    h_n = harmonic_number(n)
    return Result(
        n=n,
        reps=reps,
        mean_time=avg,
        sd_time=sd,
        se_time=sd / math.sqrt(reps),
        harmonic=h_n,
        lower_bound=n * h_n,
        upper_bound=2 * n * h_n,
        ratio_n_log_n=avg / (n * math.log(n)),
    )


def collect_recovery_stats(ns: List[int], reps: int, seed: int) -> Tuple[List[int], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Run the random-configuration recovery sweep."""
    rng = random.Random(seed)
    results: List[Result] = []
    print(f"[Info] Sweeping {len(ns)} population sizes with {reps} repetitions per N")
    for n in ns:
        if n < 2:
            raise ValueError("All N values must be at least 2.")
        result = simulate(n, reps, rng)
        results.append(result)
        print(
            f"N={result.n:4d} mean={result.mean_time:10.3f} "
            f"stderr={result.se_time:8.3f} "
            f"N*H_N={result.lower_bound:10.3f} "
            f"mean/(N log N)={result.ratio_n_log_n:.4f}"
        )

    return (
        [r.n for r in results],
        np.array([r.mean_time for r in results], dtype=float),
        np.array([r.se_time for r in results], dtype=float),
        np.array([r.lower_bound for r in results], dtype=float),
        np.array([r.upper_bound for r in results], dtype=float),
    )


# %%
# CONFIG (edit and re-run this cell)
NS = [20, 30, 50, 75, 100, 150, 200, 300, 500]
REPS = 300
SEED = 1
OUTPUT_PATH = str(figure_path("recovery_random_scaling.pdf"))
SHOW_PLOT = True


# %%
# RUN SWEEP
n_values, avg_arr, err_arr, lower_bound_arr, upper_bound_arr = collect_recovery_stats(
    NS,
    REPS,
    SEED,
)


# %%
# PLOT
Y_SCALE = 1e3
plt.clf()
fig, ax = plt.subplots(figsize=(8, 5))
ax.errorbar(
    n_values,
    avg_arr / Y_SCALE,
    yerr=err_arr / Y_SCALE,
    fmt="-o",
    color="tab:blue",
    ecolor="tab:blue",
    elinewidth=1.0,
    capsize=2,
    markersize=4,
    markerfacecolor="white",
    markeredgewidth=1.5,
    alpha=0.85,
    label="Simulation",
    zorder=5,
)
ax.plot(
    n_values,
    lower_bound_arr / Y_SCALE,
    label=r"$N H_N$",
    color="tab:orange",
    linestyle="--",
    linewidth=2.0,
    alpha=0.9,
    zorder=4,
)
ax.plot(
    n_values,
    upper_bound_arr / Y_SCALE,
    label=r"$2 N H_N$",
    color="tab:orange",
    linestyle=":",
    linewidth=2.0,
    alpha=0.9,
    zorder=4,
)
ax.set_xlabel("population size N", fontsize=20)
ax.set_ylabel(r"recovery time ($\times 10^3$)", fontsize=20)
ax.set_ylim((0, 5))
ax.tick_params(axis="x", labelsize=13)
ax.tick_params(axis="y", labelsize=12)
ax.grid(True, linestyle=":", alpha=0.5)
ax.legend(fontsize=14)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.subplots_adjust(left=0.18, right=0.93, top=0.96, bottom=0.15)

if OUTPUT_PATH:
    out_dir = os.path.dirname(OUTPUT_PATH)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    fig.savefig(OUTPUT_PATH, bbox_inches="tight", pad_inches=0.1)
    print(f"[Info] Plot saved to {OUTPUT_PATH}")

# %%
