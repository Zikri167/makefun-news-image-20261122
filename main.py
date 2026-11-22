"""main.py - NI-22 v3: 'The World in One Day', Sunday 22 November 2026.

Draws a one-page broadsheet summing up the day's world news and writes
it to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png). Pure
standard library, fully deterministic: two runs write the same bytes.

Every story happened, or was first reported, on 22 November 2026:
two leads (Iran strikes US assets in Bahrain; the EU-Indonesia trade
pact), a grid of six, and ten one-line briefs - 18 stories in all.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from draw import (Canvas, INK, RED, draw_text, draw_text_centered,
                  icon_ballot, icon_bridge, icon_database, icon_drone,
                  icon_globe, icon_quake, icon_strike, icon_trade,
                  save_png, text_width, wrap_lines)

W, H = 1024, 1024
PAPER = (250, 248, 241)
PANEL = (240, 235, 224)
STRIP = (243, 239, 230)
GREY = (96, 92, 84)
MARGIN = 28

LEADS = [
    {
        "icon": "strike",
        "headline": "IRAN STRIKES US BASES IN BAHRAIN",
        "body": ("Missiles and drones hit two US Patriot radar sites; "
                 "Manama condemns the attack as Gulf tensions peak."),
    },
    {
        "icon": "trade",
        "headline": "EU AND INDONESIA SIGN HISTORIC DEAL",
        "body": ("After 10 years of talks, 98.5% of tariffs are "
                 "scrapped in a landmark trade pact."),
    },
]

GRID = [
    {
        "icon": "globe",
        "headline": "COP31 TALKS GO INTO OVERTIME",
        "body": "Deadlock on fossil fuels drags on.",
    },
    {
        "icon": "drone",
        "headline": "DRONE HITS RUSSIAN SHIP",
        "body": "Finland blames Ukraine for Gulf ship attack.",
    },
    {
        "icon": "bridge",
        "headline": "ZELENSKY: NATO IS THE GUARANTEE",
        "body": "Crimea bridge hit called a fair response.",
    },
    {
        "icon": "ballot",
        "headline": "HONG KONG OPENS ELECTION VOTE",
        "body": "5,700 electors vote for the Election Committee.",
    },
    {
        "icon": "quake",
        "headline": "QUAKE 6.7 ROCKS PERU ANDES",
        "body": "Tremor felt in Lima; no deaths reported yet.",
    },
    {
        "icon": "database",
        "headline": "FBI PROBES NCIC DATABASE HACK",
        "body": "Suspected breach of US criminal records probed.",
    },
]

BRIEFS_LEFT = [
    "Denmark: Russia plotted rapper killing",
    "UN killer-robot talks fail to agree",
    "Sudan: Tasis alliance seizes Bau area",
    "Myanmar: 4.1 quake strikes before dawn",
    "India: toxic liquor kills 11 in Manipur",
]

BRIEFS_RIGHT = [
    "Oman: tanker attacked off the coast",
    "Vance balks at backing strike on Iran",
    "Trump: Iran deal could last 20 years",
    "Israel: Eisenkot invites Likud talks",
    "South Africa: ANC fights to hold cities",
]


def warn(msg):
    sys.stderr.write("layout: " + msg + "\n")


def fit_lines(text, scale, width, want, what):
    lines = wrap_lines(text, scale, width)
    if len(lines) != want:
        warn("%s wraps to %d lines (want %d): %r" % (what, len(lines), want, lines))
    return lines


def draw_lead(cv, x, y, w, lead):
    cv.rect(x, y, w, 140, PANEL)
    cv.frame(x, y, w, 140, INK, 2)
    if lead["icon"] == "strike":
        icon_strike(cv, x + 10, y + 6, w - 20, 128)
    else:
        icon_trade(cv, x + 10, y + 6, w - 20, 128)
    inner = w - 24
    lines = fit_lines(lead["headline"], 4, inner, 2, "lead headline")
    for i, ln in enumerate(lines[:2]):
        draw_text(cv, x + 12, y + 154 + i * 34, ln, 4, INK, bold=True)
    body = fit_lines(lead["body"], 2, inner, 3, "lead body")
    for i, ln in enumerate(body[:3]):
        draw_text(cv, x + 12, y + 232 + i * 22, ln, 2, INK)


def draw_cell(cv, x, y, w, cell):
    cv.rect(x, y, w, 62, STRIP)
    cx = x + w // 2
    cy = y + 31
    if cell["icon"] == "globe":
        icon_globe(cv, cx, cy, 24)
    elif cell["icon"] == "drone":
        icon_drone(cv, cx, cy, 44)
    elif cell["icon"] == "bridge":
        icon_bridge(cv, x + w // 2 - 70, y + 5, 140, 52)
    elif cell["icon"] == "ballot":
        icon_ballot(cv, cx, cy + 4, 44)
    elif cell["icon"] == "quake":
        icon_quake(cv, x + w // 2 - 48, y + 8, 96, 46)
    elif cell["icon"] == "database":
        icon_database(cv, cx, cy, 40)
    inner = w - 8
    lines = fit_lines(cell["headline"], 3, inner, 2, "grid headline")
    for i, ln in enumerate(lines[:2]):
        draw_text(cv, x + 4, y + 72 + i * 25, ln, 3, INK, bold=True)
    body = fit_lines(cell["body"], 2, inner, 2, "grid body")
    for i, ln in enumerate(body[:2]):
        draw_text(cv, x + 4, y + 126 + i * 20, ln, 2, INK)


def build():
    cv = Canvas(W, H, PAPER)

    # ---- masthead
    draw_text_centered(cv, W // 2, 16, "THE WORLD IN ONE DAY", 7, INK, bold=True)
    draw_text_centered(cv, W // 2, 76, "SUNDAY 22 NOVEMBER 2026", 3, RED, bold=True)
    cv.rect(MARGIN, 106, W - 2 * MARGIN, 3, INK)
    cv.rect(MARGIN, 111, W - 2 * MARGIN, 5, RED)

    # ---- leads
    lead_y = 128
    lead_w = (W - 2 * MARGIN - 16) // 2
    draw_lead(cv, MARGIN, lead_y, lead_w, LEADS[0])
    draw_lead(cv, MARGIN + lead_w + 16, lead_y, lead_w, LEADS[1])
    cv.line(W // 2, lead_y + 150, W // 2, lead_y + 262, GREY, 1)
    leads_end = lead_y + 290

    cv.rect(MARGIN, leads_end + 12, W - 2 * MARGIN, 2, INK)

    # ---- grid of six
    grid_y = leads_end + 26
    cell_w = (W - 2 * MARGIN - 2 * 12) // 3
    for r in range(2):
        for c in range(3):
            x = MARGIN + c * (cell_w + 12)
            y = grid_y + r * 176
            draw_cell(cv, x, y, cell_w, GRID[r * 3 + c])
    grid_end = grid_y + 176 + 160

    cv.rect(MARGIN, grid_end + 14, W - 2 * MARGIN, 2, INK)

    # ---- in brief
    brief_y = grid_end + 28
    draw_text(cv, MARGIN, brief_y, "IN BRIEF", 3, INK, bold=True)
    cv.rect(MARGIN, brief_y + 26, text_width("IN BRIEF", 3), 3, RED)
    lines_y = brief_y + 42
    for col, briefs in enumerate((BRIEFS_LEFT, BRIEFS_RIGHT)):
        x = MARGIN + col * ((W - 2 * MARGIN) // 2 + 6)
        for i, item in enumerate(briefs):
            y = lines_y + i * 24
            cv.rect(x, y + 4, 6, 6, RED)
            draw_text(cv, x + 14, y, item, 2, INK)
    brief_end = lines_y + 5 * 24

    # ---- footer
    cv.rect(MARGIN, brief_end + 16, W - 2 * MARGIN, 2, INK)
    draw_text_centered(cv, W // 2, brief_end + 28,
                       "COMPILED FROM WIRE REPORTS * SUNDAY 22 NOVEMBER 2026",
                       2, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = save_png(build(), path)
    sys.stderr.write("wrote %s (%d bytes)\n" % (path, size))


if __name__ == "__main__":
    main()
