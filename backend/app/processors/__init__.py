"""Procesadores de contenido de los materiales educativos."""

from app.processors.pdf_processor import BULLET_RE, extract_from_pdf

__all__ = ["BULLET_RE", "extract_from_pdf"]
