# -*- coding: utf-8 -*-
"""一条命令把片子从素材建到成片。

     py -3 scripts/build_film.py            # 全流程：图版 → 音轨 → 分段并行渲染 → 拼接 → 混流
     py -3 scripts/build_film.py --skip-plates --skip-audio   # 只重渲画面

为什么分段并行：本机 12 核，单进程 0.55 s/帧、全片 7272 帧要 67 分钟；
四路并行压到 20 分钟出头。每段写自己的文件，绝不让两个 ffmpeg 碰同一个 mp4
（中枢教训：双 ffmpeg 同写一个文件会静默损坏，判据是抽帧 0/0）。
中间产物一律不带 -movflags +faststart（这台机器末尾重写 moov 会写坏 mp4）。
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUT = ROOT / "out"
PY = sys.executable

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import story as S


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run([str(c) for c in cmd], **kw)
    if r.returncode != 0:
        raise SystemExit(f"failed: {cmd[0]} (exit {r.returncode})")


def total_frames():
    return sum(int(round(s["dur"] * S.FPS)) for s in S.SHOTS)


def split(n, parts):
    """把 n 帧切成 parts 段，尽量均匀。"""
    step = (n + parts - 1) // parts
    return [(i, min(i + step, n)) for i in range(0, n, step)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-plates", action="store_true")
    ap.add_argument("--skip-audio", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--crf", default="23")
    ap.add_argument("--maxrate", default="14M")
    ap.add_argument("--keep-segs", action="store_true")
    a = ap.parse_args()

    BUILD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    if not a.skip_plates:
        print("[1/5] 图版处理", flush=True)
        run([PY, "scripts/plates.py"])

    if not a.skip_audio:
        print("[2/5] 音轨合成（含 edge-tts 配音）", flush=True)
        run([PY, "scripts/audio.py"])

    n = total_frames()
    segs = split(n, a.jobs)
    print(f"[3/5] 渲染 {n} 帧（{S.FPS} fps，{n / S.FPS:.1f} s）分 {len(segs)} 段，{a.jobs} 路并行", flush=True)

    # 颗粒层先由主进程生成一次，避免多个 worker 抢写同一个 npy
    import render as R
    R.grain_tiles()

    t0 = time.time()
    procs = []
    for i, (f0, f1) in enumerate(segs):
        out = BUILD / f"seg{i}.mp4"
        cmd = [PY, "scripts/render.py", "--from", str(f0), "--to", str(f1),
               "--out", str(out.relative_to(ROOT)), "--crf", a.crf,
               "--maxrate", a.maxrate]
        procs.append((i, f0, f1, subprocess.Popen([str(c) for c in cmd],
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.STDOUT)))
    # 最多 jobs 路并发：这里一次全起，超出核数由 OS 调度
    for i, f0, f1, p in procs:
        log = p.stdout.read().decode("utf-8", "replace") if p.stdout else ""
        rc = p.wait()
        tail = [ln for ln in log.strip().splitlines() if ln.strip()][-1:] or [""]
        print(f"  seg{i} [{f0},{f1}) exit={rc} {tail[0]}", flush=True)
        if rc != 0:
            print(log[-2000:], flush=True)
            raise SystemExit(f"seg{i} 渲染失败")

    print(f"  渲染用时 {time.time() - t0:.1f}s", flush=True)

    print("[4/5] 拼接", flush=True)
    lst = BUILD / "concat.txt"
    lst.write_text("".join(f"file 'seg{i}.mp4'\n" for i in range(len(segs))), encoding="utf-8")
    silent = BUILD / "silent.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", str(silent)])

    print("[5/5] 混流", flush=True)
    final = OUT / "zongji.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error",
         "-i", str(silent), "-i", str(BUILD / "audio.wav"),
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-shortest", str(final)])

    if not a.keep_segs:
        for i, _, _ in segs:
            (BUILD / f"seg{i}.mp4").unlink(missing_ok=True)
        silent.unlink(missing_ok=True)

    size = final.stat().st_size / 1e6
    print(f"完成 {final}  {size:.1f} MB  {n} 帧 / {n / S.FPS:.1f} s")


if __name__ == "__main__":
    main()
