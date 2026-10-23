"""Détecte si une entreprise a un site web, son état, et une adresse email de contact."""
import html as htmllib
import re
import threading
import time
import unicodedata
from datetime import datetime
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests

from . import config

UA = {"User-Agent": "Mozilla/5.0 (compatible; prospec-bat/1.0)"}

# Annuaires et réseaux sociaux : ce ne sont pas le site de l'entreprise
DIRECTORIES = (
    "pagesjaunes", "societe.com", "pappers", "verif.com", "infogreffe", "facebook", "instagram",
    "linkedin", "youtube", "google", "mappy", "kompass", "manageo", "entreprises.lefigaro",
    "annuaire-entreprises", "indeed", "cylex", "118218", "starofservice", "houzz", "travaux.com",
    "batiweb", "artisans", "twitter", "tiktok", "bing", "duckduckgo", "wikipedia", "societeinfo",
    "bfmtv", "lefigaro", "ouest-france", "midilibre", "ladepeche", "centrepresseaveyron",
)
BAD_EMAIL_PARTS = ("example.", "sentry", "wixpress", "domain.", "votre", "email@", ".png", ".jpg", ".webp", ".gif")
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s)


def name_tokens(nom):
    stop = {"sarl", "sas", "sasu", "eurl", "societe", "entreprise", "ets", "etablissements", "groupe", "les", "des", "and"}
    words = re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", nom.lower()).encode("ascii", "ignore").decode())
    return [w for w in words if len(w) >= 4 and w not in stop]


def pick_site(nom, urls):
    """Premier résultat hors annuaires dont le domaine ressemble au nom de l'entreprise."""
    tokens = name_tokens(nom)
    for u in urls:
        host = urlparse(u).netloc.lower()
        if not host or any(d in host for d in DIRECTORIES):
            continue
        h = norm(host)
        if any(t in h for t in tokens):
            return f"{urlparse(u).scheme}://{urlparse(u).netloc}"
    return None


_local = threading.local()
_search = {"lock": threading.Lock(), "last": 0.0, "penalty": 0.0}


def thread_session():
    """Une session HTTP par fil de recherche (requests.Session n'est pas partageable entre threads)."""
    if not hasattr(_local, "session"):
        _local.session = requests.Session()
    return _local.session


def throttle_search():
    """Espace les recherches web de tous les fils : SEARCH_INTERVAL secondes, davantage après un refus."""
    interval = float(config.env("SEARCH_INTERVAL", "1.0")) + _search["penalty"]
    with _search["lock"]:
        wait = _search["last"] + interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _search["last"] = time.monotonic()


def search_feedback(ok):
    """Ralentit automatiquement si le moteur refuse des requêtes, réaccélère quand il répond."""
    with _search["lock"]:
        _search["penalty"] = max(0.0, _search["penalty"] - 0.5) if ok else min(30.0, _search["penalty"] * 2 + 2)


def search_urls(nom, commune, session):
    q = quote_plus(f"{nom} {commune}")
    throttle_search()
    try:
        r = session.get(f"https://html.duckduckgo.com/html/?q={q}", headers=UA, timeout=20)
        r.raise_for_status()
    except requests.RequestException:
        search_feedback(False)
        raise
    search_feedback(True)
    urls = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"', r.text):
        href = m.group(1)
        if "uddg=" in href:
            href = parse_qs(urlparse(href).query).get("uddg", [href])[0]
        urls.append(href)
    return urls


def decode_cloudflare(html):
    """Décode les adresses masquées par Cloudflare (data-cfemail)."""
    out = []
    for h in re.findall(r'data-cfemail="([0-9a-fA-F]+)"', html):
        try:
            key = int(h[:2], 16)
            out.append("".join(chr(int(h[i:i + 2], 16) ^ key) for i in range(2, len(h), 2)))
        except ValueError:
            pass
    return " ".join(out)


def deobfuscate(text):
    """Remet en clair « nom [at] domaine [dot] fr », « nom (arobase) domaine.fr », « nom&#64;domaine.fr »."""
    text = unquote(htmllib.unescape(text))
    text = re.sub(r"\s*[\[\(\{]\s*(?:at|arobase)\s*[\]\)\}]\s*", "@", text, flags=re.I)
    text = re.sub(r"\s*[\[\(\{]\s*(?:dot|point)\s*[\]\)\}]\s*", ".", text, flags=re.I)
    return text


def extract_emails(html):
    found = []
    for e in EMAIL_RE.findall(deobfuscate(html) + " " + decode_cloudflare(html)):
        e = e.lower().rstrip(".")
        if not any(b in e for b in BAD_EMAIL_PARTS) and e not in found:
            found.append(e)
    return found


def analyse_html(html, url):
    """Retourne (statut, liste de constats) pour la page d'accueil."""
    issues = []
    if not url.startswith("https://"):
        issues.append("le site n'est pas sécurisé (pas de HTTPS)")
    if not re.search(r'<meta[^>]+name=["\']viewport', html, re.I):
        issues.append("le site ne s'adapte pas aux téléphones")
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(20\d{2}|19\d{2})", html, re.I)]
    if years and max(years) <= datetime.now().year - 4:
        issues.append(f"le site semble ancien (dernière mise à jour affichée : {max(years)})")
    if re.search(r"<(frameset|marquee|blink)\b", html, re.I):
        issues.append("le site utilise une technologie obsolète")
    return ("outdated" if issues else "ok"), issues


def best_email(emails, domain):
    own = [e for e in emails if domain and e.endswith(domain.replace("www.", ""))]
    return (own or emails or [None])[0]


def fetch(url, session):
    r = session.get(url, headers=UA, timeout=10, allow_redirects=True)
    r.raise_for_status()
    return r.url, r.text


def places_site(nom, commune, session):
    """Site web de l'entreprise d'après Google Places (clé GOOGLE_PLACES_KEY). Retourne l'URL ou None."""
    r = session.post(
        "https://places.googleapis.com/v1/places:searchText",
        headers={"X-Goog-Api-Key": config.env("GOOGLE_PLACES_KEY"),
                 "X-Goog-FieldMask": "places.displayName,places.websiteUri"},
        json={"textQuery": f"{nom} {commune}", "languageCode": "fr", "regionCode": "FR"},
        timeout=20,
    )
    r.raise_for_status()
    tokens = name_tokens(nom)
    for place in r.json().get("places", []):
        label = norm(place.get("displayName", {}).get("text", ""))
        uri = place.get("websiteUri")
        if uri and any(t in label for t in tokens) and not any(d in uri for d in DIRECTORIES):
            return f"{urlparse(uri).scheme}://{urlparse(uri).netloc}"
    return None


def qualify_company(row, session=None):
    """row: dict avec nom, commune. Retourne dict site_url, site_status, site_issues, email."""
    session = session or thread_session()
    try:
        if row.get("site_url"):  # déjà connu (OpenStreetMap ou recherche précédente) : pas de recherche web
            site = row["site_url"]
        elif config.env("GOOGLE_PLACES_KEY"):
            site = places_site(row["nom"], row["commune"], session)
        else:
            site = pick_site(row["nom"], search_urls(row["nom"], row["commune"], session))
    except requests.RequestException:
        return {"site_url": None, "site_status": "unknown", "site_issues": "", "email": None}
    if not site:
        return {"site_url": None, "site_status": "none", "site_issues": "", "email": None}
    try:
        final_url, html = fetch(site, session)
    except requests.RequestException:
        # le site existe dans les résultats mais ne répond pas : à vérifier à la main
        return {"site_url": site, "site_status": "outdated", "site_issues": "le site ne répond pas actuellement", "email": None}
    status, issues = analyse_html(html, final_url)
    emails = extract_emails(html)
    domain = urlparse(final_url).netloc
    for path in ("/contact", "/contact.html", "/nous-contacter", "/mentions-legales", "/mentions-legales.html", "/a-propos"):
        if emails:
            break
        try:
            _, sub = fetch(site.rstrip("/") + path, session)
            emails = extract_emails(sub)
        except requests.RequestException:
            pass
    return {
        "site_url": final_url,
        "site_status": status,
        "site_issues": "; ".join(issues),
        "email": best_email(emails, domain),
    }
