#!/usr/bin/env python3
#%%
"""
Combine triad figures into a single multi-panel figure.

Usage:
  VSCode Interactive: Run cells sequentially
"""

#%% Imports
import matplotlib.pyplot as plt
from pdf2image import convert_from_path
from utils import FIGURES_DIR, figure_path

#%% Parameters
figures_dir = FIGURES_DIR
output_path = figure_path("combined_triads.pdf")

# Norms to include (order matters)
norms = ["L6", "L8", "L5", "L3", "L6-IS", "L8-IS", "L5-IS", "L3-IS"]

# Grid layout: 2 rows x 4 columns
nrows, ncols = 2, 4
dpi = 150  # Balanced resolution for smaller file size (was 300)

#%% Load PDFs and convert to images
print(f"[INFO] Loading {len(norms)} triad figures...")
images = []
for norm in norms:
    pdf_path = figures_dir / f"triad_{norm}.pdf"
    if not pdf_path.exists():
        print(f"[WARNING] File not found: {pdf_path}")
        images.append(None)
        continue
    
    print(f"[INFO] Converting {pdf_path.name} to image (dpi={dpi})...")
    img = convert_from_path(pdf_path, dpi=dpi)[0]
    images.append(img)

#%% Create combined figure
print(f"[INFO] Creating {nrows}x{ncols} combined figure...")
fig, axes = plt.subplots(nrows, ncols, figsize=(20, 10))

for i, (norm, img) in enumerate(zip(norms, images)):
    row = i // ncols
    col = i % ncols
    ax = axes[row, col]
    
    if img is not None:
        ax.imshow(img)
    else:
        ax.text(0.5, 0.5, f"Missing:\n{norm}", 
                ha='center', va='center', fontsize=16)
    
    ax.axis('off')

plt.tight_layout(pad=0.5)

#%% Save combined figure
print(f"[INFO] Saving to {output_path}...")
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches='tight', 
            metadata={'Creator': '', 'Producer': '', 'CreationDate': None})
print(f"[INFO] Saved: {output_path}")

#%% All other norms combined figure
print(f"\n[INFO] Creating combined figure for all other norms...")

# All other norms: L1, L1v, L2, L2v, L4, L7
norms_other = ["L1", "L1-IS", "L1v", "L1v-IS", "L2", "L2-IS", "L2v", "L2v-IS", "L4", "L4-IS", "L7", "L7-IS"]
output_path_other = figure_path("combined_triads_others.pdf")

# Grid layout: 3 rows x 4 columns (12 panels total)
nrows_other, ncols_other = 3, 4

print(f"[INFO] Loading {len(norms_other)} triad figures...")
images_other = []
for norm in norms_other:
    pdf_path = figures_dir / f"triad_{norm}.pdf"
    if not pdf_path.exists():
        print(f"[WARNING] File not found: {pdf_path}")
        images_other.append(None)
        continue
    
    print(f"[INFO] Converting {pdf_path.name} to image (dpi={dpi})...")
    img = convert_from_path(pdf_path, dpi=dpi)[0]
    images_other.append(img)

print(f"[INFO] Creating {nrows_other}x{ncols_other} combined figure...")
fig_other, axes_other = plt.subplots(nrows_other, ncols_other, figsize=(20, 15))

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

plt.tight_layout(pad=0.5)

print(f"[INFO] Saving to {output_path_other}...")
fig_other.savefig(output_path_other, dpi=150, bbox_inches='tight', 
                  metadata={'Creator': '', 'Producer': '', 'CreationDate': None})
print(f"[INFO] Saved: {output_path_other}")
plt.show()

# %%
