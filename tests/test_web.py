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
    assert b"DUPONT" not in client.get("/?tab=drafts").data


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
