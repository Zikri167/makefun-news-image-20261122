"""Entry point: draw the 22 November 2026 broadsheet and write it out.

Runs with the standard library only, no network. Writes one PNG to
$MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png) and is byte-for-byte
deterministic across runs.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from draw import build_image

OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
OUT_PATH = os.path.join(OUT_DIR, "entry.png")


def main():
    data = build_image()
    if len(data) > 1048576:
        raise SystemExit("entry.png exceeds 1 MiB: %d bytes" % len(data))
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (OUT_PATH, len(data)))


if __name__ == "__main__":
    main()
