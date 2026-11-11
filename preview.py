#!/usr/bin/env python3
"""A flat preview of the film before any 3D: the real timeline, and the
night city in 2D at six moments of the film. -> preview.png"""
import math, random, colorsys
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Polygon, Circle
import os
import timeline as TL

for _face in ("Light", "Regular", "Bold"):  # Lato comes with the repo
    font_manager.fontManager.addfont(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "assets", "fonts", f"Lato-{_face}.ttf"))

BG, INK, GREEN = "#070a12", "#e8edf5", "#4dff74"
plt.rcParams.update({"font.family": "Lato", "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.edgecolor": "#33415c"})

def spiral(n):
    cells, r = [(0, 0)], 1
    while len(cells) < n:
        ring = [(x, y) for x in range(-r, r + 1) for y in range(-r, r + 1) if max(abs(x), abs(y)) == r]
        ring.sort(key=lambda c: (math.atan2(c[1], c[0]) + 2 * math.pi + 1.2) % (2 * math.pi))
        cells += ring; r += 1
    return cells[:n]

def hue(i):
    h = (0.45 + 0.8 * (i * 0.618034 % 1.0)) % 1.0
    if 0.22 < h < 0.42: h += 0.2
    return colorsys.hsv_to_rgb(h, 0.75, 1.0)

CELLS = spiral(len(TL.SUITES))

fig = plt.figure(figsize=(16, 10), facecolor=BG)
gs = fig.add_gridspec(3, 3, height_ratios=[1.15, 1, 1], hspace=0.35, wspace=0.06,
                      left=0.05, right=0.97, top=0.9, bottom=0.04)
fig.suptitle("QtPass, a city of tests: flat preview", fontsize=20, color=INK, x=0.05, ha="left")

# --- the real timeline
ax = fig.add_subplot(gs[0, :2], facecolor=BG)
ts = [s["t"] for s in TL.SAMPLES]
dates = [datetime.fromtimestamp(t) for t in ts]
tot = [sum(s["suites"].values()) for s in TL.SAMPLES]
ax.step(dates, tot, where="post", color=GREEN, lw=2)
ax.fill_between(dates, tot, step="post", color=GREEN, alpha=0.15)
for name, t in TL.TAGS:
    ax.axvline(datetime.fromtimestamp(t), color="#ffb347", alpha=0.25, lw=0.8)
ax2 = ax.twinx()
ax2.step(dates, [s["ci"] for s in TL.SAMPLES], where="post", color="#9cc4ff", lw=1.2, alpha=0.8)
ax2.set_ylim(0, 40); ax2.set_yticks([0, 6, 12]); ax2.set_ylabel("CI workflows (searchlights)", color="#9cc4ff")
ax.set_ylabel("tests on main")
ax.set_title("The real history: every commit on main that touched tests", loc="left", color=INK)
ax.annotate("first test, 13 Dec 2016:\n“LOL wut, also how do I link ..”",
            (datetime(2016, 12, 28), 1), (datetime(2016, 1, 1), 450), color=INK, fontsize=9,
            arrowprops=dict(arrowstyle="->", color=INK))
ax.annotate("three tests, 2018 – March 2026", (datetime(2022, 1, 1), 3),
            (datetime(2019, 1, 1), 250), color=INK, fontsize=9, arrowprops=dict(arrowstyle="->", color=INK))
ax.text(datetime(2026, 11, 4), tot[-1], f"  {tot[-1]:,}", color=GREEN, va="center", fontsize=12)
ax.text(datetime(2014, 9, 1), 1150, "orange lines: releases (fireworks)", color="#ffb347", fontsize=9)

# --- the film's clock
bx = fig.add_subplot(gs[0, 2], facecolor=BG)
secs = [TL.t_of(f) for f in range(1, TL.FRAMES + 1, 6)]
bx.plot(secs, [TL.total_at(TL.date_at(f)) for f in range(1, TL.FRAMES + 1, 6)], color=GREEN, lw=2)
for f, _ in TL.releases():
    bx.axvline(TL.t_of(f), color="#ffb347", alpha=0.25, lw=0.8)
for t0, t1, _, big, _ in TL.cards():
    bx.axvspan(t0, t1, color="#ffffff", alpha=0.04)
    bx.text((t0 + t1) / 2, 1320, big.replace(" – ", "–"), rotation=90, fontsize=7, ha="center", va="top", alpha=0.7)
bx.set_xlim(0, TL.SECONDS); bx.set_ylim(0, 1330); bx.set_yticks([])
bx.set_xlabel("film seconds"); bx.set_title("In the 1:25 film", loc="left", color=INK)

# --- six moments in 2D
MOMENTS = [(5.2, "0:05  2015: releases, no tests"), (9.5, "0:09  the first lit window"),
           (13, "0:13  eight years in a blink: still three"), (20, "0:20  March 2026: 140 in a week"),
           (44, "0:44  September: 526 in one week"), (78, "1:18  today, at dawn")]
for k, (sec, label) in enumerate(MOMENTS):
    a = fig.add_subplot(gs[1 + k // 3, k % 3], facecolor=BG)
    frame = int(sec * TL.FPS) + 1
    t = TL.date_at(frame)
    dawn = TL.dawn(sec)
    sky = (0.02 + 0.25 * dawn, 0.025 + 0.1 * dawn, 0.06 + 0.06 * dawn)
    a.set_facecolor(sky)
    rnd = random.Random(k)
    for _ in range(90):
        a.add_patch(Circle((rnd.uniform(-60, 60), rnd.uniform(8, 40)), 0.12, color="white", alpha=rnd.uniform(0.3, 0.9) * (1 - dawn)))
    # searchlights
    for i in range(TL.ci_at(t)):
        x0 = -55 + 110 * (i * 0.381966 % 1.0)
        ang = math.radians(90 + 25 * math.sin(sec * 0.4 + i * 2.1))
        tip = (x0 + 60 * math.cos(ang), 60 * math.sin(ang))
        a.add_patch(Polygon([(x0, 0), (tip[0] - 4, tip[1]), (tip[0] + 4, tip[1])], color="#bcd4ff", alpha=0.08, lw=0))
    # fireworks
    for f0, name in TL.releases():
        tau = (frame - f0) / TL.FPS
        if 0 <= tau < 2.5:
            r2 = random.Random(f0)
            cx, cy = r2.uniform(-40, 40), r2.uniform(26, 36)
            col = ["#ff7a3d", "#66b3ff", "#ffd95a", "#f05ad0", "#9dffe6"][f0 % 5]
            for j in range(40):
                ang = 2 * math.pi * j / 40
                rr = 9 * (1 - math.exp(-1.6 * tau))
                a.add_patch(Circle((cx + rr * math.cos(ang), cy + rr * math.sin(ang) - 2 * tau * tau), 0.35, color=col, alpha=max(1 - tau / 2.5, 0)))
    # towers, back to front
    order = sorted(range(len(TL.SUITES)), key=lambda i: -CELLS[i][1])
    for i in order:
        s = TL.SUITES[i]
        n = TL.count_at(s, t)
        if n < 0.5:
            continue
        side = int(min(max(round(math.sqrt(max(TL.PEAK[s], 1)) / 2.6), 2), 5))
        wpf = 4 * side
        floors = math.ceil(n / wpf - 1e-6)
        cx, cy = CELLS[i]
        x = cx * 11 + cy * 4.0
        w = side + 0.4
        depth = 1 - 0.07 * (cy + 3)
        a.add_patch(Rectangle((x - w / 2, 0), w, floors * 1.0 + 0.3, color=(0.05 * depth, 0.055 * depth, 0.08 * depth), zorder=10 - cy))
        a.add_patch(Rectangle((x - w / 2, floors + 0.3), w, 0.12, color=hue(i), zorder=10 - cy))
        lit = int(n)
        for wi in range(min(lit, floors * wpf)):
            fl, p = divmod(wi, wpf)
            col = p % side
            if p >= side:   # only the front face shows: one in four windows
                continue
            a.add_patch(Rectangle((x - w / 2 + 0.25 + col * 1.0, fl + 0.22), 0.55, 0.6, color=GREEN, zorder=11 - cy))
        if floors >= 3 or sec < 14:
            a.text(x, floors + 0.7, s, color=hue(i), fontsize=6 if sec > 14 else 9, ha="center", zorder=12 - cy)
    a.add_patch(Rectangle((-80, -2), 160, 2, color="#0b0d13", zorder=20))
    if sec < 14:
        a.set_xlim(-6, 10); a.set_ylim(-0.5, 7)
    else:
        a.set_xlim(-48, 52); a.set_ylim(-1, 44)
    a.set_xticks([]); a.set_yticks([])
    d = datetime.fromtimestamp(t)
    a.set_title(f"{label}   ({d:%b %Y}, {int(TL.total_at(t)):,} tests)", loc="left", fontsize=10, color=INK)
fig.savefig("preview.png", dpi=100, facecolor=BG)
print("ok")
