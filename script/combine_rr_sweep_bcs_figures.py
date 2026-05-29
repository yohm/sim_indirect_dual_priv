#!/usr/bin/env python3
#%%
"""
Combine rr_sweep_bcs figures into a single multi-panel figure.

Usage:
  VSCode Interactive: Run cells sequentially
"""

#%% Imports
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pdf2image import convert_from_path
from utils import FIGURES_DIR, figure_path

#%% Parameters
figures_dir = FIGURES_DIR
output_path = figure_path("combined_rr_sweep_bcs.pdf")

# Norms to include (order matters)
norms = ["L6", "L8", "L5", "L3"]

# Grid layout: 1 row x 4 columns
nrows, ncols = 1, 4
dpi = 150  # Balanced resolution for smaller file size

#%% Load PDFs and convert to images
print(f"[INFO] Loading {len(norms)} rr_sweep_bcs figures...")
images = []
for norm in norms:
    pdf_path = figures_dir / f"rr_sweep_bcs_{norm}.pdf"
    if not pdf_path.exists():
        print(f"[WARNING] File not found: {pdf_path}")
        images.append(None)
        continue
    
    print(f"[INFO] Converting {pdf_path.name} to image (dpi={dpi})...")
    img = convert_from_path(pdf_path, dpi=dpi)[0]
    images.append(img)

#%% Create combined figure
print(f"[INFO] Creating {nrows}x{ncols} combined figure...")
fig, axes = plt.subplots(nrows, ncols, figsize=(20, 5))

for i, (norm, img) in enumerate(zip(norms, images)):
    row = i // ncols
    col = i % ncols
    ax = axes[col] if nrows == 1 else axes[row, col]
    
    if img is not None:
        ax.imshow(img)
    else:
        ax.text(0.5, 0.5, f"Missing:\n{norm}", 
                ha='center', va='center', fontsize=16)
    
    ax.axis('off')
    # Add panel label
    # ax.text(0.02, 1.05, f"({chr(97 + i)})", transform=ax.transAxes,
    #        fontsize=20, fontweight='bold', va='top', ha='left')

plt.tight_layout(pad=0.5)

#%% Save combined figure
print(f"[INFO] Saving to {output_path}...")
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches='tight', 
            metadata={'Creator': '', 'Producer': '', 'CreationDate': None})
print(f"[INFO] Saved: {output_path}")

#%% All other norms combined figure
print(f"\n[INFO] Creating combined figure for all other norms...")

# All other norms: top row (L1v, L2v, L4, L7), bottom row (L1, L2)
norms_other = ["L1v", "L2v", "L4", "L7", "L1", "L2"]
output_path_other = figure_path("combined_rr_sweep_bcs_others.pdf")

# Grid layout: 2 rows x 4 columns (8 panels total, 2 empty)
nrows_other, ncols_other = 2, 4

print(f"[INFO] Loading {len(norms_other)} rr_sweep_bcs figures...")
images_other = []
for norm in norms_other:
    pdf_path = figures_dir / f"rr_sweep_bcs_{norm}.pdf"
    if not pdf_path.exists():
        print(f"[WARNING] File not found: {pdf_path}")
        images_other.append(None)
        continue
    
    print(f"[INFO] Converting {pdf_path.name} to image (dpi={dpi})...")
    img = convert_from_path(pdf_path, dpi=dpi)[0]
    images_other.append(img)

print(f"[INFO] Creating {nrows_other}x{ncols_other} combined figure...")
fig_other, axes_other = plt.subplots(nrows_other, ncols_other, figsize=(20, 10))

for i, (norm, img) in enumerate(zip(norms_other, images_other)):
    row = i // ncols_other
    col = i % ncols_other
    ax = axes_other[row, col]
    
    if img is not None:
        ax.imshow(img)
    else:
        ax.text(0.5, 0.5, f"Missing:\n{norm}", 
                ha='center', va='center', fontsize=16)
    
    ax.axis('off')
    # Add panel label
    # ax.text(0.02, 1.05, f"({chr(97 + i)})", transform=ax.transAxes,
    #         fontsize=20, fontweight='bold', va='top', ha='left')

# Hide empty panels (last 2 positions)
for i in range(len(norms_other), nrows_other * ncols_other):
    row = i // ncols_other
    col = i % ncols_other
    axes_other[row, col].axis('off')

# Add legend to the panel next to L2 (bottom row, 3rd column)
legend_ax = axes_other[1, 2]
legend_ax.axis('off')

# Create legend elements matching plot_rr_sweep_bcs.py
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='base',
           markerfacecolor='navy', markersize=15),
    Line2D([0], [0], marker='s', color='w', label='RIS',
           markerfacecolor='darkorange', markersize=15),
    Line2D([0], [0], marker='^', color='w', label='GDT',
           markerfacecolor='purple', markersize=15),
    Line2D([0], [0], marker='D', color='w', label='ALLG',
           markerfacecolor='#009E73', markersize=11)
]
legend_ax.legend(handles=legend_elements, loc='center left', frameon=True, fontsize=24,
                labelspacing=0.3, handletextpad=0.5, borderpad=0.4)

plt.tight_layout(pad=0.5)

print(f"[INFO] Saving to {output_path_other}...")
fig_other.savefig(output_path_other, dpi=150, bbox_inches='tight', 
                  metadata={'Creator': '', 'Producer': '', 'CreationDate': None})
print(f"[INFO] Saved: {output_path_other}")

#%% Secondary sixteen combined figure
print(f"\n[INFO] Creating combined figure for secondary sixteen norms...")

secondary_norms = [f"S{i}" for i in range(1, 17)]
output_path_secondary = figure_path("combined_rr_sweep_bcs_secondary_sixteen.pdf")

# Grid layout: 4 rows x 4 columns
nrows_secondary, ncols_secondary = 4, 4

print(f"[INFO] Loading {len(secondary_norms)} rr_sweep_bcs figures...")
secondary_images = []
for norm in secondary_norms:
    pdf_path = figures_dir / f"rr_sweep_bcs_{norm}.pdf"
    if not pdf_path.exists():
        print(f"[WARNING] File not found: {pdf_path}")
        secondary_images.append(None)
        continue

    print(f"[INFO] Converting {pdf_path.name} to image (dpi={dpi})...")
    img = convert_from_path(pdf_path, dpi=dpi)[0]
    secondary_images.append(img)

print(f"[INFO] Creating {nrows_secondary}x{ncols_secondary} combined figure...")
fig_secondary, axes_secondary = plt.subplots(
    nrows_secondary, ncols_secondary, figsize=(20, 20)
)

for i, (norm, img) in enumerate(zip(secondary_norms, secondary_images)):
    row = i // ncols_secondary
    col = i % ncols_secondary
    ax = axes_secondary[row, col]

    if img is not None:
        ax.imshow(img)
    else:
        ax.text(0.5, 0.5, f"Missing:\n{norm}",
                ha='center', va='center', fontsize=16)

    ax.axis('off')

plt.tight_layout(pad=0.5)

print(f"[INFO] Saving to {output_path_secondary}...")
fig_secondary.savefig(output_path_secondary, dpi=150, bbox_inches='tight',
                      metadata={'Creator': '', 'Producer': '', 'CreationDate': None})
print(f"[INFO] Saved: {output_path_secondary}")

#%% Secondary sixteen variants combined figure
print(f"\n[INFO] Creating combined figure for secondary sixteen variant norms...")

secondary_variant_norms = [f"S{i}v" for i in range(1, 17)]
output_path_secondary_variants = figure_path("combined_rr_sweep_bcs_secondary_sixteen_variants.pdf")

print(f"[INFO] Loading {len(secondary_variant_norms)} rr_sweep_bcs figures...")
secondary_variant_images = []
for norm in secondary_variant_norms:
    pdf_path = figures_dir / f"rr_sweep_bcs_{norm}.pdf"
    if not pdf_path.exists():
        print(f"[WARNING] File not found: {pdf_path}")
        secondary_variant_images.append(None)
        continue

    print(f"[INFO] Converting {pdf_path.name} to image (dpi={dpi})...")
    img = convert_from_path(pdf_path, dpi=dpi)[0]
    secondary_variant_images.append(img)

print(f"[INFO] Creating {nrows_secondary}x{ncols_secondary} combined figure...")
fig_secondary_variants, axes_secondary_variants = plt.subplots(
    nrows_secondary, ncols_secondary, figsize=(20, 20)
)

for i, (norm, img) in enumerate(zip(secondary_variant_norms, secondary_variant_images)):
    row = i // ncols_secondary
    col = i % ncols_secondary
    ax = axes_secondary_variants[row, col]

    if img is not None:
        ax.imshow(img)
    else:
        ax.text(0.5, 0.5, f"Missing:\n{norm}",
                ha='center', va='center', fontsize=16)

    ax.axis('off')

plt.tight_layout(pad=0.5)

print(f"[INFO] Saving to {output_path_secondary_variants}...")
fig_secondary_variants.savefig(output_path_secondary_variants, dpi=150, bbox_inches='tight',
                               metadata={'Creator': '', 'Producer': '', 'CreationDate': None})
print(f"[INFO] Saved: {output_path_secondary_variants}")
plt.show()

# %%
