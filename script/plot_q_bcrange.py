#!/usr/bin/env python3
#%%
"""
Plot q-dependence of self-cooperation level and stable b/c range.

The four-panel figure compares L6 and L6-IS/RIS:
  rows:    L6, L6-RIS
  columns: self-cooperation level, stable b/c range

Usage:
  VS Code Interactive: Run cells sequentially, edit PARAMS below.
"""

#%% Imports and setup
from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path
from typing import Optional

mpl_config_dir = Path(tempfile.gettempdir()) / "sim_indirect_dual_priv_matplotlib"
mpl_config_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(mpl_config_dir / "mpl"))
os.environ.setdefault("XDG_CACHE_HOME", str(mpl_config_dir / "xdg"))

import matplotlib.pyplot as plt

from utils import dumps_json_arg, figure_path, resolve_build_exe, run_json_command


PARAMS = {
  "residents": ["L6", "L6-IS"],
  "build_dir": None,
  "N": 50,
  "t_init": 5000,
  "t_measure": 45000,
  "mu_impl": 0.02,
  "mu_percept": 0.0,
  "mu_assess1": 0.02,
  "mu_assess2": 0.02,
  "_seed": 123456789,
  "mutant_size": 1,
  "q_min": 0.05,
  "q_max": 1.0,
  "q_count": 20,
  "bcrange_q_min_by_resident": {"L6-IS": 0.4},
  "skip_bcrange_residents": ["L6"],
  "x_min": 0.0,
  "x_max": 1.02,
  "y_max": 4.0,
  "output_prefix": "l6_l6_is_q_panels",
}


#%% Helpers

def resolve_prg_exe(build_dir: str | None) -> Path:
  if build_dir:
    return resolve_build_exe("inspect_PrivRepGame", build_dir)

  for candidate in [
      resolve_build_exe("inspect_PrivRepGame", "cmake-build-release"),
      resolve_build_exe("inspect_PrivRepGame", "build"),
  ]:
    if candidate.exists():
      return candidate
  return resolve_build_exe("inspect_PrivRepGame", "cmake-build-release")


def q_grid(q_min: float, q_max: float, q_count: int) -> list[float]:
  if q_count < 2:
    raise ValueError("q_count must be at least 2")
  if q_min > q_max:
    raise ValueError("q_min must be <= q_max")
  step = (q_max - q_min) / (q_count - 1)
  return [q_min + i * step for i in range(q_count)]


def filtered_q_grid(params: dict, resident: str) -> list[float]:
  qs = q_grid(params["q_min"], params["q_max"], params["q_count"])
  q_min = params.get("bcrange_q_min_by_resident", {}).get(resident)
  if q_min is None:
    return qs
  return [q for q in qs if q >= q_min]


def sim_params(params: dict, q: float) -> dict:
  return {
    "t_init": params["t_init"],
    "t_measure": params["t_measure"],
    "q": q,
    "mu_impl": params["mu_impl"],
    "mu_percept": params["mu_percept"],
    "mu_assess1": params["mu_assess1"],
    "mu_assess2": params["mu_assess2"],
    "_seed": params["_seed"],
  }


def display_norm_name(norm: str) -> str:
  if norm == "L6":
    return "L6-base"
  if norm.endswith("-IS"):
    return norm[:-3] + "-RIS"
  return norm


def finite_or_nan(value: Optional[float]) -> float:
  return math.nan if value is None else value


#%% Simulation

def compute_self_coop(exe: Path, resident: str, params: dict, qs: list[float]) -> list[dict[str, Optional[float]]]:
  rows = []
  for q in qs:
    print(f"[INFO] q={q:.4f}: {resident} monomorphic N={params['N']}")
    result = run_json_command(exe, ["-j", dumps_json_arg(sim_params(params, q)), resident, str(params["N"])])
    rows.append({"q": q, "self_coop": result.get("SystemWideCooperationLevel")})
  return rows


def compute_bcrange(exe: Path, resident: str, params: dict, qs: list[float]) -> list[dict[str, Optional[float]]]:
  resident_size = params["N"] - params["mutant_size"]
  mutant_size = params["mutant_size"]
  rows = []

  for q in qs:
    q_params = sim_params(params, q)

    print(f"[INFO] q={q:.4f}: {resident} {resident_size} + AllD {mutant_size}")
    alld = run_json_command(exe, ["-j", dumps_json_arg(q_params), resident, str(resident_size), "AllD", str(mutant_size)])
    alld_invasion = alld.get("Invasion", {})

    print(f"[INFO] q={q:.4f}: {resident} {resident_size} + AllC {mutant_size}")
    allc = run_json_command(exe, ["-j", dumps_json_arg(q_params), resident, str(resident_size), "AllC", str(mutant_size)])
    allc_invasion = allc.get("Invasion", {})

    rows.append({
      "q": q,
      "bc_min": alld_invasion.get("bc_min"),
      "bc_max": allc_invasion.get("bc_max"),
    })

  return rows


def compute_panel_data(params: dict) -> dict:
  if len(params["residents"]) != 2:
    raise ValueError("residents must contain exactly two norms")
  if params["mutant_size"] < 1 or params["mutant_size"] >= params["N"]:
    raise ValueError("mutant_size must be between 1 and N-1")

  exe = resolve_prg_exe(params["build_dir"])
  qs = q_grid(params["q_min"], params["q_max"], params["q_count"])
  data = {}

  for resident in params["residents"]:
    bcrange_qs = filtered_q_grid(params, resident)
    if resident in params.get("skip_bcrange_residents", []):
      bcrange_rows = []
    else:
      bcrange_rows = compute_bcrange(exe, resident, params, bcrange_qs)
    data[resident] = {
      "self_coop": compute_self_coop(exe, resident, params, qs),
      "bcrange": bcrange_rows,
    }

  return data


#%% Plotting

def draw_self_coop(ax, rows: list[dict[str, Optional[float]]], params: dict, *, show_xlabel: bool):
  qs = [float(row["q"]) for row in rows]
  values = [finite_or_nan(row["self_coop"]) for row in rows]

  ax.plot(qs, values, color="tab:blue", linewidth=2.6, marker="o", markersize=5)
  ax.set_xlim(params["x_min"], params["x_max"])
  ax.set_ylim(0.0, 1.0)
  ax.set_xlabel("$q$" if show_xlabel else "", fontsize=22)
  ax.set_ylabel("self-cooperation level", fontsize=18)
  ax.tick_params(axis="both", labelsize=14)
  ax.spines["top"].set_visible(False)
  ax.spines["right"].set_visible(False)


def draw_bcrange(ax, rows: list[dict[str, Optional[float]]], params: dict, *, show_xlabel: bool):
  if not rows:
    ax.set_xlim(params["x_min"], params["x_max"])
    ax.set_ylim(1.0, params["y_max"])
    ax.set_xlabel("$q$" if show_xlabel else "", fontsize=22)
    ax.set_ylabel("$b/c$", fontsize=22)
    ax.tick_params(axis="both", labelsize=14)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return

  qs = [float(row["q"]) for row in rows]
  lows = [finite_or_nan(row["bc_min"]) for row in rows]
  highs_for_fill = [params["y_max"] if row["bc_max"] is None else min(float(row["bc_max"]), params["y_max"]) for row in rows]
  highs_for_line = [
    finite_or_nan(row["bc_max"]) if row["bc_max"] is not None and float(row["bc_max"]) <= params["y_max"] else math.nan
    for row in rows
  ]
  valid = [
    math.isfinite(low) and math.isfinite(high) and high >= low
    for low, high in zip(lows, highs_for_fill)
  ]

  ax.fill_between(
    qs,
    lows,
    highs_for_fill,
    where=valid,
    color="tab:purple",
    alpha=0.28,
    interpolate=True,
    edgecolor="none",
    linewidth=0,
  )
  ax.plot(qs, lows, color="tab:purple", linewidth=2.6, marker="o", markersize=5)
  if any(math.isfinite(high) for high in highs_for_line):
    ax.plot(qs, highs_for_line, color="tab:orange", linewidth=2.6, marker="o", markersize=5)

  ax.set_xlim(params["x_min"], params["x_max"])
  ax.set_ylim(1.0, params["y_max"])
  ax.set_xlabel("$q$" if show_xlabel else "", fontsize=22)
  ax.set_ylabel("$b/c$", fontsize=22)
  ax.tick_params(axis="both", labelsize=14)
  ax.spines["top"].set_visible(False)
  ax.spines["right"].set_visible(False)


def plot_panel(data: dict, params: dict):
  fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True)

  for row_index, resident in enumerate(params["residents"]):
    show_xlabel = row_index == 1
    draw_self_coop(axes[row_index][0], data[resident]["self_coop"], params, show_xlabel=show_xlabel)
    draw_bcrange(axes[row_index][1], data[resident]["bcrange"], params, show_xlabel=show_xlabel)
    axes[row_index][0].text(
      -0.28,
      0.5,
      display_norm_name(resident),
      transform=axes[row_index][0].transAxes,
      rotation=90,
      ha="center",
      va="center",
      fontsize=18,
    )

  axes[0][0].set_title("self-cooperation level", fontsize=18)
  axes[0][1].set_title("stable $b/c$ range", fontsize=18)
  fig.subplots_adjust(left=0.14, right=0.98, top=0.92, bottom=0.10, wspace=0.32, hspace=0.22)
  return fig, axes


def run(params: dict):
  data = compute_panel_data(params)
  fig, axes = plot_panel(data, params)
  pdf_path = figure_path(f"{params['output_prefix']}.pdf")
  fig.savefig(pdf_path)
  print(f"[INFO] wrote {pdf_path}")
  return {"data": data, "fig": fig, "axes": axes, "pdf_path": pdf_path}


#%% Run

result = run(PARAMS)

# %%
