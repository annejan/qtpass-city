"""One clock for the film: which date it is at every frame, and how many
tests each suite has then.

Shared by build_scene.py (inside Blender), cards.py and audio.py, so the
windows, the titles and the sound agree. Plain Python, no bpy.
"""
import bisect
import json
import math
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24
SECONDS = 85
FRAMES = SECONDS * FPS

SAMPLES = json.load(open(os.path.join(HERE, "data", "tests.json")))
TAGS = json.load(open(os.path.join(HERE, "data", "tags.json")))
_ST = [s["t"] for s in SAMPLES]


def ts(day):
    return datetime.fromisoformat(day).timestamp()


# The calendar: (second, date). Eight empty years go by in a blur; 2026
# gets room.
NOW = ts(datetime.fromtimestamp(_ST[-1]).date().isoformat()) + 86400
KEYS = [
    (0, ts("2014-07-30")), (2.5, ts("2014-07-30")),   # the first commit, no tests
    (6.5, ts("2016-11-20")),                           # releases, no tests
    (8.5, ts("2016-12-28")),                           # the first test
    (10.0, ts("2018-03-10")),
    (11.0, ts("2018-04-20")),                          # three tests
    (14.5, ts("2026-03-19")),                          # eight years, in a blink
    (21.0, ts("2026-03-26")),                          # 140 tests in a week
    (27.0, ts("2026-05-12")),
    (32.0, ts("2026-05-19")),                          # another 140 in four days
    (35.0, ts("2026-09-12")),                          # a quiet summer
    (48.0, ts("2026-09-23")),                          # 526 in one week
    (56.0, NOW),
    (SECONDS, NOW),
]
T_NOW = KEYS[-1][1]


def _raw(sec):
    for (s0, d0), (s1, d1) in zip(KEYS, KEYS[1:]):
        if sec <= s1:
            u = min(max((sec - s0) / (s1 - s0), 0.0), 1.0)
            return d0 + (d1 - d0) * u
    return KEYS[-1][1]


def _smooth():
    half = int(0.6 * FPS)
    raw = [_raw((f - 1) / FPS) for f in range(1 - half, FRAMES + 2 + half)]
    out = [raw[half]]
    for f in range(1, FRAMES + 2):
        w = raw[f - 1:f + 2 * half]
        out.append(sum(w) / len(w))
    for f in range(2, len(out)):
        out[f] = max(out[f], out[f - 1])
    return out


DATE = _smooth()  # unix time at every frame (1-based)


def t_of(frame):
    return (frame - 1) / FPS


def date_at(frame):
    return DATE[min(max(int(frame), 1), FRAMES + 1)]


def frame_of_date(t):
    """First frame at which the calendar has reached t (the last one at most)."""
    return max(1, bisect.bisect_left(DATE, min(t, DATE[-1]), 1))


# ---------------------------------------------------------------- tests

SUITES = sorted({s for o in SAMPLES for s in o["suites"]},
                key=lambda s: (next(o["t"] for o in SAMPLES if s in o["suites"]), s))
FINAL = {s: SAMPLES[-1]["suites"].get(s, max(o["suites"].get(s, 0) for o in SAMPLES))
         for s in SUITES}
PEAK = {s: max(o["suites"].get(s, 0) for o in SAMPLES) for s in SUITES}
BORN = {s: next(o["t"] for o in SAMPLES if s in o["suites"]) for s in SUITES}


def count_at(suite, t):
    """Tests in a suite at unix time t, linear between the weekly samples."""
    i = bisect.bisect_right(_ST, t) - 1
    if i < 0:
        return 0.0
    a = SAMPLES[i]["suites"].get(suite, 0)
    if i + 1 >= len(SAMPLES):
        return float(a)
    b = SAMPLES[i + 1]["suites"].get(suite, 0)
    u = (t - _ST[i]) / (_ST[i + 1] - _ST[i])
    return a + (b - a) * u


def total_at(t):
    return sum(count_at(s, t) for s in SUITES)


def ci_at(t):
    i = bisect.bisect_right(_ST, t) - 1
    return SAMPLES[max(i, 0)]["ci"] if i >= 0 else 0


def lit_events():
    """(frame, suite, window index) for every window as it first lights."""
    out = []
    counts = {s: 0 for s in SUITES}
    for f in range(1, FRAMES + 1):
        t = date_at(f)
        for s in SUITES:
            n = int(count_at(s, t) + 1e-6)
            while counts[s] < n:
                out.append((f, s, counts[s]))
                counts[s] += 1
    return out


def releases():
    """(frame, name) for every tag, at the frame the calendar reaches it."""
    return [(frame_of_date(t), name) for name, t in TAGS if t <= T_NOW + 86400]


# ---------------------------------------------------------------- camera
# (second, camera xyz, target xyz, lens). The first suite stands at the
# origin; the city grows around it.
CAMERA = [
    (0.0, (-6.0, -15.0, 1.5), (0.0, 10.0, 15.0), 26),   # an empty lot, fireworks
    (5.5, (-5.0, -12.0, 1.4), (0.0, 6.0, 9.0), 28),
    (8.5, (-2.6, -6.5, 1.1), (0.0, 0.0, 0.7), 32),      # the first window
    (11.0, (-4.0, -14.0, 2.0), (6.0, -5.0, 1.0), 26),   # and the second suite
    (14.5, (-8.0, -24.0, 4.0), (6.0, -4.0, 1.5), 26),
    (21.0, (-14.0, -17.0, 7.0), (2.0, 2.0, 3.0), 24),
    (32.0, (-26.0, -34.0, 13.0), (3.0, 3.0, 6.0), 24),
    (35.0, (-22.0, -44.0, 16.0), (4.0, 4.0, 7.0), 24),
    (48.0, (8.0, -60.0, 26.0), (5.0, 8.0, 7.0), 26),
    (56.0, (40.0, -46.0, 34.0), (5.0, 8.0, 5.0), 28),
    (70.0, (30.0, -66.0, 6.0), (2.0, 10.0, 12.0), 30),
    (SECONDS, (18.0, -80.0, 3.0), (2.0, 10.0, 14.0), 32),
]


def _hermite(ts_, vs, t):
    n = len(ts_)
    i = min(max(bisect.bisect_right(ts_, t) - 1, 0), n - 2)
    t0, t1 = ts_[i], ts_[i + 1]
    u = min(max((t - t0) / (t1 - t0), 0.0), 1.0)

    def slope(j):
        if j <= 0 or j >= n - 1:
            return 0.0
        return (vs[j + 1] - vs[j - 1]) / (ts_[j + 1] - ts_[j - 1])

    m0, m1 = slope(i) * (t1 - t0), slope(i + 1) * (t1 - t0)
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1
    h10 = u ** 3 - 2 * u ** 2 + u
    h01 = -2 * u ** 3 + 3 * u ** 2
    h11 = u ** 3 - u ** 2
    return h00 * vs[i] + h10 * m0 + h01 * vs[i + 1] + h11 * m1


_CT = [k[0] for k in CAMERA]


def camera(frame):
    t = t_of(frame)
    cam = tuple(_hermite(_CT, [k[1][a] for k in CAMERA], t) for a in range(3))
    tgt = tuple(_hermite(_CT, [k[2][a] for k in CAMERA], t) for a in range(3))
    lens = _hermite(_CT, [k[3] for k in CAMERA], t)
    return cam, tgt, lens


def dawn(t):
    """0..1: the sky lightening over the finished city."""
    return min(max((t - (SECONDS - 22)) / 18, 0.0), 1.0) ** 1.5


# ---------------------------------------------------------------- titles

def cards():
    total = sum(SAMPLES[-1]["suites"].values())
    suites = len(SAMPLES[-1]["suites"])
    return [
        (0.3, 4.5, "centre", "QtPass", "a city of tests"),
        (4.8, 8.0, "lower", "2014 – 2016", "releases, fireworks, no tests"),
        (8.2, 11.4, "lower", "13 December 2016",
         "the first test: \u201cLOL wut, also how do I link ..\u201d"),
        (11.6, 14.8, "lower", "2018 – 2025", "three tests, for eight years"),
        (15.5, 20.8, "lower", "March 2026", "140 tests in a week"),
        (27.5, 32.5, "lower", "May", "another 140 in four days"),
        (32.8, 35.6, "lower", "summer", "quiet"),
        (37.5, 46.5, "lower", "September", "526 tests in one week"),
        (57.0, 63.5, "lower", "today",
         f"{total:,} tests in {suites} suites, every one of them green"),
        (70.0, 83.5, "centre", "QtPass", f"{total:,} tests · {suites} suites · "
         "one of them from 2016"),
    ]
