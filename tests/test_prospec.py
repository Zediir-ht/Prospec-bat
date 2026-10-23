import pytest

from prospec import db, mailer, qualify, sourcing


def test_parse_result():
    r = {"siren": "123456789", "nom_complet": "DUPONT COUVERTURE", "activite_principale": "43.91A",
         "siege": {"libelle_commune": "RODEZ", "code_postal": "12000"},
         "dirigeants": [{"type_dirigeant": "personne physique", "prenoms": "JEAN, PAUL", "nom": "DUPONT"}],
         "nature_juridique": "5499"}
    c = sourcing.parse_result(r)
    assert c["commune"] == "Rodez" and c["dirigeant"] == "Jean Dupont" and c["metier"] == "couverture et charpente"


def test_pick_site_skips_directories():
    urls = ["https://www.pagesjaunes.fr/dupont-couverture", "https://www.dupont-couverture.fr/accueil"]
    assert qualify.pick_site("DUPONT COUVERTURE", urls) == "https://www.dupont-couverture.fr"
    assert qualify.pick_site("MARTIN SARL", urls) is None


def test_analyse_html():
    old = "<html><body>© 2014 Dupont</body></html>"
    status, issues = qualify.analyse_html(old, "http://x.fr")
    assert status == "outdated" and len(issues) == 3
    good = '<html><head><meta name="viewport" content="x"></head><body>© 2025</body></html>'
    assert qualify.analyse_html(good, "https://x.fr")[0] == "ok"


def test_emails():
    html = "contact: info@dupont.fr logo@2x.png sentry@wixpress.com"
    assert qualify.extract_emails(html) == ["info@dupont.fr"]


def test_signature_has_optout_and_no_price():
    msg = mailer.build_message("a@b.fr", "Un site ?", "Bonjour,\n\nJe peux préparer une maquette gratuite de votre site, sans engagement.")
    text = msg.get_content()
    assert "STOP" in text and msg["List-Unsubscribe"] and "€" not in text


def test_check_mail_rejects_price():
    import pytest
    with pytest.raises(ValueError):
        mailer.check_mail("Un site ?", "Bonjour, votre site pour seulement 500 € avec une maquette gratuite et sans engagement du tout.")
    with pytest.raises(ValueError):
        mailer.check_mail("", "court")


def test_batch_prompt_and_parse():
    c = {"siren": "1", "nom": "DUPONT", "commune": "Rodez", "metier": "boulangerie", "dirigeant": "Jean Dupont",
         "site_status": "none", "site_issues": ""}
    prompt = mailer.batch_prompt([c])
    assert "DUPONT" in prompt and "JSON" in prompt and "aucun prix" in prompt.lower()
    reply = """Voici :
```json
[{"siren": "1", "subject": "Un site pour Dupont ?", "body": "Bonjour Jean,\\n\\nEn cherchant boulangerie Rodez, je n'ai pas trouvé votre site. Je peux préparer une maquette gratuite, sans engagement. Cela vous intéresse ?"},
 {"siren": "9", "subject": "x", "body": "y"}]
```"""
    ok, errors = mailer.parse_batch(reply, {"1": "DUPONT"})
    assert list(ok) == ["1"] and ok["1"][0] == "Un site pour Dupont ?" and len(errors) == 1
    assert mailer.parse_batch("pas de json", {"1": "X"})[0] == {}


def test_suppression(tmp_path):
    con = db.connect(tmp_path / "t.db")
    db.suppress(con, "a@b.fr")
    assert db.is_suppressed(con, "A@b.fr") and not db.is_suppressed(con, "c@d.fr")


def test_metier_for_other_sectors():
    assert sourcing.metier_for("10.71C") == "boulangerie"
    assert sourcing.metier_for("56.10A") == "restaurant"
    assert sourcing.metier_for("43.91A") == "couverture et charpente"


def test_source_stops_when_pool_is_enough(tmp_path, monkeypatch):
    from prospec import config
    monkeypatch.setattr(config, "DEPARTEMENTS", ["12", "48"])
    monkeypatch.setattr(config, "NAF_CODES", ["10.71C", "56.10A", "47.76Z"])
    calls = []

    def fake_fetch(naf, dept, session=None, max_pages=40):
        calls.append((dept, naf))
        yield {"siren": f"{dept}{naf}", "nom": "X", "commune": "Rodez", "code_postal": dept + "000", "naf": naf,
               "metier": "x", "dirigeant": "", "effectif": "", "nature_juridique": "5499"}

    monkeypatch.setattr(sourcing, "fetch_naf", fake_fetch)
    con = db.connect(tmp_path / "t.db")
    assert sourcing.source(con, min_pool=2) == 2
    assert [d for d, _ in calls] == ["12", "12"]          # Aveyron d'abord, arrêt dès 2 entreprises
    assert sourcing.source(con, min_pool=2) == 0           # vivier déjà suffisant : rien de plus
    assert sourcing.source(con, min_pool=10) == 4          # reprend où on s'est arrêté, sans doublon
    assert len(calls) == 6


def test_qualify_stops_at_target(tmp_path, monkeypatch):
    from prospec import cli, qualify

    monkeypatch.setenv("DAILY_LIMIT", "3")
    monkeypatch.setattr(cli.time, "sleep", lambda s: None)
    con = db.connect(tmp_path / "t.db")
    for i in range(10):
        con.execute("INSERT INTO companies(siren,nom,commune,code_postal,naf,metier) VALUES(?,?,?,?,?,?)",
                    (str(i), f"E{i}", "Rodez", "12000", "10.71C", "boulangerie"))
    con.commit()
    calls = []

    def fake(row, session=None):
        calls.append(row["siren"])
        return {"site_url": None, "site_status": "none", "site_issues": "", "email": f"contact{row['siren']}@e{row['siren']}.fr"}

    monkeypatch.setattr(qualify, "qualify_company", fake)

    class A:
        n = 50

    cli.cmd_qualify(con, A)
    assert len(calls) == 3 and cli.pending(con) == 3
    cli.cmd_qualify(con, A)                      # objectif déjà atteint : aucune nouvelle recherche
    assert len(calls) == 3


def test_claude_mail_via_http(monkeypatch):
    from prospec import config

    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    sent = {}

    class R:
        def raise_for_status(self): pass
        def json(self):
            return {"content": [{"text": "Un site pour Dupont ?\n\nBonjour Jean,\n\nEn cherchant boulangerie Rodez, je n'ai pas trouvé votre site. "
                                          "Je peux préparer une maquette gratuite, sans engagement. Cela vous intéresse ?"}]}

    import requests
    monkeypatch.setattr(requests, "post", lambda url, **kw: sent.update(kw) or R())
    c = {"siren": "1", "nom": "DUPONT", "commune": "Rodez", "metier": "boulangerie", "dirigeant": "Jean",
         "site_status": "none", "site_issues": ""}
    subject, body = mailer.compose(c)
    assert subject == "Un site pour Dupont ?" and body.startswith("Bonjour Jean")
    assert sent["headers"]["x-api-key"] == "k" and "DUPONT" in sent["json"]["messages"][0]["content"]
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert mailer.compose(c) is None


def _cf(email, key=0x55):
    return f"{key:02x}" + "".join(f"{ord(ch) ^ key:02x}" for ch in email)


def test_extract_emails_obfuscated():
    html = (f'<a class="__cf_email__" data-cfemail="{_cf("contact@dupont-plomberie.fr")}">[email protected]</a> '
            'ou écrivez à jean [at] martin-toiture [dot] fr, '
            '<a href="mailto:info%40vidal-maconnerie.fr">mail</a>, accueil&#64;hotel-rouergue.fr')
    found = qualify.extract_emails(html)
    assert {"contact@dupont-plomberie.fr", "jean@martin-toiture.fr", "info@vidal-maconnerie.fr",
            "accueil@hotel-rouergue.fr"} <= set(found)


def test_osm_parse_and_match(tmp_path):
    from prospec import osm

    el = {"type": "node", "id": 42, "tags": {"name": "Boulangerie Calmels", "contact:email": "Calmels.Pain@orange.fr; autre@x.fr",
                                              "addr:postcode": "12100", "addr:city": "Millau"}}
    place = osm.parse_element(el, "12")
    assert place["email"] == "calmels.pain@orange.fr" and place["osm_id"] == "node/42"
    assert osm.parse_element({"type": "node", "id": 1, "tags": {"name": "X"}}, "12") is None

    con = db.connect(tmp_path / "t.db")
    con.execute("INSERT INTO osm_places VALUES (:osm_id,:dept,:name,:email,:website,:city,:postcode)", place)
    for siren, nom, cp in (("1", "SARL CALMELS", "12100"), ("2", "CALMELS PLOMBERIE", "48000"), ("3", "BOULANGERIE DURAND", "12100")):
        con.execute("INSERT INTO companies(siren,nom,commune,code_postal,status) VALUES(?,?,?,?,'new')", (siren, nom, "Millau", cp))
    con.commit()
    assert osm.match(con) == 1
    row = con.execute("SELECT email, email_source FROM companies WHERE siren='1'").fetchone()
    assert tuple(row) == ("calmels.pain@orange.fr", "osm")
    assert con.execute("SELECT email FROM companies WHERE siren IN ('2','3') AND email IS NOT NULL").fetchone() is None


def test_signature_mentions_email_source():
    for source, expected in (("site", "site web de votre entreprise"), ("osm", "OpenStreetMap")):
        assert expected in mailer.build_message("a@b.fr", "S", "B", source).get_content()
    assert "trouvé votre adresse" not in mailer.build_message("a@b.fr", "S", "B").get_content()


def test_qualify_keeps_osm_email(tmp_path, monkeypatch):
    from prospec import cli, qualify

    monkeypatch.setattr(cli.time, "sleep", lambda s: None)
    con = db.connect(tmp_path / "t.db")
    con.execute("INSERT INTO companies(siren,nom,commune,code_postal,email,email_source,status) "
                "VALUES('1','CALMELS','Millau','12100','c@calmels.fr','osm','new')")
    con.commit()
    monkeypatch.setattr(qualify, "qualify_company",
                        lambda row, session=None: {"site_url": None, "site_status": "none", "site_issues": "", "email": None})

    class A:
        n = 5

    cli.cmd_qualify(con, A)
    row = con.execute("SELECT status, email, email_source FROM companies").fetchone()
    assert tuple(row) == ("qualified", "c@calmels.fr", "osm")


def test_never_send_to_unsourced_address(tmp_path):
    import pytest
    from prospec import cli

    con = db.connect(tmp_path / "t.db")
    con.execute("INSERT INTO companies(siren,nom,email,email_source,status) VALUES('1','A','info@a.fr',NULL,'qualified')")
    con.execute("INSERT INTO companies(siren,nom,email,email_source,status) VALUES('2','B','x@b.fr','deviné','qualified')")
    con.execute("INSERT INTO companies(siren,nom,email,email_source,status) VALUES('3','C','c@c.fr','osm','qualified')")
    con.commit()
    con.execute("UPDATE companies SET email_source=NULL WHERE siren='1'")  # une base ancienne passerait par la migration
    rows = con.execute("SELECT * FROM companies").fetchall()
    assert [r["siren"] for r in cli.next_to_write(con)] == ["3"]
    for r in rows[:2]:
        with pytest.raises(ValueError):
            mailer.assert_sourced(r)
    mailer.assert_sourced(rows[2])


def test_migration_marks_old_emails_as_site(tmp_path):
    import sqlite3

    path = tmp_path / "old.db"
    con = db.connect(path)
    con.execute("INSERT INTO companies(siren,nom,email,status) VALUES('1','A','contact@a.fr','qualified')")
    con.commit()
    con.close()
    assert db.connect(path).execute("SELECT email_source FROM companies").fetchone()[0] == "site"


def test_osm_website_only_and_reuse(tmp_path, monkeypatch):
    from prospec import osm

    assert osm.parse_element({"type": "node", "id": 2, "tags": {"name": "Garage Bru", "website": "garage-bru.fr"}}, "12")["website"] == "https://garage-bru.fr"
    assert osm.parse_element({"type": "node", "id": 3, "tags": {"name": "Bar X", "website": "https://facebook.com/barx"}}, "12") is None
    assert '"ref:INSEE"="12"' in osm.QUERY.format(dept="12") and '["craft"]' in osm.QUERY

    con = db.connect(tmp_path / "t.db")
    con.execute("INSERT INTO osm_places VALUES ('node/2','12','Garage Bru','','https://garage-bru.fr','Rodez','12000')")
    con.execute("INSERT INTO companies(siren,nom,commune,code_postal,status,site_status) VALUES('1','BRU AUTOMOBILES','Rodez','12000','no_email','none')")
    con.commit()
    assert osm.match(con) == 1
    row = dict(con.execute("SELECT * FROM companies").fetchone())
    assert row["site_url"] == "https://garage-bru.fr" and row["status"] == "new" and row["email"] is None

    # le site connu est lu directement, sans recherche web
    monkeypatch.setattr(qualify, "search_urls", lambda *a: pytest.fail("recherche web inutile"))
    monkeypatch.setattr(qualify, "fetch", lambda url, session: ("https://garage-bru.fr/", "<html>contact@garage-bru.fr © 2015</html>"))
    res = qualify.qualify_company(row)
    assert res["email"] == "contact@garage-bru.fr" and res["site_status"] == "outdated"


def test_collect_goes_beyond_daily_target(tmp_path, monkeypatch):
    from prospec import cli, osm

    monkeypatch.setenv("DAILY_LIMIT", "2")
    monkeypatch.setattr(cli.time, "sleep", lambda s: None)
    monkeypatch.setattr(sourcing, "source", lambda con, min_pool=300: 0)
    monkeypatch.setattr(osm, "refresh", lambda con: 0)
    con = db.connect(tmp_path / "t.db")
    for i in range(8):
        con.execute("INSERT INTO companies(siren,nom,commune,code_postal) VALUES(?,?,?,?)", (str(i), f"E{i}", "Rodez", "12000"))
    con.commit()
    monkeypatch.setattr(qualify, "qualify_company", lambda row, session=None: {
        "site_url": None, "site_status": "none", "site_issues": "", "email": f"c{row['siren']}@e{row['siren']}.fr"})
    logs = []

    class A:
        n = 100

    assert cli.cmd_collect(con, A, log=logs.append) == (8, 8)
    assert cli.pending(con) == 8 and logs[-1] == "8 entreprises testées, 8 adresses trouvées"

    stops = iter([False, True])
    con.execute("UPDATE companies SET status='new'")
    con.commit()
    assert cli.cmd_collect(con, A, stop=lambda: next(stops, True))[0] <= 1
