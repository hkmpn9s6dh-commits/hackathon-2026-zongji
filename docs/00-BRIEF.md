# 00 — 这届要什么，我们交什么

**Artefact AI Film Festival · 第三屆**（巴黎，Artefact × mk2 Bibliothèque）
主题 **(Dis)Connection**｜投稿 2026-09-02 ~ **2026-12-02**｜观众投票 12-09 ~ 2027-01-13｜评审 2027-01｜颁奖 2027-02

## 官方硬条件（逐条抄自 rules 页）

| 官方原文 | 我们的做法 |
| --- | --- |
| open to everyone worldwide | 个人投稿，无国籍/年龄/经验限制 |
| films should be a **maximum of 314 seconds** | **303.000 s**（含片尾字幕），`ffprobe` 读出来，不按分镜表算 |
| **at least one Gen AI Technology in each of the 3 phases**：pre-production / production / post-production | 前制＝语言模型起草剧本与分镜；制作＝ImageGen 出 21 张图版；后制＝TTS 配音 + 程序合成音乐音效 + 程序化剪辑与调色。逐条见 `03-PRODUCTION-LOG.md` |
| 交件：影片链接、一张视觉图、synopsis、short presentation、production log | `submission/` 四件 + 本文档的照抄单 `05-SUBMISSION.md` |
| 一人只能交一件 | 本片是本账号唯一投稿 |

官方**没有**明说必须公开（public）还是可 unlisted——照最严的准备：上传 **public**，
带英文字幕，简介里写明使用的生成式 AI。

## 主题怎么落地

(Dis)Connection 直译是"断连"。最容易被写成"人和人不再说话"，也太容易写成"AI 让人孤立"。
我们选了一个**物理意义上的断连**：**1987 年冬**，县城人工电话交换所割接成自动。
线被剪断的那一夜，话务员手里还剩一句没送到的口信。

> 线断了，人还可以过去。—— 这是全片的主张。

## 片子

| 项 | 值 |
| --- | --- |
| 片名 | 总机 / NUMBER, PLEASE |
| 时长 | 303.000 s（上限 314） |
| 画幅 | 1920×1080 / 24 fps / 黑白（唯一彩色：门上红纸） |
| 语言 | 汉语对白 + 英文字幕（烧入 + srt） |
| 镜头 | 23 个镜头，5 幕 |
| 声音 | 全程序合成 + edge-tts 配音；主音是 450 Hz 拨号音 |
| 生成式 AI | 前制/制作/后制三阶段各有 |

## 为什么这个题不撞车

官方提示的三类第一反应：机器人学会爱、城市里没人抬头、AI 与人对话。
本片的"断连"是一个**已经发生过**的技术事件（人工台退网），人物不是被 AI 取代，
而是被一台机器取代之后仍然把话送到。它不控诉技术，也不歌颂技术——只记录一个人怎么交接。
