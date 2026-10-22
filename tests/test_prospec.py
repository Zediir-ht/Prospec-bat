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


def test_mail_has_no_price_and_has_optout():
    c = {"nom": "DUPONT", "commune": "Rodez", "metier": "plomberie", "dirigeant": "Jean Dupont",
         "site_status": "none", "site_issues": ""}
    subject, body = mailer.fallback_mail(c)
    msg = mailer.build_message("a@b.fr", subject, body)
    text = msg.get_content()
    assert "€" not in text and "maquette gratuite" in text and "STOP" in text and msg["List-Unsubscribe"]


def test_suppression(tmp_path):
    con = db.connect(tmp_path / "t.db")
    db.suppress(con, "a@b.fr")
    assert db.is_suppressed(con, "A@b.fr") and not db.is_suppressed(con, "c@d.fr")
