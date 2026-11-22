"""The World in One Day - Sunday 22 November 2026.

A procedural broadsheet: two lead stories (Iran's strikes on US bases
in Bahrain; Russia's overnight barrage on Ukraine), the EU-Indonesia
trade deal, six more stories in a grid, and an IN BRIEF column.
Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png (or
/output/entry.png). Standard library only; deterministic: the same
code always writes the same bytes.
"""

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from draw import (Canvas, INK, PAPER, WHITE, GREY, LIGHT, RED, DARKRED,
                  NAVY, GOLD, GREEN, TEAL, write_png, pic_missiles,
                  pic_blast, pic_trade, pic_quake, pic_cuffs, pic_laptop,
                  pic_bridge, pic_ship, pic_globe)

W = 1024
H = 1024
M = 28                      # side margin
CW = W - 2 * M              # content width: 968


def lead(cv, x, y, w, h, pic, headline, body):
    cv.rect(x, y, w, h, WHITE)
    cv.frame(x, y, w, h, INK, 2)
    pic(cv, x + 2, y + 2, w - 4, 84)
    hy = y + 96
    lines = cv.wrap(headline, 4, w - 32)
    for ln in lines[:2]:
        cv.text(ln, x + 16, hy, 4, INK)
        hy += 32
    by = hy + 10
    for ln in cv.wrap(body, 2, w - 32)[:4]:
        cv.text(ln, x + 16, by, 2, INK)
        by += 16


def cell(cv, x, y, w, h, pic, tag, headline, body):
    cv.rect(x, y, w, h, WHITE)
    cv.frame(x, y, w, h, INK, 2)
    cv.rect(x + 2, y + 2, w - 4, 6, tag[1])
    pic(cv, x + 2, y + 8, w - 4, 46)
    hy = y + 60
    for ln in cv.wrap(headline, 2, w - 24)[:2]:
        cv.text(ln, x + 12, hy, 2, INK)
        hy += 16
    by = hy + 6
    for ln in cv.wrap(body, 2, w - 24)[:2]:
        cv.text(ln, x + 12, by, 2, GREY)
        by += 15


def main():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.rect(0, 0, W, 96, INK)
    cv.center("THE WORLD IN ONE DAY", 0, 22, W, 6, WHITE)
    cv.rect(0, 96, W, 34, RED)
    cv.center("SUNDAY 22 NOVEMBER 2026", 0, 103, W, 3, WHITE)
    cv.center("MISSILES OVER BAHRAIN - RUSSIA'S NIGHT BARRAGE - EU SIGNS ASIA PACT",
              M, 142, CW, 2, DARKRED)

    # Two leads.
    lead(cv, M, 166, 472, 276, pic_missiles,
         "IRAN STRIKES US BASES IN BAHRAIN",
         "IRGC MISSILES AND DRONES HIT US PATRIOT RADARS. "
         "BAHRAIN SAYS A FACTORY CAUGHT FIRE, NO INJURIES. "
         "TANKERS HIT NEAR HORMUZ.")
    lead(cv, 524, 166, 472, 276, pic_blast,
         "RUSSIA'S NIGHT BARRAGE ON UKRAINE",
         "MORE THAN 50 MISSILES AND 500 DRONES OVERNIGHT. "
         "FIVE KILLED, HOMES HIT IN LVIV. "
         "POLAND SCRAMBLES JETS.")

    # Trade band.
    bx, by, bw, bh = M, 452, CW, 84
    cv.rect(bx, by, bw, bh, WHITE)
    cv.frame(bx, by, bw, bh, INK, 2)
    pic_trade(cv, bx + 2, by + 2, 150, bh - 4)
    cv.text("EU AND INDONESIA SIGN TRADE DEAL", bx + 166, by + 12, 3, INK)
    cv.text("AFTER 10 YEARS OF TALKS, 98.5% OF TARIFFS GO.",
            bx + 166, by + 44, 2, INK)
    cv.text("THE PACT ENTERS FORCE IN EARLY 2027.",
            bx + 166, by + 62, 2, GREY)

    # Six-story grid.
    gy = 546
    gh = 144
    gap = 14
    cw3 = (CW - 2 * gap) // 3
    stories = [
        (pic_globe, ("CLIMATE", TEAL),
         "COP31 DEADLOCK ON FOSSIL FUELS",
         "ANTALYA TALKS STALL IN A ROW OVER OIL AND GAS."),
        (pic_quake, ("QUAKE", NAVY),
         "STRONG QUAKE SHAKES PERU",
         "QUAKE 6.7 HITS PERU. FELT IN LIMA. NO DEAD."),
        (pic_cuffs, ("ARREST", DARKRED),
         "'EL CHAPO ISIDRO' HELD",
         "MEXICO NABS FBI MOST-WANTED LORD."),
        (pic_laptop, ("CYBER", NAVY),
         "FBI PROBES DATABASE HACK",
         "AGENTS PROBE APPARENT BREACH OF NCIC DATABASE."),
        (pic_bridge, ("UKRAINE", DARKRED),
         "ZELENSKY: BRIDGE STRIKES FAIR",
         "KYIV DEFENDS HITS ON THE CRIMEAN BRIDGE AS FAIR."),
        (pic_ship, ("BALTIC", TEAL),
         "DRONES HIT RUSSIAN SHIP",
         "SHIP HIT IN BALTIC. FINLAND ON ALERT."),
    ]
    for i, (pic, tag, head, body) in enumerate(stories):
        cx = M + (i % 3) * (cw3 + gap)
        cy = gy + (i // 3) * (gh + gap)
        cell(cv, cx, cy, cw3, gh, pic, tag, head, body)

    # IN BRIEF.
    iy = 856
    cv.text("IN BRIEF", M, iy, 3, INK)
    cv.rect(M, iy + 28, CW, 3, INK)
    briefs = [
        "DENMARK: RUSSIA PLOT TO KILL RAPPER",
        "ANC FIGHTS TO KEEP S. AFRICA CITIES",
        "BOLSONARO IN ICU, BOWEL BLOCKAGE",
        "SINALOA: 11 KILLED AFTER CARTEL ARREST",
        "TRUMP SEEKS LASTING IRAN DEAL",
        "ADNOC SHIP HIT IN HORMUZ, 1 MISSING",
        "ESTONIA SHUTS BORDER WITH RUSSIA",
        "INDIA FACE NZ IN WELLINGTON TEST",
    ]
    for i, item in enumerate(briefs):
        col = i % 2
        row = i // 2
        ix = M + col * (CW // 2)
        byy = iy + 42 + row * 26
        cv.rect(ix, byy + 4, 8, 8, RED)
        cv.text(item, ix + 16, byy, 2, INK)

    # Footer.
    cv.center("FROM WIRE REPORTS - ALL EVENTS OF 22 NOVEMBER 2026",
              0, 998, W, 2, GREY)

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    n = write_png(cv, path)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("wrote %s (%d bytes) sha256=%s" % (path, n, h))


if __name__ == "__main__":
    main()
