#!/usr/bin/env python3
"""
Sweep recipient assessment rule (Rr) while keeping donor assessment (Rd) and action rule (P) fixed.

For each Rr in [0..255], runs inspect_EvolPrivRepGame in single-norm mode and
records eq_cooperation_level (and self_cooperation_level) to a TSV for later plotting.

Accepted base norm formats (same as executables):
  - Norm name: AllC, L3, S12, GSCO-5.0, etc.
  - Decimal/hex ID: 857181, 0xd145d
  - Triplet: Rd-Rr-P (e.g., 128-132-2)
  - 20-number serialization: c1 c2 c3 c4 g1..g8 r1..r8

Usage examples:
  python script/sweep_rr.py --norm L3 --out results_tables/rr_sweep_L3.tsv
  python script/sweep_rr.py --norm 128-132-2 --build-dir cmake-build-release
  python script/sweep_rr.py --norm S16 --params '{"benefit":5,"beta":1,"N":30}'
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
  parser = argparse.ArgumentParser(description="Sweep Rr while keeping Rd and P fixed.")
  parser.add_argument("--norm", required=True, help="Base norm string (name/ID/0xHEX/Rd-Rr-P/20 nums)")
  parser.add_argument("--build-dir", default="cmake-build-release", help="CMake build dir with executables")
  parser.add_argument("--params", default=None, help="JSON string or path to JSON file for -j params (optional)")
  parser.add_argument("--out", default=None, help="Output TSV path (defaults to results_tables/rr_sweep_<rd>_<p>.tsv)")
  parser.add_argument("--start", type=int, default=0, help="Start Rr id (inclusive)")
  parser.add_argument("--end", type=int, default=255, help="End Rr id (inclusive)")
  args = parser.parse_args()

  build_dir = args.build_dir
  inspect_norm = os.path.join(build_dir, "inspect_Norm")
  inspect_evo = os.path.join(build_dir, "inspect_EvolPrivRepGame")
  if not os.path.exists(inspect_evo):
    print(f"Error: executable not found: {inspect_evo}", file=sys.stderr)
    sys.exit(1)
  if not os.path.exists(inspect_norm):
    print(f"Error: executable not found: {inspect_norm}", file=sys.stderr)
    sys.exit(1)

  # Prepare params for -j
  j_arg = None
  if args.params:
    if os.path.exists(args.params):
      with open(args.params) as f:
        j_arg = f.read()
    else:
      j_arg = args.params

  # Determine fixed Rd and P
  rd, p = parse_rd_p(args.norm, inspect_norm)

  # Output path
  if args.out:
    out_path = args.out
  else:
    os.makedirs("results_tables", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join("results_tables", f"rr_sweep_rd{rd}_p{p}_{ts}.tsv")

  # Write header
  with open(out_path, "w") as fout:
    meta = {
      "rd": rd,
      "p": p,
      "base_norm": args.norm,
      "start_rr": args.start,
      "end_rr": args.end,
      "params": json.loads(j_arg) if j_arg else None,
    }
    fout.write(f"# sweep_rr meta: {json.dumps(meta)}\n")
    fout.write("# rr\teq_coop\tself_coop\teq[0]\teq[1]\teq[2]\n")

  # Sweep Rr
  for rr in range(args.start, args.end + 1):
    norm_str = f"{rd}-{rr}-{p}"
    cmd = [inspect_evo]
    if j_arg:
      cmd += ["-j", j_arg]
    cmd += [norm_str]
    code, out, err = run(cmd)
    if code != 0:
      print(f"warn: rr={rr} failed: {err.strip()}", file=sys.stderr)
      continue
    try:
      data = json.loads(out)
    except json.JSONDecodeError as e:
      print(f"warn: rr={rr} invalid JSON: {e}", file=sys.stderr)
      continue

    eq_coop = data.get("eq_cooperation_level")
    self_coop = data.get("self_cooperation_level")
    eq_vec = data.get("eq")
    with open(out_path, "a") as fout:
      fout.write(f"{rr}\t{eq_coop}\t{self_coop}\t{eq_vec[0]}\t{eq_vec[1]}\t{eq_vec[2]}\n")

  print(f"Wrote: {out_path}")


if __name__ == "__main__":
  main()
