#!/usr/bin/env python
"""Annotate the TCS Amsterdam Marathon 2026 course map with supporter spots + stations.

Usage: python -I annotate_map.py [src.pdf] [out_dir]
Writes support-map.pdf (p1 annotated map, p2 supporter plan), support-map.jpg (zoom 1.5),
support-map-preview.jpg (zoom 0.6).
"""
import json, math, os, sys
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


JD = json.load(open(os.path.join(HERE, "journey_pdf.json")))


def walk_line(page, pts, width=4.5):
    """Walking leg: dashed magenta along a footpath polyline, white halo."""
    for col, wd, dash in ((WHT, width + 4, None), (MAG, width, "[16 12] 0")):
        s = page.new_shape()
        s.draw_polyline([P(*q) for q in pts])
        s.finish(color=col, width=wd, dashes=dash, lineCap=0, lineJoin=1, closePath=False,
                 stroke_opacity=0.95 if col == MAG else 0.75)
        s.commit()


def metro_line(page, pts, width=9):
    """Metro track: solid thick navy with white halo."""
    for col, wd in ((WHT, width + 6), (NAVY, width)):
        s = page.new_shape()
        s.draw_polyline([P(*q) for q in pts])
        s.finish(color=col, width=wd, lineCap=1, lineJoin=1, closePath=False, stroke_opacity=0.95)
        s.commit()


def along(pts, f):
    """Point at fraction f of the polyline's arc length."""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    want, acc = f * sum(seg), 0
    for i, sl in enumerate(seg):
        if acc + sl >= want:
            u = (want - acc) / sl if sl else 0
            return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u)
        acc += sl
    return tuple(pts[-1])


def near_idx(pts, q):
    return min(range(len(pts)), key=lambda i: math.dist(pts[i], q))


def tag_at(page, text, pt, fs=17, col=MAG):
    small_tag(page, text, pt, pt, fs=fs, col=col)


def small_tag(page, text, a, b, fs=17, f=0.5, col=MAG):
    m = P(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
    w = tlen(text, fs) + 14
    r = pymupdf.Rect(m.x - w / 2, m.y - fs * 0.85, m.x + w / 2, m.y + fs * 0.75)
    s = page.new_shape()
    s.draw_rect(r, radius=0.3)
    s.finish(fill=col, color=WHT, width=2)
    s.commit()
    page.insert_text(P(r.x0 + 7, m.y + fs * 0.33), text, **FB, fontsize=fs, color=WHT)



# ---------------------------------------------------------------- data
# spots: key -> (point, arrow angle deg (direction of travel), text, badge)
SPOTS = {
    "1": ((526, 936), 120, "km 6 · Beethovenstraat · ~10:33", "1"),
    "2": ((953, 1136), 180, "km 13 · Pres. Kennedylaan · ~11:29", "2"),
    "3": ((1441, 915.5), -45, "km 32 · MOST IMPORTANT · ~14:01\nHugo de Vrieslaan", "3"),
    "4": ((1045, 573.5), 45, "km 37 · Weesperplein · ~14:41", "4"),
    "5": ((150, 1010), -120, "FINISH ~15:23 · HUG!\nOlympic Stadium", "5"),
}
ST_ = {k: tuple(v) for k, v in JD['stations'].items()}
STATIONS = [
    # name, sub, badges, box top-left, icon points
    ("ZUID", "Metro 51 + Train", "MT", (360, 1300), [ST_["Zuid"]]),
    ("RAI", "Metro 51 + Train", "MT", (570, 1245), [ST_["RAI"]]),
    ("AMSTEL", "Metro 51 + Train", "MT", (1000, 775), [ST_["Amstel"]]),
    ("WEESPERPLEIN", "Metro 51", "M", (1140, 445), [ST_["Weesperplein"]]),
    ("AMSTELVEENSEWEG", "CLOSED 13:00-18:00 - use Zuid", "M", (15, 1290), [(196, 1158)], True),
]


def annotate(page):
    track = JD["metro51"]
    ST = JD["stations"]
    # walks (each footpath drawn once), then the single metro track on top
    for key, tag, f in (("km6-Zuid", "walk 1.1 km · 14 min", 0.5), ("RAI-km13", "walk 1.0 km · 13 min", 0.62),
                        ("Amstel-km32", "walk 1.0 km · 13 min", 0.45), ("Zuid-finish", "walk 1.9 km · 23 min", 0.72),
                        ("Weesperplein-km37", None, 0)):
        walk_line(page, JD["walks"][key]["path"])
    metro_line(page, track)
    idx = {k: near_idx(track, v) for k, v in ST.items()}
    # intermediate stops: small white dots with navy border
    for k in ("Overamstel", "Spaklerweg", "Wibautstraat"):
        s = page.new_shape(); s.draw_circle(P(*track[idx[k]]), 9)
        s.finish(fill=WHT, color=NAVY, width=4); s.commit()

    def seg_mid(a, b, f=0.5):
        i, j = sorted((idx[a], idx[b]))
        return along(track[i:j + 1], f)
    tag_at(page, "Metro 51 · 2 min", seg_mid("Zuid", "RAI"), col=NAVY)
    tag_at(page, "Metro 51 · 6 min", seg_mid("Overamstel", "Spaklerweg", 0.5), col=NAVY)
    tag_at(page, "Metro 51 · 3 min", seg_mid("Amstel", "Weesperplein", 0.45), col=NAVY)
    for key, tag, f in (("km6-Zuid", "walk 1.1 km · 14 min", 0.5), ("RAI-km13", "walk 1.0 km · 13 min", 0.62),
                        ("Amstel-km32", "walk 1.0 km · 13 min", 0.45), ("Zuid-finish", "walk 1.9 km · 23 min", 0.72)):
        tag_at(page, tag, along(JD["walks"][key]["path"], f))
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
    # title banner
    r = pymupdf.Rect(20, 20, 20 + 840, 20 + 100)
    s = page.new_shape(); s.draw_rect(r, radius=0.15); s.finish(fill=NAVY, color=WHT, width=4); s.commit()
    page.insert_text(P(44, 72), "Cheer for me!", **FB, fontsize=48, color=NSY)
    page.insert_text(P(44, 104), "TCS Amsterdam Marathon · Sunday 18 Oct 2026", **FB, fontsize=27, color=WHT)
    # legend panel
    PH = 545
    pr = pymupdf.Rect(1100, 2355 - PH, 1790, 2355)
    s = page.new_shape(); s.draw_rect(pr, radius=0.03)
    s.finish(fill=WHT, color=NAVY, width=4, fill_opacity=0.96); s.commit()
    x0 = pr.x0 + 18
    page.insert_text(P(x0, pr.y0 + 38), "Cheer plan · pace 8:00/km · times ≈ ±10 min", **FB, fontsize=27, color=NAVY)
    # line-style key
    ky = pr.y0 + 74
    metro_line(page, [(x0, ky), (x0 + 70, ky)])
    page.insert_text(P(x0 + 82, ky + 7), "Metro 51", **FB, fontsize=22, color=NAVY)
    walk_line(page, [(x0 + 250, ky), (x0 + 330, ky)])
    page.insert_text(P(x0 + 332, ky + 7), "Walk", **FB, fontsize=22, color=MAG)
    items = [
        ("1", "km 6 Beethovenstraat", "walk 14 min to Zuid · Metro 51 to RAI (2 min) · walk 13 min", False),
        ("2", "km 13 President Kennedylaan", "walk 13 min to RAI · Metro 51 to Amstel (6 min) · walk 13 min", False),
        ("3", "*STAR* km 32 Hugo de Vrieslaan - MOST IMPORTANT", "walk 13 min to Amstel · Metro 51 to Weesperplein (3 min)", True),
        ("4", "km 37 Weesperplein (at the metro exit)", "Metro 51 to Zuid (13 min, same line) · walk 23 min", False),
        ("5", "FINISH Olympic Stadium - we hug!", "", False),
    ]
    y = pr.y0 + 128
    tx = pr.x0 + 68
    for n, head, sub, hot in items:
        bc = P(pr.x0 + 38, y - 6)
        s = page.new_shape(); s.draw_circle(bc, 18); s.finish(fill=YEL, color=BLK, width=2.5); s.commit()
        page.insert_text(P(bc.x - tlen(n, 22) / 2, bc.y + 8), n, **FB, fontsize=22, color=BLK)
        if "*STAR*" in head:
            b = head.split("*STAR*")[1].strip()
            star(page, (tx + 14, y - 9), 15, fill=YEL, width=2)
            page.insert_text(P(tx + 36, y), b, **FB, fontsize=24, color=RED)
        else:
            page.insert_text(P(tx, y), head, **FB, fontsize=26 if len(head) < 30 else 24, color=BLK)
        yy = y + 29
        if sub:
            page.insert_text(P(tx, yy - 3), "→", **FR, fontsize=22, color=NAVY)
            for ln in wrap(sub, 21, pr.x1 - 10 - tx - 28):
                page.insert_text(P(tx + 28, yy), ln, **FR, fontsize=21, color=(0.15, 0.15, 0.15))
                yy += 26
        y = yy + 14
    fy = pr.y1 - 14 - 22 * (len(wrap("Metro & train only · Amstelveenseweg metro closed 13:00–18:00 · check GVB/9292 on race day", 20, pr.width - 36, True)) - 1)
    for ln in wrap("Metro & train only · Amstelveenseweg metro closed 13:00–18:00 · check GVB/9292 on race day", 20, pr.width - 36, True):
        page.insert_text(P(x0, fy), ln, **FB, fontsize=20, color=NAVY)
        fy += 22
    print("panel content ends at", y, "limit", pr.y1 - 60)


PLAN = [
    ("1 · ~10:33", "km 6 - Beethovenstraat", "Metro or train to Zuid (be there by 10:20), then walk to km 6. Stand on the west side.", "Walk 1.1 km · 14 min"),
    ("2 · ~11:29", "km 13 - President Kennedylaan", "Walk to Zuid, Metro 51 to RAI, walk to km 13.", "Walk 14 min + Metro 51 2 min + walk 13 min"),
    ("3 · ~14:01", "km 32 - Hugo de Vrieslaan (MOST IMPORTANT)", "Walk to RAI, Metro 51 to Amstel, walk to km 32. Be there by 13:45.", "Walk 13 min + Metro 51 6 min + walk 13 min"),
    ("4 · ~14:41", "km 37 - Weesperplein", "Walk to Amstel, Metro 51 to Weesperplein. The spot is right at the metro exit.", "Walk 13 min + Metro 51 3 min"),
    ("5 · ~15:23", "FINISH - Olympic Stadium", "Metro 51 from Weesperplein to Zuid, then walk to the stadium.", "Metro 51 13 min + walk 23 min"),
]


def plan_page(doc, size):
    page = doc.new_page(width=595, height=842)
    W = 595
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(0, 0, W, 100)); s.finish(fill=NAVY, color=NAVY); s.commit()
    page.insert_text(P(36, 52), "Supporter plan", **FB, fontsize=34, color=NSY)
    page.insert_text(P(36, 80), "TCS Amsterdam Marathon - Sunday 18 Oct 2026 - pace 8:00/km, start 09:45", **FB, fontsize=14, color=WHT)
    # table
    cols = [36, 98, 214, 408]  # stop | where | how | walk / ride
    heads = ["Stop", "Where", "How to get there from previous stop", "Walk / ride"]
    y = 116
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, y, W - 36, y + 24)); s.finish(fill=NAVY, color=NAVY); s.commit()
    for cx, h in zip(cols, heads):
        page.insert_text(P(cx + 5, y + 17), h, **FB, fontsize=10, color=WHT)
    y += 24
    ends = cols[1:] + [W - 36]
    for k, (t, where, how, walk) in enumerate(PLAN):
        cells = [t, where, how, walk]
        fs = 11
        wrapped = [wrap(c, fs, ends[i] - cols[i] - 10, bold=(i < 2)) for i, c in enumerate(cells)]
        h = max(len(w) for w in wrapped) * 14 + 12
        s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, y, W - 36, y + h))
        s.finish(fill=(1, 0.97, 0.85) if k == 2 else ((0.95, 0.95, 0.95) if k % 2 else WHT), color=(0.7, 0.7, 0.7), width=0.6); s.commit()
        for i, w in enumerate(wrapped):
            for li, ln in enumerate(w):
                page.insert_text(P(cols[i] + 5, y + 16 + li * 14), ln, **(FB if i < 2 else FR), fontsize=fs,
                                 color=NAVY if i == 1 else BLK)
        y += h
    y += 16
    # important box
    bullets = [
        "Metro station Amstelveenseweg is CLOSED Sunday 13:00-18:00. Use Zuid and walk to the Olympic Stadium (~1.9 km, ~23 min).",
        "Half-marathon runners are also on the road between km 32 and km 37. Look carefully, it will be busy there.",
        "Metro and train only; check GVB / 9292 on race day.",
    ]
    bh = 46 + sum(len(wrap(b, 12, W - 36 - 50 - 30)) * 16 + 8 for b in bullets)
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, y, W - 36, y + bh), radius=0.04)
    s.finish(fill=(1, 0.93, 0.93), color=RED, width=2); s.commit()
    page.insert_text(P(50, y + 24), "Important", **FB, fontsize=16, color=RED)
    yy = y + 46
    for b in bullets:
        ls = wrap(b, 12, W - 36 - 50 - 30)
        page.insert_text(P(52, yy), "-", **FB, fontsize=12, color=RED)
        for ln in ls:
            page.insert_text(P(66, yy), ln, **FR, fontsize=12, color=BLK)
            yy += 16
        yy += 8
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, 770, W - 36, 815), radius=0.15)
    s.finish(fill=NAVY, color=NAVY); s.commit()
    page.insert_textbox(pymupdf.Rect(48, 780, W - 48, 812),
                        "No rush - we hug at the finish! Spot 3 (km 32) is the most important one.",
                        **FB, fontsize=14, color=WHT, align=1)
    print("plan page content bottom", yy)


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
