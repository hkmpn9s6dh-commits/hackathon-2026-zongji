# -*- coding: utf-8 -*-
"""从成片抽证据帧：关键帧、联系表、评委用的六帧。

    py -3 scripts/proof.py
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import story as S

FILM = ROOT / "out" / "zongji.mp4"
OUT = ROOT / "proof" / "frames"
JUDGE = ROOT / "proof" / "judge"

# 每一幕取一帧：幕一 台 / 幕二 声 / 幕三 断 / 幕四 走 / 幕五 音
KEYS = [6.0, 30.0, 62.0, 100.0, 122.0, 146.0, 165.0, 201.0, 224.0, 240.0, 262.0, 282.0]

# 评委盲读的六帧（跨五幕，含一处人物、一处器物、一处动作、一处地点）
JUDGE_T = [8.0, 24.0, 96.0, 148.0, 208.0, 262.0]


def grab(t, dst):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(FILM), "-ss", f"{t:.2f}",
                    "-frames:v", "1", str(dst)], check=True)
    return Image.open(dst).convert("RGB")


def main():
    for d in (OUT / "keys", JUDGE):
        d.mkdir(parents=True, exist_ok=True)

    ims = []
    for t in KEYS:
        im = grab(t, OUT / "keys" / f"f{int(t)}.png")
        ims.append(im.resize((480, 270), Image.LANCZOS))

    # 联系表 4×3
    sheet = Image.new("RGB", (480 * 4, 270 * 3), (0, 0, 0))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 4) * 480, (i // 4) * 270))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(str(ROOT / "assets" / "fonts" / "NotoSansSC-Subset.ttf"), 16)
    for i, t in enumerate(KEYS):
        d.text(((i % 4) * 480 + 8, (i // 4) * 270 + 244), f"{t:.0f}s", font=f, fill=(200, 200, 200))
    sheet.save(OUT / "contact.png")
    print(f"{OUT/'contact.png'} {sheet.size}")

    for i, t in enumerate(JUDGE_T, 1):
        grab(t, JUDGE / f"f{i:02d}.png")
    print(f"{JUDGE}  f01..f06")


if __name__ == "__main__":
    main()
