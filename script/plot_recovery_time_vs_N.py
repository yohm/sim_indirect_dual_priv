#!/usr/bin/env python3
# %%
"""
Sweep population size N, run main_RecoveryAnalysis for the L6-IS norm,
and plot the average recovery time (with standard-error bars) as a function of N.
Optionally overlay a theoretical prediction curve.

Example (from repo root, assuming cmake-build-release already built):
  # run cell-by-cell inside VSCode
  # (adjust configuration values in the CONFIG cell)
"""

# %%
import csv
import json
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np


# %%
def run_recovery_sample(exe_path: str, norm: str, params: Dict) -> Dict:
    """Invoke main_RecoveryAnalysis with the provided params and return parsed JSON."""
    params_str = json.dumps(params, separators=(",", ":"))
    cmd = [exe_path, "-j", params_str, norm]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(
            f"main_RecoveryAnalysis failed for N={params.get('N')}: {res.stderr.strip()}"
        )
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Failed to parse JSON output for N={params.get('N')}: {exc}\nstdout:\n{res.stdout}"
        ) from exc


# %%
@dataclass
class SweepConfig:
    norm: str
    min_N: int
    max_N: int
    step: int
    num_samples: int
    max_t: int
    seed: int
    exe_path: str


def collect_recovery_stats(cfg: SweepConfig) -> Tuple[List[int], np.ndarray, np.ndarray, List[int]]:
    """Run the sweep and return (N values, averages, std_errs, recoveries)."""
    n_values = list(range(cfg.min_N, cfg.max_N + 1, cfg.step))
    averages: List[float] = []
    std_errs: List[float] = []
    recoveries: List[int] = []

    print(f"[Info] Sweeping N from {cfg.min_N} to {cfg.max_N} (step {cfg.step}) for norm {cfg.norm}")
    for N in n_values:
        params = {
            "N": N,
            "max_t": cfg.max_t,
            "num_samples": cfg.num_samples,
            "_seed": cfg.seed,
        }
        result = run_recovery_sample(cfg.exe_path, cfg.norm, params)
        avg = result.get("avg_recovery_time")
        std_err = result.get("std_err_recovery_time")
        averages.append(float(avg) if avg is not None else np.nan)
        std_errs.append(float(std_err) if std_err is not None else np.nan)
        recoveries.append(int(result.get("num_recoveries", 0)))
        print(
            f"N={N:3d} avg={averages[-1]:10.3f} "
            f"stderr={std_errs[-1]:10.3f} recoveries={recoveries[-1]}"
        )

    return n_values, np.array(averages, dtype=float), np.array(std_errs, dtype=float), recoveries

# %%
# CONFIG (edit and re-run this cell)
NORM = "L6-IS"
MIN_N = 2
MAX_N = 100
STEP = 1
NUM_SAMPLES = 100000
MAX_T = 100000
SEED = 123456789
BUILD_DIR = "../cmake-build-release"
EXE_PATH = os.path.join(BUILD_DIR, "main_RecoveryAnalysis")
OUTPUT_PATH = None #"figures/recovery_time_vs_N.png"  # set to None to skip saving
SHOW_PLOT = True
THEORETICAL_DATA_PATH = "Recoverytimes_L6IS.csv"  # e.g., "data/theory_recovery.csv"


# %%
# RUN SWEEP
if not os.path.exists(EXE_PATH):
    raise FileNotFoundError(f"main_RecoveryAnalysis not found at {EXE_PATH}")

CONFIG = SweepConfig(
    norm=NORM,
    min_N=MIN_N,
    max_N=MAX_N,
    step=STEP,
    num_samples=NUM_SAMPLES,
    max_t=MAX_T,
    seed=SEED,
    exe_path=EXE_PATH,
)

n_values, avg_arr, err_arr, recoveries = collect_recovery_stats(CONFIG)


# %%
# PLOT
plt.clf()
fig, ax = plt.subplots(figsize=(8, 5))
ax.errorbar( n_values, avg_arr, yerr=err_arr,
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
    zorder=1,
)
ax.set_xlabel("Population size N")
ax.set_ylabel("Average recovery time")
ax.set_title(f"Recovery time vs N (norm: L6-IS)")
#ax.grid(True, linestyle="--", alpha=0.4)
ax.legend()

theory_vals = [3,3.85,4.801097394,5.77591186,6.760432349,7.7499252,8.7423168,9.736549406,10.73202536,11.72838095,12.72538195,13.72287063,14.72073686,15.71890135,16.71730561,17.71590549,18.71466709,19.7135639,20.7125749,21.71168323,22.7108752,23.71013955,24.70946698,25.70884969,26.70828115,27.7077558,28.70726889,29.70681635,30.70639467,31.70600079,32.70563206,33.70528613,34.70496095,35.70465472,36.70436582,37.70409282,38.70383444,39.70358955,40.7033571,41.70313618,42.70292595,43.70272565,44.70253459,45.70235215,46.70217775,47.70201089,48.70185107,49.70169787,50.70155087,51.70140972,52.70127406,53.70114359,54.70101801,55.70089705,56.70078047,57.70066802,58.70055949,59.70045468,60.70035341,61.70025549,62.70016077,63.70006908,64.69998029,65.69989426,66.69981086,67.69972998,68.69965149,69.69957531,70.69950132,71.69942944,72.69935957,73.69929163,74.69922554,75.69916124,76.69909864,77.69903768,78.69897829,79.69892042,80.69886401,81.69880901,82.69875536,83.69870301,84.69865191,85.69860203,86.69855332,87.69850573,88.69845924,89.69841379,90.69836937,91.69832593,92.69828344,93.69824187,94.69820119,95.69816137,96.69812239,97.69808421,98.69804682,99.6980102,100.6979743]
theory_N = np.arange(2, 101)
ax.plot(
    theory_N,
    theory_vals,
    label="Theory",
    color="tab:orange",
    linestyle="-",
    linewidth=2.0,
    alpha=0.9,
    zorder=4,
)
ax.legend()

if OUTPUT_PATH:
    out_dir = os.path.dirname(OUTPUT_PATH)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=200)
    print(f"[Info] Plot saved to {OUTPUT_PATH}")

if SHOW_PLOT:
    plt.show()
else:
    plt.close(fig)

# %%
# MULTI-NORM CONFIG (edit and re-run this cell)
NORMS_TO_SWEEP = [f"L{i}-IS" for i in range(1, 9)] + ["L1v-IS", "L2v-IS"]
MULTI_MIN_N = MIN_N
MULTI_MAX_N = MAX_N
MULTI_STEP = STEP
MULTI_NUM_SAMPLES = NUM_SAMPLES
MULTI_MAX_T = MAX_T
MULTI_SEED = SEED
MULTI_EXE_PATH = EXE_PATH
MULTI_OUTPUT_PATH = None  # e.g., "figures/recovery_time_vs_N_multi.png"
MULTI_RESULTS_PATH = "data/recovery_time_vs_N_multi.tsv"  # set to None to skip saving/loading
MULTI_SHOW_PLOT = True


# %%
# MULTI-NORM SWEEP
multi_norm_results = {}
for norm in NORMS_TO_SWEEP:
    multi_cfg = SweepConfig(
        norm=norm,
        min_N=MULTI_MIN_N,
        max_N=MULTI_MAX_N,
        step=MULTI_STEP,
        num_samples=MULTI_NUM_SAMPLES,
        max_t=MULTI_MAX_T,
        seed=MULTI_SEED,
        exe_path=MULTI_EXE_PATH,
    )
    (
        norm_n_values,
        norm_avg_arr,
        norm_err_arr,
        norm_recoveries,
    ) = collect_recovery_stats(multi_cfg)
    multi_norm_results[norm] = {
        "N": norm_n_values,
        "avg": norm_avg_arr,
        "err": norm_err_arr,
        "recoveries": norm_recoveries,
    }

# %%
# MULTI-NORM SAVE RESULTS
if MULTI_RESULTS_PATH and multi_norm_results:
    out_dir = os.path.dirname(MULTI_RESULTS_PATH)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(MULTI_RESULTS_PATH, "w", newline="") as fp:
        writer = csv.writer(fp, delimiter="\t")
        writer.writerow(["norm", "N", "avg", "std_err", "num_recoveries"])
        for norm, result in multi_norm_results.items():
            for n, avg, err, rec in zip(
                result["N"],
                result["avg"],
                result["err"],
                result["recoveries"],
            ):
                writer.writerow([norm, int(n), float(avg), float(err), int(rec)])
    print(f"[Info] Saved multi-norm sweep results to {MULTI_RESULTS_PATH}")

# %%
# MULTI-NORM LOAD RESULTS
if MULTI_RESULTS_PATH and os.path.exists(MULTI_RESULTS_PATH):
    multi_norm_results = {}
    with open(MULTI_RESULTS_PATH, "r", newline="") as fp:
        reader = csv.DictReader(fp, delimiter="\t")
        for row in reader:
            norm = row["norm"]
            multi_norm_results.setdefault(norm, {"N": [], "avg": [], "err": [], "recoveries": []})
            multi_norm_results[norm]["N"].append(int(row["N"]))
            multi_norm_results[norm]["avg"].append(float(row["avg"]))
            multi_norm_results[norm]["err"].append(float(row["std_err"]))
            multi_norm_results[norm]["recoveries"].append(int(row["num_recoveries"]))
    for norm, result in multi_norm_results.items():
        result["avg"] = np.array(result["avg"], dtype=float)
        result["err"] = np.array(result["err"], dtype=float)
    print(f"[Info] Loaded multi-norm sweep results from {MULTI_RESULTS_PATH}")


# %%
# MULTI-NORM PLOT
if not multi_norm_results:
    raise RuntimeError("Run the multi-norm sweep cell first to populate results.")

plt.clf()
fig, ax = plt.subplots(figsize=(9, 5.5))
for norm, result in multi_norm_results.items():
    ax.errorbar(
        result["N"],
        result["avg"],
        yerr=result["err"],
        fmt="-o",
        markersize=3,
        capsize=2,
        alpha=0.85,
        label=norm,
    )

ax.set_xlabel("Population size N")
ax.set_ylabel("Average recovery time")
ax.set_title("Recovery time vs N for multiple norms")
ax.legend(ncol=2)

if MULTI_OUTPUT_PATH:
    out_dir = os.path.dirname(MULTI_OUTPUT_PATH)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    fig.tight_layout()
    fig.savefig(MULTI_OUTPUT_PATH, dpi=200)
    print(f"[Info] Multi-norm plot saved to {MULTI_OUTPUT_PATH}")

if MULTI_SHOW_PLOT:
    plt.show()
else:
    plt.close(fig)

# %%
for norm in NORMS_TO_SWEEP:
    print(f"Norm: {norm}")
    print(multi_norm_results[norm]['avg'][-1])

# %%
