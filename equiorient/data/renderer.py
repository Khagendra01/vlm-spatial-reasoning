"""Phase-2 renderer: math coords -> PIL image, no text.

Shapes are rotation-safe primitives (circle, square, regular octagon)
so H/R introduce no semantic artifacts. Renders 192x192 RGB.
Pixel ops for H/R/R2/R3 are provided for the renderer tests.

ESCALATION v3: heavier per-pixel noise (amp=10), low-contrast background
to make target detection harder against the muted palette.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

from equiorient.data.transforms import to_pixel

HALF = 96.0
SIZE = int(2 * HALF)
# Darker background (was 248,248,248 = near-white; now low-contrast gray)
BG = (180, 180, 180)


def render(scene, half: float = HALF) -> Image.Image:
    img = Image.new("RGB", (2 * int(half), 2 * int(half)), BG)
    d = ImageDraw.Draw(img)
    for o in scene.objects():
        px, py = to_pixel(o.x, o.y, half)
        s = o.size
        if o.shape == "circle":
            d.ellipse([px - s, py - s, px + s, py + s], fill=o.color)
        elif o.shape == "square":
            d.rectangle([px - s, py - s, px + s, py + s], fill=o.color)
        elif o.shape == "octagon":
            pts = []
            for k in range(8):
                ang = math.pi / 8 + k * math.pi / 4
                pts.append((px + s * math.cos(ang), py + s * math.sin(ang)))
            d.polygon(pts, fill=o.color)
        else:
            raise ValueError(f"shape {o.shape}")
    return img


def add_noise(img: Image.Image, seed: int, amp: int = 10) -> Image.Image:
    """Per-pixel background jitter (deterministic per seed).
    v3: heavier noise (amp=10) to degrade feature quality."""
    import numpy as np
    rng = np.random.default_rng(seed)
    arr = np.asarray(img).astype(np.int16)
    noise = rng.integers(-amp, amp + 1, size=arr.shape[:2])[..., None]
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def pixel_transform(g_name: str, img: Image.Image) -> Image.Image:
    """Apply the group element as a pure pixel operation (no resampling)."""
    if g_name == "I":
        return img
    if g_name == "H":
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    if g_name == "R":
        return img.transpose(Image.ROTATE_90)  # CW 90 in pixel coords
    if g_name == "R2":
        return img.transpose(Image.ROTATE_180)
    if g_name == "R3":
        return img.transpose(Image.ROTATE_270)  # CCW 90 in pixel coords
    raise ValueError(f"no pixel op for {g_name}")
