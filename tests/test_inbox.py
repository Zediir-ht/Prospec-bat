from email.message import EmailMessage

import pytest

from prospec import cli, db, inbox, mailer


@pytest.fixture
def con(tmp_path, monkeypatch):
    monkeypatch.setenv("SENDER_EMAIL", "corentin.mayrand@gmail.com")
    con = db.connect(tmp_path / "t.db")
    con.execute("INSERT INTO companies(siren,nom,email,email_source,status,contacted_at,message_ids) "
                "VALUES('1','DUPONT','contact@dupont.fr','site','sent','2026-10-20T09:00:00','<abc@gmail.com>')")
    con.execute("INSERT INTO companies(siren,nom,email,email_source,status,contacted_at) "
                "VALUES('2','MARTIN','info@martin-pain.fr','site','sent','2026-10-20T09:00:00')")
    con.commit()
    return con


def msg(frm, body, subject="Re: Un site ?", **headers):
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = frm, "corentin.mayrand@gmail.com", subject
    for k, v in headers.items():
        m[k.replace("_", "-")] = v
    m.set_content(body)
    return m


def status(con, siren):
    return con.execute("SELECT status FROM companies WHERE siren=?", (siren,)).fetchone()[0]


def test_reply_matched_by_thread_from_other_address(con):
    m = msg("Jean Dupont <jean.dupont@orange.fr>", "Bonjour, oui ça m'intéresse, appelez-moi.\n\nLe 20 oct. 2026, Corentin a écrit :\n> Bonjour STOP",
            In_Reply_To="<abc@gmail.com>")
    assert inbox.process(con, m) == "replied"
    row = con.execute("SELECT status, reply_snippet FROM companies WHERE siren='1'").fetchone()
    assert row[0] == "replied" and row[1].startswith("Bonjour, oui") and "STOP" not in row[1]  # la citation est ignorée


def test_reply_matched_by_address_and_domain(con):
    assert inbox.process(con, msg("info@martin-pain.fr", "Merci, je regarde.")) == "replied"
    con.execute("UPDATE companies SET status='sent' WHERE siren='2'")
    assert inbox.process(con, msg("patron@martin-pain.fr", "Bonjour, combien de temps ?")) == "replied"


def test_stop_suppresses(con):
    assert inbox.process(con, msg("contact@dupont.fr", "STOP merci")) == "stop"
    assert status(con, "1") == "refused" and db.is_suppressed(con, "contact@dupont.fr")
    con.execute("UPDATE companies SET status='sent' WHERE siren='2'")
    assert inbox.process(con, msg("info@martin-pain.fr", "Nous ne sommes pas intéressés.")) == "stop"


def test_bounce_marks_address_invalid(con):
    m = msg("Mail Delivery Subsystem <mailer-daemon@googlemail.com>",
            "Adresse introuvable. Votre message n'a pas été distribué à info@martin-pain.fr", subject="Delivery Status Notification (Failure)")
    m["X-Failed-Recipients"] = "info@martin-pain.fr"
    assert inbox.process(con, m) == "bounced"
    assert status(con, "2") == "bounced" and db.is_suppressed(con, "info@martin-pain.fr")


def test_ignores_auto_replies_unknown_and_own(con):
    assert inbox.process(con, msg("contact@dupont.fr", "Je suis absent", subject="Réponse automatique : absence")) is None
    assert inbox.process(con, msg("contact@dupont.fr", "x", Auto_Submitted="auto-replied")) is None
    assert inbox.process(con, msg("inconnu@ailleurs.fr", "Bonjour")) is None
    assert inbox.process(con, msg("corentin.mayrand@gmail.com", "copie")) is None
    assert status(con, "1") == "sent"


def test_no_followup_after_reply(con):
    inbox.process(con, msg("contact@dupont.fr", "Oui !"))
    assert [r["siren"] for r in db.due_followups(con, 0)] == ["2"]


def test_imap_date_is_english():
    from datetime import date
    assert inbox.imap_date(date(2026, 8, 3)) == "03-Aug-2026"


def test_send_now_remembers_message_id(con, monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, "send", sent.append)
    con.execute("INSERT INTO companies(siren,nom,email,email_source,status) VALUES('3','X','a@x.fr','site','drafted')")
    row = con.execute("SELECT * FROM companies WHERE siren='3'").fetchone()
    cli.send_now(con, row, "Objet", "Corps")
    mid = con.execute("SELECT message_ids, status FROM companies WHERE siren='3'").fetchone()
    assert mid[0] == sent[0]["Message-ID"] and mid[1] == "sent"
    reply = msg("autre@gmail.com", "Bonjour, d'accord", In_Reply_To=sent[0]["Message-ID"])
    assert inbox.process(con, reply) == "replied" and status(con, "3") == "replied"
