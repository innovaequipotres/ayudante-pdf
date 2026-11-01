"""Inspecciona los bloques detectados por el procesador de PDFs.

Uso:
    .venv/bin/python scripts/inspect_pdf.py ruta/al/documento.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite ejecutar el script desde backend/ sin instalar el paquete.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.exceptions import AppError
from app.processors.pdf_processor import extract_from_pdf
from app.schemas.content import BlockType, ContentBlock


def _format_block(index: int, block: ContentBlock) -> str:
    prefix = f"{index:03d}. [p.{block.page}]"
    if block.type == BlockType.HEADING:
        return f"{prefix} H{block.level}: {block.text}"
    if block.type == BlockType.PARAGRAPH:
        return f"{prefix} P: {block.text}"
    if block.type == BlockType.LIST:
        items = "\n".join(f"      - {item}" for item in (block.items or []))
        return f"{prefix} LISTA:\n{items}"
    return f"{prefix} IMAGEN: {block.width} x {block.height} pt"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Muestra los bloques detectados en un PDF.",
    )
    parser.add_argument("pdf", type=Path, help="Ruta del PDF a inspeccionar.")
    args = parser.parse_args()

    try:
        content = args.pdf.read_bytes()
    except OSError as exc:
        print(f"No se pudo leer el archivo: {exc}")
        return 1

    try:
        blocks, page_count = extract_from_pdf(content)
    except AppError as exc:
        print(f"Error {exc.code} ({exc.status_code}): {exc.message}")
        return 1

    try:
        print(f"Páginas: {page_count}")
        print(f"Bloques: {len(blocks)}")
        for index, block in enumerate(blocks, start=1):
            print(_format_block(index, block))
    except BrokenPipeError:
        # Permite usar el script con `head`, `less`, etc.
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
