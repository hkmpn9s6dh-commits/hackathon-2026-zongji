# -*- coding: utf-8 -*-
"""逐帧渲染《总机》。

一个镜头 = 一张图版 + 一条运镜 + 若干程序化叠加层。
不做整帧色彩运算（中枢 C-20261115-326cff81 的教训）：暗角烘焙在图版里，
颗粒是一张预乘好的层，雪是滚动贴图，文字只在有字幕的帧上画。

用法：
    py -3 scripts/render.py --from 0 --to 1800 --out build/seg00.mp4
"""
import argparse, math, random, subprocess, sys, time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import story as S

ROOT = Path(__file__).resolve().parent.parent
PLATES = ROOT / "plates"
FONTS = ROOT / "assets" / "fonts"
W, H = S.W, S.H
FPS = S.FPS
GRAIN_SIGMA = 4.5   # 颗粒强度：9.0 时 x264 会到 57 Mbps，4.5 仍看得出颗粒

# ------------------------------------------------------------------ 时间轴
def layout():
    out, t = [], 0.0
    for sh in S.SHOTS:
        n = int(round(sh["dur"] * FPS))
        out.append(dict(shot=sh, start=t, n=n))
        t += sh["dur"]
    return out


LAYOUT = layout()
TOTAL_N = sum(x["n"] for x in LAYOUT)


def shot_at(fi):
    """返回 (镜头条目, 本镜内的帧号)。"""
    for x in LAYOUT:
        if fi < x["n"]:
            return x, fi
        fi -= x["n"]
    return LAYOUT[-1], LAYOUT[-1]["n"] - 1


# ------------------------------------------------------------------ 素材
_grain = []
def grain_tiles():
    global _grain
    if _grain:
        return _grain
    cache = ROOT / "build" / "grain"
    cache.mkdir(parents=True, exist_ok=True)
    f = cache / "tiles.npy"
    if f.exists():
        _grain = [Image.fromarray(np.asarray(a), "RGB") for a in np.load(f)]
        return _grain
    rng = np.random.default_rng(7)
    arrs = []
    for i in range(12):
        g = rng.normal(0, GRAIN_SIGMA, (H, W)).astype(np.float32)
        g = np.clip(g + 128, 0, 255).astype(np.uint8)
        arrs.append(Image.merge("RGB", (Image.fromarray(g, "L"),) * 3))
    np.save(f, np.array([np.asarray(a, dtype=np.uint8) for a in arrs]))
    _grain = arrs
    return _grain


_snow = {}
def snow_layers():
    """三层雪，各自不同的密度与速度；预乘成加法层。"""
    if _snow:
        return _snow
    rng = np.random.default_rng(11)
    for i, (num, rad, bright) in enumerate([(340, 0.9, 55), (150, 1.5, 80), (46, 2.4, 105)]):
        w, h = W + 200, H + 400
        layer = np.zeros((h, w), dtype=np.float32)
        xs = rng.uniform(0, w, num)
        ys = rng.uniform(0, h, num)
        for x, y in zip(xs, ys):
            rr = rad * rng.uniform(0.6, 1.4)
            x0, x1 = int(max(0, x - 3 * rr)), int(min(w, x + 3 * rr + 1))
            y0, y1 = int(max(0, y - 6 * rr)), int(min(h, y + 6 * rr + 1))
            if x1 <= x0 or y1 <= y0:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1]
            d2 = ((xx - x) ** 2) / (2 * rr * rr) + ((yy - y) ** 2) / (2 * (rr * 2.4) ** 2)
            layer[y0:y1, x0:x1] += np.exp(-d2) * bright
        layer = np.clip(layer, 0, 255).astype(np.uint8)
        _snow[i] = Image.merge("RGB", (Image.fromarray(layer, "L"),) * 3)
    return _snow


_fade = None
def bottom_fade():
    """底部渐暗：让字幕在任何画面上都读得出来，同时像一层印片。"""
    global _fade
    if _fade is None:
        y = np.arange(H, dtype=np.float32)[:, None]
        t0 = 0.72 * H
        k = np.clip((y - t0) / (H - t0), 0, 1) ** 1.6
        v = (1.0 - 0.42 * k) * np.ones((1, W), dtype=np.float32)
        g = (np.clip(v, 0, 1) * 255).astype(np.uint8)
        _fade = Image.merge("RGB", (Image.fromarray(g, "L"),) * 3)
    return _fade


_font_cache = {}
def font(name, size):
    key = (name, size)
    if key not in _font_cache:
        path = FONTS / name
        _font_cache[key] = ImageFont.truetype(str(path), size)
    return _font_cache[key]


# ------------------------------------------------------------------ 运镜
def crop_box(sh, p):
    """返回图版上的裁切框 (l,t,r,b)。p 是本镜内进度 0..1。"""
    pw, ph = PLATES.size if False else (2400, 1350)
    move = sh.get("move")
    kind = move[0] if move else "static"
    if kind == "push":
        z0, z1 = move[1], move[2]
        z = z0 + (z1 - z0) * ease(p)
        cw, ch = pw / z, ph / z
        cx, cy = pw * 0.5, ph * 0.5
    elif kind == "pan":
        z = 1.14
        cw, ch = pw / z, ph / z
        (x0, y0), (x1, y1) = move[1], move[2]
        cx = pw * (x0 + (x1 - x0) * ease(p)) + cw * 0.5
        cy = ph * (y0 + (y1 - y0) * ease(p)) + ch * 0.5
    else:
        z = move[1] if move else 1.0
        cw, ch = pw / z, ph / z
        cx, cy = pw * 0.5, ph * 0.5
    l = min(max(0, cx - cw / 2), pw - cw)
    t = min(max(0, cy - ch / 2), ph - ch)
    return (l, t, l + cw, t + ch)


def ease(p):
    return p * p * (3 - 2 * p)


# ------------------------------------------------------------------ 叠加
def add_snow(im, t, strength=1.0):
    layers = snow_layers()
    out = im
    for i, (dx, dy) in enumerate([(26, 130), (-14, 80), (7, 44)]):
        lay = layers[i]
        ox = int((dx * t) % 200)
        oy = int((dy * t) % 400)
        sub = lay.crop((ox, oy, ox + W, oy + H))
        if strength < 0.999:
            sub = sub.point(lambda v, s=strength: int(v * s))
        out = ImageChops.add(out, sub)
    return out


def add_puff(im, cx, cy, r, a):
    """呼吸／蒸汽：一团柔光，加在画面上。"""
    if a <= 0.01:
        return im
    w = h = int(r * 6)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d2 = ((xx - w / 2) ** 2 + (yy - h / 2) ** 2) / (2 * (r * 1.4) ** 2)
    g = np.exp(-d2) * a
    patch = Image.fromarray(np.clip(g * 255, 0, 255).astype(np.uint8), "L").resize((w, h))
    mask = Image.new("L", im.size, 0)
    mask.paste(patch, (int(cx - w / 2), int(cy - h / 2)))
    return ImageChops.add(im, Image.merge("RGB", (mask, mask, mask)))


def wrap(txt, n):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= n:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text(draw, xy, s, f, fill=245, shadow=True, anchor="mm"):
    x, y = xy
    if shadow:
        draw.text((x + 2, y + 2), s, font=f, fill=8, anchor=anchor)
    draw.text((x, y), s, font=f, fill=(fill, fill, fill), anchor=anchor)


# ------------------------------------------------------------------ 字幕表
def subtitle_ranges():
    """由 LINES 自动推字幕时间，另加 CARDS。返回 [(t0, t1, text)]（全局秒）。"""
    starts = {}
    t = 0.0
    for sh in S.SHOTS:
        starts[sh["id"]] = t
        t += sh["dur"]
    out = []
    for ln in S.LINES:
        if not ln["en"]:
            continue
        t0 = starts[ln["shot"]] + ln["t"]
        dur = min(6.0, max(2.0, len(ln["en"]) / 13.0)) + 0.5
        out.append((t0, t0 + dur, ln["en"]))
    for sid, a, b, txt in S.CARDS:
        out.append((starts[sid] + a, starts[sid] + b, txt))
    return out


SUBS = subtitle_ranges()


def subs_at(t):
    return [s for s in SUBS if s[0] <= t < s[1]]


# ------------------------------------------------------------------ 画一帧
def frame(fi):
    x, local = shot_at(fi)
    sh = x["shot"]
    p = local / max(1, x["n"] - 1)
    t = fi / FPS

    if sh.get("plate") is None:
        im = Image.new("RGB", (W, H), (0, 0, 0))
    else:
        plate = Image.open(PLATES / f"{sh['plate']}.png").convert("RGB")
        box = list(crop_box(sh, p))
        dx = 5.0 * math.sin(t * 0.31) + 2.0 * math.sin(t * 0.83)
        dy = 3.5 * math.sin(t * 0.23 + 1.1)
        box[0] += dx; box[2] += dx; box[1] += dy; box[3] += dy
        box[0] = max(0, box[0]); box[1] = max(0, box[1])
        box[2] = min(2400, box[2]); box[3] = min(1350, box[3])
        im = plate.crop(tuple(int(round(v)) for v in box)).resize((W, H), Image.BILINEAR)

    ov = set(sh.get("ov") or [])

    # 灯闪：极轻微的曝光呼吸
    if "lamp" in ov:
        k = 1.0 + 0.022 * math.sin(t * 13.7) + 0.012 * math.sin(t * 3.1 + 1.2)
        im = Image.eval(im, lambda v, k=k: min(255, int(v * k)))

    if "dim" in ov:
        # 灯一盏一盏灭：整场压暗，末段留一点余光
        k = 1.0 - 0.42 * ease(min(1.0, p * 1.05))
        im = Image.eval(im, lambda v, k=k: int(v * k))

    if "dying" in ov:
        # 话路一条条退：亮度分三级下台阶，每个台阶口抖两下。
        # 不给整镜十八秒一个不变的脸——闸 D 上"没有一张脸"是上一场的教训。
        k = 1.0
        if p > 0.30:
            k = 0.90
        if p > 0.60:
            k = 0.76
        if p > 0.86:
            k = 0.64
        for c0 in (0.27, 0.57, 0.84):
            if c0 <= p < c0 + 0.05:
                k *= 0.52 + 0.48 * abs(math.sin((p - c0) * 300.0))
        im = Image.eval(im, lambda v, k=k: int(v * k))

    if "snow" in ov:
        im = add_snow(im, t, 1.0 if sh["id"] != "S20" else 0.7)

    if "breath" in ov:
        cyc = (t * 0.42) % 1.0
        a = 0.24 * max(0.0, math.sin(cyc * math.pi))
        im = add_puff(im, W * 0.52, H * 0.46 - 40 * cyc, 46 + 26 * cyc, a)

    if "steam" in ov:
        cyc = (t * 0.33) % 1.0
        im = add_puff(im, W * 0.42, H * 0.55 - 120 * cyc, 60 + 30 * cyc, 0.18 * (1 - cyc))

    im = ImageChops.multiply(im, bottom_fade())

    # 颗粒
    if "grain" in ov:
        g = grain_tiles()[fi % 12]
        im = ImageChops.add(im, g, scale=1.0, offset=-128)

    # 字幕
    d = ImageDraw.Draw(im)
    f = font("NotoSansSC-Subset.ttf", 42)
    cur = subs_at(t)
    if cur:
        for i, (a, b, txt) in enumerate(cur):
            lines = wrap(txt, 56)
            base = H - 96 - (len(lines) - 1) * 56 - i * 116
            for j, ln in enumerate(lines):
                text(d, (W // 2, base + j * 56), ln, f, fill=240)

    # 片名字卡
    if sh["id"] == "S01":
        if 3.2 <= t < 11.0:
            a = min(1.0, (t - 3.2) / 1.4, (11.0 - t) / 1.2)
            ft = font("NotoSerifSC-Subset.ttf", 132)
            fe = font("NotoSansSC-Subset.ttf", 40)
            text(d, (W // 2, H // 2 - 30), "总机", ft, fill=int(30 + 210 * a))
            text(d, (W // 2, H // 2 + 96), "N U M B E R ,   P L E A S E", fe, fill=int(20 + 140 * a))

    # 片尾
    if sh["id"] == "S23":
        local = t - x["start"]
        ft = font("NotoSerifSC-Subset.ttf", 96)
        fs = font("NotoSansSC-Subset.ttf", 38)
        fl = font("NotoSansSC-Subset.ttf", 34)
        y = H // 2 - 230
        for i, (s, kind) in enumerate(S.CREDITS):
            if not s:
                y += 34
                continue
            a = 1.0
            appear = 0.6 + i * 0.14
            if local < appear:
                y += 0
                continue
            a = min(1.0, (local - appear) / 0.8)
            fnt = {"title": ft, "sub": fs, "line": fl, "note": fl, "note_en": fl}[kind]
            text(d, (W // 2, y), s, fnt, fill=int(20 + 225 * a))
            y += {"title": 140, "sub": 90, "line": 62, "note": 54, "note_en": 54}[kind]

    return im


# ------------------------------------------------------------------ 主程序
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="f0", type=int, default=0)
    ap.add_argument("--to", dest="f1", type=int, default=TOTAL_N)
    ap.add_argument("--out", required=True)
    ap.add_argument("--crf", default="18")
    ap.add_argument("--maxrate", default="")  # 给颗粒片封顶，否则 CRF 只认画质、码率失控
    a = ap.parse_args()
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".part.mp4")

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", a.crf,
           "-pix_fmt", "yuv420p", "-g", "48"]
    if a.maxrate:
        cmd += ["-maxrate", a.maxrate, "-bufsize", str(int(a.maxrate.rstrip("Mmk")) * 2) + "M"]
    cmd.append(str(tmp))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(a.f0, min(a.f1, TOTAL_N)):
        im = frame(fi)
        proc.stdin.write(im.tobytes())
        if fi % 240 == 0:
            el = time.time() - t0
            done = fi - a.f0 + 1
            print(f"  {done}/{a.f1-a.f0}  {done/max(el,1e-6):.1f} fps  {el:.0f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise SystemExit("ffmpeg failed")
    tmp.replace(out)
    print(f"{out}  {a.f1-a.f0} frames  {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
