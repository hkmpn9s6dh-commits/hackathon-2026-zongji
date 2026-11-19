# -*- coding: utf-8 -*-
"""把 raw 图版处理成可用的 plates：去工具水印 → 裁 16:9 → 统一影调 → 只留红。

水印不能靠裁：裁掉的 6% 往往就是主体（中枢 C-20261119-57824124 的教训）。
这里对水印框做中值滤波，再用断言量成品右下角还有没有字形边缘。
"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "plates" / "raw"
OUT = ROOT / "plates"

# raw 文件名 → 交付名
MAP = {
    "p-xiaolan-portrait": "her-face-lit",
    "Black_and_white_35mm_film_stil_2026-11-18T21-17-44": "board-wide",
    "Black_and_white_35mm_film_stil_2026-11-18T21-18-09": "panel-macro",
    "Black_and_white_35mm_film_stil_2026-11-18T21-17-56": "hands-plug",
    "Same_woman__same_face__same_ag_2026-11-18T21-19-35": "her-board-back",
    "Black_and_white_35mm_film_stil_2026-11-18T21-18-49": "window-snow",
    "Black_and_white_35mm_film_stil_2026-11-18T21-19-03": "laozhou-door",
    "Black_and_white_35mm_film_stil_2026-11-18T21-20-22": "form-seal",
    "Black_and_white_35mm_film_stil_2026-11-18T21-20-35": "headset-hook",
    "Black_and_white_35mm_film_stil_2026-11-18T21-20-49": "unused-sparkplug",
    "Black_and_white_35mm_film_stil_2026-11-18T22-18-51": "board-dead-lamp",
    "Same_woman__same_face__same_ag_2026-11-18T21-19-56": "her-face-listening",
    "Black_and_white_35mm_film_stil_2026-11-18T21-21-09": "street-pole",
    "Black_and_white_35mm_film_stil_2026-11-18T21-21-22": "new-exchange",
    "Black_and_white_35mm_film_stil_2026-11-18T21-21-37": "lane-door",
    "Black_and_white_35mm_film_stil_2026-11-18T21-22-06": "mother-doorway",
    "Black_and_white_35mm_film_stil_2026-11-18T21-22-19": "two-hands",
    "Black_and_white_35mm_film_stil_2026-11-18T21-22-30": "walk-back",
    "Same_woman__same_face__same_ag_2026-11-18T21-23-03": "headset-hands",
    "Black_and_white_35mm_film_stil_2026-11-18T21-23-19": "board-dawn",
    "Black_and_white_35mm_film_stil_2026-11-18T21-23-46": "door-speak",
}

# 每张的 16:9 取窗竖直偏移（0=顶，1=底）。默认 0.42，主体偏上的图调小。
OFFSET = {
    "her-face-lit": 0.20,
    "hands-plug": 0.55,
    "form-seal": 0.50,
    "two-hands": 0.55,
    "board-dawn": 0.50,
    "board-dead-lamp": 0.50,
    "headset-hook": 0.45,
    "door-speak": 0.45,
    "walk-back": 0.40,
}

OUT_W, OUT_H = 2400, 1350  # 留 1.25x 推镜余量，成片再降到 1080p


def kill_watermark(im: Image.Image) -> Image.Image:
    """对右下角工具水印做中值滤波（不裁）。"""
    w, h = im.size
    box = (int(w * 0.845), int(h * 0.935), w, h)
    crop = im.crop(box).filter(ImageFilter.MedianFilter(size=9))
    crop = crop.filter(ImageFilter.GaussianBlur(0.6))
    im = im.copy()
    im.paste(crop, box)
    return im


def grade(im: Image.Image) -> Image.Image:
    """统一影调：去色，但保留强红（红纸／红灯／红章）。"""
    a = np.asarray(im.convert("RGB"), dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    # 强红掩膜：红显著高于绿蓝
    red = np.clip((r - np.maximum(g, b) - 18.0) / 40.0, 0.0, 1.0)
    # 只留红灯／红纸，别把皮肤的暖调也留下
    red = np.where(lum < 40, red * 0.6, red)
    red3 = red[..., None]
    gray = np.repeat(lum[..., None], 3, axis=2)
    # 轻微冷调 + 抬黑
    gray = gray * np.array([0.985, 1.0, 1.02], dtype=np.float32)
    gray = 10.0 + (gray ** 0.94) * 1.10  # 抬黑 + 提亮（试片太暗，实测改法）
    gray = np.clip(gray, 0, 255)
    out = gray * (1.0 - red3) + a * red3
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def vignette(im: Image.Image) -> Image.Image:
    """烘焙暗角：四角压到 0.55，中心 1.0。渲染时就不用逐帧乘了。"""
    w, h = im.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2.0, h / 2.0
    nx = (xx - cx) / cx
    ny = (yy - cy) / cy
    r = np.sqrt(nx * nx * 0.85 + ny * ny)
    m = np.clip(1.0 - 0.30 * np.clip(r - 0.38, 0, None) ** 1.7, 0.66, 1.0)[..., None]
    a = np.asarray(im, dtype=np.float32) * m
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for src, name in MAP.items():
        p = RAW / f"{src}.png"
        if not p.exists():
            print(f"MISSING {p}")
            continue
        im = Image.open(p).convert("RGB")
        im = kill_watermark(im)
        w, h = im.size
        target_h = int(round(w * OUT_H / OUT_W))
        if target_h > h:
            target_h = h
        off = OFFSET.get(name, 0.42)
        top = int(round((h - target_h) * off))
        top = max(0, min(h - target_h, top))
        im = im.crop((0, top, w, top + target_h))
        im = im.resize((OUT_W, OUT_H), Image.LANCZOS)
        im = grade(im)
        im = vignette(im)
        im.save(OUT / f"{name}.png", optimize=True)
        made.append(name)
        print(f"{name:18s} <- {src[:44]:44s} {im.size}")
    print(f"\n{len(made)} plates -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
