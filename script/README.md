# Script Guide

This directory contains plotting, post-processing, and sweep helpers for the C++ simulations.

## Scope

The scripts fall into two groups:

- scripts that read precomputed TSV or PDF files from `script/output/` and `script/figures/`
- scripts that call compiled executables such as `inspect_PrivRepGame`, `inspect_EvolPrivRepGame`, or `main_RecoveryAnalysis`

Many of the older plotting scripts use relative paths such as `output/...` and `figures/...`. In practice, run those scripts from the `script/` directory unless noted otherwise.

## Python requirements

Install dependencies from the repository root:

```bash
python -m pip install -r script/requirements.txt
```

Some figure-composition scripts also require `pdf2image`, which in turn requires Poppler.

macOS:

```bash
brew install poppler
```

## Build requirements

Several scripts expect compiled binaries in `cmake-build-release/`. Build them from the repository root:

```bash
cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release
cmake --build cmake-build-release -j
```

The main executable dependencies are:

- `cmake-build-release/main_SweepR2`
- `cmake-build-release/inspect_PrivRepGame`
- `cmake-build-release/inspect_EvolPrivRepGame`
- `cmake-build-release/main_RecoveryAnalysis`

## Typical workflow

If you want the publication-style sweep figures, the usual order is:

1. generate `R2_sweep_*.tsv`
2. create individual plots from those TSV files
3. combine the generated PDFs into multi-panel figures

The commands below assume you start from the repository root.

## 1. Generate sweep tables

`run_sweepR2.sh` calls `main_SweepR2` for a predefined set of norms and writes TSV files to `script/output/`.

```bash
cd script
bash run_sweepR2.sh
```

Expected outputs include:

- `script/output/R2_sweep_L1.tsv`
- `script/output/R2_sweep_L1v.tsv`
- `script/output/R2_sweep_L2.tsv`
- `script/output/R2_sweep_L2v.tsv`
- `script/output/R2_sweep_L3.tsv` through `script/output/R2_sweep_L8.tsv`

## 2. Create individual figures

The following scripts are primarily notebook-style scripts with `#%%` cells. They are easiest to run from `script/` in VS Code interactive mode, or as plain Python scripts after editing the parameter cell near the bottom.

```bash
cd script
python plot_rr_sweep.py
python plot_rr_sweep_bcs.py
python plot_image_matrix_mono.py
python plot_pc_bcrange.py
python plot_triadic_competition.py
```

Representative outputs:

- `script/figures/rr_sweep_<norm>.pdf`
- `script/figures/rr_sweep_bcs_<norm>.pdf`
- `script/figures/image_matrix_mono_<norm>_mono.pdf`
- `script/figures/pc_<norm>_vs_<norm>-IS.pdf`
- `script/figures/bc_range_<norm>_vs_<norm>-IS.pdf`
- `script/figures/triad_<norm>.pdf`

### Notes by script

- `plot_rr_sweep.py`
  - reads `script/output/R2_sweep_<norm>.tsv`
  - plots self-cooperation level vs equilibrium fraction
- `plot_rr_sweep_bcs.py`
  - reads `script/output/R2_sweep_<norm>.tsv`
  - plots self-cooperation level vs lower `b/c` threshold
- `plot_image_matrix_mono.py`
  - calls `inspect_PrivRepGame -g`
  - writes `image_matrix_mono_*.pdf`
- `plot_pc_bcrange.py`
  - calls `inspect_PrivRepGame`
  - compares a base norm and its `-IS` variant
- `plot_triadic_competition.py`
  - calls `inspect_EvolPrivRepGame`
  - writes triadic competition diagrams

## 3. Combine figures

These scripts assemble previously generated PDFs into publication-style panels.

```bash
python script/combine_rr_sweep_figures.py
python script/combine_rr_sweep_bcs_figures.py
python script/combine_image_pc_bcrange.py
python script/combine_triad_figures.py
```

Outputs are written under `script/figures/`:

- `combined_rr_sweep.pdf`
- `combined_rr_sweep_others.pdf`
- `combined_rr_sweep_bcs.pdf`
- `combined_rr_sweep_bcs_others.pdf`
- `combined_image_pc_bcrange.pdf`
- `combined_triads.pdf`
- `combined_triads_others.pdf`

## Other utilities

### `compare_Norm.py`

CLI tool for comparing norms with configurable simulation parameters. It calls both `inspect_PrivRepGame` and `inspect_EvolPrivRepGame`.

Run `python script/compare_Norm.py --help` for options.

### `plot_recovery_time_vs_N.py`

Sweeps population size and calls `main_RecoveryAnalysis`. This script is useful for recovery-time experiments rather than the main figure pipeline.

### `plot_resident_mutant_payoff.py`

CLI tool that plots resident and mutant payoffs as the mutant fraction changes.

Example:

```bash
python script/plot_resident_mutant_payoff.py \
  --resident L6-IS \
  --mutant AllD \
  --benefit 5 \
  --cost 1 \
  --N 50 \
  --points 51 \
  --build-dir cmake-build-release \
  --params '{"t_init":1000,"t_measure":1000,"q":0.9,"mu_assess1":0.01,"mu_assess2":0.01,"mu_impl":0.0,"mu_percept":0.0,"_seed":123456789}' \
  --save \
  --format pdf \
  --no-show
```

## Directory conventions

Typical inputs and outputs in this directory:

```text
script/
├── output/
│   └── R2_sweep_*.tsv
├── figures/
│   ├── rr_sweep_*.pdf
│   ├── rr_sweep_bcs_*.pdf
│   ├── image_matrix_mono_*.pdf
│   ├── pc_*_vs_*.pdf
│   ├── bc_range_*_vs_*.pdf
│   ├── triad_*.pdf
│   └── combined_*.pdf
└── image.txt
```

`image.txt` is a transient output produced by `inspect_PrivRepGame -g` and may be overwritten.

## Caveats

- Several scripts are parameterized by variables in the source rather than command-line flags.
- Some scripts assume the current working directory is `script/`.
- Most plotting scripts do not validate missing intermediate files beyond simple existence checks.
- Generated PDFs and TSVs are outputs, not authoritative inputs.
