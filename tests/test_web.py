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
    con.execute("INSERT INTO companies(siren,nom,commune,metier,email,email_source,status,site_status,subject,body,contacted_at) "
                "VALUES('1','DUPONT','Rodez','plomberie','a@dupont.fr','site','drafted','none','Un site ?','Bonjour','2026-01-01')")
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
    con.execute("INSERT INTO companies(siren,nom,commune,code_postal,metier,email,email_source,status,site_status) "
                "VALUES('2','MARTIN','Millau','12100','boulangerie','m@martin-pain.fr','site','qualified','none')")
    con.commit()
    login(client)
    page = client.get("/?tab=write").data
    assert b"MARTIN" in page and b"Copier toutes les demandes (1)" in page
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


def test_status_endpoint_and_pagination(client):
    login(client)
    assert client.get("/status").json == {"job": {"running": False, "log": ""}, "send": {"running": False, "log": web._send["log"]}}
    con = db.connect()
    for i in range(40):
        con.execute("INSERT INTO companies(siren,nom,email,email_source,status,subject,body,contacted_at) VALUES(?,?,?,?,?,?,?,?)",
                    (f"9{i}", f"N{i}", f"a{i}@b{i}.fr", "site", "drafted", "S", "B", "2026-01-02"))
    con.commit()
    page = client.get("/?tab=drafts").data.decode()
    assert "41 mails prêts" in page and "Tout envoyer (41)" in page
    assert page.count('class="swipe"') == 30 and "Afficher 11 de plus" in page
    assert client.get("/?tab=drafts&n=60").data.decode().count('class="swipe"') == 41
    assert client.get("/?tab=drafts&n=abc").status_code == 200


def test_company_names_are_escaped(client):
    con = db.connect()
    con.execute("UPDATE companies SET nom='<script>alert(1)</script>', subject='<b>x</b>' WHERE siren='1'")
    con.commit()
    login(client)
    page = client.get("/?tab=drafts").data.decode()
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_write_has_no_limit_and_big_import(client):
    import json
    con = db.connect()
    for i in range(150):
        con.execute("INSERT INTO companies(siren,nom,commune,code_postal,metier,email,email_source,status,site_status) "
                    "VALUES(?,?,?,?,?,?,?,?,?)", (f"5{i:03d}", f"ENTREPRISE {i}", "Rodez", "12000", "boulangerie", f"c{i}@e{i}.fr", "site", "qualified", "none"))
    con.commit()
    login(client)
    page = client.get("/?tab=write").data.decode()
    assert "150 entreprises prêtes" in page and "Copier toutes les demandes (150)" in page and "Au-delà d'environ 40" in page
    data = json.loads(page.split('id="pdata">')[1].split("</script>")[0].replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u0026", "&").replace("\\u0027", "'"))
    assert len(data["companies"]) == 150 and "exactement un élément par entreprise" in data["intro"]
    reply = json.dumps([{"siren": f"5{i:03d}", "subject": f"Un site pour E{i} ?",
                         "body": "Bonjour,\n\nEn cherchant boulangerie Rodez, je n'ai pas trouvé votre site. Je peux préparer une maquette gratuite, sans engagement. Cela vous intéresse ?" + " Merci." * 600}
                        for i in range(150)], ensure_ascii=False)
    assert len(reply) > 500_000                                   # au-dessus de l'ancienne limite de formulaire
    assert client.post("/import", data={"text": reply}).status_code == 302
    assert con.execute("SELECT COUNT(*) FROM companies WHERE status='drafted' AND siren LIKE '5%'").fetchone()[0] == 150
    assert "0 entreprise" in client.get("/?tab=write").data.decode()


def test_followup_prompt_contains_all_due_not_just_page(client):
    con = db.connect()
    for i in range(45):
        con.execute("INSERT INTO companies(siren,nom,email,email_source,status,contacted_at,message_ids,subject,body) VALUES(?,?,?,?,?,?,?,?,?)",
                    (f"7{i:03d}", f"R{i}", f"r{i}@x{i}.fr", "site", "sent", "2026-01-01T09:00:00", f"<m{i}@g>", "Un site ?", "Bonjour, ma proposition."))
    con.commit()
    login(client)
    page = client.get("/?tab=followups").data.decode()
    assert page.count('class="swipe"') == 30                      # affichage par pages
    prompt = page.split('id="fprompt" readonly hidden>')[1].split("</textarea>")[0]
    assert all(f"R{i}" in prompt for i in range(45))               # mais la demande à Claude contient toutes les relances


def test_home_tiles_link_to_pages(client):
    login(client)
    html = client.get("/").get_data(as_text=True)
    for tab in ("stock", "drafts", "replies", "refused"):
        assert f"tab={tab}" in html


def test_list_pages(client):
    login(client)
    con = db.connect(db.DB_PATH)
    con.execute("INSERT INTO companies(siren,nom,commune,metier,email,email_source,status,site_status) "
                "VALUES('2','MARTIN','Millau','maçonnerie','m@martin.fr','osm','qualified','none')")
    con.execute("INSERT INTO companies(siren,nom,commune,email,status,reply_snippet,reply_at) "
                "VALUES('3','DURAND','Albi','d@durand.fr','replied','Intéressé','2026-02-01')")
    con.execute("INSERT INTO companies(siren,nom,commune,email,status) VALUES('4','LEROY','Foix','l@leroy.fr','refused')")
    con.commit()
    stock = client.get("/?tab=stock").get_data(as_text=True)
    assert "MARTIN" in stock and "m@martin.fr" in stock and "OpenStreetMap" in stock
    assert "Intéressé" in client.get("/?tab=replies").get_data(as_text=True)
    refused = client.get("/?tab=refused").get_data(as_text=True)
    assert "LEROY" in refused and "DURAND" not in refused


def test_collect_auto_toggle_and_daily_preempts(client, monkeypatch):
    login(client)
    assert "Collecte permanente activée" in client.get("/").get_data(as_text=True)
    client.post("/collect/auto")
    assert web.collect_auto(db.connect(db.DB_PATH)) is False
    client.post("/collect/auto")
    assert web.collect_auto(db.connect(db.DB_PATH)) is True
    # une collecte en cours cède la place aux mails du jour
    started = []
    monkeypatch.setattr(web.threading, "Thread", lambda target, daemon: type("T", (), {"start": lambda s: started.append(target)})())
    web._job.update(running=True, kind="collect", stop=False, next=None)
    try:
        assert web.start_job() is True
        assert web._job["stop"] and web._job["next"] is web._run_daily and not started
        client.post("/job/stop")
        assert web.collect_auto(db.connect(db.DB_PATH)) is False
    finally:
        web._job.update(running=False, kind="", stop=False, next=None)


def test_collect_progress(client):
    login(client)
    con = db.connect(db.DB_PATH)
    con.execute("INSERT INTO companies(siren,nom,status) VALUES('9','NOUVELLE','new')")
    con.commit()
    p = web.collect_progress(con)
    assert (p["total"], p["tested"], p["untested"], p["found"], p["finished"]) == (2, 1, 1, 1, False)
    html = client.get("/").get_data(as_text=True)
    assert "Entreprises testées" in html and "1 / 2" in html and "Encore 1 entreprise à tester" in html
    con.execute("UPDATE companies SET status='no_email' WHERE siren='9'")
    con.executemany("INSERT INTO sourced VALUES (?, ?)", [(d, n) for d in web.config.DEPARTEMENTS for n in web.config.NAF_CODES])
    con.commit()
    assert "Toutes les entreprises ont été testées" in client.get("/").get_data(as_text=True)


def test_social_tab(client):
    login(client)
    con = db.connect(db.DB_PATH)
    con.execute("INSERT INTO companies(siren,nom,commune,metier,status,site_status,facebook,dirigeant) "
                "VALUES('5','LULU','Rodez','restaurant','no_email','none','https://www.facebook.com/chezlulu12','Lucie Martin')")
    con.commit()
    html = client.get("/?tab=social").get_data(as_text=True)
    assert "LULU" in html and "https://m.me/chezlulu12" in html and "Bonjour Lucie," in html
    client.post("/social/5", data={"s": "sent", "message": "Bonjour"})
    html = client.get("/?tab=social").get_data(as_text=True)
    assert "Messages envoyés" in html and "Aucune page Facebook" in html
    client.post("/social/5", data={"s": "replied"})
    assert db.connect(db.DB_PATH).execute("SELECT status FROM companies WHERE siren='5'").fetchone()[0] == "replied"
    for tab in ("pipeline", "replies", "stats", "sent"):
        assert client.get(f"/?tab={tab}").status_code == 200
