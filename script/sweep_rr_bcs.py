#!/usr/bin/env python3
"""
Sweep recipient assessment rule (Rr) while keeping donor assessment (Rd) and
action rule (P) fixed. For each Rr:

1) Compute monomorphic self-cooperation level via inspect_PrivRepGame.
2) Compute bc_min by introducing a single AllD mutant via inspect_PrivRepGame.
3) Compute bc_max by introducing a single AllC mutant via inspect_PrivRepGame.

Writes a TSV with columns: rr_id, self_coop, bc_min, bc_max

Accepted base norm formats (same as executables):
  - Norm name: L3, L1-IS, S12, GSCO-5.0, etc.
  - Decimal/hex ID: 857181, 0xd145d
  - Triplet: Rd-Rr-P (e.g., 128-132-2)
  - 20-number serialization: c1 c2 c3 c4 g1..g8 r1..r8

Usage examples:
  python script/sweep_rr_bcs.py --norm L3 --out results_tables/rr_bcs_L3.tsv
  python script/sweep_rr_bcs.py --norm 128-132-2 --build-dir cmake-build-release
  python script/sweep_rr_bcs.py --norm S16 --params '{"benefit":5,"beta":1,"N":30}'
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime


def run(cmd, input_text=None):
  res = subprocess.run(cmd, input=input_text, capture_output=True, text=True)
  return res.returncode, res.stdout, res.stderr


def extract_triplet_from_inspect(inspect_output: str):
  # Expect a header line like: Norm: 0x..... ..... [Rd-Rr-P] : Name
  m = re.search(r"\[(\d+)-(\d+)-(\d+)\]", inspect_output)
  if not m:
    return None
  rd, rr, p = map(int, m.groups())
  return rd, rr, p


def parse_rd_p(norm_str: str, inspect_norm_path: str):
  triplet_re = re.compile(r"^(\d+)-(\d+)-(\d+)$")
  m = triplet_re.match(norm_str.strip())
  if m:
    rd = int(m.group(1))
    p = int(m.group(3))
    return rd, p

  # Fall back to calling inspect_Norm and parsing header triplet
  code, out, err = run([inspect_norm_path, norm_str])
  if code != 0:
    raise RuntimeError(f"inspect_Norm failed: {err.strip()}")
  t = extract_triplet_from_inspect(out)
  if not t:
    raise RuntimeError("Failed to extract [Rd-Rr-P] from inspect_Norm output")
  rd, _rr, p = t
  return rd, p


def main():
  parser = argparse.ArgumentParser(description="Sweep Rr; output rr_id, self_coop, bc_min, bc_max.")
  parser.add_argument("--norm", required=True, help="Base norm string (name/ID/0xHEX/Rd-Rr-P/20 nums)")
  parser.add_argument("--build-dir", default="cmake-build-release", help="CMake build dir with executables")
  parser.add_argument("--params", default=None, help="JSON string or path to JSON file for -j params (optional)")
  parser.add_argument("--out", default=None, help="Output TSV path (defaults to results_tables/rr_bcs_<rd>_<p>.tsv)")
  parser.add_argument("--N", type=int, default=50, help="Total population size used in PRG runs (default: 50)")
  parser.add_argument("--start", type=int, default=0, help="Start Rr id (inclusive)")
  parser.add_argument("--end", type=int, default=255, help="End Rr id (inclusive)")
  args = parser.parse_args()

  build_dir = args.build_dir
  inspect_norm = os.path.join(build_dir, "inspect_Norm")
  inspect_prg = os.path.join(build_dir, "inspect_PrivRepGame")
  missing = [p for p in [inspect_prg, inspect_norm] if not os.path.exists(p)]
  if missing:
    print(f"Error: executable(s) not found: {', '.join(missing)}", file=sys.stderr)
    sys.exit(1)

  # Prepare params for -j (passed to inspect_PrivRepGame)
  j_arg = None
  if args.params:
    if os.path.exists(args.params):
      with open(args.params) as f:
        j_arg = f.read()
    else:
      j_arg = args.params

  # Determine fixed Rd and P from the base norm
  rd, p = parse_rd_p(args.norm, inspect_norm)

  # Validate N
  if args.N < 2:
    print("Error: --N must be >= 2", file=sys.stderr)
    sys.exit(1)

  # Output path
  if args.out:
    out_path = args.out
  else:
    os.makedirs("results_tables", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join("results_tables", f"rr_bcs_rd{rd}_p{p}_{ts}.tsv")

  # Write header
  with open(out_path, "w") as fout:
    meta = {
      "rd": rd,
      "p": p,
      "base_norm": args.norm,
      "N": args.N,
      "start_rr": args.start,
      "end_rr": args.end,
      "params": json.loads(j_arg) if j_arg else None,
    }
    fout.write(f"# sweep_rr_bcs meta: {json.dumps(meta)}\n")
    fout.write("# rr\tself_coop\tbc_min(AllD)\tbc_max(AllC)\n")

  # Sweep Rr
  for rr in range(args.start, args.end + 1):
    norm_str = f"{rd}-{rr}-{p}"

    # 1) self_cooperation_level (monomorphic) via inspect_PrivRepGame
    cmd = [inspect_prg]
    if j_arg:
      cmd += ["-j", j_arg]
    cmd += [norm_str, str(args.N)]  # single norm, total size N
    code, out, err = run(cmd)
    if code != 0:
      print(f"warn: rr={rr} prg(self) failed: {err.strip()}", file=sys.stderr)
      continue
    try:
      data = json.loads(out)
    except json.JSONDecodeError as e:
      print(f"warn: rr={rr} prg(self) invalid JSON: {e}", file=sys.stderr)
      continue
    self_coop = data.get("SystemWideCooperationLevel")

    # 2) bc_min with AllD mutant
    cmd = [inspect_prg]
    if j_arg:
      cmd += ["-j", j_arg]
    cmd += [norm_str, str(args.N-1), "AllD", "1"]  # N-1 residents, 1 mutant
    code, out, err = run(cmd)
    bc_min = None
    if code == 0:
      try:
        prg_data = json.loads(out)
        inv = prg_data.get("Invasion") or {}
        bc_min = inv.get("bc_min")
      except json.JSONDecodeError as e:
        print(f"warn: rr={rr} prg(AllD) invalid JSON: {e}", file=sys.stderr)
    else:
      print(f"warn: rr={rr} prg(AllD) failed: {err.strip()}", file=sys.stderr)

    # 3) bc_max with AllC mutant
    cmd = [inspect_prg]
    if j_arg:
      cmd += ["-j", j_arg]
    cmd += [norm_str, str(args.N-1), "AllC", "1"]  # N-1 residents, 1 mutant
    code, out, err = run(cmd)
    bc_max = None
    if code == 0:
      try:
        prg_data = json.loads(out)
        inv = prg_data.get("Invasion") or {}
        bc_max = inv.get("bc_max")
      except json.JSONDecodeError as e:
        print(f"warn: rr={rr} prg(AllC) invalid JSON: {e}", file=sys.stderr)
    else:
      print(f"warn: rr={rr} prg(AllC) failed: {err.strip()}", file=sys.stderr)

    with open(out_path, "a") as fout:
      fout.write(f"{rr}\t{self_coop}\t{bc_min}\t{bc_max}\n")

  print(f"Wrote: {out_path}")


if __name__ == "__main__":
  main()
