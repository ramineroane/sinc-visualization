import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- Canvas settings ---
W, H = 1200, 700
MARGIN = 80

# --- Domain ---
x = torch.linspace(-4 * torch.pi, 4 * torch.pi, 4000)

# sinc: sin(x)/x, with limit = 1 at x=0
y = torch.where(x == 0, torch.ones_like(x), torch.sin(x) / x)

x_np = x.numpy()
y_np = y.numpy()

# --- Map to pixel coordinates ---
x_min, x_max = float(x_np.min()), float(x_np.max())
y_min, y_max = -0.25, 1.10   # a bit of padding around [-0.22, 1.0]

def to_px(xv, yv):
    px = MARGIN + (xv - x_min) / (x_max - x_min) * (W - 2 * MARGIN)
    py = MARGIN + (1 - (yv - y_min) / (y_max - y_min)) * (H - 2 * MARGIN)
    return px, py

# --- Background ---
img = Image.new("RGB", (W, H), (18, 18, 28))
draw = ImageDraw.Draw(img)

# --- Grid lines (faint) ---
grid_color = (50, 55, 70)
# Horizontal grid
for yg in np.arange(-0.2, 1.1, 0.2):
    _, py = to_px(x_min, yg)
    draw.line([(MARGIN, py), (W - MARGIN, py)], fill=grid_color, width=1)
# Vertical grid (at multiples of pi)
for k in range(-4, 5):
    xg = k * np.pi
    px, _ = to_px(xg, 0)
    draw.line([(px, MARGIN), (px, H - MARGIN)], fill=grid_color, width=1)

# --- Axes ---
axis_color = (160, 165, 185)
_, y0 = to_px(0, 0)   # y-axis zero line
x0, _ = to_px(0, 0)   # x-axis zero line
draw.line([(MARGIN, y0), (W - MARGIN, y0)], fill=axis_color, width=2)
draw.line([(x0, MARGIN), (x0, H - MARGIN)], fill=axis_color, width=2)

# --- Filled area under curve (green positive, red negative) ---
# Build polygons between each consecutive pair of sample points and the x-axis
pos_color = (30, 180, 80)    # green for positive
neg_color = (210, 50, 50)    # red  for negative
pos_shadow = (20, 100, 45, 140)   # RGBA for shading (we'll composite)
neg_shadow = (160, 30, 30, 140)

# Use RGBA overlay image for shading
overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
odraw = ImageDraw.Draw(overlay)

for i in range(len(x_np) - 1):
    xA, yA = to_px(x_np[i],   y_np[i])
    xB, yB = to_px(x_np[i+1], y_np[i+1])
    x0A, _ = to_px(x_np[i],   0.0)
    x0B, _ = to_px(x_np[i+1], 0.0)
    # average sign to pick color
    avg_y = (y_np[i] + y_np[i+1]) / 2
    color = pos_shadow if avg_y >= 0 else neg_shadow
    poly = [(xA, yA), (xB, yB), (xB, x0B[1] if False else to_px(x_np[i+1], 0)[1]),
            (xA, to_px(x_np[i], 0)[1])]
    odraw.polygon(poly, fill=color)

img = img.convert("RGBA")
img = Image.alpha_composite(img, overlay)
img = img.convert("RGB")
draw = ImageDraw.Draw(img)

# --- Draw the curve (colored by sign) ---
for i in range(len(x_np) - 1):
    xA, yA = to_px(x_np[i],   y_np[i])
    xB, yB = to_px(x_np[i+1], y_np[i+1])
    avg_y = (y_np[i] + y_np[i+1]) / 2
    color = (80, 230, 120) if avg_y >= 0 else (255, 90, 90)
    draw.line([(xA, yA), (xB, yB)], fill=color, width=3)

# --- Axis tick labels ---
label_color = (200, 205, 220)
# Try to load a font; fall back to default
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
except:
    font = ImageFont.load_default()
    font_small = font

pi_labels = {-4: "-4π", -3: "-3π", -2: "-2π", -1: "-π", 0: "0", 1: "π", 2: "2π", 3: "3π", 4: "4π"}
for k, lbl in pi_labels.items():
    xg = k * np.pi
    px, _ = to_px(xg, 0)
    draw.text((px - 12, y0 + 6), lbl, fill=label_color, font=font_small)

for yg in np.arange(-0.2, 1.1, 0.2):
    _, py = to_px(0, yg)
    draw.text((MARGIN - 46, py - 9), f"{yg:.1f}", fill=label_color, font=font_small)

# --- Title ---
draw.text((W // 2 - 90, 18), "sin(x) / x", fill=(240, 240, 255), font=font)

# --- Save ---
output_path = "sinc.jpg"
img.save(output_path, "JPEG", quality=95)
print(f"Saved to {output_path}")
