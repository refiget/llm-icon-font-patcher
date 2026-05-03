#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch patch all SVG icons in ./icons into all TTF fonts in ./font.

Outputs patched fonts into ./out, creating it if needed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

try:
    import fontforge
except ImportError as exc:  # pragma: no cover - runtime dependency
    fontforge = None  # type: ignore[assignment]
    _FONTFORGE_IMPORT_ERROR = exc
else:
    _FONTFORGE_IMPORT_ERROR = None


def parse_codepoint(value: str) -> int:
    """Parse hex string like '0xE900', 'U+E900', or decimal text."""
    value = value.strip()
    if value.lower().startswith("0x"):
        return int(value, 16)
    if value.lower().startswith("u+"):
        return int(value[2:], 16)
    try:
        return int(value, 16)
    except ValueError:
        return int(value)


def iter_files(directory: Path, suffix: str) -> list[Path]:
    return sorted(
        path for path in directory.iterdir() if path.is_file() and path.suffix.lower() == suffix
    )


def resolve_standard_width(font) -> int:
    """Get a reasonable advance width from the font itself."""
    em = font.em
    for cp in (0x20, 0x41, 0x4D):
        if cp in font:
            return int(font[cp].width)
    return int(em * 0.5)


def patch_single_glyph(font, svg_path: Path, codepoint: int, *, use_monospace_width: bool) -> None:
    """Import one SVG icon into an already opened font."""
    em = font.em
    cap_height = getattr(font, "capHeight", em * 0.7)
    std_width = resolve_standard_width(font)

    if codepoint in font:
        glyph = font[codepoint]
    else:
        glyph = font.createMappedChar(codepoint)

    glyph.clear()
    glyph.importOutlines(str(svg_path))
    glyph.correctDirection()

    raw_bbox = glyph.boundingBox()
    raw_height = raw_bbox[3] - raw_bbox[1]
    if raw_height == 0:
        raise ValueError(f"SVG has no outlines or empty bounding box: {svg_path}")

    target_height = cap_height * 0.95
    scale = target_height / raw_height
    glyph.transform((scale, 0, 0, scale, 0, 0))

    new_bbox = glyph.boundingBox()
    tx = -new_bbox[0]
    ty = -new_bbox[1] - (em * 0.025)
    glyph.transform((1, 0, 0, 1, tx, ty))
    glyph.round()

    if use_monospace_width:
        glyph.width = std_width
    else:
        glyph.width = max(int(new_bbox[2] - new_bbox[0]), std_width // 2)


def rename_font(font, output_path: Path) -> None:
    """Rename font metadata so generated files do not collide with the source."""
    base_ps_name = (
        output_path.stem.replace(" ", "-").replace("_", "-")
    )
    font.fontname = base_ps_name
    font.fullname = base_ps_name.replace("-", " ")
    font.familyname = (font.familyname or "Font") + " Patched"

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


def patch_font_with_icons(
    font_path: Path,
    svg_paths: Iterable[Path],
    start_codepoint: int,
    output_path: Path,
    *,
    use_monospace_width: bool = True,
) -> None:
    """Patch all icons into a single font and generate one output file."""
    if fontforge is None:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            "fontforge Python bindings are not installed. "
            f"Original import error: {_FONTFORGE_IMPORT_ERROR}"
        )

    font = fontforge.open(str(font_path))
    try:
        for offset, svg_path in enumerate(svg_paths):
            codepoint = start_codepoint + offset
            patch_single_glyph(
                font,
                svg_path,
                codepoint,
                use_monospace_width=use_monospace_width,
            )

        rename_font(font, output_path)
        font.generate(str(output_path))
    finally:
        font.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patch all SVG icons in ./icons into all .ttf fonts in ./font."
    )
    parser.add_argument(
        "--font-dir",
        default="font",
        help="Directory containing source .ttf fonts (default: ./font)",
    )
    parser.add_argument(
        "--icon-dir",
        default="icons",
        help="Directory containing SVG icons (default: ./icons)",
    )
    parser.add_argument(
        "--out-dir",
        default="out",
        help="Directory for generated fonts (default: ./out)",
    )
    parser.add_argument(
        "--start-codepoint",
        default="0xE900",
        help="First PUA codepoint used for the first icon (default: 0xE900)",
    )
    parser.add_argument(
        "--proportional",
        action="store_true",
        help="Use proportional width instead of forcing monospace width",
    )

    args = parser.parse_args()

    try:
        start_codepoint = parse_codepoint(args.start_codepoint)
    except Exception as exc:
        print(f"Error parsing --start-codepoint: {exc}", file=sys.stderr)
        sys.exit(1)

    font_dir = Path(args.font_dir)
    icon_dir = Path(args.icon_dir)
    out_dir = Path(args.out_dir)

    if not font_dir.is_dir():
        print(f"Error: font directory not found: {font_dir}", file=sys.stderr)
        sys.exit(1)
    if not icon_dir.is_dir():
        print(f"Error: icon directory not found: {icon_dir}", file=sys.stderr)
        sys.exit(1)

    ttf_files = iter_files(font_dir, ".ttf")
    svg_files = iter_files(icon_dir, ".svg")

    if not ttf_files:
        print(f"Error: no .ttf files found in {font_dir}", file=sys.stderr)
        sys.exit(1)
    if not svg_files:
        print(f"Error: no .svg files found in {icon_dir}", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    end_codepoint = start_codepoint + len(svg_files) - 1
    if not (0xE000 <= start_codepoint <= 0x10FFFD and 0xE000 <= end_codepoint <= 0x10FFFD):
        print(
            f"Warning: icon codepoints span {hex(start_codepoint)} to {hex(end_codepoint)}, "
            "which is outside the usual Private Use Area range.",
            file=sys.stderr,
        )

    print(f"Fonts: {len(ttf_files)}")
    print(f"Icons: {len(svg_files)}")
    print(f"Codepoints: {hex(start_codepoint)} - {hex(end_codepoint)}")
    print(f"Output dir: {out_dir}")

    for font_path in ttf_files:
        output_path = out_dir / f"{font_path.stem}-patched{font_path.suffix}"
        print(f"Patching {font_path.name} -> {output_path}")
        try:
            patch_font_with_icons(
                font_path=font_path,
                svg_paths=svg_files,
                start_codepoint=start_codepoint,
                output_path=output_path,
                use_monospace_width=not args.proportional,
            )
        except Exception as exc:
            print(f"Error patching {font_path}: {exc}", file=sys.stderr)
            sys.exit(1)

        print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
