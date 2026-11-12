"""Ejecuta las reglas y el análisis con IA sobre un PDF.

Uso:
    .venv/bin/python scripts/try_ai_analysis.py --pdf ruta/al/documento.pdf
    .venv/bin/python scripts/try_ai_analysis.py --pdf documento.pdf \
        --provider openrouter --max-chars 300

El proveedor se toma de ``AI_PROVIDER`` (gemini por defecto); ``--provider``
lo pisa solo para esta ejecución. Nunca imprime claves.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# Permite ejecutar el script desde backend/ sin instalar el paquete.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _build_content(pdf: Path):  # type: ignore[no-untyped-def]
    """Extrae y enriquece el contenido como lo hace el servicio."""
    from app.processors.pdf_processor import extract_from_pdf
    from app.schemas.session import SessionResponse, SessionStatus, SourceType
    from app.services.content_service import build_content

    blocks, page_count = extract_from_pdf(pdf.read_bytes())
    session = SessionResponse(
        session_id=uuid4(),
        source_type=SourceType.PDF,
        filename=pdf.name,
        status=SessionStatus.UPLOADED,
        created_at=datetime.now(UTC),
    )
    return build_content(session, blocks, page_count)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Muestra el diagnóstico por reglas y el análisis con IA.",
    )
    parser.add_argument("--pdf", type=Path, required=True, help="PDF a analizar.")
    parser.add_argument(
        "--provider",
        choices=("gemini", "openrouter"),
        default=None,
        help="Pisa AI_PROVIDER para esta ejecución.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=None,
        help="Tope de caracteres enviados a la IA.",
    )
    args = parser.parse_args()

    # Debe definirse antes de importar la configuración de la app.
    if args.provider is not None:
        os.environ["AI_PROVIDER"] = args.provider

    from app.core.exceptions import AppError
    from app.scanner.ai_analysis import analyze_with_ai
    from app.scanner.rules import run_rules

    try:
        content = _build_content(args.pdf)
    except AppError as exc:
        print(f"Error {exc.code} ({exc.status_code}): {exc.message}")
        return 1
    except OSError as exc:
        print(f"No se pudo leer el archivo: {exc}")
        return 1

    observations = run_rules(content)
    result = analyze_with_ai(content.blocks, max_chars=args.max_chars)

    print(f"Material: {content.title or args.pdf.name}")
    print(
        f"Bloques: {len(content.blocks)} | "
        f"Palabras: {content.summary.word_count}"
    )
    print(f"ai_status: {result.status.value}")
    print(f"ai_notice: {result.notice}")
    print(f"truncated: {str(result.truncated).lower()}")
    print(
        f"Observaciones: {len(observations)} por reglas | "
        f"{len(result.observations)} por IA"
    )

    for observation in observations + result.observations:
        print(f"\n[{observation.severity.value}] {observation.title}")
        print(f"  id: {observation.id}")
        print(f"  source: {observation.source.value}")
        print(f"  severity: {observation.severity.value}")
        print(f"  block_id: {observation.block_id or '-'}")
        print(f"  excerpt: {observation.excerpt or '-'}")
        print(f"  detail: {observation.detail or '-'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
