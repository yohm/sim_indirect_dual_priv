"""
Usage (from repo root):
  uv venv .venv && source .venv/bin/activate
  uv pip install -r script/requirements.txt
  cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release && cmake --build cmake-build-release -j
  python script/compare_Norm.py

This script compares a fixed set of named norms using the compiled
inspect_PrivRepGame and inspect_EvolPrivRepGame executables.

Notes:
- Norm strings are passed by name (e.g., "L1", "L1-IS", "AllC").
- Named norms like "Lk-IS" are supported by the C++ parser (Norm::ConstructFromName).
"""

import subprocess, json, sys, shutil
from pathlib import Path

# Resolve repo root and executables regardless of CWD
ROOT = Path(__file__).resolve().parents[1]
PRG_EXE  = str(ROOT / "cmake-build-release" / "inspect_PrivRepGame")
EPRG_EXE = str(ROOT / "cmake-build-release" / "inspect_EvolPrivRepGame")

# Named norms to evaluate. These are recognized by the C++ parser.
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

def run(exe: str, args: list[str]) -> str | None:
    try:
        res = subprocess.run([exe] + args, capture_output=True, text=True, check=True)
        return res.stdout
    except FileNotFoundError:
        print(f"[ERROR] Executable not found: {exe}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Execution failed: {exe} {args}\n{e.stdout}\n{e.stderr}", file=sys.stderr)
        return None

def parse_obj(text: str) -> dict:
    return json.loads(text)

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

def main():
    for exe in (PRG_EXE, EPRG_EXE):
        if not (Path(exe).exists() or shutil.which(exe)):
            print(f"[ERROR] Executable not found: {exe}", file=sys.stderr); sys.exit(1)

    labels = list(LABELS)
    rows = []
    for i, label in enumerate(labels, 1):
        norm_str = label
        print(f"[{i}/{len(labels)}] {label} ...")

        out1 = run(PRG_EXE,  [norm_str, "50"])
        swcl = pick_swcl_obj(parse_obj(out1)) if out1 else None

        out2 = run(PRG_EXE,  [norm_str, "49", "AllC", "1"])
        bcmax_c, bcmin_c = pick_invasion_bcs_obj(parse_obj(out2)) if out2 else (None, None)

        out3 = run(EPRG_EXE, [norm_str, "AllC"])
        eqpop_c = pick_eq_pop_str_obj(parse_obj(out3)) if out3 else "N/A"

        out4 = run(PRG_EXE,  [norm_str, "49", "AllD", "1"])
        bcmax_d, bcmin_d = pick_invasion_bcs_obj(parse_obj(out4)) if out4 else (None, None)

        out5 = run(EPRG_EXE, [norm_str, "AllD"])
        eqpop_d = pick_eq_pop_str_obj(parse_obj(out5)) if out5 else "N/A"

        out6 = run(EPRG_EXE, [norm_str])                    
        eq1, eq2, eq3 = pick_eq3_obj(parse_obj(out6)) if out6 else (None, None, None)
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

    pair_rows = []
    for k in range(1, 9):
        a = f"L{k}"
        b = f"L{k}-IS"
        pair_label = f"{a} vs. {b}"
        out = run(EPRG_EXE, [a, b])
        eq_pop = pick_eq_pop_str_obj(parse_obj(out)) if out else "N/A"
        pair_rows.append({"Pair": pair_label, "eq_pop": eq_pop})

    # Add variant pairs where available
    for a, b in [("L1v", "L1v-IS"), ("L2v", "L2v-IS")]:
        pair_label = f"{a} vs. {b}"
        out = run(EPRG_EXE, [a, b])
        eq_pop = pick_eq_pop_str_obj(parse_obj(out)) if out else "N/A"
        pair_rows.append({"Pair": pair_label, "eq_pop": eq_pop})

    print_pair_eqpop_table(pair_rows)

if __name__ == "__main__":
    main()
