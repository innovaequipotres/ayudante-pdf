"""Verifica que la suite no pueda salir a internet."""

from __future__ import annotations

import socket

import pytest


def test_external_connection_is_blocked() -> None:
    with pytest.raises(AssertionError, match="llamada de red"):
        socket.create_connection(("example.com", 80), timeout=1)


def test_external_dns_lookup_is_blocked() -> None:
    with pytest.raises(AssertionError, match="llamada de red"):
        socket.getaddrinfo("example.com", 443)
