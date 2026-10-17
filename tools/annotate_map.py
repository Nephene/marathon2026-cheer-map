#!/usr/bin/env python
"""Annotate the TCS Amsterdam Marathon 2026 course map with supporter spots + stations.

Usage: python -I annotate_map.py [src.pdf] [out_dir]
Writes support-map.pdf (p1 annotated map, p2 supporter plan), support-map.jpg (zoom 1.5),
support-map-preview.jpg (zoom 0.6).
"""
import math, os, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "parcours-tcs-amsterdam-marathon-zondag-2026-v2.pdf")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "docs", "assets")
os.makedirs(OUT, exist_ok=True)

YEL = (1.0, 0.831, 0.0)
BLK = (0, 0, 0)
WHT = (1, 1, 1)
NAVY = (0, 0x30 / 255, 0x82 / 255)
NSY = (1.0, 0xC9 / 255, 0x17 / 255)
MAG = (0.90, 0.0, 0.50)
RED = (0.80, 0.0, 0.0)
_FD = "/System/Library/Fonts/Supplemental/"
FB = dict(fontname="arialb", fontfile=_FD + "Arial Bold.ttf")
FR = dict(fontname="arialr", fontfile=_FD + "Arial.ttf")
_FBF = pymupdf.Font(fontfile=_FD + "Arial Bold.ttf")
_FRF = pymupdf.Font(fontfile=_FD + "Arial.ttf")
P = pymupdf.Point


def tlen(t, fs, bold=True):
    return (_FBF if bold else _FRF).text_length(t, fontsize=fs)


def wrap(t, fs, width, bold=False):
    lines, cur = [], ""
    for w in t.split():
        trial = (cur + " " + w).strip()
        if tlen(trial, fs, bold) <= width or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def star(page, c, r, fill=YEL, width=2.5):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(P(c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    s = page.new_shape()
    s.draw_polyline(pts + [pts[0]])
    s.finish(fill=fill, color=BLK, width=width, closePath=True)
    s.commit()


def arrow(page, tip, ang, length=80, w=14, hw=34, hl=40, gap=6):
    """Arrow whose tip lands `gap` pt from `tip`, travelling in direction ang (deg, y down).
    Returns the tail point."""
    d = P(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    n = P(-d.y, d.x)
    t = P(tip[0] - d.x * gap, tip[1] - d.y * gap)
    base = t - d * hl
    tail = t - d * length
    pts = [tail + n * w / 2, base + n * w / 2, base + n * hw / 2, t,
           base - n * hw / 2, base - n * w / 2, tail - n * w / 2]
    s = page.new_shape()
    s.draw_polyline(pts + [pts[0]])
    s.finish(fill=YEL, color=BLK, width=3.2, closePath=True, lineJoin=1)
    s.commit()
    return tail, d


def label(page, tail, d, text, num, fs=24, big=False, has_star=False):
    lines = text.split("\n")
    pad = 9
    nb = fs * 1.7  # badge size
    tw = max(tlen(t, fs) for t in lines)
    w = tw + 2 * pad + (nb + 6) + (fs * 1.2 if has_star else 0)
    h = fs * 1.55 if len(lines) == 1 else fs * 2.5
    hw, hh = w / 2, h / 2
    t = min(hw / abs(d.x) if abs(d.x) > 1e-3 else 1e9, hh / abs(d.y) if abs(d.y) > 1e-3 else 1e9)
    c = P(tail.x - d.x * t, tail.y - d.y * t)
    r = pymupdf.Rect(c.x - hw, c.y - hh, c.x + hw, c.y + hh)
    s = page.new_shape()
    s.draw_rect(r)
    s.finish(fill=YEL, color=BLK, width=3.2 if not big else 4.5)
    s.commit()
    bc = P(r.x0 + pad + nb / 2, c.y)
    s = page.new_shape()
    s.draw_circle(bc, nb / 2)
    s.finish(fill=BLK, color=BLK)
    s.commit()
    nfs = fs * 0.95
    page.insert_text(P(bc.x - tlen(num, nfs) / 2, bc.y + nfs * 0.35), num, **FB, fontsize=nfs, color=YEL)
    x = r.x0 + pad + nb + 6
    if has_star:
        star(page, (x + fs * 0.5, c.y), fs * 0.62, fill=BLK, width=1)
        x += fs * 1.2
    n = len(lines)
    for i, ln in enumerate(lines):
        yy = c.y + (i - (n - 1) / 2) * fs * 1.15 + fs * 0.35
        page.insert_text(P(x, yy), ln, **FB, fontsize=fs, color=BLK)
    return r


def metro_badge(page, x, y, sz):
    r = pymupdf.Rect(x, y, x + sz, y + sz)
    s = page.new_shape()
    s.draw_rect(r)
    s.finish(fill=NAVY, color=WHT, width=1.5)
    s.commit()
    fs = sz * 0.8
    page.insert_text(P(x + sz / 2 - tlen("M", fs) / 2, y + sz * 0.78), "M", **FB, fontsize=fs, color=WHT)


def train_badge(page, x, y, sz):
    r = pymupdf.Rect(x, y, x + sz * 1.45, y + sz)
    s = page.new_shape()
    s.draw_rect(r, radius=0.2)
    s.finish(fill=NAVY, color=NAVY, width=1)
    s.commit()
    fs = sz * 0.6
    page.insert_text(P(r.x0 + r.width / 2 - tlen("NS", fs) / 2, y + sz * 0.7), "NS", **FB, fontsize=fs, color=NSY)


def station(page, name, sub, badges, tl, icons, fs=22, closed=False):
    """Callout: white rounded box, navy border, badges + name/lines, leader lines to icons."""
    bsz = 30
    bw = sum(bsz * (1.45 if b == "T" else 1) + 5 for b in badges)
    tw = max(tlen(name, fs), tlen(sub, fs * 0.82))
    if closed:
        tw = max(tlen(name, fs), tlen(sub, fs * 0.82))
    w = 12 + bw + tw + 12
    h = fs * 2.35 + 4
    r = pymupdf.Rect(tl[0], tl[1], tl[0] + w, tl[1] + h)
    cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
    # leader lines first (under box)
    for ic in icons:
        # attach to nearest point on box
        ax = min(max(ic[0], r.x0 + 8), r.x1 - 8)
        ay = min(max(ic[1], r.y0 + 8), r.y1 - 8)
        s = page.new_shape()
        s.draw_line(P(ax, ay), P(*ic))
        s.finish(color=NAVY, width=3.5)
        s.commit()
        s = page.new_shape()
        s.draw_circle(P(*ic), 20)
        s.finish(color=NAVY, width=3.5)
        s.commit()
    s = page.new_shape()
    s.draw_rect(r, radius=0.18)
    s.finish(fill=WHT, color=RED if closed else NAVY, width=6 if closed else 4.5)
    s.commit()
    x = r.x0 + 12
    by = cy - bsz / 2
    for b in badges:
        if b == "M":
            metro_badge(page, x, by, bsz)
            if closed:
                s = page.new_shape()
                s.draw_line(P(x - 4, by + bsz + 4), P(x + bsz + 4, by - 4))
                s.finish(color=RED, width=6, lineCap=1)
                s.commit()
            x += bsz + 5
        else:
            train_badge(page, x, by, bsz); x += bsz * 1.45 + 5
    page.insert_text(P(x, r.y0 + fs * 1.15 + 2), name, **FB, fontsize=fs, color=RED if closed else NAVY)
    page.insert_text(P(x, r.y0 + fs * 1.15 + 2 + fs * 0.98), sub, **FB, fontsize=fs * 0.82, color=RED if closed else BLK)
    return r


def dashed(page, a, b, width=4.5):
    for col, wd, dash in ((WHT, width + 4, None), (MAG, width, "[14 9] 0")):
        s = page.new_shape()
        s.draw_line(P(*a), P(*b))
        s.finish(color=col, width=wd, dashes=dash, lineCap=1, stroke_opacity=0.9 if col == MAG else 0.7)
        s.commit()


def small_tag(page, text, a, b, fs=17, f=0.5):
    m = P(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
    w = tlen(text, fs) + 14
    r = pymupdf.Rect(m.x - w / 2, m.y - fs * 0.85, m.x + w / 2, m.y + fs * 0.75)
    s = page.new_shape()
    s.draw_rect(r, radius=0.3)
    s.finish(fill=MAG, color=WHT, width=2)
    s.commit()
    page.insert_text(P(r.x0 + 7, m.y + fs * 0.33), text, **FB, fontsize=fs, color=WHT)


# ---------------------------------------------------------------- data
# spots: key -> (point, arrow angle deg (direction of travel), text, badge, big)
SPOTS = {
    "1": ((526, 936), 120, "km 6 · Beethovenstraat · ~10:33", "1"),
    "2a": ((1020.5, 978), 150, "km 12 · ~11:21 (only if early)", "2a"),
    "2b": ((953, 1136), 180, "2b km 13 · Pres. Kennedylaan · ~11:29 (best)", "2b"),
    "2c": ((939, 1276), -160, "km 14 · Amsteldijk · ~11:37", "2c"),
    "3": ((1441, 915.5), -45, "km 32 · MOST IMPORTANT · ~14:01\nHugo de Vrieslaan", "3"),
    "4": ((1045, 573.5), 45, "km 37 · Weesperplein · ~14:41", "4"),
    "5": ((150, 1010), -120, "FINISH ~15:23 · HUG!\nOlympic Stadium", "5"),
}
STATIONS = [
    # name, sub, badges, box top-left, icon points
    ("ZUID", "Metro 50 · 51 · 52 + Train", "MT", (360, 1300), [(448, 1151), (456, 1126)]),
    ("RAI", "Metro 50 · 51 + Train", "MT", (570, 1245), [(760, 1180), (768, 1205)]),
    ("EUROPAPLEIN", "Metro 52", "M", (625, 1010), [(776, 1066)]),
    ("AMSTEL", "Metro 51 · 53 · 54 + Train", "MT", (1000, 775), [(1232, 914), (1229, 944)]),
    ("WEESPERPLEIN", "Metro 51 · 53 · 54", "M", (1140, 445), [(1070, 527)]),
    ("AMSTELVEENSEWEG", "CLOSED 13:00-18:00 - use Zuid", "M", (15, 1290), [(196, 1158)], True),
]


def annotate(page):
    # journey lines first (under everything)
    Z, RAI, AMS, WPL, AVW = (448, 1151), (768, 1205), (1229, 944), (1070, 527), (196, 1158)
    legs = [
        (SPOTS["1"][0], Z, None), (Z, RAI, "Metro 50/51/52"),
        (RAI, SPOTS["2a"][0], None), (RAI, SPOTS["2b"][0], None), (RAI, SPOTS["2c"][0], None),
        (RAI, AMS, "Metro 51"), (AMS, SPOTS["3"][0], None),
        (AMS, WPL, "Metro 51/53/54"), (WPL, SPOTS["4"][0], None),
        (WPL, Z, "Metro 51"), (Z, SPOTS["5"][0], "walk ~23 min"),
    ]
    for a, b, t in legs:
        dashed(page, a, b, 4.5 if t else 3.5)
    for a, b, t in legs:
        if t:
            if not t.startswith('walk'):
                small_tag(page, t, a, b)
    # station callouts
    for name, sub, bd, tl, icons, *cl in STATIONS:
        station(page, name, sub, bd, tl, icons, closed=bool(cl))
    # arrows + labels
    for k, (pt, ang, text, num) in SPOTS.items():
        big = k == "3"
        if big:
            s = page.new_shape()
            s.draw_circle(P(*pt), 24)
            s.finish(color=YEL, width=9)
            s.commit()
            s = page.new_shape()
            s.draw_circle(P(*pt), 24)
            s.finish(color=BLK, width=2, dashes="[1 0] 0")
            s.commit()
        tail, d = arrow(page, pt, ang, length=118 if big else 80, w=22 if big else 14,
                        hw=54 if big else 34, hl=60 if big else 40, gap=30 if big else 6)
        label(page, tail, d, text, num, fs=28 if big else 24, big=big, has_star=big)
    small_tag(page, 'walk ~23 min', Z, SPOTS['5'][0], f=0.55)
    # title banner
    r = pymupdf.Rect(20, 20, 20 + 840, 20 + 100)
    s = page.new_shape(); s.draw_rect(r, radius=0.15); s.finish(fill=NAVY, color=WHT, width=4); s.commit()
    page.insert_text(P(44, 72), "Cheer for me!", **FB, fontsize=48, color=NSY)
    page.insert_text(P(44, 104), "TCS Amsterdam Marathon · Sunday 18 Oct 2026", **FB, fontsize=27, color=WHT)
    # legend panel
    pr = pymupdf.Rect(1100, 1640, 1790, 2355)
    s = page.new_shape(); s.draw_rect(pr, radius=0.03)
    s.finish(fill=WHT, color=NAVY, width=4, fill_opacity=0.94); s.commit()
    x0 = pr.x0 + 18
    page.insert_text(P(x0, pr.y0 + 38), "Cheer plan · pace 8:00/km · times ≈ ±10 min", **FB, fontsize=27, color=NAVY)
    page.insert_text(P(x0, pr.y0 + 68), "Metro & train only (no trams/buses)", **FB, fontsize=22, color=NAVY)
    items = [
        ("1", "~10:33 km 6 Beethovenstraat", "Be there by 10:20 (Zuid, 13 min walk). Stand on the west side.", False),
        ("2", "~11:29 km 13 Pres. Kennedylaan (best)", "Metro/train Zuid -> RAI, walk 14 min. (km 14 ~11:37 also OK)", False),
        (None, "Gap ~11:45-13:30: lunch near Amstel station.", "", False),
        ("3", "~14:01 *STAR* km 32 Hugo de Vrieslaan", "Metro 51 RAI -> Amstel, walk 16 min. Be there by 13:45. MOST IMPORTANT!", True),
        ("4", "EITHER ~14:41 km 37 Weesperplein", "Metro 51/53/54 Amstel -> Weesperplein; you'll reach the finish ~15:30, after me - meet at Meeting Point. OR go straight to the finish: Metro 51 Amstel -> Zuid + 23 min walk (there ~15:00).", False),
        ("5", "~15:23 FINISH Olympic Stadium", "From Zuid, walk 23 min. Amstelveenseweg metro CLOSED 13:00-18:00!", False),
    ]
    y = pr.y0 + 108
    tx = pr.x0 + 68
    for n, head, sub, hot in items:
        if n is None:
            page.insert_text(P(tx, y), head, **FB, fontsize=23, color=(0.35, 0.35, 0.35))
            y += 42
            continue
        bc = P(pr.x0 + 38, y - 6)
        s = page.new_shape(); s.draw_circle(bc, 18); s.finish(fill=YEL, color=BLK, width=2.5); s.commit()
        page.insert_text(P(bc.x - tlen(n, 22) / 2, bc.y + 8), n, **FB, fontsize=22, color=BLK)
        if "*STAR*" in head:
            a, b = head.split("*STAR*")
            page.insert_text(P(tx, y), a, **FB, fontsize=26, color=RED)
            sx = tx + tlen(a, 26)
            star(page, (sx + 14, y - 9), 15, fill=YEL, width=2)
            page.insert_text(P(sx + 32, y), b.strip(), **FB, fontsize=26, color=RED)
        else:
            page.insert_text(P(tx, y), head, **FB, fontsize=26, color=BLK)
        yy = y + 29
        for ln in wrap(sub, 22, pr.x1 - 14 - tx):
            page.insert_text(P(tx, yy), ln, **FR, fontsize=22, color=(0.15, 0.15, 0.15))
            yy += 26
        y = yy + 18
    page.insert_text(P(x0, pr.y1 - 20), "Check GVB / 9292 on race day. No rush - we hug at the finish!", **FB, fontsize=20, color=NAVY)
    print("panel content ends at", y, "limit", pr.y1 - 40)


PLAN = [
    ("~10:33", "km 6 - Beethovenstraat", "Metro/train to ZUID, be there by 10:20. Stand on the west side.", "km 6 -> Zuid 13 min"),
    ("~11:29", "km 13 - Pres. Kennedylaan (best; km 14 ~11:37 also OK)", "Metro/train Zuid -> RAI.", "RAI -> km 13: 14 min"),
    ("11:45-13:30", "Lunch near Amstel station", "Rest and eat. Metro 51 RAI -> Amstel.", "-"),
    ("~14:01", "km 32 - Hugo de Vrieslaan (MOST IMPORTANT)", "Metro 51 RAI -> Amstel. Be there by 13:45.", "Amstel -> km 32: 16 min"),
    ("~14:41", "km 37 - Weesperplein (optional)", "Metro 51/53/54 Amstel -> Weesperplein. You reach the finish ~15:30, after me - meet at the Meeting Point.", "~3 min from metro"),
    ("~15:23", "FINISH - Olympic Stadium", "Metro 51 Weesperplein or Amstel -> Zuid (there ~15:00 if you skip km 37).", "Zuid -> finish: 23 min"),
]


def plan_page(doc, size):
    page = doc.new_page(width=595, height=842)
    W = 595
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(0, 0, W, 100)); s.finish(fill=NAVY, color=NAVY); s.commit()
    page.insert_text(P(36, 52), "Supporter plan", **FB, fontsize=34, color=NSY)
    page.insert_text(P(36, 80), "TCS Amsterdam Marathon - Sunday 18 Oct 2026 - pace 8:00/km, start 09:45", **FB, fontsize=14, color=WHT)
    # table
    cols = [36, 104, 262, 462]  # time | where | how | walk
    heads = ["Time", "Where", "How to get there", "Walk"]
    y = 116
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, y, W - 36, y + 24)); s.finish(fill=NAVY, color=NAVY); s.commit()
    for cx, h in zip(cols, heads):
        page.insert_text(P(cx + 5, y + 17), h, **FB, fontsize=12, color=WHT)
    y += 24
    ends = cols[1:] + [W - 36]
    for k, (t, where, how, walk) in enumerate(PLAN):
        cells = [t, where, how, walk]
        fs = 11
        wrapped = [wrap(c, fs, ends[i] - cols[i] - 10, bold=(i < 2)) for i, c in enumerate(cells)]
        h = max(len(w) for w in wrapped) * 14 + 12
        s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, y, W - 36, y + h))
        s.finish(fill=(1, 0.97, 0.85) if k == 3 else ((0.95, 0.95, 0.95) if k % 2 else WHT), color=(0.7, 0.7, 0.7), width=0.6); s.commit()
        for i, w in enumerate(wrapped):
            for li, ln in enumerate(w):
                page.insert_text(P(cols[i] + 5, y + 16 + li * 14), ln, **(FB if i < 2 else FR), fontsize=fs,
                                 color=NAVY if i == 1 else BLK)
        y += h
    y += 16
    # important box
    bh = 165
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, y, W - 36, y + bh), radius=0.04)
    s.finish(fill=(1, 0.93, 0.93), color=RED, width=2); s.commit()
    page.insert_text(P(50, y + 24), "Important", **FB, fontsize=16, color=RED)
    bullets = [
        "Metro station Amstelveenseweg is CLOSED Sunday 13:00-18:00. Walk between Zuid station and the Olympic Stadium (~1.9 km, ~23 min).",
        "The half marathon (start 13:20) runs on the same roads around km 32-37. Look carefully, it will be busy there.",
        "Trams and buses are limited. Use metro and train; check GVB / 9292 on race day.",
        "Times assume 8:00/km and a 09:45 start. Adjust by about +/- 10 min.",
    ]
    yy = y + 46
    for b in bullets:
        ls = wrap(b, 12, W - 36 - 50 - 30)
        page.insert_text(P(52, yy), "-", **FB, fontsize=12, color=RED)
        for ln in ls:
            page.insert_text(P(66, yy), ln, **FR, fontsize=12, color=BLK)
            yy += 16
        yy += 8
    y = max(yy, y + 100) + 10
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, 770, W - 36, 815), radius=0.15)
    s.finish(fill=NAVY, color=NAVY); s.commit()
    page.insert_textbox(pymupdf.Rect(48, 780, W - 48, 812),
                        "No rush - we hug at the finish! Spot 3 (km 32) is the most important one.",
                        **FB, fontsize=14, color=WHT, align=1)
    print("plan page content bottom", yy, "box", y, "(box top + bh) =", y)


def main():
    doc = pymupdf.open(SRC)
    page = doc[0]
    annotate(page)
    plan_page(doc, None)
    doc.save(os.path.join(OUT, "support-map.pdf"), garbage=3, deflate=True)
    page = doc[0]
    page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(os.path.join(OUT, "support-map.jpg"), jpg_quality=79)
    page.get_pixmap(matrix=pymupdf.Matrix(0.6, 0.6)).save(os.path.join(OUT, "support-map-preview.jpg"), jpg_quality=80)


if __name__ == "__main__":
    main()
