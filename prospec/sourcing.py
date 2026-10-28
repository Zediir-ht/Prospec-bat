"""Récupère les entreprises du bâtiment de l'Aveyron via l'API officielle Recherche d'entreprises."""
import random
import time
from datetime import datetime, timedelta

import requests

from . import config, db

API = "https://recherche-entreprises.api.gouv.fr/search"
ENTREPRENEUR_INDIVIDUEL = "1000"


def metier_for(naf):
    return config.NAF_METIERS.get(naf) or config.METIERS.get(naf[:5]) or "entreprise"


def enseigne_of(siege, nom):
    """Nom commercial affiché par l'établissement (« Plomberie du Rouergue »), s'il diffère du nom légal."""
    candidates = list(siege.get("liste_enseignes") or []) + [siege.get("nom_commercial") or ""]
    for e in candidates:
        e = (e or "").strip()
        if e and e.lower() not in nom.lower():
            return e.title()
    return ""


def parse_result(r):
    siege = r.get("siege") or {}
    naf = r.get("activite_principale") or siege.get("activite_principale") or ""
    dirigeant = ""
    for d in r.get("dirigeants") or []:
        if d.get("type_dirigeant") == "personne physique":
            dirigeant = f"{(d.get('prenoms') or '').split(',')[0].title()} {(d.get('nom') or '').title()}".strip()
            break
    nom = r.get("nom_complet") or r.get("nom_raison_sociale") or ""
    return {
        "siren": r["siren"],
        "nom": nom,
        "enseigne": enseigne_of(siege, nom),
        "commune": (siege.get("libelle_commune") or "").title(),
        "code_postal": siege.get("code_postal") or "",
        "naf": naf,
        "metier": metier_for(naf),
        "dirigeant": dirigeant,
        "effectif": r.get("tranche_effectif_salarie") or "",
        "nature_juridique": str(r.get("nature_juridique") or ""),
    }


def fetch_naf(naf, dept, session=None, max_pages=40):
    session = session or requests.Session()
    page = 1
    while page <= max_pages:
        resp = session.get(
            API,
            params={
                "departement": dept,
                "activite_principale": naf,
                "etat_administratif": "A",
                "per_page": 25,
                "page": page,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        for r in data.get("results", []):
            yield parse_result(r)
        if page >= data.get("total_pages", 1):
            break
        page += 1
        time.sleep(0.25)  # limite API : ~7 requêtes/s


def pool_size(con):
    return con.execute("SELECT COUNT(*) FROM companies WHERE status='new'").fetchone()[0]


def refresh_days():
    return int(config.env("SOURCE_REFRESH_DAYS", "7"))


def next_refresh(con):
    """Date du prochain passage sur toutes les catégories (pour les entreprises créées depuis), ou None
    tant que le passage en cours n'est pas terminé. Note la date de fin du passage la première fois."""
    if con.execute("SELECT COUNT(*) FROM sourced").fetchone()[0] < len(config.DEPARTEMENTS) * len(config.NAF_CODES):
        return None
    full = db.get_setting(con, "sourced_full_at")
    if not full:
        full = datetime.now().isoformat(timespec="seconds")
        db.set_setting(con, "sourced_full_at", full)
    return datetime.fromisoformat(full) + timedelta(days=refresh_days())


def refresh_if_due(con):
    """Toutes les SOURCE_REFRESH_DAYS jours (7 par défaut), reprend toutes les catégories : seules les
    entreprises encore inconnues sont ajoutées. Retourne True si un nouveau passage commence."""
    due = next_refresh(con)
    if due is None or datetime.now() < due:
        return False
    con.execute("DELETE FROM sourced")
    db.set_setting(con, "sourced_full_at", "")
    return True


def source(con, session=None, min_pool=300):
    """Récupère les entreprises par (département, code NAF) dans un ordre mélangé, Aveyron d'abord, et
    s'arrête dès que `min_pool` entreprises restent à tester : inutile de tout télécharger."""
    refresh_if_due(con)
    done = {(r["dept"], r["naf"]) for r in con.execute("SELECT dept, naf FROM sourced")}
    added = 0
    for dept in config.DEPARTEMENTS:
        codes = [n for n in config.NAF_CODES if (dept, n) not in done]
        random.shuffle(codes)
        for naf in codes:
            if pool_size(con) >= min_pool:
                return added
            for c in fetch_naf(naf, dept, session):
                c.setdefault("enseigne", "")
                cur = con.execute(
                    """INSERT OR IGNORE INTO companies
                       (siren, nom, enseigne, commune, code_postal, naf, metier, dirigeant, effectif, nature_juridique)
                       VALUES (:siren,:nom,:enseigne,:commune,:code_postal,:naf,:metier,:dirigeant,:effectif,:nature_juridique)""",
                    c,
                )
                added += cur.rowcount
                if not cur.rowcount and c["enseigne"]:  # entreprise déjà connue : on complète son enseigne
                    con.execute("UPDATE companies SET enseigne=? WHERE siren=? AND COALESCE(enseigne,'')=''",
                                (c["enseigne"], c["siren"]))
            con.execute("INSERT OR IGNORE INTO sourced(dept, naf) VALUES (?, ?)", (dept, naf))
            con.commit()
    return added
