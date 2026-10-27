import pytest

from prospec import cli, db, emails, qualify


def test_check_rejects_garbage():
    good = ["contact@dupont-plomberie.fr", "jean.dupont@orange.fr", "info@maison-bedel.fr", "a.b+c@sarl-x.com"]
    bad = {"logo@2x.png": "extension", "image@site.webp": "extension", "noreply@dupont.fr": "automatique",
           "nom@domaine.fr": "factice", "votre@email.com": "factice", "email@dupont.fr": "factice",
           "contact@wixpress.com": "tiers", "x@sentry.io": "tiers", "webmaster@dupont.fr": "automatique",
           "a@b": "domaine", "a..b@dupont.fr": "partie locale", ".a@dupont.fr": "partie locale", "a@-dupont.fr": "domaine",
           "0123456789abcdef0123456789abcdef@dupont.fr": "débris", "contact@dupont.frtel": "extension",
           "contact@dupont.jsx": "extension", "": "format", "a@b@c.fr": "format"}
    for e in good:
        assert emails.check(e)[0], e
    for e, why in bad.items():
        ok, reason = emails.check(e)
        assert not ok and why in reason, (e, reason)


def test_repair_without_inventing():
    assert emails.repair("u003einfo@dupont.fr") == "info@dupont.fr"
    assert emails.repair("0565123456contact@dupont.fr") == "contact@dupont.fr"
    assert emails.repair("contact@dupont.frTel") == "contact@dupont.fr"
    assert emails.repair("Contact@Dupont.FR.") == "contact@dupont.fr"
    assert emails.repair("logo@2x.png") == "logo@2x.png"          # fichier : jamais « réparé » en vraie extension
    assert emails.repair("contact@dupont.frc") == "contact@dupont.frc"  # reste suspect (1 lettre seulement collée)
    assert emails.extract("Écrire à u003einfo@dupont.fr ou contact@dupont.frTél ou logo@2x.png") == ["info@dupont.fr", "contact@dupont.fr"]


def test_related_domain():
    names = ("SARL DUPONT ET FILS", "Plomberie du Rouergue")
    site = "https://www.plomberie-du-rouergue.fr/"
    assert emails.related("contact@plomberie-du-rouergue.fr", site, names)
    assert emails.related("jean@gmail.com", site, names)                      # messagerie grand public : fréquent chez les artisans
    assert emails.related("contact@dupont-sarl.fr", site, names)              # le nom de l'entreprise est dans le domaine
    assert not emails.related("contact@agence-webdesign.fr", site, names)     # agence citée en bas de page
    assert not emails.related("support@ovh.net", site, names)


def test_best_email_ignores_agency():
    found = ["contact@agence-webdesign.fr", "boutique@dupont-couverture.fr", "dupont@gmail.com"]
    names = (None, "DUPONT COUVERTURE")
    assert qualify.best_email(found, "https://dupont-couverture.fr", names) == "boutique@dupont-couverture.fr"
    assert qualify.best_email(["contact@agence-webdesign.fr"], "https://dupont-couverture.fr", names) is None
    assert qualify.best_email(["dupont@gmail.com", "contact@agence-webdesign.fr"], "https://dupont-couverture.fr", names) == "dupont@gmail.com"


@pytest.fixture
def con(tmp_path):
    return db.connect(tmp_path / "t.db")


def add(con, siren, nom, email, status="qualified", source="site", site="https://dupont.fr", **kw):
    con.execute("INSERT INTO companies(siren,nom,email,email_source,status,site_url,subject,body) VALUES(?,?,?,?,?,?,?,?)",
                (siren, nom, email, source, status, site, "S", "B"))
    con.commit()


def test_clean_database(con, monkeypatch):
    from prospec import dnscheck
    monkeypatch.setattr(dnscheck, "domain_status", lambda d: "invalid" if d == "mort.fr" else "ok")
    add(con, "1", "DUPONT", "contact@dupont.fr")                              # bonne
    add(con, "2", "MARTIN", "logo@2x.png")                                    # fichier
    add(con, "3", "BRU", "contact@agence-web.fr", status="drafted")           # autre domaine : agence
    add(con, "4", "CAYLA", "info@mort.fr", site="https://mort.fr")            # domaine sans messagerie
    add(con, "5", "OSM", "info@autre-domaine.fr", source="osm", site=None)    # OpenStreetMap : pas de test de domaine
    for i in (6, 7, 8):
        add(con, str(i), f"AGENCE CLIENT {i}", "shared@dupont.fr", site="https://dupont.fr")   # même adresse sur 3 entreprises
    add(con, "9", "ENVOYE", "logo@2x.png", status="sent")                     # déjà envoyé : intact
    removed = emails.clean_database(con)
    gone = {r[0] for r in removed}
    assert gone == {"MARTIN", "BRU", "CAYLA", "AGENCE CLIENT 6", "AGENCE CLIENT 7", "AGENCE CLIENT 8"}
    rows = {r["siren"]: r for r in con.execute("SELECT * FROM companies")}
    assert rows["1"]["status"] == "qualified" and rows["5"]["status"] == "qualified" and rows["9"]["status"] == "sent"
    assert rows["3"]["status"] == "no_email" and rows["3"]["email"] is None and rows["3"]["subject"] is None


def test_search_discards_bad_and_shared_addresses(con, monkeypatch):
    from prospec import dnscheck
    monkeypatch.setattr(dnscheck, "domain_status", lambda d: "ok")
    for i in (1, 2):
        add(con, str(i), f"E{i}", "shared@x.fr", site=None)
    con.execute("INSERT INTO companies(siren,nom,status) VALUES('3','E3','new')")
    row = con.execute("SELECT * FROM companies WHERE siren='3'").fetchone()
    res = {"site_url": None, "site_status": "none", "site_issues": "", "email": "shared@x.fr"}
    assert cli.apply_result(con, row, res) == "no_email"
    res = {"site_url": None, "site_status": "none", "site_issues": "", "email": "logo@2x.png"}
    assert cli.apply_result(con, row, res) == "no_email"
    res = {"site_url": None, "site_status": "none", "site_issues": "", "email": "contact@vrai-nom.fr"}
    assert cli.apply_result(con, row, res) == "qualified"


def test_last_defense_before_sending(con, monkeypatch):
    monkeypatch.setattr(cli.mailer, "send", lambda m: pytest.fail("ne doit pas partir"))
    add(con, "1", "X", "logo@2x.png", status="drafted")
    row = con.execute("SELECT * FROM companies").fetchone()
    with pytest.raises(ValueError, match="adresse invalide"):
        cli.send_now(con, row, "S", "B")


def test_cleanup_button_and_report(tmp_path, monkeypatch):
    import os
    from prospec import dnscheck, web

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setattr(dnscheck, "domain_status", lambda d: "ok")
    os.environ["DASHBOARD_PASSWORD"] = "pw"
    con = db.connect()
    add(con, "1", "MARTIN", "logo@2x.png")
    add(con, "2", "DUPONT", "contact@dupont.fr")
    web.app.config["TESTING"] = True
    c = web.app.test_client()
    c.post("/login", data={"pw": "pw"})
    web.run_cleanup()
    assert con.execute("SELECT status FROM companies WHERE siren='1'").fetchone()[0] == "no_email"
    assert con.execute("SELECT status FROM companies WHERE siren='2'").fetchone()[0] == "qualified"
    home = c.get("/").data.decode()
    assert "Nettoyer les adresses" in home and "1 adresse(s) retirée(s)" in home
    r = c.post("/clean", follow_redirects=True)
    assert "Nettoyage lancé" in r.data.decode()
