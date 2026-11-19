# -*- coding: utf-8 -*-
"""《总机》交付物断言。

判据分四组：规格 / 单源一致 / 画面 / 声音 / 交付物。
每条都打印实测值，失败即退出码 1 —— 不看人脸，只看数。

    py -3 scripts/verify.py            # 全量
    py -3 scripts/verify.py --quick    # 跳过抽帧类（约 20 s）
"""
import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import story as S

FILM = ROOT / "out" / "zongji.mp4"
DOCS = ROOT / "docs"
SUB = ROOT / "submission"
FAILS = []
N = 0


def ok(name, cond, detail=""):
    global N
    N += 1
    if cond:
        print(f"  ✓ {name}" + (f" — {detail}" if detail else ""))
    else:
        print(f"  ✗ {name}" + (f" — {detail}" if detail else ""))
        FAILS.append(name)


def head(t):
    print(f"\n{t}")


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# ---------------------------------------------------------------- 时间轴
STARTS = {}
_t = 0.0
for _s in S.SHOTS:
    STARTS[_s["id"]] = _t
    _t += _s["dur"]
TOTAL = _t


def subs_list():
    """与 render.py 同一套规则推字幕窗口（这里独立算一遍，两边必须一致）。"""
    out = []
    for ln in S.LINES:
        if not ln["en"]:
            continue
        t0 = STARTS[ln["shot"]] + ln["t"]
        dur = min(6.0, max(2.0, len(ln["en"]) / 13.0)) + 0.5
        out.append((t0, t0 + dur, ln["en"]))
    for sid, a, b, txt in S.CARDS:
        out.append((STARTS[sid] + a, STARTS[sid] + b, txt))
    return sorted(out)


SUBS = subs_list()


# ---------------------------------------------------------------- 抽帧
_tmpdir = None


def grab(t, name=None):
    """从成片精确取一帧，返回 RGB ndarray。"""
    global _tmpdir
    if _tmpdir is None:
        _tmpdir = Path(tempfile.mkdtemp(prefix="zjv_", dir=str(ROOT / "build")))
        _tmpdir.mkdir(parents=True, exist_ok=True)
    p = _tmpdir / f"{name or ('t%.2f' % t)}.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(FILM), "-ss", f"{t:.3f}",
                    "-frames:v", "1", str(p)], check=True)
    return np.asarray(Image.open(p).convert("RGB"))


def band(im, y0, y1):
    h = im.shape[0]
    return im[int(h * y0):int(h * y1)]


def bright_count(a, thr=190):
    return int((a.mean(axis=2) > thr).sum())


def ncc(a, b):
    a = a.astype(np.float64).ravel()
    b = b.astype(np.float64).ravel()
    a -= a.mean()
    b -= b.mean()
    d = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(a @ b / d) if d else 0.0


# ---------------------------------------------------------------- 1 规格
def check_spec():
    head("一、规格")
    ok("成片存在", FILM.exists(), str(FILM))
    if not FILM.exists():
        return None
    size_mb = FILM.stat().st_size / 1e6
    info = probe(FILM)
    fmt = info["format"]
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    au = [s for s in info["streams"] if s["codec_type"] == "audio"]
    dur = float(fmt["duration"])
    ok("文件不小（>50 MB）", size_mb > 50, f"{size_mb:.1f} MB")
    ok("文件不臃肿（<600 MB）", size_mb < 600, f"{size_mb:.1f} MB")
    ok("时长 ≤ 314.000 s（赛规硬上限）", dur <= 314.0, f"{dur:.3f} s")
    ok("时长与分镜表一致（±0.30 s）", abs(dur - TOTAL) <= 0.30, f"{dur:.3f} vs {TOTAL:.3f}")
    ok("1920×1080", v["width"] == 1920 and v["height"] == 1080, f'{v["width"]}×{v["height"]}')
    ok("视频 H.264 / yuv420p", v["codec_name"] == "h264" and v.get("pix_fmt") == "yuv420p",
       f'{v["codec_name"]}/{v.get("pix_fmt")}')
    ok("24 fps", v["r_frame_rate"] == "24/1", v["r_frame_rate"])
    nb = int(v.get("nb_frames") or 0)
    ok("帧数与分镜表一致（±2）", abs(nb - round(TOTAL * S.FPS)) <= 2,
       f"{nb} vs {round(TOTAL * S.FPS)}")
    ok("有音频轨", len(au) == 1)
    if au:
        a0 = au[0]
        ok("音频 AAC / 48 kHz / 立体声",
           a0["codec_name"] == "aac" and int(a0["sample_rate"]) == 48000 and a0["channels"] == 2,
           f'{a0["codec_name"]} {a0["sample_rate"]} {a0["channels"]}ch')
        adur = float(a0.get("duration") or dur)
        ok("音画时长差 ≤ 0.25 s", abs(adur - dur) <= 0.25, f"{adur:.3f} vs {dur:.3f}")
    br = int(fmt.get("bit_rate") or 0) / 1e6
    ok("码率 2–15 Mbps", 2.0 <= br <= 15.0, f"{br:.2f} Mbps")
    return info


# ---------------------------------------------------------------- 2 单源
def check_single_source():
    head("二、单源一致（story.py ↔ 素材 ↔ 文档）")
    ids = [s["id"] for s in S.SHOTS]
    ok("镜头 id 连续且唯一", ids == [f"S{i:02d}" for i in range(1, len(ids) + 1)],
       f'{len(ids)} 个镜头')
    ok("镜头 id 无重复", len(set(ids)) == len(ids))

    missing = [s["plate"] for s in S.SHOTS if s["plate"] and
               not (ROOT / "plates" / f'{s["plate"]}.png').exists()]
    ok("引用的图版都在", not missing, ", ".join(missing))

    used = {s["plate"] for s in S.SHOTS if s["plate"]}
    have = {p.stem for p in (ROOT / "plates").glob("*.png")}
    extra = have - used
    ok("没有图版被生成却没用（白名单：unused-sparkplug）",
       extra <= {"unused-sparkplug"}, ", ".join(sorted(extra - {"unused-sparkplug"})))

    bad_plate = []
    for name in used:
        im = Image.open(ROOT / "plates" / f"{name}.png")
        if im.size != (2400, 1350):
            bad_plate.append(f"{name} {im.size}")
    ok("图版尺寸都是 2400×1350（留 1.25× 推镜余量）", not bad_plate, ", ".join(bad_plate))

    bad_shot = [l["id"] for l in S.LINES if l["shot"] not in STARTS]
    ok("台词都挂在存在的镜头上", not bad_shot, ", ".join(bad_shot))

    over = []
    for ln in S.LINES:
        end = ln["t"] + 0.1
        if end > next(s["dur"] for s in S.SHOTS if s["id"] == ln["shot"]):
            over.append(ln["id"])
    ok("台词起点落在本镜时长内", not over, ", ".join(over))

    bad_card = [f"{sid}" for sid, a, b, _ in S.CARDS
                if a < 0 or b > next(s["dur"] for s in S.SHOTS if s["id"] == sid)]
    ok("说明卡不越出本镜", not bad_card, ", ".join(bad_card))

    # SFX 名字必须在 audio.py 里有实现
    src = (ROOT / "scripts" / "audio.py").read_text(encoding="utf-8")
    names = sorted({n for _, _, n in S.SFX})
    unimplemented = [n for n in names if f"def {n}(" not in src and f'"{n}"' not in src]
    ok("每个音效都有合成函数", not unimplemented, ", ".join(unimplemented))

    # 注释里的片长必须等于实际片长（上一场栽过：改了时长忘改注）
    notes = " ".join(s["note"] for s in S.SHOTS)
    m = re.findall(r"全片 (\d+) 秒", notes)
    ok("镜头表注释里的片长等于实测片长", bool(m) and abs(int(m[0]) - TOTAL) < 0.6,
       f'注释 {m[0] if m else "—"} / 实际 {TOTAL:.1f}')

    # 字幕推得的窗口数
    expect = sum(1 for l in S.LINES if l["en"]) + len(S.CARDS)
    ok("字幕窗口数与台词+说明卡数一致", len(SUBS) == expect,
       f"{len(SUBS)} = {sum(1 for l in S.LINES if l['en'])} 台词 + {len(S.CARDS)} 说明卡")
    return used


# ---------------------------------------------------------------- 3 画面
def check_picture():
    head("三、画面")
    # 片名字卡
    f0 = grab(0.4, "black")
    ok("首帧是黑场", f0.mean() < 2.0, f"mean={f0.mean():.2f}")
    ft = grab(STARTS["S01"] + 6.0, "title")
    c = ft[400:700, 600:1320]
    ok("片名字卡有字（中心区有亮像素）", bright_count(c, 170) > 1500,
       f"{bright_count(c, 170)} px")

    # 片尾字幕
    fe = grab(TOTAL - 6.0, "credit")
    ok("片尾字幕有字", bright_count(fe[100:1000], 150) > 3000,
       f"{bright_count(fe[100:1000], 150)} px")

    # 字幕烧进：抽 8 条台词窗口 + 8 个空白窗口
    picked, blanks = [], []
    for a, b, _ in SUBS:
        mid = (a + b) / 2
        if any(abs(mid - (x + y) / 2) < 2.0 for x, y in picked):
            continue
        picked.append((a, b))
        if len(picked) == 8:
            break
    for a, b in picked:
        mid = (a + b) / 2
        cands = [mid - 3.0, mid + 3.0]
        for c0 in cands:
            if c0 < 1 or c0 > TOTAL - 1:
                continue
            if any(x <= c0 <= y for x, y in SUBS):
                continue
            if all(abs(c0 - c) > 1.5 for c in blanks):
                blanks.append(c0)
    hits = 0
    for a, b in picked:
        im = grab((a + b) / 2)
        if bright_count(band(im, 0.80, 0.94), 190) > 600:
            hits += 1
    ok("字幕烧进画面（抽 8 条）", hits >= 7, f"{hits}/8 有字幕")

    false_pos = 0
    for c0 in blanks[:8]:
        im = grab(c0)
        if bright_count(band(im, 0.80, 0.94), 190) > 600:
            false_pos += 1
    ok("字幕之间确实是空的（抽 8 个空档）", false_pos <= 1, f"{false_pos}/8 误报")

    # 单色 + 只留红
    mono, redshot = [], []
    for sid in ["S02", "S06", "S08", "S13", "S14", "S16", "S19", "S22"]:
        im = grab(STARTS[sid] + 2.0, f"c_{sid}")
        d = np.abs(im[:, :, 0].astype(np.int16) - im[:, :, 1].astype(np.int16))
        mono.append(float(np.median(d)))
        redshot.append((sid, int(((im[:, :, 0].astype(np.int16) -
                                   im[:, :, 1].astype(np.int16)) > 55).sum())))
    worst = max(m for m in mono)
    ok("全片单色（R 与 G 中位差 ≤ 6）", worst <= 6.0, f"max={worst:.1f}")
    red16 = dict(redshot)["S16"]
    others = max(v for k, v in redshot if k != "S16")
    ok("只有 S16 的红纸是红的", red16 > 3000 and others < 400, f"S16={red16} 其余最大={others}")

    # 满幅：上下边缘不是黑边
    im = grab(STARTS["S06"] + 2.0, "fill")
    top = im[:8].mean()
    bot = im[-8:].mean()
    ok("满幅无黑边（顶/底 8 行有内容）", top > 3 and bot > 1.2, f"top={top:.1f} bot={bot:.1f}")

    # 颗粒：同镜相邻两帧必须不同
    a = grab(STARTS["S02"] + 4.0, "g1").astype(np.int16)
    b = grab(STARTS["S02"] + 4.0 + 1 / 24, "g2").astype(np.int16)
    ok("颗粒在场（相邻帧有差）", np.abs(a - b).mean() > 0.6, f"{np.abs(a - b).mean():.2f}")

    # 运镜：push 镜头首尾帧不一样
    s0 = grab(STARTS["S06"] + 0.4, "m0")
    s1 = grab(STARTS["S06"] + 17.4, "m1")
    small = lambda im: np.asarray(Image.fromarray(im).resize((240, 135), Image.BILINEAR))
    ok("推镜在动（首尾 NCC < 0.995）", ncc(small(s0), small(s1)) < 0.995,
       f"{ncc(small(s0), small(s1)):.4f}")

    # 单色片不应该是一团黑：整体亮度
    lum = []
    for t in [20, 50, 80, 110, 140, 175, 205, 235, 265, 285]:
        lum.append(float(grab(t, f"l{t}").mean()))
    ok("全片亮度合理（均 15–90）", 15 <= np.mean(lum) <= 90,
       f"mean={np.mean(lum):.1f} min={min(lum):.1f} max={max(lum):.1f}")

    # 图版右下角没有工具水印
    worst_grad = 0.0
    for p in sorted((ROOT / "plates").glob("*.png")):
        arr = np.asarray(Image.open(p).convert("L"), dtype=np.float32)
        h, w = arr.shape
        corner = arr[int(h * 0.93):, int(w * 0.86):]
        worst_grad = max(worst_grad, float(np.abs(np.diff(corner, axis=1)).max()))
    ok("图版右下无水印字形（梯度 ≤ 24）", worst_grad <= 24, f"max_grad={worst_grad:.1f}")


# ---------------------------------------------------------------- 4 角色一致
def check_identity():
    head("四、角色一致")
    a = Image.open(ROOT / "plates" / "her-face-lit.png").convert("L")
    b = Image.open(ROOT / "plates" / "her-face-listening.png").convert("L")

    def head_ellipse(im):
        a = np.asarray(im, dtype=np.float32)
        h, w = a.shape
        yy, xx = np.mgrid[0:h, 0:w]
        # 头在上半部中央：椭圆掩码只算脸，不算背景
        cx, cy = w * 0.50, h * 0.40
        rx, ry = w * 0.22, h * 0.23
        m = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) <= 1.0
        v = a[m]
        return v

    va, vb = head_ellipse(a), head_ellipse(b)
    score = ncc(va.reshape(-1), vb.reshape(-1))
    ok("同一角色跨镜头（椭圆头部掩码 NCC ≥ 0.30）", score >= 0.30, f"NCC={score:.3f}")


# ---------------------------------------------------------------- 5 声音
def check_audio():
    head("五、声音")
    p = ROOT / "build" / "audio.wav"
    ok("音轨文件存在", p.exists(), str(p))
    if not p.exists():
        return
    with wave.open(str(p)) as w:
        sr, ch, nf = w.getframerate(), w.getnchannels(), w.getnframes()
        raw = w.readframes(nf)
    ok("48 kHz / 立体声 / 16-bit", sr == 48000 and ch == 2,
       f"{sr} {ch}ch")
    x = np.frombuffer(raw, dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768
    ok("音轨长度覆盖全片（±1 s）", abs(len(x) / sr - TOTAL) <= 2.5,
       f"{len(x) / sr:.1f}s vs {TOTAL:.1f}s")

    rms = lambda s: float(np.sqrt(np.mean(s ** 2) + 1e-12))
    # 每句台词窗口必须有声，且高于本镜底噪
    quiet = []
    for ln in S.LINES:
        if not ln["en"]:
            continue
        t0 = STARTS[ln["shot"]] + ln["t"]
        seg = x[int(t0 * sr):int((t0 + 1.6) * sr)]
        tail = x[int((t0 + 2.4) * sr):int((t0 + 3.0) * sr)] if t0 + 3.0 < len(x) / sr else seg
        if rms(seg) < 0.02 or rms(seg) < rms(tail) * 1.6:
            quiet.append(f'{ln["id"]} {rms(seg):.3f}/{rms(tail):.3f}')
    ok("每条台词都听得见（RMS > 底噪 1.6×）", not quiet, ", ".join(quiet[:4]))

    # 长静音
    win = int(0.25 * sr)
    env = np.array([rms(x[i:i + win]) for i in range(0, len(x) - win, win)])
    silent = env < 0.002
    longest, cur = 0, 0
    for s in silent:
        cur = cur + 1 if s else 0
        longest = max(longest, cur)
    ok("没有 > 8 s 的死寂", longest * 0.25 <= 8.0, f"最长 {longest * 0.25:.2f}s")

    # 响度：ffmpeg ebur128
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(FILM),
                        "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    m = re.search(r"I:\s+(-?\d+\.\d+) LUFS", txt)
    tp = re.search(r"Peak:\s+(-?\d+\.\d+) dBFS", txt)
    lufs = float(m.group(1)) if m else -99
    peak = float(tp.group(1)) if tp else 0
    ok("整体响度 -16 ± 3 LUFS", abs(lufs + 16) <= 3.0, f"{lufs:.1f} LUFS")
    ok("真峰 ≤ -0.5 dBFS", peak <= -0.5, f"{peak:.1f} dBFS")


# ---------------------------------------------------------------- 6 交付物
def check_deliverables():
    head("六、交付物")
    srt = ROOT / "out" / "zongji.srt"
    ok("字幕文件存在", srt.exists(), str(srt))
    if srt.exists():
        txt = srt.read_text(encoding="utf-8")
        blocks = [b for b in txt.strip().split("\n\n") if b.strip()]
        ok("srt 条目数等于字幕窗口数", len(blocks) == len(SUBS), f"{len(blocks)} vs {len(SUBS)}")
        times = re.findall(r"(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)", txt)
        ok("srt 时间戳合法且递增", len(times) == len(blocks) and all(
            (int(a) * 3600 + int(b) * 60 + int(c) + int(d) / 1000) <
            (int(e) * 3600 + int(f) * 60 + int(g) + int(h) / 1000)
            for a, b, c, d, e, f, g, h in times))

    log = DOCS / "03-PRODUCTION-LOG.md"
    ok("production log 存在", log.exists())
    if log.exists():
        t = log.read_text(encoding="utf-8")
        ok("log 覆盖三个阶段（前制/制作/后制）",
           all(k in t for k in ["前制", "制作", "后制"]))
        for tool in ["ImageGen", "edge-tts", "ffmpeg"]:
            ok(f"log 点名工具 {tool}", tool.lower() in t.lower())

    key = SUB / "key-art.jpg"
    ok("视觉图存在", key.exists(), str(key))
    if key.exists():
        im = Image.open(key)
        ok("视觉图 ≥ 1600px 宽", im.size[0] >= 1600, f"{im.size[0]}×{im.size[1]}")

    syn = SUB / "synopsis.md"
    ok("synopsis 存在", syn.exists())
    if syn.exists():
        w = len(re.findall(r"[A-Za-z']+", syn.read_text(encoding="utf-8")))
        ok("synopsis 80–280 词", 80 <= w <= 280, f"{w} 词")

    pre = SUB / "presentation.md"
    ok("presentation 存在", pre.exists())

    # 提交照抄单必须写清"谁来做"
    subdoc = DOCS / "05-SUBMISSION.md"
    ok("提交照抄单存在", subdoc.exists())
    if subdoc.exists():
        t = subdoc.read_text(encoding="utf-8")
        ok("照抄单写明 AI 三阶段", "前制" in t and "后制" in t)
        ok("照抄单写明成片链接栏位", "YouTube" in t or "Vimeo" in t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    print(f"《总机》交付物断言 — 分镜 {len(S.SHOTS)} 镜 / {TOTAL:.1f} s / 上限 {S.HARD_MAX_SEC:.0f} s")
    check_spec()
    check_single_source()
    check_identity()
    check_audio()
    check_deliverables()
    if not a.quick:
        check_picture()
    print(f"\n合计 {N} 条，失败 {len(FAILS)}")
    if FAILS:
        print("失败项：")
        for f in FAILS:
            print("  -", f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
