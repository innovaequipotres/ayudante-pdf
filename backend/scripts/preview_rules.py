"""Muestra las observaciones de las reglas automáticas.

Uso:
    .venv/bin/python scripts/preview_rules.py --pdf ruta/al/documento.pdf
    .venv/bin/python scripts/preview_rules.py --text "texto pegado"
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# Permite ejecutar el script desde backend/ sin instalar el paquete.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.exceptions import AppError
from app.processors.pdf_processor import extract_from_pdf
from app.processors.text_processor import extract_from_text
from app.scanner.rules import run_rules
from app.scanner.scoring import build_diagnosis
from app.schemas.content import ExtractedContent
from app.schemas.session import SessionResponse, SessionStatus, SourceType
from app.services.content_service import build_content


def _build_content(pdf: Path | None, text: str | None) -> ExtractedContent:
    """Extrae y enriquece el contenido como lo hace el servicio."""
    if pdf is not None:
        blocks, page_count = extract_from_pdf(pdf.read_bytes())
        source_type = SourceType.PDF
        filename = pdf.name
    else:
        blocks, page_count = extract_from_text(text or ""), None
        source_type = SourceType.TEXT
        filename = "Texto pegado"

    session = SessionResponse(
        session_id=uuid4(),
        source_type=source_type,
        filename=filename,
        status=SessionStatus.UPLOADED,
        created_at=datetime.now(UTC),
    )
    return build_content(session, blocks, page_count)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Muestra las observaciones de las reglas automáticas.",
    )
    parser.add_argument("--pdf", type=Path, help="Ruta del PDF a analizar.")
    parser.add_argument("--text", help="Texto pegado a analizar.")
    args = parser.parse_args()

    if (args.pdf is None) == (args.text is None):
        parser.error("Indicá --pdf o --text, pero no ambos.")

    try:
        content = _build_content(args.pdf, args.text)
    except AppError as exc:
        print(f"Error {exc.code} ({exc.status_code}): {exc.message}")
        return 1
    except OSError as exc:
        print(f"No se pudo leer el archivo: {exc}")
        return 1

    observations = run_rules(content)
    diagnosis = build_diagnosis(content.session_id, observations)
    print(
        f"Bloques: {len(content.blocks)} | "
        f"Palabras: {content.summary.word_count} | "
        f"Observaciones: {len(observations)}"
    )
    print(f"Puntaje: {diagnosis.score}/100 | Nivel: {diagnosis.level.value}")
    print("Categorías:")
    for result in diagnosis.categories:
        print(
            f"  - {result.category.value}: {result.severity.value} "
            f"(barreras: {result.barrier_count}, "
            f"revisar: {result.review_count}, "
            f"mejoras: {result.suggestion_count})"
        )
    print(f"\n{diagnosis.disclaimer}")

    for observation in observations:
        print(f"\n[{observation.severity.value}] {observation.title}")
        print(f"  Regla: {observation.rule_id}")
        print(
            f"  Ubicación: bloque {observation.block_id or '-'}, "
            f"página {observation.page or '-'}"
        )
        print(f"  Detalle: {observation.detail or '-'}")
        if observation.excerpt:
            print(f"  Extracto: {observation.excerpt}")
        print(f"  Por qué importa: {observation.why_it_matters}")
        print(f"  Recomendación: {observation.recommendation}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
