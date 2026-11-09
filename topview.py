#!/usr/bin/env python3
"""A flat top-down preview of the town with its traffic: suites as squares
that fill with green as their tests land, commits as light snakes on the
streets. -> topview.mp4 (with audio.wav when it is there)"""
import colorsys
import math
import os
import subprocess
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

import layout as L
import timeline as TL
import traffic

W = 720
VIEW = 2 * (L.RINGS + 0.2) * L.SPACING   # metres across
SMALL = ImageFont.truetype(os.path.expanduser("~/.local/share/fonts/Lato/Lato-Regular.ttf"), 14)
FONT = ImageFont.truetype(os.path.expanduser("~/.local/share/fonts/Lato/Lato-Regular.ttf"), 20)


def px(x, y):
    return (W / 2 + x * W / VIEW, W / 2 - y * W / VIEW)


def hue(i):
    h = (0.45 + 0.8 * (i * 0.618034 % 1.0)) % 1.0
    if 0.22 < h < 0.42:
        h += 0.2
    return tuple(int(255 * c) for c in colorsys.hsv_to_rgb(h, 0.75, 1.0))


def frame_image(f):
    im = Image.new("RGB", (W, W), (5, 7, 14))
    d = ImageDraw.Draw(im, "RGBA")
    t = TL.date_at(f)
    for k in list(L.K if hasattr(L, "K") else range(-L.RINGS, L.RINGS)):
        s = L.street(k)
        a, b = px(s, -L.RINGS * L.SPACING), px(s, L.RINGS * L.SPACING)
        d.line([a, b], fill=(120, 70, 30, 90), width=1)
        a, b = px(-L.RINGS * L.SPACING, s), px(L.RINGS * L.SPACING, s)
        d.line([a, b], fill=(120, 70, 30, 90), width=1)
    for i, s in enumerate(TL.SUITES):
        n = TL.count_at(s, t)
        if n < 0.5:
            continue
        x, y = L.xy_of(i)
        hw = L.width_of(s) / 2 * 1.6
        frac = min(n / max(TL.FINAL[s], 1), 1)
        g = (int(30 + 60 * frac), int(80 + 175 * frac), int(40 + 70 * frac), 255)
        d.rectangle([px(x - hw, y + hw), px(x + hw, y - hw)], fill=g, outline=hue(i), width=2)
    for pts, glow, kind in traffic.snakes(f):
        rgb = traffic.COLOURS[kind]
        for k in range(len(pts) - 1):
            u = k / (len(pts) - 1)
            # white-hot head, the commit's colour along the body, a dim tail
            w = max(1 - u * 12, 0)
            c = [int(255 * (w + (1 - w) * ch * (1 - 0.4 * u))) for ch in rgb]
            d.line([px(*pts[k]), px(*pts[k + 1])], fill=(*c, int(255 * glow * (1 - 0.8 * u))),
                   width=4 if k < 6 else 3)
    for n, (kind, label) in enumerate((("l10n", "translations"), ("fix", "fixes"),
                                       ("feat", "features"), ("test", "tests"), ("ci", "CI"),
                                       ("docs", "docs"), ("tidy", "tidying"), ("other", "other"))):
        c = tuple(int(255 * ch) for ch in traffic.COLOURS[kind])
        y0 = W - 24 - 20 * (7 - n)
        d.rectangle([W - 132, y0 + 6, W - 120, y0 + 12], fill=c)
        d.text((W - 112, y0), label, font=SMALL, fill=c)
    date = datetime.fromtimestamp(t)
    d.text((14, 10), f"{date:%d %b %Y}", font=FONT, fill=(230, 238, 248))
    d.text((14, 36), f"{int(TL.total_at(t)):,} tests   {len(traffic.snakes(f))} snakes",
           font=FONT, fill=(120, 230, 140))
    return im


def main():
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{W}", "-r", str(TL.FPS), "-i", "-"]
    if os.path.exists("audio.wav"):
        cmd += ["-i", "audio.wav", "-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += ["-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p", "topview.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(1, TL.FRAMES + 1):
        p.stdin.write(frame_image(f).tobytes())
    p.stdin.close()
    p.wait()
    print("wrote topview.mp4")


if __name__ == "__main__":
    main()
