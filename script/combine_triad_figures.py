#!/usr/bin/env python3
#%%
"""
Combine triad figures into a single multi-panel figure.

Usage:
  VSCode Interactive: Run cells sequentially
"""

#%% Imports
from pathlib import Path
from pdf2image import convert_from_path
import matplotlib.pyplot as plt

#%% Parameters
ROOT = Path(__file__).resolve().parents[1]
figures_dir = ROOT / "script" / "figures"
output_path = ROOT / "script" / "figures" / "combined_triads.pdf"

# Norms to include (order matters)
norms = ["L6", "L6-IS", "L8", "L8-IS", "L5", "L5-IS", "L3", "L3-IS"]

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
    # Add panel label
    ax.text(0.02, 0.98, f"({chr(97 + i)})", transform=ax.transAxes,
            fontsize=20, fontweight='bold', va='top', ha='left')

plt.tight_layout(pad=0.5)

#%% Save combined figure
print(f"[INFO] Saving to {output_path}...")
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches='tight', 
            metadata={'Creator': '', 'Producer': '', 'CreationDate': None})
print(f"[INFO] Saved: {output_path}")

#%% Display
plt.show()

# %%
