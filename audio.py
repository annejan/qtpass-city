#!/usr/bin/env python3
"""The soundtrack, generated from the same clock as the picture.

audio.py [OUT.wav]   (default audio.wav; 48 kHz stereo, SECONDS long)

Crickets and a city hum that grows with the city, a drone that changes
chord with each chapter, one soft blip per test as its window lights
(pitch by suite, on a pentatonic scale, so September turns into a
shimmer), a bell for the first test, a pop and crackle for every
release's firework, a riser into September and a major chord at dawn.
"""
import random
import sys
import wave

import numpy as np
from scipy import signal

import timeline as TL

SR = 48000
N = TL.SECONDS * SR
T = np.arange(N) / SR
rng = np.random.default_rng(2016)
rnd = random.Random(1256)


def lowpass(x, hz, order=2):
    b, a = signal.butter(order, hz / (SR / 2))
    return signal.lfilter(b, a, x)


def bandpass(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band")
    return signal.lfilter(b, a, x)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def keyed(keys):
    """Smoothstep between (second, value) keys, at every sample."""
    grid = np.arange(0, TL.SECONDS + 1, 0.05)
    vals = []
    for t in grid:
        v = keys[-1][1]
        for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
            if t <= t1:
                u = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
                v = v0 + (v1 - v0) * u * u * (3 - 2 * u)
                break
        vals.append(v)
    return np.interp(T, grid, vals)


out = np.zeros((N, 2))
frames = np.arange(1, TL.FRAMES + 2)
size = np.array([TL.total_at(TL.date_at(f)) for f in frames])
city = np.interp(T, (frames - 1) / TL.FPS, np.minimum(size / 1256, 1))

# ---------------------------------------------------------------- night
for ch in range(2):
    # crickets: bursts of a high, pulsed tone
    chirp = np.sin(2 * np.pi * (4300 + 180 * ch) * T)
    gate = (np.sin(2 * np.pi * 21 * T + ch) > 0.2) * (np.sin(2 * np.pi * (0.43 + 0.07 * ch) * T + 2 * ch) > 0.35)
    out[:, ch] += lowpass(gate.astype(float), 300) * chirp * 0.012 * (1 - 0.6 * city)
    # the city's hum, growing with it
    hum = lowpass(rng.standard_normal(N), 160, 3) * 3 + 0.25 * np.sin(2 * np.pi * (55 + ch * 0.3) * T)
    out[:, ch] += hum * (0.01 + 0.07 * city)

# ---------------------------------------------------------------- drone
CHORDS = [  # (from second, MIDI notes)
    (0, [38, 45, 50, 53]),        # Dm
    (8.5, [41, 48, 53, 57]),      # F: the first test
    (11, [38, 45, 52]),           # Dm9, sparse: eight years
    (15.5, [34, 41, 46, 50]),     # Bb: March
    (27, [36, 43, 48, 52]),       # C: May
    (32.5, [38, 45, 52]),         # sparse: summer
    (35, [34, 41, 46, 50, 53]),   # Bb: September builds
    (42, [36, 43, 48, 52, 55]),   # C
    (48, [38, 45, 50, 54, 57]),   # D major: there
    (64, [38, 45, 52, 54, 57]),   # Dsus2/6, dawn
]
drone = np.zeros(N)
fade = int(2.0 * SR)
for i, (t0, notes) in enumerate(CHORDS):
    t1 = CHORDS[i + 1][0] if i + 1 < len(CHORDS) else TL.SECONDS
    a, b = int(t0 * SR), min(int(t1 * SR) + fade, N)
    tt = T[a:b]
    g = np.ones(b - a)
    g[:fade] = np.linspace(0, 1, fade) ** 1.5
    if b < N:
        g[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    for n in notes:
        for h, amp in ((1, 1.0), (2, 0.3), (3, 0.1)):
            for det in (-0.5, 0.5):
                drone[a:b] += np.sin(2 * np.pi * (hz(n) * h + det) * tt + rng.uniform(0, 6.28)) * amp * g
drone = lowpass(drone, 1500) / 30
level = keyed([(0, 0), (3, 0.4), (11, 0.35), (15.5, 0.5), (35, 0.55), (48, 0.95),
               (60, 0.75), (TL.SECONDS - 4, 0.6), (TL.SECONDS, 0)])
out[:, 0] += drone * level
out[:, 1] += np.roll(drone, 240) * level

# ---------------------------------------------------------------- tests
PENTA = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86]  # D major pentatonic
events = TL.lit_events()
per_sec = np.zeros(TL.SECONDS + 1)
for f, _, _ in events:
    per_sec[min(int(TL.t_of(f)), TL.SECONDS)] += 1
L = int(0.3 * SR)
tg = np.arange(L) / SR
for f, suite, k in events:
    t = TL.t_of(f) + rnd.uniform(0, 1 / TL.FPS)
    si = TL.SUITES.index(suite)
    note = PENTA[(si * 3 + k % 3) % len(PENTA)]
    fr = hz(note) * (1 + rnd.uniform(-0.002, 0.002))
    dens = per_sec[min(int(t), TL.SECONDS)]
    amp = 0.1 / np.sqrt(max(dens, 1))
    g = np.sin(2 * np.pi * fr * tg) * np.exp(-tg * 16) * (1 - np.exp(-tg * 900))
    g += 0.25 * np.sin(2 * np.pi * fr * 3.0 * tg) * np.exp(-tg * 30)
    i = int(t * SR)
    j = min(i + L, N)
    pan = 0.5 + 0.35 * np.sin(si * 1.7)
    out[i:j, 0] += g[:j - i] * amp * (1 - pan)
    out[i:j, 1] += g[:j - i] * amp * pan


def bell(t, f0, amp, decay=3.0):
    i = int(t * SR)
    L = min(int(decay * 2.5 * SR), N - i)
    tt = np.arange(L) / SR
    g = sum(a * np.sin(2 * np.pi * f0 * p * tt) * np.exp(-tt * (1 + p) / decay)
            for p, a in ((1, 1), (2.76, 0.5), (5.4, 0.25), (8.9, 0.1)))
    out[i:i + L, 0] += g * amp
    out[i:i + L, 1] += np.roll(g, 120) * amp


first = next(f for f, s, k in events)
bell(TL.t_of(first), hz(74), 0.2, decay=4.5)

# ---------------------------------------------------------------- fireworks
for f0, name in TL.releases():
    t = TL.t_of(f0) + rnd.uniform(0, 4) / TL.FPS
    i = int(t * SR)
    big = "rc" not in name and "beta" not in name
    # the launch whistle, then the pop and the crackle
    wl = int(0.5 * SR)
    a0 = max(i - wl, 0)
    tw = np.arange(i - a0) / SR
    whistle = np.sin(2 * np.pi * np.cumsum(1200 + 1600 * tw / 0.5) / SR) * np.linspace(0, 1, i - a0) * 0.008
    Lp = min(int(1.6 * SR), N - i)
    tp = np.arange(Lp) / SR
    pop = lowpass(rng.standard_normal(Lp), 900, 2) * np.exp(-tp * 9) * (0.5 if big else 0.3)
    crack = (rng.random(Lp) < 0.004 * np.exp(-tp * 1.5)) * rng.standard_normal(Lp)
    crack = bandpass(crack, 1500, 9000) * 2.5
    pan = rnd.uniform(0.25, 0.75)
    for ch, w in ((0, 1 - pan), (1, pan)):
        out[a0:i, ch] += whistle * w
        out[i:i + Lp, ch] += (pop + crack) * w * 0.5

# ---------------------------------------------------------------- September
rise = keyed([(0, 0), (35, 0), (46, 1), (48, 0), (TL.SECONDS, 0)])
noise = bandpass(rng.standard_normal(N), 400, 6000)
for ch in range(2):
    out[:, ch] += np.roll(noise, ch * 31) * rise ** 2 * 0.05
bell(48.0, hz(74), 0.16, decay=5)
bell(48.02, hz(78), 0.1, decay=5)
bell(48.04, hz(81), 0.08, decay=5)

# ---------------------------------------------------------------- room
ir_len = int(2.2 * SR)
ti = np.arange(ir_len) / SR
wet = np.zeros_like(out)
for ch in range(2):
    ir = lowpass(rng.standard_normal(ir_len) * np.exp(-ti * 2.8), 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    wet[:, ch] = signal.fftconvolve(out[:, ch], ir)[:N]
mix = out * 0.8 + wet * 0.35
mix *= (np.minimum(T / 0.5, 1) * np.clip((TL.SECONDS - T) / 3.0, 0, 1))[:, None]
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.4) / np.tanh(1.4) * 0.9

path = sys.argv[1] if len(sys.argv) > 1 else "audio.wav"
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("wrote", path, f"{TL.SECONDS} s,", len(events), "test blips,", len(TL.releases()), "fireworks")
