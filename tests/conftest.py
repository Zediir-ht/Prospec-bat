import pytest

from prospec import dnscheck


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    """Tests sans réseau."""
    monkeypatch.setenv("NTFY_TOPIC", "")
    monkeypatch.setattr(dnscheck, "domain_status", lambda domain: "ok")
