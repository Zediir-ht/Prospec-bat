import pytest

from prospec import config, db, mailer, osm, qualify, sourcing


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

    cli.qualify_batch(con, A.n, workers=1)
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
    con.execute("INSERT INTO osm_places(osm_id,dept,name,email,website,city,postcode,facebook) "
                "VALUES (:osm_id,:dept,:name,:email,:website,:city,:postcode,:facebook)", place)
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
    db._migrated.discard(str(path))  # nouveau processus : la migration est rejouée
    assert db.connect(path).execute("SELECT email_source FROM companies").fetchone()[0] == "site"


def test_osm_website_only_and_reuse(tmp_path, monkeypatch):
    from prospec import osm

    assert osm.parse_element({"type": "node", "id": 2, "tags": {"name": "Garage Bru", "website": "garage-bru.fr"}}, "12")["website"] == "https://garage-bru.fr"
    bar = osm.parse_element({"type": "node", "id": 3, "tags": {"name": "Bar X", "website": "https://facebook.com/barx"}}, "12")
    assert bar["website"] == "" and bar["facebook"] == "https://www.facebook.com/barx"  # page Facebook, pas un site
    assert '"ref:INSEE"="12"' in osm.QUERY.format(dept="12") and '["craft"]' in osm.QUERY

    con = db.connect(tmp_path / "t.db")
    con.execute("INSERT INTO osm_places VALUES ('node/2','12','Garage Bru','','https://garage-bru.fr','Rodez','12000','')")
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


def test_qualify_runs_in_parallel(tmp_path, monkeypatch):
    import threading
    import time
    from prospec import cli

    monkeypatch.setenv("DAILY_LIMIT", "1000")
    con = db.connect(tmp_path / "t.db")
    for i in range(20):
        con.execute("INSERT INTO companies(siren,nom,commune,code_postal) VALUES(?,?,?,?)", (str(i), f"E{i}", "Rodez", "12000"))
    con.commit()
    active, peak, lock = [0], [0], threading.Lock()

    def slow(row, session=None):
        with lock:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        time.sleep(0.2)
        with lock:
            active[0] -= 1
        if row["siren"] == "5":
            raise RuntimeError("site en panne")
        return {"site_url": None, "site_status": "none", "site_issues": "", "email": f"c{row['siren']}@e{row['siren']}.fr"}

    monkeypatch.setattr(qualify, "qualify_company", slow)
    start = time.monotonic()
    tested, found = cli.qualify_batch(con, 100, workers=10)
    assert time.monotonic() - start < 1.5          # 20 × 0,2 s en séquentiel = 4 s
    assert peak[0] == 10 and (tested, found) == (19, 19)
    assert con.execute("SELECT COUNT(*) FROM companies WHERE status='qualified'").fetchone()[0] == 19


def test_parallel_stops_near_target(tmp_path, monkeypatch):
    from prospec import cli

    monkeypatch.setenv("DAILY_LIMIT", "10")
    con = db.connect(tmp_path / "t.db")
    for i in range(100):
        con.execute("INSERT INTO companies(siren,nom,commune,code_postal) VALUES(?,?,?,?)", (str(i), f"E{i}", "Rodez", "12000"))
    con.commit()
    monkeypatch.setattr(qualify, "qualify_company", lambda row, session=None: {
        "site_url": None, "site_status": "none", "site_issues": "", "email": f"c{row['siren']}@e{row['siren']}.fr"})
    tested, _ = cli.qualify_batch(con, 100, workers=5)
    assert 10 <= tested <= 15                     # au plus les recherches déjà lancées en plus


def test_search_throttle_spaces_requests(monkeypatch):
    import time

    monkeypatch.setenv("SEARCH_INTERVAL", "0.1")
    qualify._search.update(last=0.0, penalty=0.0)
    start = time.monotonic()
    for _ in range(4):
        qualify.throttle_search()
    assert time.monotonic() - start >= 0.3
    qualify.search_feedback(False)
    assert qualify._search["penalty"] == 2.0
    qualify.search_feedback(True)
    assert qualify._search["penalty"] == 1.5
    qualify._search["penalty"] = 0.0


def test_enseigne_parsed_and_used_for_search(monkeypatch):
    r = {"siren": "1", "nom_complet": "SARL DUPONT ET FILS", "activite_principale": "43.22A",
         "siege": {"libelle_commune": "RODEZ", "code_postal": "12000", "liste_enseignes": ["PLOMBERIE DU ROUERGUE"]}}
    c = sourcing.parse_result(r)
    assert c["enseigne"] == "Plomberie Du Rouergue"
    assert sourcing.enseigne_of({"liste_enseignes": ["DUPONT"]}, "SARL DUPONT") == ""  # identique au nom : ignorée

    queries = []

    def fake_search(name, commune, session):
        queries.append(name)
        return ["https://www.plomberie-du-rouergue.fr/"] if "Rouergue" in name else []

    monkeypatch.setattr(qualify, "search_urls", fake_search)
    monkeypatch.setattr(qualify, "fetch", lambda url, session: (url, '<meta name="viewport"> © 2025 contact@plomberie-du-rouergue.fr'))
    res = qualify.qualify_company({"nom": c["nom"], "enseigne": c["enseigne"], "commune": "Rodez"})
    assert queries == ["Plomberie Du Rouergue"] and res["email"] == "contact@plomberie-du-rouergue.fr"


def test_osm_matches_on_enseigne(tmp_path):
    from prospec import osm

    con = db.connect(tmp_path / "t.db")
    con.execute("INSERT INTO osm_places VALUES ('node/1','12','Le Fournil Ruthénois','pain@fournil-ruthenois.fr','','Rodez','12000','')")
    con.execute("INSERT INTO companies(siren,nom,enseigne,commune,code_postal,status) VALUES('1','SAS MARTY','Le Fournil Ruthénois','Rodez','12000','new')")
    con.commit()
    assert osm.match(con) == 1
    assert con.execute("SELECT email FROM companies").fetchone()[0] == "pain@fournil-ruthenois.fr"


def test_discovery_links_sites_by_siren_and_name(tmp_path, monkeypatch):
    from prospec import discovery

    con = db.connect(tmp_path / "t.db")
    rows = [("123456789", "SARL ALBOUY", "", "plomberie et chauffage"), ("987654321", "BOUSQUET", "", "plomberie et chauffage"),
            ("555555555", "CAYLA", "", "plomberie et chauffage"), ("444444444", "ROUX", "", "boulangerie")]
    for siren, nom, ens, metier in rows:
        con.execute("INSERT INTO companies(siren,nom,enseigne,commune,code_postal,metier,status) VALUES(?,?,?,?,?,?,'new')",
                    (siren, nom, ens, "Rodez", "12000", metier))
    con.commit()
    assert discovery.next_queries(con, 5)[0][0] == "plomberie et chauffage Rodez"

    monkeypatch.setattr(discovery, "search_urls", lambda metier, commune, session: [
        "https://www.pagesjaunes.fr/x", "https://chauffage-ruthenois.fr/", "https://www.bousquet-plomberie.fr/contact",
        "https://autre-site.fr/"])
    pages = {"https://chauffage-ruthenois.fr/mentions-legales": "SARL Albouy - SIRET 123 456 789 00015"}

    def fake_fetch(url, session):
        if url in pages:
            return url, pages[url]
        if url.endswith(("legales", ".html", "/", "_legales")) and "mentions" in url:
            raise discovery.requests.RequestException()
        return url, "<html>accueil</html>"

    monkeypatch.setattr(discovery, "fetch", fake_fetch)
    done, linked = discovery.run(con, max_queries=1, workers=3)
    assert (done, linked) == (1, 2)
    sites = dict(con.execute("SELECT siren, site_url FROM companies WHERE site_url IS NOT NULL").fetchall())
    assert sites == {"123456789": "https://chauffage-ruthenois.fr", "987654321": "https://www.bousquet-plomberie.fr"}
    assert discovery.next_queries(con, 5) == [("boulangerie Rodez", "boulangerie", "Rodez")]  # requête déjà faite


def test_signature_has_contact_details(monkeypatch):
    monkeypatch.setenv("SENDER_PHONE", "+33632915377")
    monkeypatch.setenv("SENDER_WEBSITE", "https://zdrdev.fr")
    text = mailer.build_message("a@b.fr", "S", "Bonjour", "site").get_content()
    assert "https://zdrdev.fr" in text and "06 32 91 53 77" in text and "corentin.mayrand@gmail.com" in text
    assert mailer.format_phone("0632915377") == "06 32 91 53 77"


def test_sourcing_refresh_after_full_round(tmp_path, monkeypatch):
    from datetime import datetime, timedelta
    con = db.connect(tmp_path / "t.db")
    con.executemany("INSERT INTO sourced VALUES (?, ?)", [(d, n) for d in config.DEPARTEMENTS for n in config.NAF_CODES])
    con.commit()
    assert sourcing.refresh_if_due(con) is False  # passage tout juste fini : on note la date
    assert sourcing.next_refresh(con) > datetime.now() + timedelta(days=6)
    db.set_setting(con, "sourced_full_at", (datetime.now() - timedelta(days=8)).isoformat())
    assert sourcing.refresh_if_due(con) is True
    assert con.execute("SELECT COUNT(*) FROM sourced").fetchone()[0] == 0
    assert sourcing.next_refresh(con) is None


def test_facebook_page_detection():
    assert qualify.facebook_page('<a href="https://www.facebook.com/sharer/sharer.php?u=x">p</a>'
                                 '<a href="https://fr-fr.facebook.com/boulangerie.calmels/">fb</a>') == "https://www.facebook.com/boulangerie.calmels"
    assert qualify.facebook_page("https://m.facebook.com/profile.php?id=1234") == "https://www.facebook.com/profile.php?id=1234"
    assert qualify.facebook_page("https://www.facebook.com/tr?id=1&ev=PageView") is None
    urls = ["https://www.facebook.com/autreentreprise", "https://www.facebook.com/plomberie.vabre12"]
    assert qualify.pick_facebook("VABRE PLOMBERIE", urls) == "https://www.facebook.com/plomberie.vabre12"
    tags = {"name": "Chez Lulu", "contact:facebook": "chezlulu12"}
    assert osm.parse_element({"type": "node", "id": 9, "tags": tags}, "12")["facebook"] == "https://www.facebook.com/chezlulu12"


def test_apply_result_keeps_facebook(tmp_path):
    from prospec import cli
    con = db.connect(tmp_path / "t.db")
    con.execute("INSERT INTO companies(siren,nom,commune,status) VALUES('1','LULU','Rodez','new')")
    row = con.execute("SELECT * FROM companies").fetchone()
    cli.apply_result(con, row, {"site_url": None, "site_status": "none", "site_issues": "", "email": None,
                                "facebook": "https://www.facebook.com/chezlulu12"})
    r = con.execute("SELECT status, facebook FROM companies").fetchone()
    assert (r["status"], r["facebook"]) == ("no_email", "https://www.facebook.com/chezlulu12")


def test_facebook_message_tone():
    c = {"siren": "123", "dirigeant": "Marie Durand", "metier": "boulangerie", "commune": "Rodez", "site_status": "none"}
    msg = mailer.facebook_message(c)
    assert msg.startswith("Bonjour Marie,") and "maquette gratuite" in msg and "€" not in msg and "prix" not in msg
    assert mailer.messenger_link("https://www.facebook.com/chezlulu12") == "https://m.me/chezlulu12"
    assert "jovial" not in mailer.SYSTEM and "moqueur" in mailer.SYSTEM and "respectueux" in mailer.SYSTEM
