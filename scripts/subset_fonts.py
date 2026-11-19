# -*- coding: utf-8 -*-
"""从唯一事实来源取字表，生成随包字体子集。

字表不另立一份（中枢 C-20261115-d40b5add 的教训：改场景标注会漏字，成片出现豆腐块）。
--check 只核对不生成：clone 里没有系统字体，也能验出「成品需要的字子集里有没有」。
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import story as S

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "fonts"
SRC = {
    "NotoSerifSC-Subset.ttf": Path("C:/Windows/Fonts/NotoSerifSC-VF.ttf"),
    "NotoSansSC-Subset.ttf": Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
}


def needed_chars() -> str:
    chars = set()
    chars |= set(S.TITLE_ZH) | set(S.TITLE_EN)
    for s, _ in S.CREDITS:
        chars |= set(s)
    for ln in S.LINES:
        chars |= set(ln["en"] or "")
    for _, _, _, txt in S.CARDS:
        chars |= set(txt)
    chars |= set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                 " .,'\"—–…:;!?()[]/-+&")
    chars |= set("总机编剧导演张一图版生成配音神经网络语音音乐效程序合成全部画面由式")
    chars.add(" ")
    return "".join(sorted(c for c in chars if c >= " "))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    chars = needed_chars()
    OUT.mkdir(parents=True, exist_ok=True)

    if a.check:
        from fontTools.ttLib import TTFont
        bad = 0
        for name in SRC:
            f = OUT / name
            if not f.exists():
                print(f"MISSING {name}")
                bad += 1
                continue
            cmap = TTFont(str(f), fontNumber=0).getBestCmap()
            miss = [c for c in chars if ord(c) not in cmap]
            if miss:
                print(f"{name}: 缺 {len(miss)} 字 -> {''.join(miss[:40])}")
                bad += 1
            else:
                print(f"{name}: ok ({len(chars)} chars)")
        return 1 if bad else 0

    from fontTools import subset
    from fontTools.ttLib import TTFont

    for name, src in SRC.items():
        if not src.exists():
            print(f"SKIP {name}: 本机没有 {src}（clone 环境正常）")
            continue
        f = TTFont(str(src), fontNumber=0)
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.recalc_bounds = True
        opts.drop_tables += ["DSIG"]
        sub = subset.Subsetter(options=opts)
        sub.populate(text=chars)
        sub.subset(f)
        dst = OUT / name
        f.save(str(dst))
        print(f"{name}: {dst.stat().st_size/1024:.0f} KB, {len(chars)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
