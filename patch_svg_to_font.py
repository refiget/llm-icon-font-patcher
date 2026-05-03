#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch an SVG icon into a TrueType/OpenType font at a specified PUA codepoint.

Requires: FontForge Python bindings (brew install fontforge)
"""

import argparse
import sys
from pathlib import Path

import fontforge


def patch_svg_to_font(
    font_path: str | Path,
    svg_path: str | Path,
    codepoint: int,
    output_path: str | Path,
    use_monospace_width: bool = True,
) -> None:
    """
    Import an SVG outline into a font glyph slot and generate a new font file.

    Args:
        font_path: Path to input font (.ttf or .otf)
        svg_path: Path to SVG file containing the icon
        codepoint: Integer Unicode codepoint (e.g. 0xE900)
        output_path: Path for the generated font file
        use_monospace_width: If True, forces the glyph advance width to match
                             the font's standard character width.
    """
    font = fontforge.open(str(font_path))

    # --- 1. Read font metrics ---
    em = font.em
    cap_height = getattr(font, "capHeight", em * 0.7)

    # Determine standard width from space (0x20), 'A' (0x41), or 'M' (0x4D)
    ref = None
    for cp in (0x20, 0x41, 0x4D):
        if cp in font:
            ref = font[cp]
            break
    std_width = ref.width if ref else em * 0.5

    # --- 2. Prepare glyph ---
    if codepoint in font:
        glyph = font[codepoint]
    else:
        glyph = font.createMappedChar(codepoint)

    glyph.clear()
    glyph.importOutlines(svg_path)
    glyph.correctDirection()

    # --- 3. Scale to match font proportions ---
    raw_bbox = glyph.boundingBox()
    raw_height = raw_bbox[3] - raw_bbox[1]
    if raw_height == 0:
        raise ValueError("SVG has no outlines or empty bounding box")

    # Target height: 95% of cap height (visually harmonious with uppercase letters)
    target_height = cap_height * 0.95
    scale = target_height / raw_height
    glyph.transform((scale, 0, 0, scale, 0, 0))

    # --- 4. Translate: align left to 0, sink baseline slightly ---
    new_bbox = glyph.boundingBox()
    tx = -new_bbox[0]
    # Sink bottom by ~2.5% of em (mimics Nerd Font icon baseline)
    ty = -new_bbox[1] - (em * 0.025)
    glyph.transform((1, 0, 0, 1, tx, ty))
    glyph.round()

    # --- 5. Set advance width ---
    if use_monospace_width:
        glyph.width = std_width
    else:
        # Use the glyph's actual width (for proportional fonts)
        # But ensure it's at least a reasonable minimum
        glyph.width = max(int(new_bbox[2] - new_bbox[0]), std_width // 2)

    # --- 6. Rename font to avoid conflicts ---
    base_ps_name = Path(output_path).stem.replace(" ", "-").replace("_", "-")
    font.fontname = base_ps_name
    font.fullname = base_ps_name.replace("-", " ")
    font.familyname = (font.familyname or "Font") + " Patched"

    # Update sfnt names
    new_sfnt = []
    for entry in font.sfnt_names:
        lang, name_id, value = entry
        if name_id == "Family":
            value = font.familyname
        elif name_id == "Fullname":
            value = font.fullname
        elif name_id == "PostScript":
            value = font.fontname
        new_sfnt.append((lang, name_id, value))
    font.sfnt_names = tuple(new_sfnt)

    # --- 7. Generate ---
    font.generate(str(output_path))
    font.close()

    final_bbox = glyph.boundingBox()
    print(f"✅ Generated: {output_path}")
    print(f"   Codepoint: {hex(codepoint)}")
    print(f"   Advance width: {glyph.width}")
    print(f"   Glyph bbox: {final_bbox}")
    print(f"   Target height: {target_height:.0f} (capHeight={cap_height:.0f}, em={em})")


def parse_codepoint(value: str) -> int:
    """Parse hex string like '0xE900' or 'E900' into int."""
    value = value.strip()
    if value.lower().startswith("0x"):
        return int(value, 16)
    elif value.lower().startswith("u+"):
        return int(value[2:], 16)
    else:
        # Try hex first, then decimal
        try:
            return int(value, 16)
        except ValueError:
            return int(value)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patch an SVG icon into a font at a given PUA codepoint."
    )
    parser.add_argument(
        "--font", "-f", required=True, help="Input font file (.ttf/.otf)"
    )
    parser.add_argument(
        "--svg", "-s", required=True, help="Input SVG icon file"
    )
    parser.add_argument(
        "--codepoint",
        "-c",
        required=True,
        help="Target Unicode codepoint (e.g. 0xE900, U+E900, or E900)",
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Output font file path"
    )
    parser.add_argument(
        "--proportional",
        "-p",
        action="store_true",
        help="Use proportional width instead of forcing monospace width",
    )

    args = parser.parse_args()

    try:
        cp = parse_codepoint(args.codepoint)
    except Exception as exc:
        print(
            f"Error parsing codepoint '{args.codepoint}': {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not (
        0xE000 <= cp <= 0xF8FF
        or 0xF0000 <= cp <= 0xFFFFD
        or 0x100000 <= cp <= 0x10FFFD
    ):
        print(
            f"Warning: codepoint {hex(cp)} is not in a Private Use Area (PUA). "
            "This may overwrite existing characters.",
            file=sys.stderr,
        )

    try:
        patch_svg_to_font(
            font_path=args.font,
            svg_path=args.svg,
            codepoint=cp,
            output_path=args.output,
            use_monospace_width=not args.proportional,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
