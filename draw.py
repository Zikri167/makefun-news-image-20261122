"""Drawing kit for the 22 November 2026 broadsheet.

Pure Python 3.13 standard library: a tiny RGB canvas, a 5x7 bitmap
font drawn from filled cells, a hand-rolled PNG encoder (zlib + CRC),
and small geometric pictograms. No network, no files read, no clock:
the same code always draws the same bytes.
"""

import binascii
import struct
import zlib

# ---------------------------------------------------------------- font

# Each glyph is 7 rows of 5 cells. '#' is ink, '.' is blank.
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
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}

BLANK = (".....",) * 7


def glyph(ch):
    return FONT.get(ch, BLANK)


# ---------------------------------------------------------------- palette

WHITE = (255, 255, 255)
PAPER = (252, 250, 244)
INK = (18, 18, 18)
GREY = (92, 92, 92)
LIGHT = (232, 228, 218)
RED = (178, 34, 34)
DARKRED = (128, 20, 20)
NAVY = (24, 38, 68)
SKY = (52, 84, 138)
STEEL = (110, 130, 160)
GOLD = (214, 158, 46)
ORANGE = (224, 110, 30)
FLAME = (240, 160, 40)
GREEN = (46, 125, 70)
TEAL = (32, 110, 110)


# ---------------------------------------------------------------- canvas


class Canvas:
    def __init__(self, width, height, bg=PAPER):
        self.w = width
        self.h = height
        self.px = bytearray(bg * (width * height))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            half = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            for xx in range(cx - half, cx + half + 1):
                self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, t=2):
        for k in range(t):
            rr = r - k
            if rr <= 0:
                return
            steps = max(24, rr * 6)
            for s in range(steps):
                a = 2 * 3.14159265 * s / steps
                self.set(int(cx + rr * _cos(a)), int(cy + rr * _sin(a)), color)

    def tri(self, ax, ay, bx, by, cx, cy, color):
        x0 = max(0, min(ax, bx, cx))
        x1 = min(self.w - 1, max(ax, bx, cx))
        y0 = max(0, min(ay, by, cy))
        y1 = min(self.h - 1, max(ay, by, cy))
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if d == 0:
            return
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                w0 = ((by - cy) * (xx - cx) + (cx - bx) * (yy - cy)) / d
                w1 = ((cy - ay) * (xx - cx) + (ax - cx) * (yy - cy)) / d
                w2 = 1 - w0 - w1
                if w0 >= 0 and w1 >= 0 and w2 >= 0:
                    self.set(xx, yy, color)

    # -- text -------------------------------------------------------------
    def text(self, s, x, y, scale, color):
        s = s.upper()
        cx = x
        for ch in s:
            g = glyph(ch)
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx - x

    def text_w(self, s, scale):
        return len(s.upper()) * 6 * scale - scale

    def center(self, s, x, y, w, scale, color):
        tw = self.text_w(s, scale)
        self.text(s, x + max(0, (w - tw) // 2), y, scale, color)

    def wrap(self, s, scale, maxw):
        """Greedy word wrap; returns a list of lines that fit maxw."""
        words = s.upper().split(" ")
        lines = []
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if self.text_w(trial, scale) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines


def _cos(a):
    # Cosine via Taylor around 0..2pi using a short table-free series.
    # Accurate enough for ring dots; keep it deterministic.
    a = a % 6.283185307179586
    x = a
    term = 1.0
    total = 1.0
    sign = -1.0
    for n in range(1, 7):
        term *= x * x / ((2 * n - 1) * (2 * n))
        total += sign * term
        sign = -sign
    return total


def _sin(a):
    return _cos(a - 1.5707963267948966)


# ---------------------------------------------------------------- PNG


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- pictograms


def pic_missiles(cv, x, y, w, h):
    """Night sky, three missile trails over a radar dish: Bahrain."""
    cv.rect(x, y, w, h, NAVY)
    for sx, sy in ((x + 14, y + 12), (x + 40, y + 8), (x + 66, y + 16),
                   (x + 96, y + 10), (x + 122, y + 14)):
        cv.disc(sx, sy, 2, WHITE)
    for x0, y0, x1, y1 in ((x + 20, y + h - 18, x + 66, y + 16),
                           (x + 52, y + h - 14, x + 104, y + 12),
                           (x + 96, y + h - 20, x + 150, y + 18)):
        cv.line(x0, y0, x1, y1, GOLD)
        cv.tri(x1 - 3, y1 + 5, x1 + 6, y1 - 2, x1 - 1, y1 - 6, FLAME)
    cv.rect(x, y + h - 10, w, 10, INK)
    cv.line(x + 170, y + h - 10, x + 190, y + h - 34, WHITE)
    cv.line(x + 190, y + h - 34, x + 210, y + h - 10, WHITE)
    cv.line(x + 176, y + h - 22, x + 204, y + h - 22, WHITE)


def pic_blast(cv, x, y, w, h):
    """Starburst blast over broken rooftops: the night barrage."""
    cv.rect(x, y, w, h, (44, 30, 26))
    cx, cy = x + w // 2, y + h // 2 + 6
    for k in range(10):
        a = 6.283185307179586 * k / 10
        tipx = int(cx + 52 * _cos(a))
        tipy = int(cy + 30 * _sin(a))
        base = 0.35
        cv.tri(cx, cy, tipx, tipy,
               int(cx + 16 * _cos(a + base)), int(cy + 10 * _sin(a + base)),
               FLAME if k % 2 == 0 else ORANGE)
    cv.disc(cx, cy, 12, GOLD)
    for fx, fw, fh in ((0.04, 0.20, 22), (0.30, 0.24, 30),
                       (0.56, 0.18, 18), (0.80, 0.16, 26)):
        bx = x + int(fx * w)
        bw = int(fw * w)
        bh = fh
        cv.rect(bx, y + h - 8 - bh, bw, bh, INK)
        cv.tri(bx, y + h - 8 - bh, bx + bw // 2, y + h - 16 - bh,
               bx + bw, y + h - 8 - bh, INK)


def pic_trade(cv, x, y, w, h):
    """Globe with two trade arrows: EU-Indonesia deal."""
    cv.rect(x, y, w, h, (226, 238, 226))
    cx, cy = x + 52, y + h // 2
    cv.disc(cx, cy, 26, STEEL)
    cv.ring(cx, cy, 26, NAVY, 2)
    cv.line(cx - 26, cy, cx + 26, cy, NAVY)
    cv.line(cx, cy - 26, cx, cy + 26, NAVY)
    cv.disc(cx - 9, cy - 8, 5, GREEN)
    cv.disc(cx + 10, cy + 9, 6, GREEN)
    cv.line(x + 92, y + 18, x + 138, y + 18, GREEN)
    cv.tri(x + 138, y + 12, x + 138, y + 24, x + 148, y + 18, GREEN)
    cv.line(x + 148, y + h - 20, x + 102, y + h - 20, SKY)
    cv.tri(x + 102, y + h - 26, x + 102, y + h - 14, x + 92, y + h - 20, SKY)


def pic_quake(cv, x, y, w, h):
    """Andes peaks split by a crack, drawn across a wide strip."""
    cv.rect(x, y, w, h, (238, 232, 214))
    cv.tri(x + 8, y + h - 4, x + 70, y + 6, x + 132, y + h - 4, STEEL)
    cv.tri(x + 100, y + h - 4, x + 165, y + 12, x + 230, y + h - 4, NAVY)
    cv.tri(x + 200, y + h - 4, x + 255, y + 10, x + w - 8, y + h - 4, STEEL)
    mx = x + w // 2
    cv.line(mx, y + 12, mx + 8, y + 22, RED)
    cv.line(mx + 8, y + 22, mx - 2, y + 32, RED)
    cv.line(mx - 2, y + 32, mx + 6, y + h - 4, RED)


def pic_cuffs(cv, x, y, w, h):
    """Handcuffs left, badge star right: the cartel arrest."""
    cv.rect(x, y, w, h, (228, 228, 232))
    cy = y + h // 2
    cv.ring(x + 48, cy, 15, INK, 3)
    cv.ring(x + 104, cy, 15, INK, 3)
    cv.line(x + 63, cy - 3, x + 89, cy - 3, INK)
    cv.line(x + 63, cy + 3, x + 89, cy + 3, INK)
    sx = x + w - 48
    cv.disc(sx, cy, 13, GOLD)
    cv.tri(sx - 4, cy - 4, sx + 4, cy - 4, sx, cy + 5, DARKRED)


def pic_laptop(cv, x, y, w, h):
    """Laptop with a warning triangle, code lines to the right."""
    cv.rect(x, y, w, h, (226, 232, 238))
    cv.rect(x + 24, y + 6, 72, 30, NAVY)
    cv.rect(x + 29, y + 11, 62, 20, (200, 220, 240))
    cv.rect(x + 14, y + 36, 92, 5, INK)
    cv.tri(x + 55, y + 14, x + 69, y + 30, x + 41, y + 30, GOLD)
    cv.rect(x + 53, y + 18, 3, 6, INK)
    cv.rect(x + 53, y + 26, 3, 3, INK)
    for k, ln in enumerate((150, 190, 170)):
        cv.rect(x + 122, y + 10 + k * 10, ln, 4, STEEL)


def pic_bridge(cv, x, y, w, h):
    """A bridge arc across the strip, blast at its span: Crimea."""
    cv.rect(x, y, w, h, (210, 226, 240))
    cv.rect(x + 12, y + 6, 8, h - 12, INK)
    cv.rect(x + w - 20, y + 6, 8, h - 12, INK)
    for k in range(13):
        t = k / 12.0
        bx = int(x + 20 + t * (w - 40))
        by = int(y + 16 - 10 * (1 - (2 * t - 1) ** 2))
        cv.set(bx, by, INK)
        cv.set(bx, by + 1, INK)
        cv.line(bx, by, bx, y + h - 8, STEEL)
    cv.rect(x + 8, y + h - 8, w - 16, 4, INK)
    cx = x + w // 2
    cv.disc(cx, y + 12, 7, FLAME)
    cv.tri(cx - 10, y + 10, cx + 10, y + 10, cx, y + 2, ORANGE)


def pic_ship(cv, x, y, w, h):
    """A cargo ship on waves with a drone above: the Baltic attack."""
    cv.rect(x, y, w, h, (208, 226, 238))
    cv.disc(x + 200, y + 8, 3, INK)
    cv.line(x + 200, y + 8, x + 170, y + 18, INK)
    cv.line(x + 170, y + 18, x + 140, y + 26, INK)
    cv.tri(x + 24, y + 26, x + 150, y + 26, x + 140, y + 38, NAVY)
    cv.rect(x + 44, y + 12, 22, 14, SKY)
    cv.rect(x + 72, y + 16, 18, 10, SKY)
    cv.line(x + 8, y + h - 8, x + w - 8, y + h - 8, STEEL)
    cv.line(x + 30, y + h - 4, x + w - 40, y + h - 4, STEEL)


def pic_globe(cv, x, y, w, h):
    """A warming globe with heat flames: COP31."""
    cv.rect(x, y, w, h, (226, 236, 228))
    cx, cy = x + 44, y + h // 2 + 2
    cv.disc(cx, cy, 17, STEEL)
    cv.ring(cx, cy, 17, NAVY, 2)
    cv.line(cx - 17, cy, cx + 17, cy, NAVY)
    cv.line(cx, cy - 17, cx, cy + 17, NAVY)
    cv.disc(cx - 6, cy - 6, 4, GREEN)
    cv.disc(cx + 7, cy + 6, 4, GREEN)
    for fx in (x + 96, x + 132, x + 168):
        cv.tri(fx, y + 8, fx + 9, y + 8, fx + 4, y + h - 12, ORANGE)
        cv.tri(fx + 2, y + 14, fx + 7, y + 14, fx + 4, y + h - 16, FLAME)
