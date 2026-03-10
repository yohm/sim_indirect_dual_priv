#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/cmake-build-release"
EXE="${BUILD_DIR}/main_SweepR2"
OUTPUT_DIR="${SCRIPT_DIR}/output"

if [[ ! -x "${EXE}" ]]; then
  echo "[ERROR] executable not found: ${EXE}" >&2
  echo "[INFO] build it first:" >&2
  echo "  cmake -S ${REPO_ROOT} -B ${BUILD_DIR} -DCMAKE_BUILD_TYPE=Release" >&2
  echo "  cmake --build ${BUILD_DIR} -j" >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

# Run for L1 to L8
for norm in L1 L1v L2 L2v L3 L4 L5 L6 L7 L8; do
  echo "[INFO] Running SweepR2 for ${norm}..."
  "${EXE}" \
    --params '{"N":50,"base_norm":"'${norm}'","mu_assess1":0.02,"mu_assess2":0.02,"mu_impl":0.02,"t_init":5000,"t_measure":5000}' \
    --out "${OUTPUT_DIR}/R2_sweep_${norm}.tsv"
  echo "[INFO] Completed ${norm}"
done

echo "[INFO] All SweepR2 runs completed successfully"

# for norm in S1 S2 S3 S4 S5 S6 S7 S8 S9 S10 S11 S12 S13 S14 S15 S16; do
#   echo "[INFO] Running SweepR2 for ${norm}..."
#   "$REPO_ROOT/cmake-build-release/main_SweepR2" \
#     --params '{"N":50,"base_norm":"'${norm}'","mu_assess1":0.02,"mu_assess2":0.02,"mu_impl":0.02,"t_init":5000,"t_measure":5000}' \
#     --out "output/R2_sweep_${norm}.tsv"
#   echo "[INFO] Completed ${norm}"
# done
# 
# echo "[INFO] All SweepR2 runs completed successfully"
