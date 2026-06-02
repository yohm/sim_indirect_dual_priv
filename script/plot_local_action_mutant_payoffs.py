#!/usr/bin/env python3
#%%
"""
Plot local action-rule mutant payoffs at a fixed b/c ratio.

Runs inspect_PrivRepGame on the fly:
  1) monomorphic resident population
  2) resident plus each one-player action-rule mutant

Usage:
  VSCode Interactive: Run cells sequentially, edit parameters in the parameter cell.
"""

#%% Imports and setup
from dataclasses import dataclass

import matplotlib.pyplot as plt

from utils import dumps_json_arg, figure_path, resolve_build_exe, run_json_command

PRG_EXE = resolve_build_exe("inspect_PrivRepGame")


#%% Data structures and helpers
@dataclass(frozen=True)
class PayoffBar:
  label: str
  payoff: float
  action_rule_id: int | None = None
  exceeds_resident: bool = False


def action_rule_label(action_rule_id: int) -> str:
  """Return action string in the same order as Norm::Inspect: GG, GB, BG, BB."""
  chars: list[str] = []
  for idx in (3, 2, 1, 0):
    chars.append("C" if ((action_rule_id >> idx) & 1) else "D")
  return "".join(chars)


def format_norm_label(norm: str) -> str:
  if norm.endswith("-IS"):
    return norm[:-3] + "-RIS"
  return norm + "-base"


def run_privrep_json(args: list[str]) -> dict:
  return run_json_command(PRG_EXE, args)


def get_resident_monomorphic_payoff(norm: str, params: dict, population_size: int, bc_ratio: float) -> tuple[float, float]:
  json_params = dumps_json_arg(params)
  print(f"[INFO] Running monomorphic resident simulation: {norm}, N={population_size}")
  result = run_privrep_json(["-j", json_params, norm, str(population_size)])
  cooperation_level = result["SystemWideCooperationLevel"]
  payoff = (bc_ratio - 1.0) * cooperation_level
  print(f"[INFO] resident cooperation={cooperation_level:.6g}, payoff={payoff:.6g}")
  return cooperation_level, payoff


def get_local_action_mutant_result(norm: str, params: dict, population_size: int) -> dict:
  json_params = dumps_json_arg(params)
  print(f"[INFO] Running local action-rule mutant analysis: {norm}, N={population_size}")
  return run_privrep_json(["-j", json_params, "--local-action-mutants", norm, str(population_size)])


def mutant_payoff(mutant_row: dict, bc_ratio: float) -> float:
  c_levels = mutant_row["NormCooperationLevels"]
  p_rm = c_levels[0][1]
  p_mr = c_levels[1][0]
  return bc_ratio * p_rm - p_mr


def build_payoff_bars(local_result: dict, resident_payoff: float, bc_ratio: float, resident_norm: str) -> list[PayoffBar]:
  bars = [PayoffBar(format_norm_label(resident_norm), resident_payoff)]
  mutants = sorted(local_result["mutants"], key=lambda row: row["action_rule_id"])

  for row in mutants:
    payoff = mutant_payoff(row, bc_ratio)
    action_rule_id = row["action_rule_id"]
    bars.append(
      PayoffBar(
        label=action_rule_label(action_rule_id),
        payoff=payoff,
        action_rule_id=action_rule_id,
        exceeds_resident=payoff > resident_payoff + 0.01,
      )
    )
  return bars


#%% Plotting
def draw_payoffs(ax, norm: str, bars: list[PayoffBar], bc_ratio: float, y_max: float = 1.05, show_ylabel: bool = True):
  xs = list(range(len(bars)))
  values = [max(0.0, bar.payoff) for bar in bars]
  labels = [bar.label for bar in bars]
  resident_payoff = bars[0].payoff

  colors = []
  for i, bar in enumerate(bars):
    if i == 0:
      colors.append("0.2")
    elif bar.payoff < 0.0:
      colors.append("0.75")
    elif bar.exceeds_resident:
      colors.append("#D55E00")
    else:
      colors.append("#0072B2")

  ax.bar(xs, values, color=colors, alpha=0.9, width=0.75)
  ax.axhline(0.0, color="0.45", linewidth=1.0)
  ax.axhline(resident_payoff, color="0.2", linewidth=1.2, linestyle="--")

  ax.set_xticks(xs)
  ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=11)
  ax.tick_params(axis="y", labelsize=14)
  if show_ylabel:
    ax.set_ylabel("payoff", fontsize=18)
  ax.set_title(f"{format_norm_label(norm)}", fontsize=18, pad=8)

  ax.set_ylim(0.0, y_max)

  ax.spines["top"].set_visible(False)
  ax.spines["right"].set_visible(False)
  ax.grid(axis="y", linestyle=":", alpha=0.35)
  return ax


def plot_payoffs(norm: str, bars: list[PayoffBar], bc_ratio: float, y_max: float = 1.05):
  fig, ax = plt.subplots(figsize=(10, 5))
  draw_payoffs(ax, norm, bars, bc_ratio, y_max=y_max)
  fig.subplots_adjust(left=0.10, right=0.98, top=0.86, bottom=0.24)
  return fig, ax


#%% Run helper
def compute_payoff_bars(norm: str, params: dict) -> list[PayoffBar]:
  population_size = params["N"]
  bc_ratio = params["bc_ratio"]
  sim_params = {k: v for k, v in params.items() if k not in ["N", "bc_ratio"]}

  _, resident_payoff = get_resident_monomorphic_payoff(norm, sim_params, population_size, bc_ratio)
  local_result = get_local_action_mutant_result(norm, sim_params, population_size)

  bars = build_payoff_bars(local_result, resident_payoff, bc_ratio, norm)

  print("[RESULTS]")
  for bar in bars:
    tag = " *exceeds resident*" if bar.exceeds_resident else ""
    print(f"  {bar.label:>8s}: payoff={bar.payoff:.6g}{tag}")

  return bars


def run_one(norm: str, params: dict, *, show: bool, save_figure: bool) -> list[PayoffBar]:
  bc_ratio = params["bc_ratio"]
  bars = compute_payoff_bars(norm, params)

  fig, ax = plot_payoffs(norm, bars, bc_ratio)
  if save_figure:
    out = figure_path(f"local_action_mutant_payoffs_{norm.replace('-', '_')}_bc{bc_ratio:g}.pdf")
    fig.savefig(out)
    print(f"[INFO] Saved figure: {out}")
  if show:
    plt.show()
  else:
    plt.close(fig)
  return bars


def run_subplot_grid(norms: list[str], params: dict, *, show: bool, save_figure: bool) -> dict[str, list[PayoffBar]]:
  bc_ratio = params["bc_ratio"]
  n_cols = 2
  n_rows = (len(norms) + n_cols - 1) // n_cols
  fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 4.2 * n_rows), squeeze=False)
  all_bars: dict[str, list[PayoffBar]] = {}

  for idx, norm in enumerate(norms):
    row = idx // n_cols
    col = idx % n_cols
    bars = compute_payoff_bars(norm, params)
    all_bars[norm] = bars
    draw_payoffs(axes[row][col], norm, bars, bc_ratio, show_ylabel=(col == 0))

  for idx in range(len(norms), n_rows * n_cols):
    row = idx // n_cols
    col = idx % n_cols
    axes[row][col].axis("off")

  fig.subplots_adjust(left=0.07, right=0.98, top=0.96, bottom=0.08, hspace=0.55, wspace=0.18)
  if save_figure:
    out = figure_path(f"local_action_mutant_payoffs_grid_bc{bc_ratio:g}.pdf")
    fig.savefig(out)
    print(f"[INFO] Saved figure: {out}")
  if show:
    plt.show()
  else:
    plt.close(fig)
  return all_bars


#%% Parameters
PARAMS = {
  "N": 50,
  "bc_ratio": 2.0,
  "t_init": 5000,
  "t_measure": 5000,
  "q": 1.0,
  "mu_impl": 0.02,
  "mu_percept": 0.0,
  "mu_assess1": 0.02,
  "mu_assess2": 0.02,
  "_seed": 123456789,
}

save_figure = True
show_figure = True
run_single_panel = False


#%% Run subplot grid
subplot_norms = [
  "L6", "L6-IS",
  "L8", "L8-IS",
  "L5", "L5-IS",
  "L3", "L3-IS",
]
grid_bars = run_subplot_grid(subplot_norms, PARAMS, show=show_figure, save_figure=save_figure)

#%% Optional: run one panel
if run_single_panel:
  bars = run_one("L6-IS", PARAMS, show=show_figure, save_figure=save_figure)
