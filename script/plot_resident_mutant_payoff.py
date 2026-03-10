#!/usr/bin/env python3
"""
Plot resident vs mutant payoffs as a function of mutant fraction f \in [0,1].

- Calls the compiled executable `inspect_PrivRepGame` for each f,
  with a 2-type population (resident, mutant).
- Reads NormCooperationLevels (2x2 cooperation matrix) from JSON output.
- Computes per-capita expected payoff for each type:
    payoff_i = b * sum_j p_j * c_{j->i} - c * sum_j p_j * c_{i->j}
  where p_0 = 1 - f, p_1 = f.
- Plots y=payoff vs x=f for both resident and mutant.

Edge handling (as requested):
  - If mutant fraction f=0, compute ONLY resident payoff; mutant is set to NaN (not computed).
  - If mutant fraction f=1, compute ONLY mutant payoff; resident is set to NaN (not computed).
  Matplotlib breaks lines at NaN, so only computable points are connected.

Usage (from repo root):
  uv venv .venv && source .venv/bin/activate
  uv pip install -r script/requirements.txt

Usage example:
  # show window for L6 vs. ALLD
  python script/plot_resident_mutant_payoff.py \
      --resident L6-IS --mutant AllD \
      --benefit 5 --cost 1 \
      --N 50 --points 51 \
      --build-dir cmake-build-release \
      --params '{"t_init":1000,"t_measure":1000,"q":0.9,"mu_assess1":0.01,"mu_assess2":0.01,"mu_impl":0.00,"mu_percept":0.00,"_seed":123456789}' \
      --out figures/payoff_L6_vs_AllD.png --show

  # multiple norms, save each as figures/payoff_<resident>_vs_<mutant>.(png|pdf|svg) without showing windows
  python script/plot_resident_mutant_payoff.py \
      --resident L3 --mutant AllC \
      --benefit 5 --cost 1 \
      --N 50 --points 51 \
      --build-dir cmake-build-release \
      --params '{"t_init":1000,"t_measure":1000,"q":0.9,"mu_assess1":0.01,"mu_assess2":0.01,"mu_impl":0.00,"mu_percept":0.05,"_seed":123456789}' \
      --save --format pdf --no-show
"""

import argparse
import json
import math
import os
import subprocess
import sys
from typing import Optional, Tuple, List

import numpy as np
import matplotlib.pyplot as plt


def run(cmd: list, input_text: Optional[str] = None) -> Tuple[int, str, str]:
    res = subprocess.run(cmd, input=input_text, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


def call_prg(inspect_prg_path: str,
             resident: str,
             mutant: str,
             size_resident: int,
             size_mutant: int,
             j_params: Optional[str]) -> dict:
    cmd = [inspect_prg_path]
    if j_params:
        cmd += ["-j", j_params]
    cmd += [resident, str(size_resident), mutant, str(size_mutant)]
    code, out, err = run(cmd)
    if code != 0:
        raise RuntimeError(f"inspect_PrivRepGame failed: {err.strip()}")
    try:
        data = json.loads(out)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from inspect_PrivRepGame: {e}")
    return data


def compute_payoffs_from_clevels(c_levels: List[List[float]],
                                 f: float,
                                 benefit: float,
                                 cost: float) -> Tuple[float, float]:
    """
    c_levels: 2x2 matrix where c_levels[i][j] = P(C | donor type i to recipient type j).
    f: mutant fraction in [0,1]; p_resident = 1-f, p_mutant = f.
    Returns (payoff_resident, payoff_mutant).
    """
    if len(c_levels) != 2 or any(len(row) != 2 for row in c_levels):
        raise ValueError("Expected NormCooperationLevels to be 2x2 for two-type population.")

    p0 = 1.0 - f  # resident fraction
    p1 = f        # mutant fraction

    # c_ij = donor i to recipient j
    c00, c01 = c_levels[0][0], c_levels[0][1]
    c10, c11 = c_levels[1][0], c_levels[1][1]

    # Benefit received by type j = sum_i p_i * c_{i->j}
    # Cost paid by type i       = sum_j p_j * c_{i->j}
    benefit_resident = benefit * (p0 * c00 + p1 * c10)
    cost_resident    = cost    * (p0 * c00 + p1 * c01)

    benefit_mutant   = benefit * (p0 * c01 + p1 * c11)
    cost_mutant      = cost    * (p0 * c10 + p1 * c11)

    return benefit_resident - cost_resident, benefit_mutant - cost_mutant


def payoff_homogeneous(c: float, benefit: float, cost: float) -> float:
    """Per-capita payoff in a homogeneous population with cooperation level c."""
    return benefit * c - cost * c


def main():
    ap = argparse.ArgumentParser(description="Plot resident & mutant payoffs vs mutant fraction f.")
    ap.add_argument("--resident", required=True, help="Resident norm (name/ID/0xHEX/Rd-Rr-P/20 nums), e.g., L6")
    ap.add_argument("--mutant", required=True, help="Mutant norm, e.g., AllD")
    ap.add_argument("--benefit", type=float, default=5.0, help="Benefit b (default: 5.0)")
    ap.add_argument("--cost", type=float, default=1.0, help="Cost c (default: 1.0)")
    ap.add_argument("--N", type=int, default=50, help="Total population size used in PRG runs (>=2; default: 50)")
    ap.add_argument("--points", type=int, default=51, help="Number of f grid points in [0,1] (default: 51)")
    ap.add_argument("--build-dir", default="cmake-build-release", help="Directory containing inspect_PrivRepGame")
    ap.add_argument("--params", default=None, help="JSON string or path to JSON with PRG params (-j); t_init/t_measure etc.")
    ap.add_argument("--out", default=None, help="Output figure path (PNG/PDF/SVG).")
    ap.add_argument("--save", action="store_true",
                help="Save to figures/payoff_<resident>_vs_<mutant>.<format> unless --out is given.")
    ap.add_argument("--format", choices=["png", "pdf", "svg"], default="png",
                help="Output format when saving without --out (default: png)")
    ap.add_argument("--show", action="store_true", help="Show window")
    ap.add_argument("--no-show", action="store_true", help="Do not open a window.")

    args = ap.parse_args()

    inspect_prg = os.path.join(args.build_dir, "inspect_PrivRepGame")
    if not os.path.exists(inspect_prg):
        print(f"[Error] executable not found: {inspect_prg}", file=sys.stderr)
        sys.exit(1)

    # Prepare -j params
    j_arg = None
    if args.params:
        if os.path.exists(args.params):
            with open(args.params) as f:
                j_arg = f.read()
        else:
            j_arg = args.params

    if args.N < 2:
        print("[Error] --N must be >= 2", file=sys.stderr)
        sys.exit(1)
    if args.points < 2:
        print("[Error] --points must be >= 2", file=sys.stderr)
        sys.exit(1)

    fs = [i / (args.points - 1) for i in range(args.points)]  # includes 0 and 1
    pay_res, pay_mut = [], []

    for f in fs:
        n_mut = int(round(f * args.N))
        n_mut = min(max(n_mut, 0), args.N)
        n_res = args.N - n_mut

        try:
            if n_mut == 0:
                # Resident-only run; compute ONLY resident payoff
                cmd = [inspect_prg]
                if j_arg:
                    cmd += ["-j", j_arg]
                cmd += [args.resident, str(args.N)]
                code, out, err = run(cmd)
                if code != 0:
                    raise RuntimeError(err.strip())
                data = json.loads(out)
                c = float(data.get("SystemWideCooperationLevel"))
                pr = payoff_homogeneous(c, args.benefit, args.cost)
                pm = np.nan  # not computed
            elif n_res == 0:
                # Mutant-only run; compute ONLY mutant payoff
                cmd = [inspect_prg]
                if j_arg:
                    cmd += ["-j", j_arg]
                cmd += [args.mutant, str(args.N)]
                code, out, err = run(cmd)
                if code != 0:
                    raise RuntimeError(err.strip())
                data = json.loads(out)
                c = float(data.get("SystemWideCooperationLevel"))
                pr = np.nan  # not computed
                pm = payoff_homogeneous(c, args.benefit, args.cost)
            else:
                data = call_prg(inspect_prg, args.resident, args.mutant, n_res, n_mut, j_arg)
                if "NormCooperationLevels" not in data:
                    raise RuntimeError("inspect_PrivRepGame did not return NormCooperationLevels")
                c_levels = data["NormCooperationLevels"]
                c_levels = [[(float(x) if x is not None else np.nan) for x in row] for row in c_levels]
                pr, pm = compute_payoffs_from_clevels(c_levels, f, args.benefit, args.cost)

            pay_res.append(pr)
            pay_mut.append(pm)
        except Exception as e:
            print(f"[warn] f={f:.3f} failed: {e}", file=sys.stderr)
            pay_res.append(np.nan)
            pay_mut.append(np.nan)

    # Plot (lines break at NaN automatically)
    fs_arr = np.array(fs, dtype=float)
    res_arr = np.array(pay_res, dtype=float)
    mut_arr = np.array(pay_mut, dtype=float)

    mask_res = np.isfinite(res_arr)
    mask_mut = np.isfinite(mut_arr)

    plt.figure(figsize=(7, 4.5))
    plt.plot(fs_arr[mask_res], res_arr[mask_res], label=f"Resident ({args.resident})", linewidth=2)
    plt.plot(fs_arr[mask_mut], mut_arr[mask_mut], label=f"Mutant ({args.mutant})", linewidth=2)

    plt.axhline(0.0, linestyle="--", alpha=0.5)
    plt.xlabel("mutant fraction f")
    plt.ylabel("per-capita payoff")
    title = f"Payoff vs mutant fraction  (b={args.benefit}, c={args.cost}, N={args.N})"
    plt.title(title)
    plt.grid(True, linestyle=":", alpha=0.5)
    plt.legend(frameon=False)
    plt.tight_layout()

    # --- decide output path ---
    out_path = None
    if args.out:
        out_path = args.out
    elif args.save:
        os.makedirs("figures", exist_ok=True)
        out_path = os.path.join("figures", f"payoff_{args.resident}_vs_{args.mutant}.{args.format}")

    # --- save / show ---
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        plt.savefig(out_path, dpi=150)
        print(f"Saved: {out_path}")

    # show if explicitly requested, or if not told to suppress and nothing was saved
    if args.show or (not args.no_show and not out_path):
        plt.show()


if __name__ == "__main__":
    main()
