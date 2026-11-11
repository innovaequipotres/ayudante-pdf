"""Reglas automáticas de accesibilidad sobre el contenido extraído."""

from app.scanner.rules import RULES, RULES_BY_CODE, Rule, run_rules, sort_observations

__all__ = [
    "RULES",
    "RULES_BY_CODE",
    "Rule",
    "run_rules",
    "sort_observations",
]
