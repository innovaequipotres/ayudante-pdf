"""Pruebas de integración con materiales reales, limpios y con problemas."""

from __future__ import annotations

from fastapi.testclient import TestClient

API_PREFIX = "/api/v1/sessions"

_PROBLEM_RULES = {"long_paragraph", "long_sentence", "no_headings"}


def _create_text_session(
    client: TestClient,
    text: str,
    title: str = "Material de prueba",
) -> dict:
    response = client.post(
        f"{API_PREFIX}/text",
        json={"title": title, "text": text},
    )
    assert response.status_code == 201
    return response.json()


def _create_pdf_session(client: TestClient, content: bytes) -> dict:
    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("material.pdf", content, "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def _extract(client: TestClient, session_id: str) -> dict:
    response = client.post(f"{API_PREFIX}/{session_id}/extract")
    assert response.status_code == 200
    return response.json()


def _analyze_without_ai(client: TestClient, session_id: str) -> dict:
    response = client.post(f"{API_PREFIX}/{session_id}/analyze?use_ai=false")
    assert response.status_code == 200
    return response.json()


def test_clean_text_flow_has_no_findings(
    client: TestClient,
    clean_text: str,
) -> None:
    session = _create_text_session(client, clean_text)
    extracted = _extract(client, session["session_id"])
    diagnosis = _analyze_without_ai(client, session["session_id"])

    assert extracted["page_count"] is None
    assert [block["type"] for block in extracted["blocks"]] == [
        "heading",
        "paragraph",
        "heading",
        "list",
        "paragraph",
    ]
    assert extracted["summary"]["word_count"] == 38
    assert diagnosis["score"] == 100
    assert diagnosis["level"] == "ok"
    assert diagnosis["observations"] == []
    assert diagnosis["ai_status"] == "skipped"

    stored = client.get(f"{API_PREFIX}/{session['session_id']}").json()
    assert stored["status"] == "analyzed"


def test_problem_text_flow_detects_expected_rules(
    client: TestClient,
    problem_text: str,
) -> None:
    session = _create_text_session(client, problem_text)
    extracted = _extract(client, session["session_id"])
    diagnosis = _analyze_without_ai(client, session["session_id"])

    assert extracted["summary"]["heading_count"] == 0
    assert extracted["summary"]["word_count"] > 150
    assert {item["rule_id"] for item in diagnosis["observations"]} == _PROBLEM_RULES
    assert {item["source"] for item in diagnosis["observations"]} == {"rule"}
    assert diagnosis["score"] == 82
    assert diagnosis["level"] == "barrier"
    assert any(item["severity"] == "high" for item in diagnosis["observations"])


def test_problem_text_score_is_deterministic(
    client: TestClient,
    problem_text: str,
) -> None:
    session = _create_text_session(client, problem_text)

    first = _analyze_without_ai(client, session["session_id"])
    second = _analyze_without_ai(client, session["session_id"])

    assert first["score"] == second["score"]
    assert first["level"] == second["level"]
    assert [item["id"] for item in first["observations"]] == [
        item["id"] for item in second["observations"]
    ]


def test_clean_pdf_flow_extracts_structure_and_scores_100(
    client: TestClient,
    clean_pdf: bytes,
) -> None:
    session = _create_pdf_session(client, clean_pdf)
    extracted = _extract(client, session["session_id"])
    diagnosis = _analyze_without_ai(client, session["session_id"])

    assert extracted["page_count"] == 1
    assert [block["type"] for block in extracted["blocks"]] == [
        "heading",
        "paragraph",
        "heading",
        "list",
        "paragraph",
    ]
    assert extracted["summary"]["heading_count"] == 2
    assert extracted["summary"]["list_count"] == 1
    assert extracted["summary"]["image_count"] == 0
    assert diagnosis["score"] == 100
    assert diagnosis["level"] == "ok"
    assert diagnosis["observations"] == []


def test_problem_pdf_flow_detects_text_rules(
    client: TestClient,
    problem_pdf: bytes,
) -> None:
    session = _create_pdf_session(client, problem_pdf)
    extracted = _extract(client, session["session_id"])
    diagnosis = _analyze_without_ai(client, session["session_id"])

    assert extracted["page_count"] == 1
    assert extracted["summary"]["heading_count"] == 0
    assert {item["rule_id"] for item in diagnosis["observations"]} == _PROBLEM_RULES
    assert diagnosis["score"] < 100
    assert diagnosis["level"] == "barrier"
    assert all(item["page"] == 1 for item in diagnosis["observations"])


def test_image_pdf_reports_missing_alt_text(
    client: TestClient,
    image_pdf: bytes,
) -> None:
    session = _create_pdf_session(client, image_pdf)
    extracted = _extract(client, session["session_id"])
    diagnosis = _analyze_without_ai(client, session["session_id"])

    assert extracted["summary"]["image_count"] == 1
    assert extracted["summary"]["images_without_alt"] == 1
    image_observations = [
        item
        for item in diagnosis["observations"]
        if item["rule_id"] == "image_without_alt"
    ]
    assert len(image_observations) == 1
    assert image_observations[0]["severity"] == "high"
    assert image_observations[0]["page"] == 1


def test_multipage_pdf_keeps_pages_and_blocks(
    client: TestClient,
    multipage_pdf: bytes,
) -> None:
    session = _create_pdf_session(client, multipage_pdf)
    extracted = _extract(client, session["session_id"])

    assert extracted["page_count"] == 3
    heading_pages = [
        block["page"]
        for block in extracted["blocks"]
        if block["type"] == "heading"
    ]
    assert heading_pages == [1, 2, 3]
    assert {
        block["page"] for block in extracted["blocks"] if block["page"] is not None
    } == {1, 2, 3}
