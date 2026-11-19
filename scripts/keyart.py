# -*- coding: utf-8 -*-
"""生成提交用的视觉图（1920×1080）。

从成片图版取一张，加底部渐暗与片名——和片子的字幕同一套字体，别另找。
    py -3 scripts/keyart.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import story as S

SRC = ROOT / "plates" / "her-face-lit.png"
OUT = ROOT / "submission" / "key-art.jpg"
FONTS = ROOT / "assets" / "fonts"
W, H = 1920, 1080


def main():
    im = Image.open(SRC).convert("RGB")
    # 2400×1350 → 1920×1080，居中取
    z = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
    top = max(0, (z.height - H) // 2)
    im = z.crop((0, top, W, top + H))

    # 底部渐暗（比成片更狠一点，海报要压得住字）
    y = np.arange(H, dtype=np.float32)[:, None]
    t0 = 0.55 * H
    k = np.clip((y - t0) / (H - t0), 0, 1) ** 1.4
    v = (1.0 - 0.78 * k) * np.ones((1, W), dtype=np.float32)
    g = (np.clip(v, 0, 1) * 255).astype(np.uint8)
    fade = Image.merge("RGB", (Image.fromarray(g, "L"),) * 3)
    im = Image.fromarray((np.asarray(im, dtype=np.float32) *
                          np.asarray(fade, dtype=np.float32) / 255).astype(np.uint8))

    d = ImageDraw.Draw(im)
    fz = ImageFont.truetype(str(FONTS / "NotoSerifSC-Subset.ttf"), 132)
    fe = ImageFont.truetype(str(FONTS / "NotoSansSC-Subset.ttf"), 34)
    fl = ImageFont.truetype(str(FONTS / "NotoSansSC-Subset.ttf"), 26)

    def t(xy, s, f, fill, anchor="ls"):
        x, y0 = xy
        d.text((x + 2, y0 + 2), s, font=f, fill=(10, 10, 10), anchor=anchor)
        d.text((x, y0), s, font=f, fill=(fill, fill, fill), anchor=anchor)

    t((104, H - 208), S.TITLE_ZH, fz, 246)
    t((112, H - 116), "N U M B E R ,   P L E A S E", fe, 210)
    t((114, H - 66), "Artefact AI Film Festival / Third Edition / (Dis)Connection", fl, 150)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.save(OUT, quality=94, subsampling=0)
    print(f"{OUT} {im.size} {OUT.stat().st_size/1e6:.2f} MB")


if __name__ == "__main__":
    main()
