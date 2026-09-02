# Indirect reciprocity with dual private assessment

Source code for Tham, Y. J., Hilbe, C., & Murase, Y. (2026). Indirect reciprocity with dual private assessment. _Proceedings of the National Academy of Sciences, 123_(35), e2624656123. https://doi.org/10.1073/pnas.2624656123 

## Overview

This repository provides:

- core C++ implementations of norms and reputation-game dynamics
- inspection binaries for checking norm properties and simulation outputs
- unit tests with GoogleTest
- Python scripts for plotting and post-processing results

The main C++ sources live at the repository root. Plotting and analysis helpers are in `script/`.

## Requirements

### C++ build

- CMake 3.7 or newer
- C++17 compiler
- OpenMP
- Eigen3
- nlohmann_json
- MPI

GoogleTest is fetched automatically by CMake during configure.

### macOS example

```bash
brew install cmake libomp eigen nlohmann-json open-mpi
```

## Build

Clone with submodules, then configure and build into `cmake-build-release/`:

```bash
git clone --recursive git@github.com:yohm/sim_indirect_dual_priv.git
cd sim_indirect_dual_priv
cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release
cmake --build cmake-build-release -j
```

On macOS, `CMakeLists.txt` will automatically use Homebrew `libomp` for AppleClang if it is installed in the default Homebrew location.

## Test

Run all unit tests with:

```bash
ctest --test-dir cmake-build-release --output-on-failure
```

You can also run a single test binary directly, for example:

```bash
./cmake-build-release/test_Norm
```

## Repository layout

```text
.
├── CMakeLists.txt
├── *.hpp / inspect_*.cpp / main_*.cpp / test_*.cpp
├── icecream-cpp/
└── script/
```

## Norm input format

The inspection and simulation binaries accept the same norm string formats:

- norm name, for example `AllC`, `L3`, `S12`, `S12v`, `ImageScoring`
- decimal ID or hex ID, for example `857181`, `0xd145d`
- deterministic triplet `Rd-Rr-P`, for example `128-132-2`
- serialized values, for example `c1 c2 c3 c4 g1 ... g8 r1 ... r8`

`inspect_Norm` and `inspect_PublicRepGame` also support `-s` to swap good and bad labels.

## Main executables

### `inspect_Norm`

Prints a human-readable description of a norm. If multiple norms are given, it prints comparisons.

```bash
./cmake-build-release/inspect_Norm L3
./cmake-build-release/inspect_Norm L3 L6
./cmake-build-release/inspect_Norm -s 128-132-2
```

### `inspect_PublicRepGame`

Evaluates a norm under the public assessment model and prints stability-related quantities.

```bash
./cmake-build-release/inspect_PublicRepGame L3
```

### `inspect_PrivRepGame`

Runs the private assessment simulation for one or more resident populations. Progress and parameters are written to `stderr`; structured results are written as JSON to `stdout`.

```bash
./cmake-build-release/inspect_PrivRepGame L3 50
./cmake-build-release/inspect_PrivRepGame L1 30 L2 30
./cmake-build-release/inspect_PrivRepGame --local-action-mutants L6-IS 50
./cmake-build-release/inspect_PrivRepGame -j '{"t_init":10000,"t_measure":10000}' L1 30 L2 30
```

Options:

- `-j <json|path>`: override simulation parameters
- `-g`: also compute average reputations and write `image.txt`
- `--local-action-mutants <resident> <N>`: evaluate one-mutant `b/c` stability against all action-rule variants of the resident

Default parameters:

```json
{
  "t_init": 1000,
  "t_measure": 1000,
  "q": 1.0,
  "mu_impl": 0.0,
  "mu_percept": 0.0,
  "mu_assess1": 0.05,
  "mu_assess2": 0.0,
  "_seed": 123456789
}
```

### `inspect_EvolPrivRepGame`

Computes evolutionary outcomes under private assessment.

```bash
./cmake-build-release/inspect_EvolPrivRepGame L3
./cmake-build-release/inspect_EvolPrivRepGame --action-mutants L3
./cmake-build-release/inspect_EvolPrivRepGame L1 L2
./cmake-build-release/inspect_EvolPrivRepGame 153-170-10 153-170-5 AllC AllD
./cmake-build-release/inspect_EvolPrivRepGame -j '{"N":50,"benefit":5.0,"beta":1.0}' L3
```

- one norm: returns selection-mutation equilibrium against `AllC` and `AllD`
- `--action-mutants` with one norm: returns the equilibrium among the resident and all deterministic action-rule mutants with the resident assessment rules fixed
- two norms: returns transition probabilities, equilibrium population, and monomorphic cooperation levels
- three or more norms: returns the low-mutation equilibrium for exactly the listed strategy set

When two norms are given, the program also writes `payoffs.dat`.

### `main_RecoveryAnalysis`

Estimates recovery time from a single bad entry in the image matrix.

```bash
./cmake-build-release/main_RecoveryAnalysis L3
./cmake-build-release/main_RecoveryAnalysis -j '{"N":50,"max_t":10000,"num_samples":1000,"_seed":123456789}' L3
```

### `main_SweepR2`

Sweeps the recipient assessment rule `R2` for a base norm and writes a TSV table.

```bash
./cmake-build-release/main_SweepR2 --params '{"base_norm":"L3","N":50,"t_init":1000,"t_measure":1000}' --out R2_sweep_L3.tsv
```

### `main_ExhaustiveSearch`

Sweeps deterministic donor and recipient assessment rules, with the action rule fixed to Discriminator.
By default it evaluates all `R1=0..255` and `R2=0..255` combinations, for 65,536 norms total.
MPI is supported and recommended for full runs.

```bash
mpirun -n 4 ./cmake-build-release/main_ExhaustiveSearch \
  --params '{"N":50,"t_init":1000,"t_measure":1000}' \
  --out R1R2_sweep.tsv
```

For local testing, restrict the rule ranges:

```bash
./cmake-build-release/main_ExhaustiveSearch \
  --params '{"N":10,"t_init":10,"t_measure":20,"q":0.9,"_seed":1}' \
  --rd-start 0 --rd-end 1 \
  --rr-start 0 --rr-end 2 \
  --out R1R2_sweep_test.tsv
```

Output is a TSV with one row per `(R1, R2, Discriminator)` norm. Columns include monomorphic cooperation, invasion thresholds against `AllD` and `AllC`, low-mutation equilibrium cooperation, equilibrium weights for resident/`AllC`/`AllD`, and the corresponding fixation probabilities.
The table also reports the maximum local payoff advantage among behavioral mutants: all deterministic action-rule variants with the resident assessment rules fixed are tested as one-player mutants, using fixed `b/c = 2`.

To sweep action rules as well, add `--sweep-actions`. This evaluates non-trivial deterministic action rules, excludes `AllC`/`AllD`, and skips norms whose good/bad-label swapped counterpart is the canonical representative.
For readability, action-sweep output is written in the good/bad orientation with the larger action-rule ID, so Discriminator-like representatives appear with `Action = 10`.

```bash
mpirun -n 4 ./cmake-build-release/main_ExhaustiveSearch \
  --params '{"N":50,"t_init":1000,"t_measure":1000}' \
  --sweep-actions \
  --out action_sweep.tsv
```

To write only candidate hits, add `--hits-only`. The hit thresholds are `self_coop > 0.8`, `eq0 > 0.95`, and `behavioral_max_advantage_bc2 < 0.02`.

```bash
mpirun -n 4 ./cmake-build-release/main_ExhaustiveSearch \
  --params '{"N":50,"t_init":1000,"t_measure":1000}' \
  --sweep-actions \
  --hits-only \
  --out action_sweep_hits.tsv
```

## Python scripts

Python utilities for plotting and figure assembly are in [`script/README.md`](/Users/murase/work/sim_indirect_dual_priv/script/README.md).

Install dependencies with:

```bash
python -m pip install -r script/requirements.txt
```

Representative scripts:

- `script/plot_rr_sweep.py`
- `script/plot_rr_sweep_bcs.py`
- `script/plot_all_norms.py`
- `script/plot_image_matrix_mono.py`
- `script/plot_triadic_competition.py`
- `script/combine_rr_sweep_figures.py`

## Notes

- Build artifacts should stay in a separate build directory such as `cmake-build-release/`.
- Large generated outputs should not be committed unless they are intended repository artifacts.
