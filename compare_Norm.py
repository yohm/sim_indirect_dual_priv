"""
Usage:
  cd ~/sim_indirect_dual_priv
  python3 compare_Norm.py 
"""

import subprocess, re, json, sys, shutil
from pathlib import Path

PRG_EXE  = "./cmake-build-release/inspect_PrivRepGame"
EPRG_EXE = "./cmake-build-release/inspect_EvolPrivRepGame"

PARAMS = {
    "L1":     "1.00 0.00 1.00 1.00 1.00 0.00 1.00 1.00 1.00 0.00 1.00 0.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00",
    "L1_IS":  "1.00 0.00 1.00 1.00 1.00 0.00 1.00 1.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00",
    "L2":     "1.00 0.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 1.00 0.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00",
    "L2_IS":  "1.00 0.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00",
    "L3":     "1.00 0.00 1.00 0.00 1.00 0.00 1.00 1.00 1.00 0.00 1.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00",
    "L3_IS":  "1.00 0.00 1.00 0.00 1.00 0.00 1.00 1.00 1.00 0.00 1.00 1.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00",
    "L4":     "1.00 0.00 1.00 0.00 1.00 0.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00",
    "L4_IS":  "1.00 0.00 1.00 0.00 1.00 0.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00",
    "L5":     "1.00 0.00 1.00 0.00 1.00 0.00 0.00 1.00 1.00 0.00 1.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00",
    "L5_IS":  "1.00 0.00 1.00 0.00 1.00 0.00 0.00 1.00 1.00 0.00 1.00 1.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00",
    "L6":     "1.00 0.00 1.00 0.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00",
    "L6_IS":  "1.00 0.00 1.00 0.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00",
    "L7":     "1.00 0.00 1.00 0.00 1.00 0.00 1.00 1.00 1.00 0.00 0.00 0.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00",
    "L7_IS":  "1.00 0.00 1.00 0.00 1.00 0.00 1.00 1.00 1.00 0.00 0.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00",
    "L8":     "1.00 0.00 1.00 0.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00 0.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00",
    "L8_IS":  "1.00 0.00 1.00 0.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00",
}

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

def iter_json_blocks(text: str):
    start = None; depth = 0; in_str = False; esc = False
    for i, ch in enumerate(text):
        if ch == '"' and not esc:
            in_str = not in_str
        esc = (ch == '\\' and not esc) if in_str else False
        if in_str: continue
        if ch == '{':
            if depth == 0: start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    chunk = text[start:i+1]
                    try: yield json.loads(chunk)
                    except json.JSONDecodeError: pass
                    start = None

def pick_swcl(text: str):
    for obj in iter_json_blocks(text):
        if "SystemWideCooperationLevel" in obj:
            v = obj["SystemWideCooperationLevel"]
            return None if v is None else float(v)
    return None

def pick_invasion_bcs(text: str):
    bc_max = bc_min = None
    for obj in iter_json_blocks(text):
        inv = obj.get("Invasion")
        if isinstance(inv, dict):
            if "bc_max" in inv and inv["bc_max"] is not None:
                bc_max = float(inv["bc_max"])
            elif "b_c_max" in inv and inv["b_c_max"] is not None:
                bc_max = float(inv["b_c_max"])
            if "bc_min" in inv and inv["bc_min"] is not None:
                bc_min = float(inv["bc_min"])
    return bc_max, bc_min

def pick_eq_pop_str(text: str):
    for obj in iter_json_blocks(text):
        ep = obj.get("equilibrium_population")
        if isinstance(ep, list) and len(ep) == 2:
            a, b = ep
            a = "N/A" if a is None else f"{float(a):.6g}"
            b = "N/A" if b is None else f"{float(b):.6g}"
            return f"{a},{b}"
    return "N/A"

def pick_eq3(text: str):
    for obj in iter_json_blocks(text):
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

    labels = list(PARAMS.keys())
    rows = []
    for i, label in enumerate(labels, 1):
        p = PARAMS[label]
        print(f"[{i}/{len(labels)}] {label} ...")

        out1 = run(PRG_EXE,  [p, "50"])
        swcl = pick_swcl(out1) if out1 else None

        out2 = run(PRG_EXE,  [p, "49", "AllC", "1"])
        bcmax_c, bcmin_c = pick_invasion_bcs(out2) if out2 else (None, None)

        out3 = run(EPRG_EXE, [p, "AllC"])
        eqpop_c = pick_eq_pop_str(out3) if out3 else "N/A"

        out4 = run(PRG_EXE,  [p, "49", "AllD", "1"])
        bcmax_d, bcmin_d = pick_invasion_bcs(out4) if out4 else (None, None)

        out5 = run(EPRG_EXE, [p, "AllD"])
        eqpop_d = pick_eq_pop_str(out5) if out5 else "N/A"

        out6 = run(EPRG_EXE, [p])                    
        eq1, eq2, eq3 = pick_eq3(out6) if out6 else (None, None, None)
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
        b = f"L{k}_IS"
        pair_label = f"{a} vs. {b}"
        if a in PARAMS and b in PARAMS:
            out = run(EPRG_EXE, [PARAMS[a], PARAMS[b]])
            eq_pop = pick_eq_pop_str(out) if out else "N/A"
        else:
            eq_pop = "N/A"
        pair_rows.append({"Pair": pair_label, "eq_pop": eq_pop})

    print_pair_eqpop_table(pair_rows)

if __name__ == "__main__":
    main()