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


def test_source_is_incremental_and_aveyron_first(tmp_path, monkeypatch):
    from prospec import config
    monkeypatch.setattr(config, "DEPARTEMENTS", ["12", "48"])
    monkeypatch.setattr(config, "NAF_CODES", ["10.71C", "56.10A"])
    calls = []

    def fake_fetch(naf, dept, session=None, max_pages=40):
        calls.append((dept, naf))
        yield {"siren": f"{dept}{naf}", "nom": "X", "commune": "Rodez", "code_postal": dept + "000", "naf": naf,
               "metier": "x", "dirigeant": "", "effectif": "", "nature_juridique": "5499"}

    monkeypatch.setattr(sourcing, "fetch_naf", fake_fetch)
    con = db.connect(tmp_path / "t.db")
    assert sourcing.source(con, max_other=1) == 3
    assert calls == [("12", "10.71C"), ("12", "56.10A"), ("48", "10.71C")]
    assert sourcing.source(con, max_other=1) == 1 and calls[-1] == ("48", "56.10A")
    assert sourcing.source(con) == 0


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
