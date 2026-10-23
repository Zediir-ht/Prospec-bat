"""Emails publiés par les entreprises elles-mêmes dans OpenStreetMap (licence ODbL, données ouvertes)."""
import re
from datetime import datetime, timedelta

import requests

from . import config, db
from .qualify import EMAIL_RE, name_tokens, norm

OVERPASS = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "prospec-bat/1.0 (prospection B2B locale)"}

QUERY = """[out:json][timeout:240];
area["boundary"="administrative"]["admin_level"="6"]["ref:INSEE"="{dept}"]->.d;
(nwr(area.d)["name"]["email"];
 nwr(area.d)["name"]["contact:email"];);
out tags center;"""

# mots trop courants pour distinguer deux entreprises
GENERIC = {"boulangerie", "patisserie", "restaurant", "garage", "coiffure", "salon", "plomberie", "chauffage",
           "electricite", "maconnerie", "menuiserie", "peinture", "couverture", "hotel", "cafe", "bar", "boucherie",
           "charcuterie", "fleuriste", "pharmacie", "tabac", "brasserie", "pizzeria", "auberge", "camping", "gite",
           "artisan", "atelier", "institut", "beaute", "coiffeur", "epicerie", "carrosserie", "automobile", "batiment"}


def parse_element(el, dept):
    t = el.get("tags") or {}
    raw = t.get("contact:email") or t.get("email") or ""
    emails = EMAIL_RE.findall(raw.replace(",", ";"))
    if not emails or not t.get("name"):
        return None
    return {
        "osm_id": f"{el.get('type', 'x')}/{el.get('id')}", "dept": dept, "name": t["name"], "email": emails[0].lower(),
        "website": t.get("contact:website") or t.get("website") or "",
        "city": t.get("addr:city", ""), "postcode": t.get("addr:postcode", ""),
    }


def fetch_dept(dept, session=None):
    session = session or requests.Session()
    r = session.post(config.env("OVERPASS_URL", OVERPASS), data={"data": QUERY.format(dept=dept)}, headers=UA, timeout=300)
    r.raise_for_status()
    return [p for p in (parse_element(e, dept) for e in r.json().get("elements", [])) if p]


def refresh(con, session=None, max_age_days=30):
    """Télécharge les lieux OSM avec email, par département (une fois par mois)."""
    n = 0
    for dept in config.DEPARTEMENTS:
        last = db.get_setting(con, f"osm:{dept}")
        if last and datetime.fromisoformat(last) > datetime.now() - timedelta(days=max_age_days):
            continue
        for p in fetch_dept(dept, session):
            con.execute("INSERT OR REPLACE INTO osm_places VALUES (:osm_id,:dept,:name,:email,:website,:city,:postcode)", p)
            n += 1
        db.set_setting(con, f"osm:{dept}", datetime.now().isoformat())
    return n


def distinctive(name):
    return {t for t in name_tokens(name) if norm(t) not in GENERIC}


def same_company(company, place):
    """Même entreprise : même lieu (code postal ou commune) et noms distinctifs recoupés."""
    a, b = distinctive(company["nom"]), distinctive(place["name"])
    if not a or not b:
        return False
    inter = a & b
    if not inter or len(inter) / len(a | b) < 0.5:
        return False
    if place["postcode"]:
        return place["postcode"] == company["code_postal"]
    if place["city"]:
        return norm(place["city"]) == norm(company["commune"])
    return a == b and len(a) >= 2  # aucun lieu dans OSM : seulement un nom identique et assez rare


def match(con):
    """Renseigne l'email des entreprises sans email dont OSM publie l'adresse. Retourne le nombre d'appariements."""
    by_token = {}
    for p in con.execute("SELECT * FROM osm_places").fetchall():
        for t in distinctive(p["name"]):
            by_token.setdefault(t, []).append(p)
    n = 0
    rows = con.execute("SELECT * FROM companies WHERE email IS NULL AND status IN ('new','no_email')").fetchall()
    for c in rows:
        for t in distinctive(c["nom"]):
            hit = next((p for p in by_token.get(t, []) if same_company(c, p)), None)
            if hit:
                con.execute("UPDATE companies SET email=?, email_source='osm', status='new' WHERE siren=?", (hit["email"], c["siren"]))
                n += 1
                break
    con.commit()
    return n
