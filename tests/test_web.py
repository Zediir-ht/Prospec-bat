import pytest

from prospec import config, db, web


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setenv("DASHBOARD_PASSWORD", "secret")
    monkeypatch.setenv("CRON_TOKEN", "tok")
    web.app.config["TESTING"] = True
    con = db.connect(tmp_path / "t.db")
    con.execute("INSERT INTO companies(siren,nom,commune,metier,email,status,site_status,subject,body,contacted_at) "
                "VALUES('1','DUPONT','Rodez','plomberie','a@dupont.fr','drafted','none','Un site ?','Bonjour','2026-01-01')")
    con.commit()
    return web.app.test_client()


def login(c):
    return c.post("/login", data={"pw": "secret"})


def test_requires_login(client):
    assert client.get("/").status_code == 302
    assert login(client).status_code == 302
    assert client.get("/").status_code == 200


def test_wrong_password(client):
    assert b"incorrect" in client.post("/login", data={"pw": "x"}).data


def test_drafts_and_skip(client):
    login(client)
    assert b"DUPONT" in client.get("/?tab=drafts").data
    client.post("/draft/1", data={"act": "skip"})
    page = client.get("/?tab=drafts").data.decode()
    assert 'data-siren="1"' not in page and "DUPONT ignorée." in page  # carte retirée, notification affichée


def test_send_calls_mailer(client, monkeypatch):
    sent = []
    monkeypatch.setattr(web.mailer, "send", lambda m: sent.append(m))
    login(client)
    client.post("/draft/1", data={"act": "send", "subject": "S", "body": "B"})
    assert len(sent) == 1 and sent[0]["To"] == "a@dupont.fr"
    assert b"DUPONT" in client.get("/?tab=sent").data


def test_suppressed_not_sent(client, monkeypatch):
    monkeypatch.setattr(web.mailer, "send", lambda m: pytest.fail("envoi interdit"))
    login(client)
    client.post("/stop", data={"email": "a@dupont.fr"})
    assert client.post("/draft/1", data={"act": "send"}).status_code == 404  # statut passé à refused


def test_cron_token(client, monkeypatch):
    monkeypatch.setattr(web, "start_job", lambda: True)
    assert client.get("/cron/bad").status_code == 404
    assert client.get("/cron/tok").json == {"started": True}


def test_write_tab_and_import(client):
    con = db.connect()
    con.execute("INSERT INTO companies(siren,nom,commune,code_postal,metier,email,status,site_status) "
                "VALUES('2','MARTIN','Millau','12100','boulangerie','m@martin-pain.fr','qualified','none')")
    con.commit()
    login(client)
    page = client.get("/?tab=write").data
    assert b"MARTIN" in page and b"Copier la demande" in page
    reply = ('[{"siren": "2", "subject": "Un site pour Martin ?", "body": "Bonjour,\\n\\nEn cherchant boulangerie Millau, '
             'je n\'ai pas trouv\u00e9 votre site. Je peux pr\u00e9parer une maquette gratuite, sans engagement. Cela vous int\u00e9resse ?"}]')
    r = client.post("/import", data={"text": reply})
    assert r.status_code == 302
    assert b"Un site pour Martin" in client.get("/?tab=drafts").data


def test_send_all(client, monkeypatch):
    sent = []
    monkeypatch.setattr(web.mailer, "send", sent.append)
    monkeypatch.setenv("SEND_SPACING", "0,0")
    con = db.connect()
    con.execute("UPDATE companies SET email_source='site'")
    con.execute("INSERT INTO companies(siren,nom,commune,email,email_source,status,site_status,subject,body,contacted_at) "
                "VALUES('5','BRU','Rodez','b@bru.fr','site','drafted','none','S2','B2','2026-01-02')")
    con.commit()
    login(client)
    page = client.get("/?tab=drafts").data.decode()
    assert "Tout envoyer (2)" in page
    web._job["running"] = True  # une collecte en cours ne doit pas bloquer l'envoi
    assert "Tout envoyer (2)" in client.get("/?tab=drafts").data.decode()
    monkeypatch.setattr(web, "start_send", lambda: web._send.update(running=True) or web._run_send_all() or True)
    client.post("/send-all", data={"subject_5": "Objet modifié", "body_5": "Corps modifié"})
    web._job["running"] = False
    assert sorted(m["To"] for m in sent) == ["a@dupont.fr", "b@bru.fr"]
    assert any(m["Subject"] == "Objet modifié" for m in sent)
    assert web._send["log"] == "2 mail(s) envoyé(s)." and not web._send["running"]
    assert "2 mail(s) envoyé(s)." in client.get("/?tab=drafts").data.decode()


def test_send_all_has_no_quota(client, monkeypatch):
    sent = []
    monkeypatch.setattr(web.mailer, "send", sent.append)
    monkeypatch.setenv("SEND_SPACING", "0,0")
    monkeypatch.setenv("DAILY_LIMIT", "1")  # objectif de lot seulement
    con = db.connect()
    con.execute("UPDATE companies SET email_source='site'")
    for i in (6, 7, 8):
        con.execute("INSERT INTO companies(siren,nom,email,email_source,status,contacted_at,subject,body) VALUES(?,?,?,?,?,?,?,?)",
                    (str(i), f"N{i}", f"a{i}@a{i}.fr", "site", "drafted", "2026-01-03", "Objet", "Corps du mail"))
    con.commit()
    login(client)
    assert "Tout envoyer (4)" in client.get("/?tab=drafts").data.decode()
    web._run_send_all()
    assert len(sent) == 4 and web._send["log"] == "4 mail(s) envoyé(s)."


def test_inbox_button(client, monkeypatch):
    monkeypatch.setattr(web.inbox, "check", lambda con: {"replied": 2, "stop": 1, "bounced": 0})
    login(client)
    client.post("/inbox")
    assert "2 réponse(s), 1 désinscription(s)" in client.get("/?tab=sent").data.decode()
