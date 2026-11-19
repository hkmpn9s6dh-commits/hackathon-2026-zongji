# 总机 / NUMBER, PLEASE

Artefact AI Film Festival · 第三屆（Paris）参赛短片。
1987 年冬，北方县城最后一夜的人工电话交换所。割接前，一通"已经打不通"的电话。

- 成片：`out/zongji.mp4`（1920×1080 / 24 fps / 303.0 s / H.264 + AAC）
- 字幕：`out/zongji.srt`
- 提交材料：`submission/`
- 唯一事实来源：**`story.py`**

## 一条命令

```bash
bash verify.sh          # 字体子集 → 图版 → 音轨 → 渲染 → 字幕 → 断言
bash verify.sh --quick  # 用已有成片只跑断言
```

依赖：Python（numpy、Pillow、fontTools）、ffmpeg/ffprobe、`edge-tts`（配音需要网络）。

## 目录

```
story.py              唯一事实来源：镜头表 / 台词 / 说明卡 / 音效 / 片尾
SPEC.md               开拍前的契约：硬指标与自我约束
verify.sh             一条命令从零到交付物
scripts/
  plates.py           raw 图版 → 成片图版（去水印、裁 16:9、黑白、留一处红）
  audio.py            配音 + 全部音效/音乐合成 → build/audio.wav
  render.py           逐帧渲染（运镜、颗粒、雪、灯、字幕、片名、片尾）
  build_film.py       分段并行渲染 → 拼接 → 混流
  make_srt.py         从 story.py 推 srt
  verify.py           40+ 条断言
  subset_fonts.py     随包带字体（子集）
plates/raw/           ImageGen 原件（带 AIGC 元数据，保留作证据）
plates/               处理后的图版 2400×1350
docs/                 00 需求 / 01 剧本 / 02 影像与声音 / 03 制作记录 / 04 教训 / 05 提交照抄单
submission/           synopsis / presentation / key art
proof/                证据帧与 clone 复验日志
```

## 为什么所有东西都从 `story.py` 长出来

上一场（AME-1435）改了时长忘了重生成分镜表，只有在全新 clone 里才被抓到。
本片把这条做成了结构：镜头表、台词、字幕、srt、配音摆位、音效时间全都读同一个文件；
`verify.py` 还会核对"注释里写的片长"是否等于实测片长——就是防这一手。
