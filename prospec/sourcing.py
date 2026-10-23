"""Récupère les entreprises du bâtiment de l'Aveyron via l'API officielle Recherche d'entreprises."""
import time

import requests

from . import config

API = "https://recherche-entreprises.api.gouv.fr/search"
ENTREPRENEUR_INDIVIDUEL = "1000"


def metier_for(naf):
    return config.NAF_METIERS.get(naf) or config.METIERS.get(naf[:5]) or "entreprise"


def parse_result(r):
    siege = r.get("siege") or {}
    naf = r.get("activite_principale") or siege.get("activite_principale") or ""
    dirigeant = ""
    for d in r.get("dirigeants") or []:
        if d.get("type_dirigeant") == "personne physique":
            dirigeant = f"{(d.get('prenoms') or '').split(',')[0].title()} {(d.get('nom') or '').title()}".strip()
            break
    return {
        "siren": r["siren"],
        "nom": r.get("nom_complet") or r.get("nom_raison_sociale") or "",
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


def source(con, session=None, max_other=30):
    """Récupère les entreprises par (département, code NAF). L'Aveyron (1er département) est traité en
    entier ; les autres départements avancent de `max_other` requêtes par appel, pour ne pas bloquer."""
    done = {(r["dept"], r["naf"]) for r in con.execute("SELECT dept, naf FROM sourced")}
    added = other = 0
    for dept in config.DEPARTEMENTS:
        for naf in config.NAF_CODES:
            if (dept, naf) in done:
                continue
            if dept != config.DEPARTEMENTS[0]:
                if other >= max_other:
                    return added
                other += 1
            for c in fetch_naf(naf, dept, session):
                cur = con.execute(
                    """INSERT OR IGNORE INTO companies
                       (siren, nom, commune, code_postal, naf, metier, dirigeant, effectif, nature_juridique)
                       VALUES (:siren,:nom,:commune,:code_postal,:naf,:metier,:dirigeant,:effectif,:nature_juridique)""",
                    c,
                )
                added += cur.rowcount
            con.execute("INSERT OR IGNORE INTO sourced(dept, naf) VALUES (?, ?)", (dept, naf))
            con.commit()
    return added
