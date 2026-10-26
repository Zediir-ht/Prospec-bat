import pytest

from prospec import dnscheck


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    """Tests sans réseau et sans montée en charge (testée à part)."""
    monkeypatch.setenv("RAMP_UP", "0")
    monkeypatch.setenv("NTFY_TOPIC", "")
    monkeypatch.setattr(dnscheck, "domain_status", lambda domain: "ok")
