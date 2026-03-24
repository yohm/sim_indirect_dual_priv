#!/usr/bin/env python3
#%%
"""
Combine image_matrix_mono and pc_bcrange figures into a single multi-panel figure.

Usage:
  VSCode Interactive: Run cells sequentially
"""

#%% Imports
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pdf2image import convert_from_path
from utils import FIGURES_DIR, figure_path

#%% Parameters
figures_dir = FIGURES_DIR
output_path = figure_path("combined_image_pc_bcrange.pdf")

# Norms to include (order matters)
norms = ["L6", "L8", "L5", "L3"]

# Grid layout: 4 rows x 4 columns
nrows, ncols = 4, 4
dpi = 150  # Balanced resolution for smaller file size

#%% Load PDFs and convert to images
print(f"[INFO] Loading figures for {len(norms)} norms...")
all_images = []

for norm in norms:
    row_images = []
    
    # Column 1: image_matrix_mono_{norm}_mono.pdf
    pdf_path1 = figures_dir / f"image_matrix_mono_{norm}_mono.pdf"
    if pdf_path1.exists():
        print(f"[INFO] Converting {pdf_path1.name} to image (dpi={dpi})...")
        img1 = convert_from_path(pdf_path1, dpi=dpi)[0]
        row_images.append(img1)
    else:
        print(f"[WARNING] File not found: {pdf_path1}")
        row_images.append(None)
    
    # Column 2: image_matrix_mono_{norm}-IS_mono.pdf
    pdf_path2 = figures_dir / f"image_matrix_mono_{norm}-IS_mono.pdf"
    if pdf_path2.exists():
        print(f"[INFO] Converting {pdf_path2.name} to image (dpi={dpi})...")
        img2 = convert_from_path(pdf_path2, dpi=dpi)[0]
        row_images.append(img2)
    else:
        print(f"[WARNING] File not found: {pdf_path2}")
        row_images.append(None)
    
    # Column 3: pc_{norm}_vs_{norm}-IS.pdf
    pdf_path3 = figures_dir / f"pc_{norm}_vs_{norm}-IS.pdf"
    if pdf_path3.exists():
        print(f"[INFO] Converting {pdf_path3.name} to image (dpi={dpi})...")
        img3 = convert_from_path(pdf_path3, dpi=dpi)[0]
        # Crop right side to reduce gap with next column
        width3, height3 = img3.size
        crop_right = int(width3 * 0.92)  # Remove 8% from right
        img3 = img3.crop((0, 0, crop_right, height3))
        row_images.append(img3)
    else:
        print(f"[WARNING] File not found: {pdf_path3}")
        row_images.append(None)
    
    # Column 4: bc_range_{norm}_vs_{norm}-IS.pdf
    pdf_path4 = figures_dir / f"bc_range_{norm}_vs_{norm}-IS.pdf"
    if pdf_path4.exists():
        print(f"[INFO] Converting {pdf_path4.name} to image (dpi={dpi})...")
        img4 = convert_from_path(pdf_path4, dpi=dpi)[0]
        # Crop left side to reduce gap with previous column
        width4, height4 = img4.size
        crop_left = int(width4 * 0.0)  # Remove 8% from left
        img4 = img4.crop((crop_left, 0, width4, height4))
        row_images.append(img4)
    else:
        print(f"[WARNING] File not found: {pdf_path4}")
        row_images.append(None)
    
    all_images.append(row_images)

#%% Create combined figure
print(f"[INFO] Creating {nrows}x{ncols} combined figure...")
fig = plt.figure(figsize=(20, 20))

gs = GridSpec(nrows, ncols, figure=fig, width_ratios=[0.75, 0.75, 1.0, 1.0], hspace=0.15, wspace=0.05)

axes_list = []
for row in range(nrows):
    for col in range(ncols):
        ax = fig.add_subplot(gs[row, col])
        img = all_images[row][col]
        
        if img is not None:
            ax.imshow(img)
        else:
            ax.text(0.5, 0.5, f"Missing", 
                    ha='center', va='center', fontsize=16)
        
        ax.axis('off')
        axes_list.append(ax)

plt.tight_layout(pad=0.5)

# Slightly reduce the gap between column 2 and 3 (0-indexed) by shifting column 3 left
gap_reduction = 0.02
for i, ax in enumerate(axes_list):
    if i % ncols >= 3:
        pos = ax.get_position()
        ax.set_position([pos.x0 - gap_reduction, pos.y0, pos.width, pos.height])

# Add row labels on the left side (after tight_layout to get correct positions)
# Define labels with types
norm_labels = {
    "L6": "L6\n(Type III)",
    "L8": "L8\n(Type III)",
    "L5": "L5\n(Type II)",
    "L3": "L3\n(Type I)"
}

for i, norm in enumerate(norms):
    # Get the position of the first subplot in this row
    ax_first = axes_list[i * ncols]  # First column of row i
    bbox = ax_first.get_position()
    # Calculate y position as the center of the row
    y_pos = (bbox.y0 + bbox.y1) / 2
    # Position label just to the left of the first subplot
    x_pos = bbox.x0 - 0.06
    label = norm_labels.get(norm, norm)
    fig.text(x_pos, y_pos, label, fontsize=32, # fontweight='bold',
             ha='center', va='center', rotation=0,
             fontfamily='sans-serif', transform=fig.transFigure)

# Add column labels at the top
# Column 0 and 1: "image matrix" (spanning first two columns)
bbox_col0 = axes_list[0].get_position()  # First column, first row
bbox_col1 = axes_list[1].get_position()  # Second column, first row
x_center_01 = (bbox_col0.x0 + bbox_col1.x1) / 2
y_top = bbox_col0.y1 + 0.06  # Higher position for main label
fig.text(x_center_01, y_top, "image matrix", fontsize=34,
         ha='center', va='top', rotation=0,
         fontfamily='sans-serif', transform=fig.transFigure)

# Sub-labels for columns 0 and 1
y_sub = bbox_col0.y1 + 0.005  # Position for sub-labels (below "image matrix")

# Column 0: "-base"
x_center_0 = (bbox_col0.x0 + bbox_col0.x1) / 2
fig.text(x_center_0, y_sub, "-base", fontsize=28,
         ha='center', va='bottom', rotation=0,
         fontfamily='sans-serif', transform=fig.transFigure)

# Column 1: "-IS"
x_center_1 = (bbox_col1.x0 + bbox_col1.x1) / 2
fig.text(x_center_1, y_sub, "-IS", fontsize=28,
         ha='center', va='bottom', rotation=0,
         fontfamily='sans-serif', transform=fig.transFigure)

# Column 2: "self-cooperation level"
bbox_col2 = axes_list[2].get_position()  # Third column, first row
x_center_2 = (bbox_col2.x0 + bbox_col2.x1) / 2 + 0.02  # Slight adjustment to the right
fig.text(x_center_2, y_top, "self-cooperation\nlevel", fontsize=34,
         ha='center', va='top', rotation=0,
         fontfamily='sans-serif', transform=fig.transFigure)

# Column 3: "stable $b/c$ range"
bbox_col3 = axes_list[3].get_position()  # Fourth column, first row
x_center_3 = (bbox_col3.x0 + bbox_col3.x1) / 2 + 0.02  # Slight adjustment to the right
fig.text(x_center_3, y_top, "stable $b/c$\nrange", fontsize=34,
         ha='center', va='top', rotation=0,
         fontfamily='sans-serif', transform=fig.transFigure)

#%% Save combined figure
print(f"[INFO] Saving to {output_path}...")
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches='tight', 
            metadata={'Creator': '', 'Producer': '', 'CreationDate': None})
print(f"[INFO] Saved: {output_path}")
plt.show()

# %%
