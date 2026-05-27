#!/bin/bash -ex

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

CXX="${CXX:-mpiFCCpx}"
JSON_INCLUDE="${JSON_INCLUDE:-${HOME}/data/sandbox/json/include}"
EIGEN_INCLUDE="${EIGEN_INCLUDE:-${HOME}/data/sandbox/eigen-3.3.7}"
OUT="${OUT}:-${REPO_ROOT}/cmake-build-release/main_ExhaustiveSearch}"

cd "${REPO_ROOT}"

"${CXX}" \
  -std=c++17 \
  -stdlib=libc++ \
  -Nclang \
  -Kfast \
  -Kopenmp \
  -I"${JSON_INCLUDE}" \
  -I"${EIGEN_INCLUDE}" \
  -Iicecream-cpp \
  ${EXTRA_CXXFLAGS:-} \
  -o "${OUT}" \
  main_ExhaustiveSearch.cpp
