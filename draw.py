"""Draw the 22 November 2026 world-news broadsheet as a 1024x1024 PNG.

Pure standard library only: a tiny 5x7 bitmap font, a bytearray RGB canvas,
and a hand-rolled PNG encoder (zlib + CRC32). No Pillow, no network, and
the same input always produces the same bytes.
"""

import struct
import zlib

W = 1024
H = 1024

PAPER = (248, 244, 232)
INK = (20, 20, 20)
RED = (163, 22, 33)
BLUE = (29, 78, 137)
GOLD = (176, 132, 32)
GREY = (110, 108, 100)
LIGHT = (233, 228, 214)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- font
# Each glyph is 7 rows of 5 cells; "1" is ink, "0" is empty.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11110", "01000", "01000", "01001", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    ";": ("00000", "01100", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "^": ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "\\": ("10000", "01000", "01000", "00100", "00010", "00010", "00001"),
    "`": ("01000", "00100", "00000", "00000", "00000", "00000", "00000"),
}

BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


def text_width(text, scale):
    """Pixel width of text at the given scale (6 units per char, minus 1)."""
    return len(text) * 6 * scale - scale if text else 0


def wrap(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bg) * (w * h)

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = color[0]
                self.buf[i + 1] = color[1]
                self.buf[i + 2] = color[2]

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - thick // 2, y0 - thick // 2, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.px(xx, yy, color)
                else:
                    if r * r - 2 * r <= d2 <= r * r:
                        self.px(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=2):
        for t in range(thick):
            self.circle(cx, cy, r - t, color, fill=False)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        # Filled triangle by scanline interpolation.
        ys = sorted([y0, y1, y2])
        for y in range(ys[0], ys[2] + 1):
            xs = []
            for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                    (x2, y2, x0, y0)):
                if ay == by:
                    continue
                if min(ay, by) <= y <= max(ay, by):
                    t = (y - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            if len(xs) >= 2:
                self.rect(int(min(xs)), y, int(max(xs)) - int(min(xs)) + 1,
                          1, color)

    def text(self, s, x, y, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, BLANK)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, s, cx, y, scale, color):
        self.text(s, cx - text_width(s, scale) // 2, y, scale, color)

    def paragraph(self, s, x, y, max_w, scale, color, leading=None):
        lh = leading if leading is not None else 9 * scale
        yy = y
        for line in wrap(s, max_w, scale):
            self.text(line, x, yy, scale, color)
            yy += lh
        return yy


# ---------------------------------------------------------------- PNG
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", ihdr)
    data += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    data += _chunk(b"IEND", b"")
    return data


# ---------------------------------------------------------------- pictograms
def globe(cv, cx, cy, r, color, accent):
    cv.circle(cx, cy, r, color, fill=False)
    cv.ring(cx, cy, r, color, thick=2)
    cv.hline(cx - r, cy, 2 * r, color)
    cv.vline(cx, cy - r, 2 * r, color)
    cv.line(cx - r + 4, cy - r // 2, cx + r - 4, cy - r // 2, color)
    cv.line(cx - r + 4, cy + r // 2, cx + r - 4, cy + r // 2, color)
    cv.circle(cx + r // 3, cy - r // 3, max(2, r // 5), accent, fill=True)


def pictogram(cv, kind, x, y, w, h):
    """Small scene drawn inside the box (x, y, w, h)."""
    cx = x + w // 2
    cy = y + h // 2
    if kind == "flags":
        # Three flags over a globe: the Shenzhen summit.
        for i, col in enumerate((RED, BLUE, GOLD)):
            fx = x + 24 + i * (w // 4)
            cv.vline(fx, y + 6, h - 12, INK, thick=3)
            cv.rect(fx + 3, y + 8, w // 6, 16, col)
        globe(cv, x + w - 48, cy, 26, BLUE, RED)
    elif kind == "climate":
        # Globe with a rising thermometer bar: COP31 deadlock.
        globe(cv, cx - 40, cy, 30, BLUE, RED)
        bx = x + w - 44
        cv.rect(bx, y + 8, 14, h - 16, WHITE)
        cv.vline(bx, y + 8, h - 16, INK, thick=2)
        cv.vline(bx + 13, y + 8, h - 16, INK, thick=2)
        cv.rect(bx + 3, y + h - 30, 8, 20, RED)
        cv.circle(bx + 7, y + h - 12, 8, RED, fill=True)
    elif kind == "quake":
        # Cracked ground and tilted blocks: Peru quake.
        pts = [(x + 6, y + h - 14), (x + w // 3, y + h // 2),
               (x + w // 2, y + h - 18), (x + 2 * w // 3, y + h // 3),
               (x + w - 8, y + h - 12)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            cv.line(ax, ay, bx, by, RED, thick=3)
        cv.rect(x + 12, y + 8, 18, 22, INK)
        cv.rect(x + 40, y + 14, 14, 16, BLUE)
        cv.rect(x + w - 34, y + 10, 20, 20, GOLD)
    elif kind == "bridge":
        # Bridge arc with towers and a burst: Crimean Bridge.
        cv.line(x + 8, y + h - 12, x + w - 8, y + h - 12, INK, thick=3)
        cv.vline(x + w // 4, y + 14, h - 26, INK, thick=3)
        cv.vline(x + 3 * w // 4, y + 14, h - 26, INK, thick=3)
        midx, midy = cx, y + h - 12
        cv.line(x + w // 4, y + 16, midx, midy - 18, BLUE, thick=2)
        cv.line(x + 3 * w // 4, y + 16, midx, midy - 18, BLUE, thick=2)
        for dx, dy in ((-8, -8), (8, -8), (-10, 0), (10, 0), (0, -10)):
            cv.line(cx, cy - 6, cx + dx, cy - 6 + dy, RED, thick=2)
        cv.circle(cx, cy - 6, 4, RED, fill=True)
    elif kind == "badge":
        # Star badge: the cartel arrest.
        cv.circle(cx, cy, 22, GOLD, fill=True)
        cv.circle(cx, cy, 22, INK, fill=False)
        cv.circle(cx, cy, 15, WHITE, fill=True)
        cv.text("*", cx - 9, cy - 13, 3, RED)
    elif kind == "fence":
        # Border fence posts and rails: Estonia closes its border.
        for i in range(5):
            fx = x + 10 + i * (w - 20) // 4
            cv.vline(fx, y + 8, h - 16, INK, thick=3)
        cv.hline(x + 6, y + 16, w - 12, RED, thick=3)
        cv.hline(x + 6, y + h - 20, w - 12, RED, thick=3)
        cv.hline(x + 6, cy - 2, w - 12, INK, thick=2)
    elif kind == "laptop":
        # Laptop with a warning mark: the FBI database hack.
        cv.rect(x + w // 4, y + 6, w // 2, h // 2 + 4, BLUE)
        cv.rect(x + w // 4 + 3, y + 9, w // 2 - 6, h // 2 - 2, WHITE)
        cv.rect(x + w // 6, y + 10 + h // 2, 2 * w // 3, 6, INK)
        tx, ty = cx, y + 12
        cv.triangle(tx, ty, tx - 12, ty + 20, tx + 12, ty + 20, GOLD)
        cv.vline(tx, ty + 6, 8, INK, thick=2)
        cv.px(tx, ty + 16, INK)
    elif kind == "ballot":
        # Ballot box with a tick: South Africa votes.
        cv.rect(x + w // 4, y + h - 26, w // 2, 20, RED)
        cv.rect(x + w // 4, y + 10, w // 2, h - 36, WHITE)
        cv.hline(x + w // 4, y + 10, w // 2, INK, thick=2)
        cv.hline(x + w // 4, y + h - 26, w // 2, INK, thick=2)
        cv.vline(x + w // 4, y + 10, h - 16, INK, thick=2)
        cv.vline(x + 3 * w // 4, y + 10, h - 16, INK, thick=2)
        cv.line(cx - 12, cy - 2, cx - 3, cy + 8, BLUE, thick=3)
        cv.line(cx - 3, cy + 8, cx + 14, cy - 12, BLUE, thick=3)
    elif kind == "ship":
        # Tanker on waves: the Hormuz attack.
        cv.rect(x + 10, y + 12, w - 20, 16, INK)
        cv.rect(x + w // 2 - 4, y + 2, 10, 10, RED)
        for i in range(3):
            wy = y + h - 14 + i * 5
            cv.line(x + 8, wy, x + w - 8, wy, BLUE, thick=2)
    elif kind == "spiral":
        # Cyclone spiral: Akvan.
        for r in (22, 16, 10, 5):
            cv.circle(cx, cy, r, BLUE, fill=False)
        cv.circle(cx, cy, 4, RED, fill=True)


# ---------------------------------------------------------------- layout
LEADS = [
    {
        "kicker": "SUMMIT IN SHENZHEN",
        "pic": "flags",
        "head": "TRUMP HAILS 'MOMENTOUS' SUMMIT WITH XI AND PUTIN",
        "stand": "Three leaders meet in Shenzhen as the US president touts a breakthrough - while critics question the cost on Iran and Ukraine.",
    },
    {
        "kicker": "CLIMATE",
        "pic": "climate",
        "head": "COP31 TALKS DEADLOCKED OVER FOSSIL FUELS",
        "stand": "Delegates from nearly 200 countries stall on a new climate deal as the fight over oil, gas and coal blocks agreement.",
    },
]

GRID = [
    {
        "kicker": "PERU",
        "pic": "quake",
        "head": "6.9 QUAKE SHAKES PERU'S ANDES",
        "body": "No damage or casualties reported at first.",
    },
    {
        "kicker": "UKRAINE",
        "pic": "bridge",
        "head": "ZELENSKY: BRIDGE STRIKES 'FAIR RESPONSE'",
        "body": "Kyiv's leader hits back after Trump calls Putin a friend.",
    },
    {
        "kicker": "MEXICO",
        "pic": "badge",
        "head": "'EL CHAPO ISIDRO' ARRESTED IN RAID",
        "body": "Alleged cartel boss seized by special forces.",
    },
    {
        "kicker": "EUROPE",
        "pic": "fence",
        "head": "ESTONIA TO CLOSE BORDER WITH RUSSIA",
        "body": "Moscow decries a 'new Iron Curtain'.",
    },
    {
        "kicker": "UNITED STATES",
        "pic": "laptop",
        "head": "FBI PROBES HACK OF ITS CRIME DATABASE",
        "body": "Apparent breach of the NCIC police system.",
    },
    {
        "kicker": "SOUTH AFRICA",
        "pic": "ballot",
        "head": "ANC FIGHTS TO HOLD ITS CITIES",
        "body": "Local elections test the ruling party.",
    },
]

BRIEF = [
    "Hormuz: ADNOC vessel attacked; one crew member missing.",
    "Cyclone Akvan cancels 14 flights at Ranchi airport.",
    "Vance refuses to back Trump's Iran strikes.",
    "Mamdani unveils plan to close New York's Rikers Island jail.",
    "Cricket: India face New Zealand in the 1st Test at Wellington.",
    "Nepal PM Balendra Shah to meet PM Modi on first visit.",
]


def build_image():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.text_center("THE WORLD IN ONE DAY", W // 2, 30, 7, INK)
    cv.text_center("SUNDAY 22 NOVEMBER 2026", W // 2, 94, 4, RED)
    cv.hline(30, 134, W - 60, INK, thick=3)
    cv.hline(30, 140, W - 60, INK, thick=1)

    # Two lead stories.
    lead_x = [30, 528]
    lead_w = 466
    for i, lead in enumerate(LEADS):
        x = lead_x[i]
        cv.text(lead["kicker"], x, 156, 2, RED)
        cv.rect(x, 176, lead_w, 80, LIGHT)
        cv.rect(x, 176, lead_w, 80, INK) if False else None
        pictogram(cv, lead["pic"], x, 176, lead_w, 80)
        y = cv.paragraph(lead["head"], x, 268, lead_w, 3, INK, leading=26)
        cv.paragraph(lead["stand"], x, y + 8, lead_w, 2, INK, leading=17)
    cv.vline(512, 156, 236, GREY, thick=1)
    cv.hline(30, 404, W - 60, INK, thick=2)

    # Grid of six stories: 3 columns x 2 rows.
    cell_w, cell_h = 308, 168
    for idx, story in enumerate(GRID):
        col, row = idx % 3, idx // 3
        x = 30 + col * (cell_w + 20)
        y = 420 + row * (cell_h + 12)
        cv.rect(x, y, cell_w, 56, LIGHT)
        pictogram(cv, story["pic"], x, y, cell_w, 56)
        cv.text(story["kicker"], x, y + 64, 2, RED)
        y2 = cv.paragraph(story["head"], x, y + 84, cell_w, 2, INK,
                          leading=17)
        cv.paragraph(story["body"], x, y2 + 4, cell_w, 2, GREY, leading=17)
        if col < 2:
            cv.vline(x + cell_w + 10, y, cell_h, GREY, thick=1)

    # In brief.
    cv.hline(30, 778, W - 60, INK, thick=2)
    cv.text("IN BRIEF", 30, 790, 3, INK)
    for i, item in enumerate(BRIEF):
        col, row = i % 2, i // 2
        x = 30 + col * 492
        y = 826 + row * 46
        cv.rect(x, y + 2, 10, 10, RED)
        cv.paragraph(item, x + 18, y, 454, 2, INK, leading=17)

    # Footer.
    cv.hline(30, 968, W - 60, INK, thick=1)
    cv.text_center("ALL STORIES REPORTED ON SUNDAY 22 NOVEMBER 2026",
                   W // 2, 978, 2, GREY)

    return png_bytes(cv)


if __name__ == "__main__":
    import sys
    data = build_image()
    sys.stdout.buffer.write(data)
