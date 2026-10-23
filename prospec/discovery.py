"""Recherche par métier et par ville (« plomberie Rodez ») : trouve des sites d'entreprises sur le moteur de
recherche et les rattache aux entreprises de la base SIRENE, par leur numéro SIREN (mentions légales) ou,
à défaut, par leur nom dans l'adresse du site. Le site rattaché est ensuite lu par la qualification."""
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urlparse

import requests

from . import config
from .osm import company_names, distinctive
from .qualify import DIRECTORIES, fetch, norm, search_urls, thread_session

# SIREN (9 chiffres) ou SIRET (14), avec ou sans espaces : « 123 456 789 00012 »
SIREN_RE = re.compile(r"(?<!\d)(\d{3})[ . ]?(\d{3})[ . ]?(\d{3})(?:[ . ]?\d{5})?(?!\d)")
LEGAL_PATHS = ("/mentions-legales", "/mentions-legales.html", "/mentions-legales/", "/mentions_legales")
MAX_SITES_PER_QUERY = 10


def next_queries(con, n):
    """Couples (métier, commune) à chercher : là où il reste le plus d'entreprises sans site connu, Aveyron d'abord."""
    rows = con.execute(
        "SELECT metier, commune, COUNT(*) AS n, MAX(code_postal LIKE '12%') AS aveyron FROM companies "
        "WHERE status IN ('new','no_email') AND site_url IS NULL AND metier IS NOT NULL AND commune <> '' "
        "GROUP BY metier, commune ORDER BY aveyron DESC, n DESC, commune"
    ).fetchall()
    done = {r[0] for r in con.execute("SELECT query FROM discovered")}
    out = []
    for r in rows:
        q = f"{r['metier']} {r['commune']}"
        if q not in done:
            out.append((q, r["metier"], r["commune"]))
            if len(out) >= n:
                break
    return out


def inspect(url):
    """Lit l'accueil et les mentions légales d'un site (dans un fil). Retourne {site, host, sirens} ou None."""
    session = thread_session()
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    try:
        final, html = fetch(base, session)
    except requests.RequestException:
        return None
    texts = [html]
    for path in LEGAL_PATHS:
        try:
            texts.append(fetch(base + path, session)[1])
            break
        except requests.RequestException:
            pass
    text = " ".join(texts)
    return {"site": base, "host": p.netloc.lower(), "sirens": {"".join(m.groups()) for m in SIREN_RE.finditer(text)}}


def match_site(info, by_siren, candidates):
    """L'entreprise à qui appartient ce site : SIREN affiché (certain), sinon un seul nom reconnu dans l'adresse."""
    for s in info["sirens"]:
        if s in by_siren:
            return by_siren[s]
    host = norm(info["host"])
    hits = [c for c in candidates
            if any(len(t) >= 4 and t in host for n in company_names(c) for t in distinctive(n))]
    return hits[0] if len(hits) == 1 else None


def run(con, max_queries=10, workers=None, stop=None, log=None):
    """Lance jusqu'à `max_queries` recherches par métier et ville. Retourne (recherches faites, sites rattachés)."""
    workers = workers or int(config.env("WORKERS", "20"))
    by_siren = {r["siren"]: r for r in con.execute(
        "SELECT * FROM companies WHERE status IN ('new','no_email') AND site_url IS NULL").fetchall()}
    done = linked = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for query, metier, commune in next_queries(con, max_queries):
            if stop and stop():
                break
            try:
                urls = search_urls(metier, commune, thread_session())
            except requests.RequestException:
                continue  # moteur indisponible : la recherche sera refaite plus tard
            sites = []
            for u in urls:
                host = urlparse(u).netloc.lower()
                if host and not any(d in host for d in DIRECTORIES) and host not in {urlparse(s).netloc for s in sites}:
                    sites.append(u)
            candidates = [c for c in by_siren.values() if norm(c["commune"]) == norm(commune) and c["metier"] == metier]
            for info in pool.map(inspect, sites[:MAX_SITES_PER_QUERY]):
                c = match_site(info, by_siren, candidates) if info else None
                if not c:
                    continue
                con.execute("UPDATE companies SET site_url=?, status='new' WHERE siren=?", (info["site"], c["siren"]))
                by_siren.pop(c["siren"], None)
                candidates = [x for x in candidates if x["siren"] != c["siren"]]
                linked += 1
                print(f"{query} -> {info['site']} = {c['nom']}")
            con.execute("INSERT OR REPLACE INTO discovered VALUES (?, ?)", (query, datetime.now().isoformat()))
            con.commit()
            done += 1
            if log:
                log(f"recherche « {query} » : {linked} sites rattachés")
    return done, linked
