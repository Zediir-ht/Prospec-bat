from datetime import date, timedelta
from email.message import EmailMessage

import pytest

from prospec import cli, db, dnscheck, inbox, mailer, notify, stats, web


@pytest.fixture
def con(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    return db.connect()


def add(con, siren, nom="X", status="sent", **kw):
    cols = {"siren": siren, "nom": nom, "email": f"c{siren}@x{siren}.fr", "email_source": "site", "status": status,
            "contacted_at": "2026-10-01T09:00:00", "message_ids": f"<m{siren}@gmail.com>", "subject": "Un site ?", **kw}
    con.execute(f"INSERT INTO companies({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", list(cols.values()))
    con.commit()


# ---------- 2. montée en charge
def test_ramp_up(con, monkeypatch):
    monkeypatch.setenv("RAMP_UP", "1")
    monkeypatch.setenv("DAILY_LIMIT", "10")
    assert cli.daily_quota(con) == 3 and "3 mails par jour" in cli.ramp_text(con)
    for days, expected in ((0, 3), (1, 3), (2, 4), (6, 6), (13, 9), (14, 10), (40, 10)):
        con.execute("DELETE FROM send_log")
        con.execute("INSERT INTO send_log VALUES (?, '1', 'first')", ((date.today() - timedelta(days=days)).isoformat() + "T09:00:00",))
        assert cli.daily_quota(con) == expected, days
    assert cli.ramp_text(con) == ""  # quota plein : plus de message
    monkeypatch.setenv("RAMP_UP", "0")
    con.execute("DELETE FROM send_log")
    assert cli.daily_quota(con) == 10


def test_quota_blocks_send_and_counts_followups(con, monkeypatch):
    monkeypatch.setenv("DAILY_LIMIT", "2")
    sent = []
    monkeypatch.setattr(mailer, "send", sent.append)
    for i in (1, 2, 3):
        add(con, str(i), status="drafted")
    rows = {r["siren"]: r for r in con.execute("SELECT * FROM companies").fetchall()}
    cli.send_now(con, rows["1"], "S", "B")
    cli.send_now(con, rows["2"], "S", "B")
    with pytest.raises(ValueError, match="Quota du jour atteint"):
        cli.send_now(con, rows["3"], "S", "B")
    assert len(sent) == 2 and db.sent_today(con) == 2


def test_send_log_backfilled_from_history(tmp_path):
    path = tmp_path / "old.db"
    c = db.connect(path)
    add(c, "1", status="replied")
    c.execute("DELETE FROM send_log")
    c.commit()
    c.close()
    assert db.first_send_date(db.connect(path)) == date(2026, 10, 1)


# ---------- 1. relances
def test_followup_in_same_thread(con, monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, "send", sent.append)
    add(con, "1")
    row = con.execute("SELECT * FROM companies").fetchone()
    subject, body = mailer.followup_mail(dict(row))
    assert subject == "Re : Un site ?"
    cli.send_followup_now(con, row, subject, body)
    msg = sent[0]
    assert msg["In-Reply-To"] == "<m1@gmail.com>" and msg["References"] == "<m1@gmail.com>"
    after = con.execute("SELECT status, followup_at, followup_body, message_ids FROM companies").fetchone()
    assert after["status"] == "followed_up" and after["followup_at"] and after["followup_body"] == body
    assert msg["Message-ID"] in after["message_ids"] and db.sent_today(con) == 1
    assert db.due_followups(con, 0) == []  # une seule relance par entreprise


def test_due_followups_exclude_replied_and_recent(con):
    add(con, "1")                                    # sans réponse, ancien -> à relancer
    add(con, "2", status="replied")
    add(con, "3", contacted_at=db.now())             # envoyé à l'instant
    assert [r["siren"] for r in db.due_followups(con, 7)] == ["1"]


def test_batch_followup_prompt_and_import(con):
    add(con, "1", body="Bonjour, voici ma proposition de maquette gratuite pour votre site.", metier="plomberie", commune="Rodez",
        site_status="none")
    row = dict(con.execute("SELECT * FROM companies").fetchone())
    prompt = mailer.batch_followup_prompt([row])
    assert "RELANCE" in prompt and "voici ma proposition" in prompt and "JSON" in prompt
    reply = '[{"siren": "1", "subject": "Re : Un site ?", "body": "Bonjour, je reviens vers vous pour la maquette gratuite. Pas de souci si ce n\'est pas le moment."}]'
    ok, errors = mailer.parse_batch(reply, {"1": "X"}, min_len=40)
    assert list(ok) == ["1"] and not errors
    assert mailer.parse_batch('[{"siren": "1", "subject": "S", "body": "à 99 € seulement pour la maquette gratuite et sans engagement"}]', {"1": "X"}, 40)[1]


# ---------- 3. vérification du domaine
def test_domain_status_with_fake_resolver(monkeypatch):
    import dns.resolver

    monkeypatch.undo()  # retire le faux domain_status de conftest
    dnscheck.domain_status.cache_clear()

    class Ans:
        def __init__(self, exchange): self.exchange = exchange

    class FakeResolver:
        lifetime = timeout = 0
        answers = {("ok.fr", "MX"): [Ans("mx.ok.fr.")], ("nullmx.fr", "MX"): [Ans(".")]}

        def resolve(self, domain, kind):
            if (domain, kind) in self.answers:
                return self.answers[(domain, kind)]
            if domain == "nxdomain.fr":
                raise dns.resolver.NXDOMAIN()
            if domain == "nomx.fr":
                if kind == "MX":
                    raise dns.resolver.NoAnswer()
                return [Ans("1.2.3.4")]
            if domain == "empty.fr":
                raise dns.resolver.NoAnswer()
            raise dns.resolver.LifetimeTimeout()

    monkeypatch.setattr(dns.resolver, "Resolver", FakeResolver)
    assert [dnscheck.domain_status(d) for d in ("ok.fr", "nullmx.fr", "nxdomain.fr", "nomx.fr", "empty.fr", "slow.fr")] == \
        ["ok", "invalid", "invalid", "ok", "invalid", "unknown"]
    assert dnscheck.email_ok("a@slow.fr") and not dnscheck.email_ok("a@nxdomain.fr")
    dnscheck.domain_status.cache_clear()


def test_invalid_domain_discarded_and_blocks_send(con, monkeypatch):
    monkeypatch.setattr(dnscheck, "domain_status", lambda d: "invalid" if d == "mort.fr" else "ok")
    con.execute("INSERT INTO companies(siren,nom,email,email_source,status) VALUES('1','A','a@mort.fr',NULL,'new')")
    con.commit()
    row = con.execute("SELECT * FROM companies").fetchone()
    res = {"site_url": None, "site_status": "none", "site_issues": "", "email": "a@mort.fr"}
    assert cli.apply_result(con, row, res) == "no_email"
    assert con.execute("SELECT email FROM companies").fetchone()[0] is None
    add(con, "2", status="drafted", email="b@mort.fr")
    with pytest.raises(ValueError, match="ne reçoit pas de courrier"):
        cli.send_now(con, con.execute("SELECT * FROM companies WHERE siren='2'").fetchone(), "S", "B")


# ---------- 6. notifications
def test_notify_channels(monkeypatch):
    import requests

    calls = []
    monkeypatch.setattr(notify.shutil, "which", lambda name: "/usr/bin/termux-notification")
    monkeypatch.setattr(notify.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    monkeypatch.setenv("NTFY_TOPIC", "prospec-secret")
    posted = []

    class R:
        def raise_for_status(self): pass

    monkeypatch.setattr(requests, "post", lambda url, **kw: posted.append((url, kw["json"])) or R())
    assert notify.notify("Réponse de Dupont", "Oui, ça m'intéresse") == ["termux", "ntfy"]
    assert calls[0][:3] == ["termux-notification", "--title", "Réponse de Dupont"]
    assert posted[0][1]["topic"] == "prospec-secret"
    monkeypatch.setenv("NTFY_TOPIC", "")
    monkeypatch.setattr(notify.shutil, "which", lambda name: None)
    assert notify.notify("t", "x") == []


def test_reply_triggers_notification(con, monkeypatch):
    got = []
    monkeypatch.setattr(inbox.notify, "notify", lambda title, text: got.append((title, text)))
    monkeypatch.setenv("SENDER_EMAIL", "corentin.mayrand@gmail.com")
    add(con, "1", nom="DUPONT", enseigne="Plomberie Dupont")
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = "c1@x1.fr", "corentin.mayrand@gmail.com", "Re: Un site ?"
    m.set_content("Oui, ça m'intéresse, appelez-moi.")
    assert inbox.process(con, m) == "replied"
    assert got == [("Réponse de Plomberie Dupont", "Oui, ça m'intéresse, appelez-moi.")]


# ---------- 7. statistiques
def test_stats(con):
    add(con, "1", status="replied", metier="plomberie", commune="Rodez", site_status="none", contacted_at="2026-10-19T09:00:00")  # lundi
    add(con, "2", metier="plomberie", commune="Rodez", site_status="outdated", site_issues="le site ne s'adapte pas aux téléphones; le site semble ancien (2019)",
        contacted_at="2026-10-19T09:00:00")
    add(con, "3", status="refused", metier="boulangerie", commune="Millau", site_status="none", contacted_at="2026-10-20T09:00:00")
    add(con, "4", status="bounced", metier="boulangerie", commune="Millau", site_status="none")
    add(con, "5", status="drafted", contacted_at=None)
    con.execute("UPDATE companies SET contacted_at=NULL WHERE siren='5'")
    d = stats.compute(con)
    assert d["total"] == {"sent": 3, "replied": 1, "stop": 1, "bounced": 1, "rate": 33}
    groups = dict(d["groups"])
    constat = {l["label"]: (l["sent"], l["replied"]) for l in groups["Constat sur le site"]}
    assert constat == {"Pas de site": (2, 1), "Pas adapté au mobile": (1, 0), "Site ancien": (1, 0)}
    metier = {l["label"]: l["rate"] for l in groups["Métier"]}
    assert metier == {"plomberie": 50, "boulangerie": 0}
    assert [l["label"] for l in groups["Jour d'envoi"]] == ["lundi", "mardi"]
    assert stats.compute(db.connect(":memory:"))["total"]["sent"] == 0


# ---------- 5. suivi, et pages
@pytest.fixture
def client(con):
    import os
    os.environ["DASHBOARD_PASSWORD"] = "pw"
    web.app.config["TESTING"] = True
    c = web.app.test_client()
    c.post("/login", data={"pw": "pw"})
    return c


def test_pipeline_flow(con, client):
    add(con, "1", nom="DUPONT", status="replied", reply_snippet="Oui, appelez-moi", reply_at="2026-10-22T10:00:00")
    page = client.get("/?tab=pipeline").data.decode()
    assert "DUPONT" in page and "À recontacter" in page and "Oui, appelez-moi" in page
    client.post("/pipeline/1", data={"stage": "mockup", "notes": "Maquette à envoyer lundi", "reminder": "2020-01-01"})
    row = con.execute("SELECT stage, notes, reminder FROM companies").fetchone()
    assert tuple(row) == ("mockup", "Maquette à envoyer lundi", "2020-01-01")
    assert "Rappel : 01/01" in client.get("/?tab=pipeline").data.decode()          # rappel échu en rouge
    assert len(web.pipeline_todo(con)) == 1
    client.post("/pipeline/1", data={"stage": "client", "notes": "ok", "reminder": "2020-01-01"})
    assert con.execute("SELECT stage, reminder FROM companies").fetchone()[0] == "client"
    assert con.execute("SELECT reminder FROM companies").fetchone()[0] is None and web.pipeline_todo(con) == []
    client.post("/pipeline/1", data={"stage": "keep", "reminder": "pas une date"})
    assert con.execute("SELECT reminder FROM companies").fetchone()[0] is None
    assert client.post("/pipeline/999", data={}).status_code == 404


def test_followup_tab_and_actions(con, client, monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, "send", sent.append)
    add(con, "1", nom="DUPONT")
    add(con, "2", nom="MARTIN")
    page = client.get("/?tab=followups").data.decode()
    assert "2 à relancer" in page and "Re : Un site ?" in page and "maquette gratuite" in page
    client.post("/followup/1", data={"act": "send", "subject": "Re : Un site ?", "body": "Bonjour, petit rappel sur la maquette gratuite."})
    assert sent[0]["In-Reply-To"] == "<m1@gmail.com>" and "petit rappel" in sent[0].get_content()
    client.post("/followup/2", data={"act": "skip"})
    assert client.get("/?tab=followups").data.decode().count("Aucune relance à faire") == 1
    assert client.post("/followup/1", data={"act": "send"}).status_code == 404       # déjà relancée
    add(con, "3", nom="BRU")
    reply = '[{"siren": "3", "subject": "Re : Un site ?", "body": "Bonjour, je reviens vers vous au sujet de la maquette gratuite. Aucun souci si ce n\'est pas le moment."}]'
    client.post("/followups/import", data={"text": reply})
    assert "je reviens vers vous au sujet" in client.get("/?tab=followups").data.decode()


def test_stats_and_quota_pages(con, client, monkeypatch):
    monkeypatch.setenv("RAMP_UP", "1")
    add(con, "1", status="replied", metier="plomberie", commune="Rodez", site_status="none",
        contacted_at=date.today().isoformat() + "T09:00:00")  # premier envoi aujourd'hui : on est encore en montée en charge
    page = client.get("/?tab=stats").data.decode()
    assert "Taux de réponse" in page and "Pas de site" in page and "plomberie" in page
    assert "Montée en charge" in client.get("/").data.decode()


def test_single_send_shows_reason_when_quota_reached(con, client, monkeypatch):
    monkeypatch.setenv("DAILY_LIMIT", "1")
    monkeypatch.setattr(mailer, "send", lambda m: None)
    add(con, "1", status="drafted", body="x")
    add(con, "2", status="drafted", body="x")
    client.post("/draft/1", data={"act": "send", "subject": "S", "body": "B"})
    r = client.post("/draft/2", data={"act": "send", "subject": "S", "body": "B"}, follow_redirects=True)
    assert "Quota du jour atteint" in r.data.decode()
