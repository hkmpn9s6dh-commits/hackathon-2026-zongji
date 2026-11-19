# -*- coding: utf-8 -*-
"""《总机》的声音：全片由代码合成，除配音（edge-tts）外不取任何外部素材。

- 音效：继电器、塞绳、雪、风、炉子、拨号音……逐个合成，按 story.SFX 摆上时间轴
- 音乐：一把「口琴」的四音动机 + 低频弦垫，出现四次；450 Hz 的拨号音是全片的主音
- 配音：edge-tts，按 story.LINES 摆位；每句都量长度，超出留给它的空档就报错

输出 build/audio.wav（48 kHz / 16-bit / stereo）。
"""
import asyncio, math, subprocess, sys, wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import story as S

ROOT = Path(__file__).resolve().parent.parent
SR = 48000
TOTAL = sum(s["dur"] for s in S.SHOTS) + 1.5
N = int(TOTAL * SR)

VOICE = {
    "xiulan": ("zh-CN-XiaoxiaoNeural", "-6%", "-10Hz"),
    "boy": ("zh-CN-YunxiaNeural", "+6%", "+20Hz"),
    "zhou": ("zh-CN-YunjianNeural", "-8%", "-14Hz"),
    "man": ("zh-CN-YunxiNeural", "+2%", "+0Hz"),
    "mother": ("zh-CN-liaoning-XiaobeiNeural", "-14%", "-10Hz"),
}

rng = np.random.default_rng(3)


# ---------------------------------------------------------------- 基础工具
def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env_ad(n, a=0.005, d=0.2, curve=2.0):
    a = max(1, int(a * SR))
    e = np.ones(n)
    if a < n:
        e[:a] = np.linspace(0, 1, a)
    k = np.linspace(0, 1, n)
    e *= np.exp(-k * curve / max(d, 1e-3))
    return e


def noise(dur, lp=0.2, hp=0.0):
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    # 一阶低通／高通（够用，省得引 scipy）
    if lp < 1.0:
        a = math.exp(-2 * math.pi * lp * 40 / SR)
        y = np.empty_like(x)
        acc = 0.0
        for i in range(n):
            acc = a * acc + (1 - a) * x[i]
            y[i] = acc
        x = y
    if hp > 0:
        a = math.exp(-2 * math.pi * hp / SR)
        y = np.empty_like(x)
        acc = x[0]
        for i in range(n):
            acc = a * (acc + x[i] - (x[i - 1] if i else 0))
            y[i] = acc
        x = y
    return x / (np.abs(x).max() + 1e-9)


def click(dur=0.05, f=1800.0, body=0.55):
    """继电器／插塞的「咔」。"""
    t = t_axis(dur)
    n = len(t)
    x = np.sin(2 * math.pi * f * t) * np.exp(-t * 90)
    x += np.sin(2 * math.pi * f * 0.47 * t) * np.exp(-t * 40) * body
    x += noise(dur)[:n] * np.exp(-t * 160) * 0.5
    return x * 0.55


def thud(dur=0.18, f=70.0):
    t = t_axis(dur)
    x = np.sin(2 * math.pi * f * t * (1 - 0.2 * t / dur)) * np.exp(-t * 22)
    x += noise(dur)[:len(t)] * np.exp(-t * 60) * 0.35
    return x * 0.8


def tone(dur, f, amp=0.2, vib=0.0, vibf=5.0, shape="sine"):
    t = t_axis(dur)
    if shape == "saw":
        x = 2 * ((f * t + 0.0) % 1.0) - 1
    else:
        x = np.sin(2 * math.pi * f * t)
    if vib:
        x = np.sin(2 * math.pi * f * t + vib * np.sin(2 * math.pi * vibf * t))
    return x * amp


def place(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i < 0 or i >= len(buf):
        return
    n = min(len(x), len(buf) - i)
    if n <= 0:
        return
    l = math.sqrt(0.5 * (1 - pan))
    r = math.sqrt(0.5 * (1 + pan))
    buf[i:i + n, 0] += x[:n] * gain * l
    buf[i:i + n, 1] += x[:n] * gain * r


# ---------------------------------------------------------------- 音效
def sfx(name):
    if name == "relay":
        return click(0.06, 1600, 0.5) * 1.0
    if name == "plug":
        a = click(0.04, 2400, 0.3)
        b = np.concatenate([np.zeros(int(0.035 * SR)), click(0.05, 900, 0.6)])
        return np.concatenate([a, np.zeros(int(0.01 * SR)), b]) * 0.9
    if name == "plug_fail":
        a = click(0.035, 2200, 0.3)
        return np.concatenate([a, np.zeros(int(0.55 * SR))]) * 0.85
    if name == "board_hum":
        t = t_axis(2.2)
        x = tone(2.2, 50, 0.05) + tone(2.2, 100, 0.03) + tone(2.2, 150, 0.012)
        return x * env_ad(len(t), 0.4, 1.2, 0.6)
    if name == "chair":
        t = t_axis(0.5)
        x = noise(0.5, lp=0.5) * np.exp(-t * 6) * 0.25
        x += tone(0.5, 320, 0.02, vib=6, vibf=9)
        return x
    if name == "ring_far":
        dur = 3.2
        t = t_axis(dur)
        g = ((t % 3.0) < 1.0).astype(float)
        g = np.convolve(g, np.ones(400) / 400, mode="same")
        x = (tone(dur, 450, 0.05) + tone(dur, 900, 0.02)) * g
        return x * 0.5
    if name == "receiver":
        a = click(0.05, 700, 0.5)
        return np.concatenate([a, noise(0.3, lp=0.4) * 0.02])
    if name == "stove":
        dur = 3.0
        x = noise(dur, lp=0.6) * 0.03
        for _ in range(26):
            i = rng.integers(0, int(dur * SR) - 2000)
            x[i:i + 400] += rng.normal(0, 0.06, 400) * np.exp(-np.arange(400) / 90)
        return x
    if name == "wind":
        dur = 4.0
        base = noise(dur, lp=0.25, hp=200)
        t = t_axis(dur)
        mod = 0.5 + 0.5 * np.sin(2 * math.pi * 0.17 * t + 1.0)
        return base * mod * 0.14
    if name == "door_open":
        t = t_axis(0.9)
        f = 180 + 120 * (t / 0.9)
        creak = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 3) * 0.08
        return creak + np.concatenate([click(0.05, 600, 0.4), np.zeros(int(0.85 * SR))])[:len(t)]
    if name == "paper":
        dur = 0.6
        x = noise(dur, lp=0.9, hp=2500) * np.exp(-t_axis(dur) * 5) * 0.16
        return x
    if name == "paper_soft":
        dur = 0.9
        return noise(dur, lp=0.8, hp=1800) * np.exp(-t_axis(dur) * 3) * 0.10
    if name == "pen":
        dur = 1.2
        t = t_axis(dur)
        x = noise(dur, lp=0.95, hp=3000) * (0.5 + 0.5 * np.sin(2 * math.pi * 7 * t)) * 0.10
        return x
    if name == "stamp":
        return thud(0.22, 95) * 0.75
    if name == "lamps_off":
        out = np.zeros(int(1.2 * SR))
        for k in range(4):
            c = click(0.03, 2000, 0.2)
            i = int(k * 0.22 * SR)
            out[i:i + len(c)] += c * (1 - 0.2 * k)
        return out
    if name == "kettle":
        t = t_axis(0.8)
        return (tone(0.8, 1400, 0.03, vib=3, vibf=6) + tone(0.8, 2100, 0.015)) * env_ad(len(t), 0.1, 0.3, 2)
    if name == "clock":
        out = np.zeros(int(1.6 * SR))
        for k in range(3):
            c = click(0.03, 3000, 0.2) * 0.5
            i = int(k * 0.55 * SR)
            out[i:i + len(c)] += c
        return out
    if name == "hook_touch":
        return click(0.08, 2600, 0.7) * 0.7
    if name == "static":
        dur = 1.4
        x = noise(dur, lp=0.9, hp=600) * 0.06
        t = t_axis(dur)
        x *= 0.4 + 0.6 * np.abs(np.sin(2 * math.pi * 2.3 * t))
        return x
    if name == "steps_snow":
        dur = 2.4
        out = np.zeros(int(dur * SR))
        for k in range(5):
            i = int((0.05 + k * 0.47) * SR)
            c = noise(0.22, lp=0.8, hp=300) * np.exp(-np.arange(int(0.22 * SR)) / (0.05 * SR)) * 0.20
            out[i:i + len(c)] += c
        return out
    if name == "mains_hum":
        t = t_axis(3.0)
        x = tone(3.0, 100, 0.05) + tone(3.0, 200, 0.03) + tone(3.0, 300, 0.015) + tone(3.0, 400, 0.008)
        return x * env_ad(len(t), 0.5, 2.0, 0.5)
    if name == "knock":
        out = np.zeros(int(1.1 * SR))
        for k in range(3):
            c = thud(0.16, 120) * 0.55
            i = int((0.02 + k * 0.34) * SR)
            out[i:i + len(c)] += c
        return out
    if name == "latch":
        return np.concatenate([click(0.04, 1500, 0.4), np.zeros(int(0.06 * SR)), thud(0.12, 260)]) * 0.6
    if name == "headset_on":
        return np.concatenate([click(0.05, 2800, 0.5), np.zeros(int(0.12 * SR)),
                               noise(0.2, lp=0.7, hp=900) * 0.05]) * 0.8
    if name == "headset_off":
        return click(0.06, 2200, 0.5) * 0.7
    if name == "dial_tone":
        dur = TOTAL
        t = t_axis(dur)
        x = tone(dur, 450, 0.10) + tone(dur, 450.6, 0.05)
        e = np.clip((t - 0.0) / 3.0, 0, 1) * np.clip((dur - t) / 1.0, 0, 1)
        return x * e
    raise KeyError(f"未知音效 {name}")


# ---------------------------------------------------------------- 音乐
def harmonica(dur, f, amp=0.10):
    t = t_axis(dur)
    x = np.zeros_like(t)
    for k, w in [(1, 1.0), (2, 0.5), (3, 0.32), (4, 0.18), (5, 0.10)]:
        x += w * np.sin(2 * math.pi * f * k * t + 0.15 * k * np.sin(2 * math.pi * 5.2 * t))
    e = np.clip(t / 0.06, 0, 1) * np.clip((dur - t) / 0.35, 0, 1)
    return x * e * amp / 2.1


def build_music():
    """低频弦垫铺全片，口琴动机出现四次。"""
    n = N
    t = np.arange(n) / SR
    pad = (np.sin(2 * math.pi * 55 * t) * 0.020 +
           np.sin(2 * math.pi * 82.5 * t) * 0.012 +
           np.sin(2 * math.pi * 110 * t) * 0.008)
    pad *= 0.6 + 0.4 * np.sin(2 * math.pi * 0.035 * t)
    out = pad.astype(np.float32)

    starts = {}
    acc = 0.0
    for sh in S.SHOTS:
        starts[sh["id"]] = acc
        acc += sh["dur"]

    base = 220.0
    semis = S.MUSIC["motif"]
    cues = [("S01", 3.0, 0.9), ("S08", 17.0, 1.0), ("S21", 6.0, 1.1), ("S22", 5.0, 0.8)]
    for sid, dt, amp in cues:
        t0 = starts[sid] + dt
        for i, sm in enumerate(semis):
            f = base * 2 ** (sm / 12.0)
            note = harmonica(1.35, f, 0.085 * amp)
            i0 = int((t0 + i * 1.05) * SR)
            m = min(len(note), n - i0)
            if m > 0:
                out[i0:i0 + m] += note[:m]
    return out


# ---------------------------------------------------------------- 配音
def tts_all():
    """生成／复用每一句配音，返回 {id: (path, dur)}。"""
    d = ROOT / "build" / "vo"
    d.mkdir(parents=True, exist_ok=True)
    out = {}

    async def one(ln):
        voice, rate, pitch = VOICE[ln["voice"]]
        rate = ln.get("rate", rate)
        pitch = ln.get("pitch", pitch)
        mp3 = d / f"{ln['id']}.mp3"
        if not mp3.exists():
            import edge_tts
            c = edge_tts.Communicate(ln["zh"], voice, rate=rate, pitch=pitch)
            await c.save(str(mp3))
        wav = d / f"{ln['id']}.wav"
        if not wav.exists():
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3),
                            "-ar", str(SR), "-ac", "1", str(wav)], check=True)
        with wave.open(str(wav)) as w:
            dur = w.getnframes() / w.getframerate()
        out[ln["id"]] = (wav, dur)

    async def run():
        for ln in S.LINES:
            await one(ln)

    asyncio.run(run())
    # 异步偶发 loop 关闭告警，忽略
    return out


def box_filter(x, k):
    """长度 k 的滑动平均，O(n)。np.convolve 在这里是 14.7M×12000，会卡到天亮。"""
    if k <= 1:
        return x
    c = np.cumsum(np.concatenate([[0.0], x.astype(np.float64)]))
    y = (c[k:] - c[:-k]) / k
    pad = len(x) - len(y)
    return np.concatenate([y, np.full(pad, y[-1])]).astype(np.float32)


def read_wav(p):
    with wave.open(str(p)) as w:
        n = w.getnframes()
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    return a


# ---------------------------------------------------------------- 主程序
def main():
    buf = np.zeros((N, 2), dtype=np.float32)

    starts = {}
    acc = 0.0
    for sh in S.SHOTS:
        starts[sh["id"]] = acc
        acc += sh["dur"]

    # 音效
    for sid, dt, name in S.SFX:
        x = sfx(name)
        place(buf, x, starts[sid] + dt, 0.9 if name != "dial_tone" else 1.0)

    # 配音
    vo = tts_all()
    spans = []
    for ln in S.LINES:
        p, dur = vo[ln["id"]]
        a = read_wav(p)
        t0 = starts[ln["shot"]] + ln["t"]
        place(buf, a, t0, 0.95)
        spans.append((t0, t0 + dur, ln["id"], dur))
        print(f"  {ln['id']:4s} {ln['shot']} t={ln['t']:5.1f} dur={dur:4.2f}s")

    # 配音是否越界
    bad = []
    for i, (a, b, lid, dur) in enumerate(spans):
        shot = next(s for s in S.SHOTS if any(l["id"] == lid and l["shot"] == s["id"] for l in S.LINES))
        end = starts[shot["id"]] + shot["dur"]
        if b > end - 0.05:
            bad.append(f"{lid} 超出镜头尾 {b-end:+.2f}s")
        for a2, b2, lid2, _ in spans[i + 1:]:
            if a2 < b:
                bad.append(f"{lid} 与 {lid2} 重叠 {-0.0:.2f}s")
    if bad:
        print("TIMING PROBLEMS:")
        for x in bad:
            print("  ", x)

    # 音乐 + 侧链压缩
    mus = build_music()
    act = np.zeros(N, dtype=np.float32)
    for a, b, _, _ in spans:
        i, j = int(a * SR), int(min(N, b * SR))
        act[i:j] = 1.0
    k = int(0.25 * SR)
    act = box_filter(act, k)   # 用 cumsum，不用 np.convolve（O(n·m) 会卡死，AME-1401 犯过一次）
    duck = 1.0 - 0.70 * np.clip(act, 0, 1)
    buf[:, 0] += mus * duck * 0.42
    buf[:, 1] += mus * duck * 0.42

    # 母带：软限幅 + 峰值归一
    peak = np.abs(buf).max()
    if peak > 0:
        buf = np.tanh(buf / peak * 1.15) / np.tanh(1.15) * 0.72
    pcm = (np.clip(buf, -1, 1) * 32767).astype(np.int16)
    outp = ROOT / "build" / "audio.wav"
    outp.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(outp), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"{outp}  {len(pcm)/SR:.1f}s  peak={peak:.3f}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
