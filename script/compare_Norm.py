"""
Usage (from repo root):
  uv venv .venv && source .venv/bin/activate
  uv pip install -r script/requirements.txt
  cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release && cmake --build cmake-build-release -j
  # default params
  python script/compare_Norm.py

Examples:
  python script/compare_Norm.py --q 0.9 --N 50 --benefit 5.0 --beta 1.0 --mu-assess1 0.01 --mu-assess2 0.01 --mu-impl 0.00 --mu-percept 0.05 
"""

import argparse
from pathlib import Path
from utils import dumps_json_arg, resolve_build_exe, run_json_command

PRG_EXE = resolve_build_exe("inspect_PrivRepGame")
EPRG_EXE = resolve_build_exe("inspect_EvolPrivRepGame")

# Named norms to evaluate. Recognized by the C++ parser (Norm::ConstructFromName).
LABELS = [
    "L1", "L1-IS",
    "L1v", "L1v-IS",
    "L2", "L2-IS",
    "L2v", "L2v-IS",
    "L3", "L3-IS",
    "L4", "L4-IS",
    "L5", "L5-IS",
    "L6", "L6-IS",
    "L7", "L7-IS",
    "L8", "L8-IS",
]

def run(exe: Path, args: list[str]) -> dict | None:
    try:
        return run_json_command(exe, args)
    except RuntimeError:
        return None

def pick_swcl_obj(obj: dict):
    v = obj.get("SystemWideCooperationLevel")
    return None if v is None else float(v)

def pick_invasion_bcs_obj(obj: dict):
    inv = obj.get("Invasion") or {}
    bc_max = inv.get("bc_max")
    bc_min = inv.get("bc_min")
    return (None if bc_max is None else float(bc_max),
            None if bc_min is None else float(bc_min))

def pick_eq_pop_str_obj(obj: dict):
    ep = obj.get("equilibrium_population")
    if isinstance(ep, list) and len(ep) == 2:
        a, b = ep
        a = "N/A" if a is None else f"{float(a):.6g}"
        b = "N/A" if b is None else f"{float(b):.6g}"
        return f"{a},{b}"
    return "N/A"

def pick_eq3_obj(obj: dict):
    eq = obj.get("eq")
    if isinstance(eq, list) and len(eq) >= 3:
        return tuple(float(eq[i]) if eq[i] is not None else None for i in range(3))
    return (None, None, None)

def fmt(v): return "N/A" if v is None else f"{v:.6g}"

def print_table(rows):
    headers = [
        "Norm",
        "SWCL",
        "AllC_bc_max","AllC_bc_min",
        "Ln_AllC_eq_pop",
        "AllD_bc_max","AllD_bc_min",
        "Ln_AllD_eq_pop",
        "Ln_AllC_AllD_eq_pop",
    ]
    colw = [len(h) for h in headers]
    for r in rows:
        colw[0] = max(colw[0], len(r["Norm"]))
        colw[1] = max(colw[1], len(fmt(r["SWCL"])))
        colw[2] = max(colw[2], len(fmt(r["AllC_bc_max"])))
        colw[3] = max(colw[3], len(fmt(r["AllC_bc_min"])))
        colw[4] = max(colw[4], len(r["Ln_AllC_eq_pop"]))
        colw[5] = max(colw[5], len(fmt(r["AllD_bc_max"])))
        colw[6] = max(colw[6], len(fmt(r["AllD_bc_min"])))
        colw[7] = max(colw[7], len(r["Ln_AllD_eq_pop"]))
        colw[8] = max(colw[8], len(r["Ln_AllC_AllD_eq_pop"]))

    def line_from(values):
        out = []
        for i, v in enumerate(values):
            out.append(str(v).ljust(colw[i]) if i==0 else str(v).rjust(colw[i]))
        return "  ".join(out)

    print(line_from(headers))
    print(line_from(["-"*w for w in colw]))
    for r in rows:
        print(line_from([
            r["Norm"],
            fmt(r["SWCL"]),
            fmt(r["AllC_bc_max"]), fmt(r["AllC_bc_min"]),
            r["Ln_AllC_eq_pop"],
            fmt(r["AllD_bc_max"]), fmt(r["AllD_bc_min"]),
            r["Ln_AllD_eq_pop"],
            r["Ln_AllC_AllD_eq_pop"],
        ]))

def print_pair_eqpop_table(rows):
    headers = ["Pair", "eq_pop"]
    w0 = max(len(headers[0]), *(len(r["Pair"]) for r in rows)) if rows else len(headers[0])
    w1 = max(len(headers[1]), *(len(r["eq_pop"]) for r in rows)) if rows else len(headers[1])

    def line(l, r):
        return f"{l.ljust(w0)}  {r.rjust(w1)}"

    print()
    print(line(headers[0], headers[1]))
    print(line("-"*w0, "-"*w1))
    for r in rows:
        print(line(r["Pair"], r["eq_pop"]))


def build_prg_params(args) -> dict:
    """
    Parameters for inspect_PrivRepGame (-j)
    Keys must match inspect_PrivRepGame.cpp's default set:
      t_init, t_measure, q, mu_impl, mu_percept, mu_assess1, mu_assess2, _seed
    """
    return {
        "t_init":    int(args.t_init),
        "t_measure": int(args.t_measure),
        "q":         float(args.q),
        "mu_impl":   float(args.mu_impl),
        "mu_percept":float(args.mu_percept),
        "mu_assess1":float(args.mu_assess1),
        "mu_assess2":float(args.mu_assess2),
        "_seed":     int(args.seed),
    }

def build_eprg_params(args) -> dict:
    """
    Parameters for inspect_EvolPrivRepGame (-j)
    EvolPrivRepGame::Parameters + optional benefit/beta.
    """
    j = {
        "N":          int(args.N),
        "t_init":     int(args.t_init),
        "t_measure":  int(args.t_measure),
        "q":          float(args.q),
        "mu_impl":    float(args.mu_impl),
        "mu_percept": float(args.mu_percept),
        "mu_assess1": float(args.mu_assess1),
        "mu_assess2": float(args.mu_assess2),
        "_seed":      int(args.seed),
        "benefit":    float(args.benefit),
        "beta":       float(args.beta),
    }
    return j


def main():
    parser = argparse.ArgumentParser(description="Compare norms with customizable error/observation parameters.")
    # --- shared sim parameters ---
    parser.add_argument("--t-init", type=int, default=1000, help="initialization steps (default: 1000)")
    parser.add_argument("--t-measure", type=int, default=1000, help="measurement steps (default: 1000)")
    parser.add_argument("--q", type=float, default=1.0, help="observation probability q (default: 1.0)")
    parser.add_argument("--mu-impl", type=float, default=0.0, help="implementation error (default: 0.0)")
    parser.add_argument("--mu-percept", type=float, default=0.0, help="perception error (default: 0.0)")
    parser.add_argument("--mu-assess1", type=float, default=0.05, help="assessment error 1 (default: 0.05)")
    parser.add_argument("--mu-assess2", type=float, default=0.0, help="assessment error 2 (default: 0.0)")
    parser.add_argument("--seed", type=int, default=123456789, help="RNG seed (default: 123456789)")

    # --- sizes / evolutionary-specific ---
    parser.add_argument("--N", type=int, default=30, help="population size for evolutionary game (EPRG) (default: 30)")
    parser.add_argument("--benefit", type=float, default=5.0, help="benefit b (default: 5.0)")
    parser.add_argument("--beta", type=float, default=1.0, help="selection strength beta (default: 1.0)")

    # --- resident/mutant sizes for PRG single/mutant runs ---
    parser.add_argument("--Nprg", type=int, default=50, help="population size used for PRG monomorphic runs (default: 50)")
    parser.add_argument("--mutant", type=int, default=1, help="mutant count in invasion checks (default: 1)")

    args = parser.parse_args()

    # Check executables
    # Build JSON payloads (passed inline to -j)
    prg_j = dumps_json_arg(build_prg_params(args))
    eprg_j = dumps_json_arg(build_eprg_params(args))

    labels = list(LABELS)
    rows = []
    for i, label in enumerate(labels, 1):
        norm_str = label
        print(f"[{i}/{len(labels)}] {label} ...")

        # Monomorphic SWCL with PRG (size = Nprg)
        out1 = run(PRG_EXE,  ["-j", prg_j, norm_str, str(args.Nprg)])
        swcl = pick_swcl_obj(out1) if out1 else None

        # Invasion analysis vs AllC (resident size = Nprg-1, mutant = mutant)
        out2 = run(PRG_EXE,  ["-j", prg_j, norm_str, str(args.Nprg-args.mutant), "AllC", str(args.mutant)])
        bcmax_c, bcmin_c = pick_invasion_bcs_obj(out2) if out2 else (None, None)

        # Equilibrium population (label vs AllC) with EPRG
        out3 = run(EPRG_EXE, ["-j", eprg_j, norm_str, "AllC"])
        eqpop_c = pick_eq_pop_str_obj(out3) if out3 else "N/A"

        # Invasion analysis vs AllD
        out4 = run(PRG_EXE,  ["-j", prg_j, norm_str, str(args.Nprg-args.mutant), "AllD", str(args.mutant)])
        bcmax_d, bcmin_d = pick_invasion_bcs_obj(out4) if out4 else (None, None)

        # Equilibrium population (label vs AllD) with EPRG
        out5 = run(EPRG_EXE, ["-j", eprg_j, norm_str, "AllD"])
        eqpop_d = pick_eq_pop_str_obj(out5) if out5 else "N/A"

        # 3-species equilibrium (label + AllC + AllD) with EPRG
        out6 = run(EPRG_EXE, ["-j", eprg_j, norm_str])
        eq1, eq2, eq3 = pick_eq3_obj(out6) if out6 else (None, None, None)
        eq_combo = ",".join([fmt(eq1), fmt(eq2), fmt(eq3)])

        rows.append({
            "Norm": label,
            "SWCL": swcl,
            "AllC_bc_max": bcmax_c, "AllC_bc_min": bcmin_c,
            "Ln_AllC_eq_pop": eqpop_c,
            "AllD_bc_max": bcmax_d, "AllD_bc_min": bcmin_d,
            "Ln_AllD_eq_pop": eqpop_d,
            "Ln_AllC_AllD_eq_pop": eq_combo,
        })

    print()
    print_table(rows)

    # Pairwise focal vs focal-IS equilibrium populations (EPRG)
    pair_rows = []
    for k in range(1, 8+1):
        a = f"L{k}"
        b = f"L{k}-IS"
        pair_label = f"{a} vs. {b}"
        out = run(EPRG_EXE, ["-j", eprg_j, a, b])
        eq_pop = pick_eq_pop_str_obj(out) if out else "N/A"
        pair_rows.append({"Pair": pair_label, "eq_pop": eq_pop})

    for a, b in [("L1v", "L1v-IS"), ("L2v", "L2v-IS")]:
        pair_label = f"{a} vs. {b}"
        out = run(EPRG_EXE, ["-j", eprg_j, a, b])
        eq_pop = pick_eq_pop_str_obj(out) if out else "N/A"
        pair_rows.append({"Pair": pair_label, "eq_pop": eq_pop})

    print_pair_eqpop_table(pair_rows)


if __name__ == "__main__":
    main()
