from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

DEFAULT_SIZES = (16, 24, 32, 48, 64, 128, 256)
DEFAULT_SVG = Path("resources/icons/flowchem_app_icon.svg")
DEFAULT_ICO = Path("resources/icons/flowchem_app_icon.ico")


def render_svg_to_png_bytes(renderer: QSvgRenderer, size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()

    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(data)


def write_ico(path: Path, images: list[tuple[int, bytes]]) -> None:
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries = []
    payload = []

    for size, png in images:
        width = 0 if size == 256 else size
        height = 0 if size == 256 else size
        entries.append(
            struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, len(png), offset)
        )
        payload.append(png)
        offset += len(png)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + b"".join(entries) + b"".join(payload))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a multi-size Windows .ico from the FlowChem app SVG."
    )
    parser.add_argument("--svg", type=Path, default=DEFAULT_SVG)
    parser.add_argument("--ico", type=Path, default=DEFAULT_ICO)
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=DEFAULT_SIZES,
        help="Icon sizes to embed, in pixels.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = QGuiApplication.instance() or QGuiApplication([])

    renderer = QSvgRenderer(str(args.svg))
    if not renderer.isValid():
        print(f"Invalid SVG: {args.svg}", file=sys.stderr)
        return 1

    images = [
        (size, render_svg_to_png_bytes(renderer, size))
        for size in sorted(set(args.sizes))
    ]
    write_ico(args.ico, images)
    app.quit()

    sizes = ", ".join(str(size) for size, _ in images)
    print(f"Wrote {args.ico} with sizes: {sizes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
