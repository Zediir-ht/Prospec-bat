"""Emails publiés par les entreprises elles-mêmes dans OpenStreetMap (licence ODbL, données ouvertes)."""
import re
from datetime import datetime, timedelta

import requests

from . import config, db
from .qualify import DIRECTORIES, EMAIL_RE, facebook_page, norm

OVERPASS = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "prospec-bat/1.0 (prospection B2B locale)"}

BUSINESS = ['["shop"]', '["craft"]', '["office"]',
            '["amenity"~"^(restaurant|cafe|bar|pub|fast_food|ice_cream|car_repair|car_wash)$"]',
            '["tourism"~"^(hotel|guest_house|camp_site|chalet|motel|apartment)$"]']
QUERY = ("[out:json][timeout:300];\n"
         'area["boundary"="administrative"]["admin_level"="6"]["ref:INSEE"="{dept}"]->.d;\n('
         + "".join(f'nwr(area.d)["name"]["{k}"];' for k in ("email", "contact:email"))
         + "".join(f'nwr(area.d)["name"]["{k}"]{b};' for k in ("website", "contact:website", "facebook", "contact:facebook") for b in BUSINESS)
         + ");\nout tags center;")

# mots trop courants pour distinguer deux entreprises
GENERIC = {"boulangerie", "patisserie", "restaurant", "garage", "coiffure", "salon", "plomberie", "chauffage",
           "electricite", "maconnerie", "menuiserie", "peinture", "couverture", "hotel", "cafe", "bar", "boucherie",
           "charcuterie", "fleuriste", "pharmacie", "tabac", "brasserie", "pizzeria", "auberge", "camping", "gite",
           "artisan", "atelier", "institut", "beaute", "coiffeur", "epicerie", "carrosserie", "automobile", "batiment"}


def parse_element(el, dept):
    t = el.get("tags") or {}
    raw = t.get("contact:email") or t.get("email") or ""
    emails = EMAIL_RE.findall(raw.replace(",", ";"))
    website = (t.get("contact:website") or t.get("website") or "").split(";")[0].strip()
    if website and not website.startswith("http"):
        website = "https://" + website
    fb = (t.get("contact:facebook") or t.get("facebook") or "").split(";")[0].strip()
    if fb and "facebook" not in fb.lower() and "fb.com" not in fb.lower():
        fb = "https://www.facebook.com/" + fb.lstrip("@/")  # tag réduit au nom de la page
    facebook = facebook_page(fb) or facebook_page(website) or ""
    if any(d in website.lower() for d in DIRECTORIES):  # page Facebook, annuaire... : pas le site de l'entreprise
        website = ""
    if not t.get("name") or not (emails or website or facebook):
        return None
    return {
        "osm_id": f"{el.get('type', 'x')}/{el.get('id')}", "dept": dept, "name": t["name"],
        "email": emails[0].lower() if emails else "", "website": website,
        "city": t.get("addr:city", ""), "postcode": t.get("addr:postcode", ""), "facebook": facebook,
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
        last = db.get_setting(con, f"osm3:{dept}")
        if last and datetime.fromisoformat(last) > datetime.now() - timedelta(days=max_age_days):
            continue
        for p in fetch_dept(dept, session):
            con.execute("INSERT OR REPLACE INTO osm_places(osm_id, dept, name, email, website, city, postcode, facebook) "
                        "VALUES (:osm_id,:dept,:name,:email,:website,:city,:postcode,:facebook)", p)
            n += 1
        db.set_setting(con, f"osm3:{dept}", datetime.now().isoformat())
    return n


STOP = {"sarl", "sas", "sasu", "eurl", "snc", "societe", "entreprise", "ets", "etablissements", "groupe",
        "les", "des", "aux", "and", "chez", "the"}


def distinctive(name):
    """Mots qui distinguent l'entreprise (3 lettres minimum : beaucoup de noms aveyronnais sont courts)."""
    words = re.findall(r"[a-z0-9]+", norm_spaces(name))
    return {w for w in words if len(w) >= 3 and w not in STOP and w.rstrip("s") not in GENERIC and w not in GENERIC}


def norm_spaces(s):
    import unicodedata
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()


def company_names(company):
    keys = company.keys() if hasattr(company, "keys") else company
    return [company["nom"]] + ([company["enseigne"]] if "enseigne" in keys and company["enseigne"] else [])


def same_company(company, place):
    """Même entreprise : même lieu et noms distinctifs recoupés (nom légal ou enseigne)."""
    return any(same_name_and_place(n, company, place) for n in company_names(company))


def same_name_and_place(name, company, place):
    a, b = distinctive(name), distinctive(place["name"])
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
    """Complète, depuis OSM, l'email et/ou le site des entreprises encore à traiter. Retourne le nombre d'entreprises complétées."""
    by_token = {}
    for p in con.execute("SELECT * FROM osm_places").fetchall():
        for t in distinctive(p["name"]):
            by_token.setdefault(t, []).append(p)
    n = 0
    rows = con.execute(
        "SELECT * FROM companies WHERE status IN ('new','no_email') AND (email IS NULL OR site_url IS NULL OR facebook IS NULL)"
    ).fetchall()
    for c in rows:
        for t in set().union(*(distinctive(n) for n in company_names(c))):
            hit = next((p for p in by_token.get(t, []) if same_company(c, p)
                        and ((p["email"] and not c["email"]) or (p["website"] and not c["site_url"])
                             or (p["facebook"] and not c["facebook"]))), None)
            if not hit:
                continue
            if hit["facebook"] and not c["facebook"]:
                con.execute("UPDATE companies SET facebook=? WHERE siren=?", (hit["facebook"], c["siren"]))
            if not ((hit["email"] and not c["email"]) or (hit["website"] and not c["site_url"])):
                n += 1
                break  # seulement la page Facebook : rien à retester
            if hit["email"] and not c["email"]:
                con.execute("UPDATE companies SET email=?, email_source='osm' WHERE siren=?", (hit["email"], c["siren"]))
            if hit["website"] and not c["site_url"]:
                con.execute("UPDATE companies SET site_url=? WHERE siren=?", (hit["website"], c["siren"]))
            con.execute("UPDATE companies SET status='new' WHERE siren=?", (c["siren"],))  # à (re)tester
            n += 1
            break
    con.commit()
    return n
