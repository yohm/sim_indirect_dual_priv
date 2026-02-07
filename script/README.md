# Figure Generation Pipeline

This document describes the workflow for generating individual figures and combining them into multi-panel figures for publication.

## Prerequisites

- Python 3.x with required packages: `matplotlib`, `pdf2image`, `numpy`
- C++ executable: `inspect_PrivRepGame` (built in `cmake-build-release/`)
- Input data files in `output/` directory: `R2_sweep_*.tsv`

## Step-by-Step Workflow

### 0. Generate Input Data (if not already available)

Before generating figures, you need to run simulations to generate the TSV data files.

```bash
# Generate R2_sweep data for all norms
bash run_sweepR2.sh
```

**Output:** `output/R2_sweep_{norm}.tsv` for each norm (L1, L1v, L2, L2v, L3, L4, L5, L6, L7, L8)

**Note:** This script runs `main_SweepR2` executable for each norm with predefined parameters (N=50, mutation rates=0.02, etc.). This may take some time depending on your system.

---

### 1. Generate Individual Figures

#### 1.1 RR Sweep Figures (Equilibrium Fraction)
Generate scatter plots showing self-cooperation level vs equilibrium fraction for each norm.

```bash
# Edit the norm parameter in plot_rr_sweep.py, then run:
python plot_rr_sweep.py
```

**Output:** `figures/rr_sweep_{norm}.pdf` for each norm (L1, L1v, L2, L2v, L3, L4, L5, L6, L7, L8)

**Note:** Run the script once, which will generate all norms automatically. Modify `norm = "L6"` in the parameters cell if you want to regenerate a specific norm.

---

#### 1.2 RR Sweep B/C Range Figures
Generate scatter plots showing self-cooperation level vs minimum b/c ratio.

```bash
python plot_rr_sweep_bcs.py
```

**Output:** `figures/rr_sweep_bcs_{norm}.pdf` for each norm

---

#### 1.3 Image Matrix Figures
Generate monomorphic image matrices showing cooperation patterns.

```bash
python plot_image_matrix_mono.py
```

**Output:** `figures/image_matrix_mono_{norm}_mono.pdf` for each norm and variant (e.g., L6, L6-IS)

---

#### 1.4 PC and B/C Range Comparison Figures
Generate bar charts and range plots comparing base norms with their IS variants.

```bash
python plot_pc_bcrange.py
```

**Output:** 
- `figures/pc_{norm}_vs_{norm}-IS.pdf` (self-cooperation level comparison)
- `figures/bc_range_{norm}_vs_{norm}-IS.pdf` (stable b/c range comparison)

---

#### 1.5 Triad Figures
Generate triadic competition analysis figures.

```bash
python plot_triadic_competition.py
```

**Output:** `figures/triad_{norm}.pdf` for each norm

---

### 2. Combine Figures into Multi-Panel Layouts

#### 2.1 Combined RR Sweep Figures

```bash
python combine_rr_sweep_figures.py
```

**Output:**
- `figures/combined_rr_sweep.pdf` - Main figure with L6, L8, L5, L3 (1 row × 4 columns)
- `figures/combined_rr_sweep_others.pdf` - Other norms: L1v, L2v, L4, L7, L1, L2 (2 rows × 4 columns with legend)

**Features:**
- Left columns are cropped to remove redundant y-axis labels
- Legend displayed in the empty panel (bottom row, 3rd column)

---

#### 2.2 Combined RR Sweep B/C Range Figures

```bash
python combine_rr_sweep_bcs_figures.py
```

**Output:**
- `figures/combined_rr_sweep_bcs.pdf` - Main figure with L6, L8, L5, L3
- `figures/combined_rr_sweep_bcs_others.pdf` - Other norms with legend

**Features:** Same layout as combined_rr_sweep figures

---

#### 2.3 Combined Image Matrix + PC + B/C Range Figures

```bash
python combine_image_pc_bcrange.py
```

**Output:**
- `figures/combined_image_pc_bcrange.pdf` - 4 rows × 4 columns layout

**Layout:**
Each row represents a norm (L6, L8, L5, L3) with:
- Column 1: Image matrix (base norm)
- Column 2: Image matrix (IS variant)
- Column 3: Self-cooperation level comparison
- Column 4: Stable b/c range comparison

**Features:**
- Row labels on the left indicating norm name and type (e.g., "L6\n(Type III)")
- Column labels at the top:
  - "image matrix" spanning columns 1-2, with "-base" and "-IS" sub-labels
  - "self-cooperation\nlevel" for column 3
  - "stable b/c\nrange" for column 4
- Custom column widths (left 2 columns narrower: 0.75, right 2 columns: 1.0)
- Custom spacing (hspace=0.15, wspace=0.05)
- Right 2 columns are cropped to reduce gap between them

---

#### 2.4 Combined Triad Figures

```bash
python combine_triad_figures.py
```

**Output:**
- `figures/combined_triads.pdf` - Main norms: L6, L6-IS, L8, L8-IS, L5, L5-IS, L3, L3-IS (2 rows × 4 columns)
- `figures/combined_triads_others.pdf` - Other norms (3 rows × 4 columns)

---

## Output Directory Structure

```
script/
├── figures/
│   ├── rr_sweep_*.pdf                    # Individual RR sweep figures
│   ├── rr_sweep_bcs_*.pdf                # Individual B/C range figures
│   ├── image_matrix_mono_*.pdf           # Individual image matrices
│   ├── pc_*_vs_*.pdf                     # PC comparison figures
│   ├── bc_range_*_vs_*.pdf               # B/C range comparison figures
│   ├── triad_*.pdf                       # Individual triad figures
│   ├── combined_rr_sweep.pdf             # Combined RR sweep (main)
│   ├── combined_rr_sweep_others.pdf      # Combined RR sweep (others)
│   ├── combined_rr_sweep_bcs.pdf         # Combined B/C range (main)
│   ├── combined_rr_sweep_bcs_others.pdf  # Combined B/C range (others)
│   ├── combined_image_pc_bcrange.pdf     # Combined image+pc+bc
│   ├── combined_triads.pdf               # Combined triads (main)
│   └── combined_triads_others.pdf        # Combined triads (others)
```

## Notes

- All scripts use VSCode interactive mode (cells starting with `#%%`)
- Figures are saved with DPI=150 for reasonable file sizes
- PDF metadata is stripped for cleaner output
- The `pdf2image` library requires `poppler` to be installed:
  - macOS: `brew install poppler`
  - Ubuntu: `apt-get install poppler-utils`

## Customization

### Adjusting Layout Parameters

In combine scripts, you can adjust:
- `figsize`: Overall figure dimensions
- `dpi`: Resolution (higher = larger file size)
- `width_ratios`: Relative column widths in GridSpec
- `hspace`, `wspace`: Vertical and horizontal spacing between subplots
- Cropping percentages for trimming images

### Font Sizes

Default font sizes used:
- Main column/row labels: 32pt
- Sub-labels: 28pt
- Panel labels (a, b, c...): 20pt
- Axis labels in individual plots: 30pt
- Tick labels: 20pt
- Legend text: 24pt
