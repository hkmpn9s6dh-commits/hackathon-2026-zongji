# -*- coding: utf-8 -*-
"""《总机》/ NUMBER, PLEASE —— 唯一事实来源。

片子的一切都从这里长出来：镜头表、台词、字幕、音效、调色。
改片子只改这一个文件；docs/ 里的镜头表由 scripts/report.py 反向生成并 --check。

为什么是单源：上一场（AME-1435）改了时长忘了重生成分镜表，只有在 clone 里才被抓到。
"""

TITLE_ZH = "总机"
TITLE_EN = "NUMBER, PLEASE"

FPS = 24
W, H = 1920, 1080

# 片子总长上限（赛规 314 秒，含片尾字幕）
HARD_MAX_SEC = 314.0

# ---------------------------------------------------------------- 镜头表
# plate: plates/<name>.png；None = 纯黑场
# move:  (kind, a, b)  a/b 是裁切窗的缩放与位移，渲染时按进度插值
# ov:    程序化叠加层（雪、蒸汽、呼吸、灯闪、胶片层）
SHOTS = [
    dict(
        id="S01", dur=12.0, plate=None, move=None, ov=[],
        # 黑场：一声继电器，一句「喂，总机」，然后出片名
        note="黑场开场。先有声，再有字。",
    ),
    dict(
        id="S02", dur=10.0, plate="board-wide", move=("push", 1.00, 1.10), ov=["grain"],
        note="整面塞孔板，一盏红灯。她坐下、戴上耳机。",
    ),
    dict(
        id="S03", dur=9.0, plate="panel-macro", move=("pan", (0.02, 0.0), (0.16, 0.0)), ov=["grain", "lamp"],
        note="塞孔微距，塞绳垂着。她插进一个孔。",
    ),
    dict(
        id="S04", dur=12.0, plate="hands-plug", move=("push", 1.00, 1.12), ov=["grain"],
        note="她的手：四十一岁，冻裂的，没有戒指。",
    ),
    dict(
        id="S05", dur=12.0, plate="her-board-back", move=("static", 1.06), ov=["grain", "lamp"],
        note="她的背影与整板。灯一盏一盏亮。",
    ),
    dict(
        id="S06", dur=18.0, plate="her-face-lit", move=("push", 1.00, 1.14), ov=["grain"],
        note="她的脸，灯从下巴底下打上来。小孩那通电话。",
    ),
    dict(
        id="S07", dur=10.0, plate="window-snow", move=("static", 1.04), ov=["snow", "grain"],
        note="窗、雪、炉子。夜更深。",
    ),
    dict(
        id="S08", dur=22.0, plate="laozhou-door", move=("push", 1.00, 1.08), ov=["grain"],
        note="老周站在门口，雪在肩上，把交接单放下。",
    ),
    dict(
        id="S09", dur=9.0, plate="form-seal", move=("push", 1.02, 1.16), ov=["grain"],
        note="交接单与红章。她签字。",
    ),
    dict(
        id="S10", dur=12.0, plate="board-wide", move=("pan", (0.42, 0.0), (0.52, 0.0)), ov=["grain", "lamp", "dim"],
        note="灯一盏一盏灭。她起身、兑水、上弦。",
    ),
    dict(
        id="S11", dur=11.0, plate="headset-hook", move=("push", 1.00, 1.10), ov=["grain"],
        note="耳机挂在钩上。她伸手拿下来——最后一通。",
    ),
    dict(
        id="S12", dur=18.0, plate="board-dead-lamp", move=("push", 1.00, 1.13), ov=["grain", "dying"],
        note="塞孔不亮。她再试一次。还是不亮。灯跟着话路一起退。",
    ),
    dict(
        id="S13", dur=16.0, plate="her-face-listening", move=("push", 1.00, 1.12), ov=["grain"],
        note="她听着话单上的字。抬头看整板——全黑。",
    ),
    dict(
        id="S14", dur=12.0, plate="street-pole", move=("pan", (0.0, 0.04), (0.10, 0.02)), ov=["snow", "grain"],
        note="街上。雪。电线杆上的新电缆与纸牌。",
    ),
    dict(
        id="S15", dur=10.0, plate="new-exchange", move=("push", 1.00, 1.10), ov=["snow", "grain"],
        note="新机房：水泥盒子，一扇亮着的窗，低频嗡鸣。",
    ),
    dict(
        id="S16", dur=10.0, plate="lane-door", move=("push", 1.00, 1.12), ov=["snow", "grain"],
        note="巷子尽头，门上倒贴的红纸。她敲门。",
    ),
    dict(
        id="S17", dur=14.0, plate="door-speak", move=("static", 1.05), ov=["snow", "grain"],
        note="门里没有声音。她隔着门说。",
    ),
    dict(
        id="S18", dur=13.0, plate="mother-doorway", move=("push", 1.00, 1.10), ov=["grain", "steam"],
        note="门开了。老太太站在门里的光里。",
    ),
    dict(
        id="S19", dur=15.0, plate="two-hands", move=("push", 1.02, 1.14), ov=["grain"],
        note="两只手：一只冻裂，一只皱。手心放着热的东西。",
    ),
    dict(
        id="S20", dur=13.0, plate="walk-back", move=("pan", (0.04, 0.02), (0.14, 0.0)), ov=["snow", "grain", "breath"],
        note="往回走。她在新机房前停下。",
    ),
    dict(
        id="S21", dur=16.0, plate="headset-hands", move=("push", 1.00, 1.12), ov=["grain"],
        note="她掏出耳机，看着它，戴上：「喂，总机。」",
    ),
    dict(
        id="S22", dur=14.0, plate="board-dawn", move=("static", 1.02), ov=["grain"],
        note="天快亮。空板。耳机挂回钩上，轻轻摆。拨号音起来。",
    ),
    dict(
        id="S23", dur=15.0, plate=None, move=None, ov=[],
        note="片尾字幕。全片 303 秒，硬上限 314。",
    ),
]

# ---------------------------------------------------------------- 台词
# t 是相对本镜开头的秒数。voice 见 scripts/audio.py 的 VOICE 表。
LINES = [
    dict(id="L01", shot="S01", t=1.2, who="XIULAN", zh="喂，总机。", en="", voice="xiulan", rate="-6%", pitch="-8Hz"),
    dict(id="L02", shot="S05", t=3.0, who="XIULAN", zh="煤站。……他出车了，给你接调度室。", en="Coal yard. …He's out on a run. I'll put you through to dispatch.", voice="xiulan", rate="-4%", pitch="-8Hz"),
    dict(id="L03", shot="S06", t=1.0, who="XIULAN", zh="医院，稍等。", en="Hospital. One moment.", voice="xiulan", rate="-4%", pitch="-8Hz"),
    dict(id="L04", shot="S06", t=5.0, who="XIULAN", zh="三百四十七。……嗯，我是总机。", en="Three-four-seven. …Yes. This is the exchange.", voice="xiulan", rate="-4%", pitch="-8Hz"),
    dict(id="L05", shot="S06", t=9.5, who="XIULAN", zh="你爸在哪个厂？", en="Which factory does your father work at?", voice="xiulan", rate="-2%", pitch="-6Hz"),
    dict(id="L06", shot="S06", t=12.5, who="BOY", zh="砖瓦厂。", en="The brickworks.", voice="boy", rate="+4%", pitch="+18Hz"),
    dict(id="L07", shot="S06", t=15.0, who="XIULAN", zh="好，阿姨给你接。", en="All right. I'll connect you.", voice="xiulan", rate="-2%", pitch="-6Hz"),
    dict(id="L08", shot="S08", t=2.0, who="ZHOU", zh="明天早上八点，割接。这片儿全改自动。", en="Eight tomorrow morning. Cut-over. This whole district goes automatic.", voice="zhou", rate="-6%", pitch="-12Hz"),
    dict(id="L09", shot="S08", t=8.0, who="XIULAN", zh="这板子呢？", en="And the board?", voice="xiulan", rate="-4%", pitch="-8Hz"),
    dict(id="L10", shot="S08", t=10.5, who="ZHOU", zh="拆。", en="Pulled out.", voice="zhou", rate="-8%", pitch="-12Hz"),
    dict(id="L11", shot="S08", t=13.0, who="XIULAN", zh="人呢？", en="And me?", voice="xiulan", rate="-6%", pitch="-8Hz"),
    dict(id="L12", shot="S08", t=15.5, who="ZHOU", zh="你去营业厅。坐着，收钱。", en="You go to the counter. Sit. Take the money.", voice="zhou", rate="-6%", pitch="-12Hz"),
    dict(id="L13", shot="S12", t=0.8, who="MAN", zh="喂……总机吗？", en="Hello… is that the exchange?", voice="man", rate="+2%", pitch="+2Hz"),
    dict(id="L14", shot="S12", t=4.0, who="XIULAN", zh="要哪里？", en="Where to?", voice="xiulan", rate="-4%", pitch="-8Hz"),
    dict(id="L15", shot="S12", t=6.0, who="MAN", zh="我是建国。我……在车上。", en="It's Jianguo. I'm… on the train.", voice="man", rate="+2%", pitch="+2Hz"),
    dict(id="L16", shot="S12", t=10.0, who="MAN", zh="我妈一个人在家。你跟她说，我今晚到不了，让她别等我吃饭。", en="My mother's alone at home. Tell her I can't make it tonight. Tell her not to wait supper.", voice="man", rate="+4%", pitch="+2Hz"),
    dict(id="L17", shot="S12", t=16.2, who="XIULAN", zh="好。", en="All right.", voice="xiulan", rate="-8%", pitch="-8Hz"),
    dict(id="L18", shot="S13", t=1.0, who="MAN", zh="喂？总机？", en="Hello? Exchange?", voice="man", rate="+6%", pitch="+2Hz"),
    dict(id="L19", shot="S13", t=4.0, who="XIULAN", zh="线路没了。你这片儿，今晚就没了。", en="The line's gone. Your district went over tonight.", voice="xiulan", rate="-6%", pitch="-8Hz"),
    dict(id="L20", shot="S13", t=9.0, who="MAN", zh="那……你能不能……", en="Then… could you…", voice="man", rate="+2%", pitch="+2Hz"),
    dict(id="L21", shot="S13", t=13.0, who="XIULAN", zh="我给你送过去。", en="I'll take it to her.", voice="xiulan", rate="-6%", pitch="-8Hz"),
    dict(id="L22", shot="S17", t=2.0, who="XIULAN", zh="嫂子。我是总机。你家建国来电话了。", en="Auntie. It's the exchange. Your Jianguo telephoned.", voice="xiulan", rate="-4%", pitch="-8Hz"),
    dict(id="L23", shot="S17", t=8.0, who="XIULAN", zh="他说，今晚到不了，让你别等他吃饭。", en="He said he can't make it tonight. He said not to wait supper.", voice="xiulan", rate="-4%", pitch="-8Hz"),
    dict(id="L24", shot="S18", t=4.0, who="MOTHER", zh="……他吃饭了没有？", en="…Has he eaten?", voice="mother", rate="-10%", pitch="-14Hz"),
    dict(id="L25", shot="S18", t=9.0, who="XIULAN", zh="他说让你别等。", en="He said not to wait.", voice="xiulan", rate="-6%", pitch="-8Hz"),
    dict(id="L26", shot="S19", t=1.0, who="MOTHER", zh="进来暖和暖和。", en="Come in and warm up.", voice="mother", rate="-10%", pitch="-14Hz"),
    dict(id="L27", shot="S19", t=5.0, who="XIULAN", zh="不了，我还没交班。", en="I can't. I'm not off duty yet.", voice="xiulan", rate="-6%", pitch="-8Hz"),
    dict(id="L28", shot="S19", t=9.0, who="MOTHER", zh="那你手上这个……还能用吗？", en="And that thing in your hand… does it still work?", voice="mother", rate="-8%", pitch="-14Hz"),
    dict(id="L29", shot="S19", t=13.2, who="XIULAN", zh="……不能了。", en="…No.", voice="xiulan", rate="-10%", pitch="-8Hz"),
    dict(id="L30", shot="S21", t=9.0, who="XIULAN", zh="喂，总机。", en="Hello. Exchange.", voice="xiulan", rate="-8%", pitch="-8Hz"),
]

# ---------------------------------------------------------------- 说明卡
# 非台词的字幕（给外国评委的上下文）。台词字幕由 LINES 自动推，不另写一份。
CARDS = [
    ("S02", 1.6, 8.6, "Winter, 1987. The last manual exchange in the county."),
    ("S14", 1.6, 9.0, "The new cable is already up."),
    ("S15", 1.6, 8.6, "Nobody has to ask for anything any more."),
    ("S22", 2.0, 9.0, "A dial tone."),
]

# ---------------------------------------------------------------- 声音
# 音效按镜头挂；scripts/audio.py 按名字查合成函数。
SFX = [
    ("S01", 0.4, "relay"), ("S01", 2.6, "relay"),
    ("S02", 1.0, "board_hum"), ("S02", 3.0, "chair"),
    ("S03", 2.0, "plug"), ("S03", 5.0, "plug"),
    ("S04", 3.0, "plug"), ("S04", 6.0, "relay"),
    ("S05", 1.5, "ring_far"),
    ("S06", 12.0, "receiver"),
    ("S07", 0.5, "stove"), ("S07", 4.0, "wind"),
    ("S08", 0.3, "door_open"), ("S08", 18.0, "paper"),
    ("S09", 0.5, "pen"), ("S09", 4.0, "stamp"),
    ("S10", 1.0, "lamps_off"), ("S10", 6.0, "kettle"), ("S10", 9.0, "clock"),
    ("S11", 1.0, "hook_touch"),
    ("S12", 0.2, "static"), ("S12", 15.0, "plug_fail"),
    ("S13", 0.2, "static"), ("S13", 16.0, "chair"),
    ("S14", 0.5, "wind"), ("S14", 4.0, "steps_snow"),
    ("S15", 0.5, "mains_hum"), ("S15", 3.0, "steps_snow"),
    ("S16", 0.5, "steps_snow"), ("S16", 8.0, "knock"),
    ("S17", 0.5, "wind"),
    ("S18", 1.0, "latch"),
    ("S19", 1.0, "paper_soft"),
    ("S20", 0.5, "steps_snow"), ("S20", 6.0, "mains_hum"),
    ("S21", 2.0, "headset_on"), ("S21", 12.0, "headset_off"),
    ("S22", 0.5, "hook_touch"), ("S22", 4.0, "dial_tone"),
]

# ---------------------------------------------------------------- 配乐
# 三个音：口琴动机 / 低频弦垫 / 拨号音（450Hz）。拨号音就是全片的主音。
MUSIC = dict(tonic_hz=450.0, motif=[0, -3, -5, -3])

# ---------------------------------------------------------------- 片尾
CREDITS = [
    ("总机", "title"),
    ("NUMBER, PLEASE", "sub"),
    ("", ""),
    ("编剧 / 导演　张一", "line"),
    ("图版生成　ImageGen（生成式图像）", "line"),
    ("配音　edge-tts 神经网络语音", "line"),
    ("音乐 / 音效　程序合成", "line"),
    ("", ""),
    ("全部画面由生成式 AI 生成", "note"),
    ("All images generated with generative AI", "note_en"),
    ("", ""),
    ("2026", "line"),
]
