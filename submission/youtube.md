# YouTube 上传照抄单（成片已经做完，只剩这一步）

赛规要一个**公开可访问**的影片链接（YouTube 或 Vimeo）。一人只能交一件，别传两版。

## 1 上传设置

| 栏位 | 填什么 |
| --- | --- |
| 文件 | `out/zongji.mp4`（303 s / 1920×1080 / 294 MB / H.264 + AAC） |
| 标题 | `NUMBER, PLEASE (总机) — Artefact AI Film Festival 2026` |
| 简介 | 复制下面「简介全文」 |
| 缩略图 | `submission/thumb-1280x720.jpg`（1280×720，已按规范导出） |
| 播放列表 | 可不填 |
| 受众 | **不是「为儿童打造」** |
| 可见性 | **公开（Public）** —— 赛规要求评审能打开；「不公开列出」不算公开 |
| 语言 | 影片语言：中文；字幕语言：英文 |
| 字幕 | 上传 `out/zongji.srt`（英文），不要用自动字幕 |
| 结束画面 / 卡片 | 都关掉，别加片尾推荐 |

## 2 简介全文（直接粘）

```
总机 / NUMBER, PLEASE
A short film by 张一 (Zhang Yi)

1987, winter. The last night of a county's manual telephone exchange.
At eight the next morning the town goes automatic. Until then, one operator
still has to say "number, please" — and one call comes in that she can no
longer connect.

—

Official selection entry for the Artefact AI Film Festival, Third Edition
(Paris, 2026), theme: (Dis)Connection.

Runtime 5:03 · Black and white · Mandarin with English subtitles

AI USE (all three phases, as required by the festival)
· Pre-production — screenplay, character development, dialogue and the
  23-shot storyboard were drafted and iterated with a large language model.
· Production — all 21 image plates were generated with a text-to-image
  model (Hunyuan ImageGen); no stock footage, no live action.
· Post-production — voice performance generated with a neural TTS
  (edge-tts, five voices); score and all 40 sound effects synthesised
  procedurally; picture, grain, snow, subtitles and grade rendered
  frame by frame from a single source file.
No paid assets, no purchased music, no camera.

Production log and full credits: see the festival submission package.
```

## 3 上传之后

1. 等处理完，用**无痕窗口**打开链接，确认不登录也能播、有声音、字幕是英文而不是自动生成。
2. 把链接贴回 AME-1474。
3. 到 `artefact-ai-film-festival.com` 的 candidate portal 提交：链接 + 视觉图（`submission/key-art.jpg`）+ synopsis（`submission/synopsis.md`）+ presentation（`submission/presentation.md`）+ production log（`docs/03-PRODUCTION-LOG.md`）。
4. AI 用途勾选：VISUAL PREPARATION / DIALOGUE / VOICE / ANIMATION / AUDIO；**IMAGE TO VIDEO 不勾**（本片是逐帧渲染，不是图生视频）。
5. 回执截图贴回 AME-1474。

## 4 别做的事

- 不要加速、不要压缩、不要重新上传第二版（一人一件）。
- 不要在简介里写"100% AI 生成"这种绝对话——片子里有人写的剧本定稿、手工剪辑决策、程序合成的音乐；按上面那段分阶段写，反而更可信。
- 不要给影片加背景音乐库里的曲子：全片声音都是本片合成的，版权链条干净。
