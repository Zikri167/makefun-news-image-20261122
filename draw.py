"""draw.py - tiny procedural drawing kit for the NI-22 v3 broadsheet.

Pure standard library: a 5x7 bitmap font, an RGB pixel canvas with
line / rect / circle / polygon primitives, a small set of news
pictograms, and a deterministic PNG writer (zlib + CRC).
"""

import binascii
import struct
import zlib

# ---------------------------------------------------------------- font
# Each glyph: 7 rows of 5 pixels, '#' = ink.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": (".##..", "..#..", "...#.", "...#.", "...#.", "..#..", ".##.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
}

GLYPH_W = 5
GLYPH_H = 7


def text_width(s, scale):
    """Pixel width of a string at the given integer scale."""
    if not s:
        return 0
    return len(s) * (GLYPH_W + 1) * scale - scale


def draw_text(cv, x, y, s, scale, color, bold=False):
    """Draw string s with its top-left corner at (x, y). Returns width."""
    s = s.upper()
    cx = x
    extra = max(1, scale // 3) if bold else 0
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == "#":
                    px = cx + col_i * scale
                    py = y + row_i * scale
                    cv.rect(px, py, scale + extra, scale, color)
        cx += (GLYPH_W + 1) * scale
    return cx - x - scale


def draw_text_centered(cv, cx, y, s, scale, color, bold=False):
    w = text_width(s.upper(), scale)
    return draw_text(cv, cx - w // 2, y, s, scale, color, bold)


def wrap_lines(s, scale, max_width):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    words = s.upper().split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def stamp(self, x, y, size, color):
        self.rect(x - size // 2, y - size // 2, size, size, color)

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + 3 * (x1 - x0)] = row

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.stamp(x, y, t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color, t=1, fill=False):
        if fill:
            for yy in range(cy - r, cy + r + 1):
                span = int((r * r - (yy - cy) ** 2) ** 0.5)
                self.rect(cx - span, yy, 2 * span + 1, 1, color)
            return
        # midpoint circle, stamped for thickness
        x, y, d = r, 0, 0
        while x >= y:
            for ox, oy in ((x, y), (-x, y), (x, -y), (-x, -y),
                           (y, x), (-y, x), (y, -x), (-y, -x)):
                self.stamp(cx + ox, cy + oy, t, color)
            y += 1
            if d <= 0:
                d += 2 * y + 1
            else:
                x -= 1
                d += 2 * (y - x) + 1

    def ellipse(self, cx, cy, rx, ry, color, t=1):
        import math
        steps = max(24, int(2 * math.pi * max(rx, ry) / 2))
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            x = int(cx + rx * math.cos(a))
            y = int(cy + ry * math.sin(a))
            self.stamp(x, y, t, color)

    def poly(self, pts, color, fill=True):
        if not fill:
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                self.line(x0, y0, x1, y1, color, 2)
            return
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(len(pts)):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % len(pts)]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(int(x0 + (yy - y0) * (x1 - x0) / (y1 - y0)))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(xs[i], yy, xs[i + 1] - xs[i] + 1, 1, color)


# ---------------------------------------------------------------- png out
def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))


def save_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.buf[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# ---------------------------------------------------------------- icons
INK = (24, 24, 24)
RED = (178, 24, 32)


def icon_strike(cv, x, y, w, h):
    """Radar dish, an incoming missile and an impact burst."""
    cy = y + h // 2
    # radar: concentric rings + sweep + mast
    rcx, rcy = x + 78, cy - 6
    for r in (16, 30, 44):
        cv.circle(rcx, rcy, r, INK, 3)
    cv.circle(rcx, rcy, 4, RED, 1, fill=True)
    cv.line(rcx, rcy, rcx + 34, rcy - 34, RED, 4)
    cv.line(rcx - 8, rcy + 46, rcx + 8, rcy + 46, INK, 5)
    cv.line(rcx, rcy + 30, rcx, rcy + 48, INK, 5)
    # missile: diagonal body from lower-left to upper-right
    mx0, my0 = x + 190, y + h - 26
    mx1, my1 = x + 330, y + 30
    cv.line(mx0, my0, mx1, my1, INK, 11)
    cv.poly([(mx1, my1), (mx1 - 26, my1 + 8), (mx1 - 8, my1 + 26)], RED)
    cv.poly([(mx0, my0), (mx0 + 4, my0 - 24), (mx0 + 18, my0 - 4)], INK)
    cv.poly([(mx0, my0), (mx0 + 24, my0 - 4), (mx0 + 4, my0 + 18)], INK)
    cv.poly([(mx0 - 4, my0 + 4), (mx0 - 26, my0 + 16), (mx0 - 8, my0 + 22)], RED)
    # burst at the tip
    bx, by = mx1 + 42, my1 - 6
    import math
    for i in range(8):
        a = 2 * math.pi * i / 8
        cv.line(bx, by, bx + int(26 * math.cos(a)), by + int(26 * math.sin(a)),
                RED, 5)
    cv.circle(bx, by, 7, RED, 1, fill=True)


def icon_trade(cv, x, y, w, h):
    """A ring with a bold percent sign: tariffs cut by a trade pact."""
    cx, cy = x + w // 2, y + h // 2
    r = min(w, h) // 2 - 10
    cv.circle(cx, cy, r, INK, 5)
    cv.circle(cx, cy, r - 12, INK, 2)
    # percent sign from primitives: two rings and a slash
    cv.circle(cx - 15, cy - 15, 9, RED, 4)
    cv.circle(cx + 15, cy + 15, 9, RED, 4)
    cv.line(cx + 18, cy - 24, cx - 18, cy + 24, RED, 6)
    # two arrowheads on the ring, opposed: exchange
    cv.poly([(cx + r - 4, cy - 16), (cx + r + 12, cy + 6), (cx + r - 20, cy + 8)],
            INK)
    cv.poly([(cx - r + 4, cy + 16), (cx - r - 12, cy - 6), (cx - r + 20, cy - 8)],
            INK)


def icon_globe(cv, cx, cy, r):
    cv.circle(cx, cy, r, INK, 3)
    cv.ellipse(cx, cy, max(4, r // 3), r, INK, 2)
    cv.ellipse(cx, cy, max(8, 2 * r // 3), r, INK, 2)
    cv.line(cx - r, cy - r // 2, cx + r, cy - r // 2, INK, 2)
    cv.line(cx - r, cy + r // 2, cx + r, cy + r // 2, INK, 2)
    cv.line(cx - r, cy, cx + r, cy, INK, 2)


def icon_drone(cv, cx, cy, s):
    d = s // 2
    cv.line(cx - d, cy - d, cx + d, cy + d, INK, 4)
    cv.line(cx - d, cy + d, cx + d, cy - d, INK, 4)
    for ox, oy in ((-d, -d), (d, -d), (-d, d), (d, d)):
        cv.circle(cx + ox, cy + oy, 9, INK, 3)
    cv.rect(cx - 9, cy - 7, 18, 14, RED)


def icon_bridge(cv, x, y, w, h):
    deck = y + h - 14
    top = y + 8
    cv.line(x + 6, deck, x + w - 6, deck, INK, 5)
    for tx in (x + 26, x + w - 26):
        cv.line(tx, top, tx, deck, INK, 6)
        cv.line(tx - 8, top, tx + 8, top, INK, 5)
    # suspension arc between the towers
    import math
    x0, x1 = x + 26, x + w - 26
    for i in range(41):
        t = i / 40
        px = int(x0 + (x1 - x0) * t)
        py = int(top + (deck - top - 16) * (4 * t * (1 - t)) ** 1.2)
        cv.stamp(px, py, 3, RED)
    for i in range(1, 6):
        t = i / 6
        px = int(x0 + (x1 - x0) * t)
        py = int(top + (deck - top - 16) * (4 * t * (1 - t)) ** 1.2)
        cv.line(px, py, px, deck, INK, 2)
    _ = math


def icon_ballot(cv, cx, cy, s):
    bw, bh = s + 26, s - 6
    x0, y0 = cx - bw // 2, cy - bh // 2 + 12
    cv.frame(x0, y0, bw, bh, INK, 4)
    cv.rect(x0 + 10, y0 + 10, bw - 20, 5, INK)
    # paper rising from the slot, with a tick
    px0, py0 = cx - 17, y0 - 30
    cv.frame(px0, py0, 34, 34, INK, 3)
    cv.line(px0 + 7, py0 + 17, px0 + 14, py0 + 25, RED, 4)
    cv.line(px0 + 14, py0 + 25, px0 + 27, py0 + 8, RED, 4)


def icon_quake(cv, x, y, w, h):
    base = y + h - 10
    cv.line(x + 4, base, x + w - 4, base, INK, 3)
    pts = []
    n = 9
    top = y + 4
    low = base - 12
    mid = (top + low) // 2
    for i in range(n + 1):
        px = x + 10 + (w - 20) * i // n
        if i in (0, n):
            py = mid
        elif i % 2:
            py = top
        else:
            py = low
        pts.append((px, py))
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 4)


def icon_database(cv, cx, cy, s):
    rx, ry = s // 2 + 8, 12
    top = cy - s // 2
    bot = cy + s // 2
    cv.ellipse(cx, top, rx, ry, INK, 3)
    cv.line(cx - rx, top, cx - rx, bot, INK, 3)
    cv.line(cx + rx, top, cx + rx, bot, INK, 3)
    cv.ellipse(cx, bot, rx, ry, INK, 3)
    cv.ellipse(cx, cy, rx, ry, INK, 2)
    tw = text_width("!", 6)
    draw_text(cv, cx - tw // 2, cy - 21, "!", 6, RED, bold=True)
