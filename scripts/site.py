# -*- coding: utf-8 -*-
"""生成一个静态阅稿页（GitHub Pages 用）：剧照 + 简介 + 制作记录 + 技术参数。

不嵌视频（5 分钟成片 300+ MB，Pages 放不下），只放剧照与文字。
    py -3 scripts/site.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
IMG = SITE / "img"

STILLS = [
    ("06", "台。整面塞孔板，一盏红灯。"),
    ("30", "她的手：四十一岁，冻裂的，没有戒指。"),
    ("62", "小孩那通电话。灯从下巴底下打上来。"),
    ("100", "老周站在门口，雪在肩上。"),
    ("146", "塞孔不亮。她再试一次。"),
    ("165", "新电缆已经架上了。"),
    ("201", "巷子尽头，门上倒贴的红纸。"),
    ("224", "门开了。"),
    ("262", "她掏出耳机，看着它。"),
]

CSS = """
:root{--ink:#e9e6e0;--dim:#9a958c;--bg:#0c0c0d;--line:#26262a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:16px/1.85 "Noto Serif SC","Songti SC",Georgia,serif}
.wrap{max-width:1000px;margin:0 auto;padding:0 28px}
header{padding:90px 0 40px;border-bottom:1px solid var(--line)}
h1{font-size:56px;margin:0 0 6px;letter-spacing:.08em;font-weight:600}
.en{font:400 14px/1.6 ui-monospace,monospace;letter-spacing:.34em;color:var(--dim)}
.meta{margin-top:26px;color:var(--dim);font-size:14px}
.meta b{color:var(--ink);font-weight:500}
section{padding:56px 0;border-bottom:1px solid var(--line)}
h2{font-size:13px;letter-spacing:.3em;color:var(--dim);font-weight:500;
 text-transform:uppercase;margin:0 0 26px}
p{margin:0 0 18px;max-width:62ch}
figure{margin:0 0 44px}
figure img{width:100%;display:block;background:#111}
figcaption{color:var(--dim);font-size:13px;margin-top:10px;
 font-family:ui-monospace,monospace}
table{width:100%;border-collapse:collapse;font-size:14px}
td{padding:10px 12px 10px 0;border-bottom:1px solid var(--line);vertical-align:top}
td:first-child{color:var(--dim);width:34%;white-space:nowrap}
a{color:#d8c9a8}
footer{padding:40px 0 90px;color:var(--dim);font-size:13px}
.red{color:#c0392b}
"""


def build():
    IMG.mkdir(parents=True, exist_ok=True)
    figs = []
    for t, cap in STILLS:
        dst = IMG / f"s{t}.jpg"
        if not dst.exists():
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(ROOT / "out" / "zongji.mp4"),
                            "-ss", t, "-frames:v", "1", "-q:v", "3", str(dst)], check=True)
        figs.append(f'<figure><img src="img/s{t}.jpg" alt="{cap}">'
                    f'<figcaption>{t.zfill(3)} s — {cap}</figcaption></figure>')

    syn = (ROOT / "submission" / "synopsis.md").read_text(encoding="utf-8")
    body = "\n".join(
        f"<p>{p.strip()}</p>" for p in syn.split("\n\n")
        if p.strip() and not p.startswith("#"))

    shutil.copy(ROOT / "submission" / "key-art.jpg", SITE / "key-art.jpg")

    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>总机 / NUMBER, PLEASE</title>
<style>{CSS}</style></head><body>
<div class="wrap">
<header>
  <div class="en">ARTEFACT AI FILM FESTIVAL / THIRD EDITION / (DIS)CONNECTION</div>
  <h1>总机</h1>
  <div class="en">NUMBER, PLEASE</div>
  <div class="meta">
    <b>303 s</b> · 1920×1080 · 24 fps · 黑白（唯一彩色：门上红纸） · 汉语对白 / 英文字幕<br>
    1987 年冬，北方县城最后一夜的人工电话交换所。
  </div>
</header>

<section>
  <h2>Synopsis</h2>
  {body}
</section>

<section>
  <h2>Stills</h2>
  {''.join(figs)}
</section>

<section>
  <h2>Production</h2>
  <table>
    <tr><td>前制 · 生成式 AI</td><td>剧本、人物、对白、23 镜分镜表由语言模型起草并迭代，作者定稿</td></tr>
    <tr><td>制作 · 生成式 AI</td><td>21 张 1024×1536 图版由图像生成模型产出（35mm 黑白剧照质感）</td></tr>
    <tr><td>后制 · 生成式 AI</td><td>五个角色的配音由神经网络 TTS（edge-tts）生成</td></tr>
    <tr><td>后制 · 程序合成</td><td>音乐与全部音效由 numpy 合成；剪辑、颗粒、雪、字幕逐帧渲染</td></tr>
    <tr><td>全片主音</td><td><span class="red">450 Hz</span> 拨号音 —— 出现三次，最后一次在片尾</td></tr>
    <tr><td>不用</td><td>无付费素材、无购买音乐、无实拍、无外部音频</td></tr>
  </table>
</section>

<section>
  <h2>Spec</h2>
  <table>
    <tr><td>时长</td><td>303.000 s（上限 314 s）</td></tr>
    <tr><td>镜头</td><td>23 镜 / 5 幕</td></tr>
    <tr><td>台词</td><td>30 句中文；英文字幕 29 条 + 4 张说明卡，烧入画面</td></tr>
    <tr><td>声音</td><td>48 kHz 立体声；40 处音效 / 33 种，全部程序合成</td></tr>
    <tr><td>交付</td><td>成片 mp4 + srt + 视觉图 + synopsis + presentation + production log</td></tr>
  </table>
</section>

<footer>
  <img src="key-art.jpg" alt="key art" style="width:100%;margin-bottom:28px">
  成片未嵌在本页（300+ MB）。本地路径 out/zongji.mp4，投稿走 YouTube 链接。<br>
  本页由 scripts/site.py 生成；文字与图片均与 story.py / docs 同源。
</footer>
</div></body></html>"""
    (SITE / "index.html").write_text(html, encoding="utf-8")
    print(f"{SITE/'index.html'}  {(SITE/'index.html').stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    build()
