# -*- coding: utf-8 -*-
"""从 story.py 推 out/zongji.srt（与烧进画面的字幕同一套规则）。

    py -3 scripts/make_srt.py            # 生成
    py -3 scripts/make_srt.py --check    # 只核对，不写
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import story as S


def ts(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s, ms = s + 1, 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build():
    starts, t = {}, 0.0
    for sh in S.SHOTS:
        starts[sh["id"]] = t
        t += sh["dur"]
    rows = []
    for ln in S.LINES:
        if not ln["en"]:
            continue
        t0 = starts[ln["shot"]] + ln["t"]
        dur = min(6.0, max(2.0, len(ln["en"]) / 13.0)) + 0.5
        rows.append((t0, t0 + dur, ln["en"]))
    for sid, a, b, txt in S.CARDS:
        rows.append((starts[sid] + a, starts[sid] + b, txt))
    rows.sort()
    out = []
    for i, (a, b, txt) in enumerate(rows, 1):
        out.append(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    body = build()
    p = ROOT / "out" / "zongji.srt"
    if a.check:
        if not p.exists():
            print(f"missing {p}")
            return 1
        if p.read_text(encoding="utf-8").strip() != body.strip():
            print("srt 与 story.py 不一致（改了台词或时间没重生成）")
            return 1
        print(f"srt 与单源一致（{body.count('-->')} 条）")
        return 0
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    print(f"{p}  {body.count('-->')} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
