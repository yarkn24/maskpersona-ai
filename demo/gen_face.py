#!/usr/bin/env python3
"""
photo-to-ASCII face generator for MaskPersona AI demos.

Usage:
    python demo/gen_face.py <image_file> [--width 26] [--height 18] [--invert]

Outputs a Python list literal you can paste as a face in visual_demo.py.
Requires: pip install Pillow

Examples:
    python demo/gen_face.py photo.jpg
    python demo/gen_face.py photo.jpg --width 30 --height 20
    python demo/gen_face.py photo.jpg --invert        # for light-background images
"""
from __future__ import annotations

import argparse
import sys


def _load_image(source: str):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow not installed. Run: pip install Pillow")
    return Image.open(source)


def photo_to_ascii(
    source: str,
    width: int = 26,
    height: int = 18,
    invert: bool = False,
) -> list[str]:
    """Convert image to ASCII art at (width x height) characters.

    Terminal characters are ~2x taller than wide, so we double the
    intermediate height to preserve aspect ratio before final crop.
    """
    from PIL import Image

    img = _load_image(source)
    img = img.convert("L")  # grayscale

    # Step 1: resize to 2x height to correct for char aspect ratio
    img = img.resize((width, height * 2), Image.LANCZOS)
    # Step 2: subsample back to target height (every other row)
    img = img.resize((width, height), Image.LANCZOS)

    # Char ramp: index 0 = lightest (space), last = darkest (@)
    CHARS = " .'`,^\":;-~+=<>|()IltfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

    rows: list[str] = []
    for y in range(height):
        row = ""
        for x in range(width):
            brightness = img.getpixel((x, y))  # 0 (black) - 255 (white)
            if invert:
                idx = int(brightness / 255 * (len(CHARS) - 1))
            else:
                # Dark background: bright pixels -> dense chars (pop out of shadow)
                idx = int((255 - brightness) / 255 * (len(CHARS) - 1))
            row += CHARS[max(0, min(idx, len(CHARS) - 1))]
        rows.append(row)
    return rows


def _preview(rows: list[str]) -> None:
    print()
    border = "+" + "-" * len(rows[0]) + "+"
    print(border)
    for row in rows:
        print("|" + row + "|")
    print(border)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert photo to ASCII art face.")
    parser.add_argument("source", help="Image file path")
    parser.add_argument("--width", type=int, default=26)
    parser.add_argument("--height", type=int, default=18)
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert brightness (use for light-background photos)",
    )
    args = parser.parse_args()

    rows = photo_to_ascii(args.source, args.width, args.height, args.invert)

    _preview(rows)

    print("# Paste the FACE constant below into your demo script:\n")
    print("FACE = [")
    for row in rows:
        print(f'    {row!r},')
    print("]")


if __name__ == "__main__":
    main()
