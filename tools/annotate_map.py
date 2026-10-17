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
FONT = "hebo"
P = pymupdf.Point


def tlen(t, fs):
    return pymupdf.get_text_length(t, fontname=FONT, fontsize=fs)


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
    page.insert_text(P(bc.x - tlen(num, nfs) / 2, bc.y + nfs * 0.35), num, fontname=FONT, fontsize=nfs, color=YEL)
    x = r.x0 + pad + nb + 6
    if has_star:
        star(page, (x + fs * 0.5, c.y), fs * 0.62, fill=BLK, width=1)
        x += fs * 1.2
    n = len(lines)
    for i, ln in enumerate(lines):
        yy = c.y + (i - (n - 1) / 2) * fs * 1.15 + fs * 0.35
        page.insert_text(P(x, yy), ln, fontname=FONT, fontsize=fs, color=BLK)
    return r


def metro_badge(page, x, y, sz):
    r = pymupdf.Rect(x, y, x + sz, y + sz)
    s = page.new_shape()
    s.draw_rect(r)
    s.finish(fill=NAVY, color=WHT, width=1.5)
    s.commit()
    fs = sz * 0.8
    page.insert_text(P(x + sz / 2 - tlen("M", fs) / 2, y + sz * 0.78), "M", fontname=FONT, fontsize=fs, color=WHT)


def train_badge(page, x, y, sz):
    r = pymupdf.Rect(x, y, x + sz * 1.45, y + sz)
    s = page.new_shape()
    s.draw_rect(r, radius=0.2)
    s.finish(fill=NAVY, color=NAVY, width=1)
    s.commit()
    fs = sz * 0.6
    page.insert_text(P(r.x0 + r.width / 2 - tlen("NS", fs) / 2, y + sz * 0.7), "NS", fontname=FONT, fontsize=fs, color=NSY)


def station(page, name, sub, badges, tl, icons, fs=22):
    """Callout: white rounded box, navy border, badges + name/lines, leader lines to icons."""
    bsz = 30
    bw = sum(bsz * (1.45 if b == "T" else 1) + 5 for b in badges)
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
    s.finish(fill=WHT, color=NAVY, width=4.5)
    s.commit()
    x = r.x0 + 12
    by = cy - bsz / 2
    for b in badges:
        if b == "M":
            metro_badge(page, x, by, bsz); x += bsz + 5
        else:
            train_badge(page, x, by, bsz); x += bsz * 1.45 + 5
    page.insert_text(P(x, r.y0 + fs * 1.15 + 2), name, fontname=FONT, fontsize=fs, color=NAVY)
    page.insert_text(P(x, r.y0 + fs * 1.15 + 2 + fs * 0.98), sub, fontname=FONT, fontsize=fs * 0.82, color=BLK)
    return r


def dashed(page, a, b, width=4.5):
    for col, wd, dash in ((WHT, width + 4, None), (MAG, width, "[14 9] 0")):
        s = page.new_shape()
        s.draw_line(P(*a), P(*b))
        s.finish(color=col, width=wd, dashes=dash, lineCap=1, stroke_opacity=0.9 if col == MAG else 0.7)
        s.commit()


def small_tag(page, text, a, b, fs=17):
    m = P((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    w = tlen(text, fs) + 14
    r = pymupdf.Rect(m.x - w / 2, m.y - fs * 0.85, m.x + w / 2, m.y + fs * 0.75)
    s = page.new_shape()
    s.draw_rect(r, radius=0.3)
    s.finish(fill=MAG, color=WHT, width=2)
    s.commit()
    page.insert_text(P(r.x0 + 7, m.y + fs * 0.33), text, fontname=FONT, fontsize=fs, color=WHT)


# ---------------------------------------------------------------- data
# spots: key -> (point, arrow angle deg (direction of travel), text, badge, big)
SPOTS = {
    "1": ((526, 936), 120, "km 6 · Beethovenstraat", "1"),
    "2a": ((1020.5, 978), 150, "km 12 · Rijnstraat", "2a"),
    "2b": ((953, 1136), 180, "km 13 · Pres. Kennedylaan", "2b"),
    "2c": ((939, 1276), -160, "km 14 · Amsteldijk", "2c"),
    "3": ((1441, 915.5), -45, "km 32 · MOST IMPORTANT\nHugo de Vrieslaan", "3"),
    "4": ((1045, 573.5), 45, "km 37 · Weesperplein", "4"),
    "5": ((150, 1010), -120, "FINISH km 42 · HUG!\nOlympic Stadium", "5"),
}
STATIONS = [
    # name, sub, badges, box top-left, icon points
    ("ZUID", "Metro 50 · 51 · 52 + Train", "MT", (360, 1300), [(448, 1151), (456, 1126)]),
    ("RAI", "Metro 50 · 51 + Train", "MT", (570, 1245), [(760, 1180), (768, 1205)]),
    ("EUROPAPLEIN", "Metro 52", "M", (625, 1010), [(776, 1066)]),
    ("AMSTEL", "Metro 51 · 53 · 54 + Train", "MT", (1000, 775), [(1232, 914), (1229, 944)]),
    ("WEESPERPLEIN", "Metro 51 · 53 · 54", "M", (1140, 445), [(1070, 527)]),
    ("AMSTELVEENSEWEG", "Metro 50 · 51 (nearest to finish)", "M", (15, 1290), [(196, 1158)]),
]


def annotate(page):
    # journey lines first (under everything)
    Z, RAI, AMS, WPL, AVW = (448, 1151), (768, 1205), (1229, 944), (1070, 527), (196, 1158)
    legs = [
        (SPOTS["1"][0], Z, None), (Z, RAI, "Metro 50/51/52"),
        (RAI, SPOTS["2a"][0], None), (RAI, SPOTS["2b"][0], None), (RAI, SPOTS["2c"][0], None),
        (RAI, AMS, "Metro 51"), (AMS, SPOTS["3"][0], None),
        (AMS, WPL, "Metro 51/53/54"), (WPL, SPOTS["4"][0], None),
        (WPL, AVW, "Metro 51"), (AVW, SPOTS["5"][0], None),
    ]
    for a, b, t in legs:
        dashed(page, a, b, 4.5 if t else 3.5)
    for a, b, t in legs:
        if t:
            small_tag(page, t, a, b)
    # station callouts
    for name, sub, bd, tl, icons in STATIONS:
        station(page, name, sub, bd, tl, icons)
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
    page.insert_text(P(44, 72), "Cheer for me!", fontname=FONT, fontsize=48, color=NSY)
    page.insert_text(P(44, 104), "TCS Amsterdam Marathon · Sunday 18 Oct 2026", fontname=FONT, fontsize=27, color=WHT)
    # legend panel
    pr = pymupdf.Rect(1180, 1800, 1790, 2355)
    s = page.new_shape(); s.draw_rect(pr, radius=0.03)
    s.finish(fill=WHT, color=NAVY, width=4, fill_opacity=0.92); s.commit()
    page.insert_text(P(pr.x0 + 18, pr.y0 + 38), "Cheer plan - Metro & Train only", fontname=FONT, fontsize=29, color=NAVY)
    page.insert_text(P(pr.x0 + 18, pr.y0 + 70), "(no trams / buses on race day)", fontname=FONT, fontsize=23, color=NAVY)
    items = [
        ("1", "km 6 Beethovenstraat", "from Zuid, ~10 min walk"),
        ("2", "km 12-14 (pick one)", "from RAI ~12-18 min walk; km 13 also ~10 min from Europaplein (M52)"),
        ("3", "km 32 Hugo de Vrieslaan", "from Amstel, ~12 min walk. MOST IMPORTANT!"),
        ("4", "km 37 Weesperplein", "right at the metro exit"),
        ("5", "FINISH Olympic Stadium", "Metro 51 to Amstelveenseweg + ~10 min walk (or ~20 min from Zuid)"),
    ]
    y = pr.y0 + 112
    for n, head, sub in items:
        bc = P(pr.x0 + 38, y + 4)
        s = page.new_shape(); s.draw_circle(bc, 18); s.finish(fill=YEL, color=BLK, width=2.5); s.commit()
        page.insert_text(P(bc.x - tlen(n, 22) / 2, bc.y + 8), n, fontname=FONT, fontsize=22, color=BLK)
        page.insert_text(P(pr.x0 + 68, y + 2), head, fontname=FONT, fontsize=23, color=BLK)
        rc = page.insert_textbox(pymupdf.Rect(pr.x0 + 68, y + 8, pr.x1 - 14, y + 70), sub, fontname="helv", fontsize=19, color=(0.15, 0.15, 0.15))
        y += 66 if len(sub) < 48 else 82
    page.insert_textbox(pymupdf.Rect(pr.x0 + 16, pr.y1 - 80, pr.x1 - 14, pr.y1 - 8),
                        "Check GVB / 9292 app on race day - service may change. No rush: we hug at the finish!",
                        fontname=FONT, fontsize=18, color=NAVY)


PLAN = [
    ("1", "km 6 - Beethovenstraat", "Metro to ZUID (lines 50 / 51 / 52, or train). Walk ~10 min to Beethovenstraat."),
    ("2", "km 12-14 - pick one", "Metro 50 / 51 from Zuid to RAI (or train). Walk ~12-18 min to Rijnstraat (km 12), Pres. Kennedylaan (km 13) or Amsteldijk (km 14). km 13 is also ~10 min from EUROPAPLEIN (metro 52)."),
    ("3", "km 32 - Hugo de Vrieslaan  (MOST IMPORTANT)", "Metro 51 from RAI to AMSTEL (or train). Walk ~12 min to Hugo de Vrieslaan."),
    ("4", "km 37 - Weesperplein", "Metro 51 / 53 / 54 from Amstel to WEESPERPLEIN. The spot is right at the metro exit."),
    ("5", "FINISH - Olympic Stadium", "Metro 51 from Weesperplein to AMSTELVEENSEWEG, then ~10 min walk to the Olympic Stadium. (From Zuid it is ~20 min on foot.) Hug!"),
]


def plan_page(doc, size):
    page = doc.new_page(width=595, height=842)
    W = 595
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(0, 0, W, 110)); s.finish(fill=NAVY, color=NAVY); s.commit()
    page.insert_text(P(36, 56), "Supporter plan", fontname=FONT, fontsize=34, color=NSY)
    page.insert_text(P(36, 86), "TCS Amsterdam Marathon - Sunday 18 Oct 2026", fontname=FONT, fontsize=16, color=WHT)
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, 126, W - 36, 196), radius=0.12)
    s.finish(fill=(1, 0.95, 0.75), color=BLK, width=1.5); s.commit()
    page.insert_textbox(pymupdf.Rect(48, 132, W - 48, 194),
                        "Trams and buses are cancelled on race day. Use METRO and TRAIN only. "
                        "Check the GVB / 9292 app - service may change.", fontname=FONT, fontsize=14, color=BLK)
    y = 222
    for n, head, body in PLAN:
        s = page.new_shape(); s.draw_circle(P(58, y + 14), 17); s.finish(fill=YEL, color=BLK, width=2); s.commit()
        page.insert_text(P(58 - tlen(n, 20) / 2, y + 21), n, fontname=FONT, fontsize=20, color=BLK)
        page.insert_text(P(90, y + 12), head, fontname=FONT, fontsize=16, color=NAVY)
        rc = page.insert_textbox(pymupdf.Rect(90, y + 20, W - 36, y + 110), body, fontname="helv", fontsize=13, color=BLK)
        y += 108 if len(body) > 150 else 88
    s = page.new_shape(); s.draw_rect(pymupdf.Rect(36, 750, W - 36, 810), radius=0.15)
    s.finish(fill=NAVY, color=NAVY); s.commit()
    page.insert_textbox(pymupdf.Rect(48, 758, W - 48, 808),
                        "No rush - we hug at the finish! Spot 3 (km 32) is the most important one.",
                        fontname=FONT, fontsize=15, color=WHT, align=1)


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
