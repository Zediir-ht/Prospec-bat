"""Détecte si une entreprise a un site web, son état, et une adresse email de contact."""
import re
import unicodedata
from datetime import datetime
from urllib.parse import parse_qs, quote_plus, urlparse

import requests

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


def search_urls(nom, commune, session):
    q = quote_plus(f"{nom} {commune}")
    r = session.get(f"https://html.duckduckgo.com/html/?q={q}", headers=UA, timeout=20)
    urls = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"', r.text):
        href = m.group(1)
        if "uddg=" in href:
            href = parse_qs(urlparse(href).query).get("uddg", [href])[0]
        urls.append(href)
    return urls


def extract_emails(html):
    found = []
    for e in EMAIL_RE.findall(html):
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
    r = session.get(url, headers=UA, timeout=15, allow_redirects=True)
    r.raise_for_status()
    return r.url, r.text


def qualify_company(row, session=None):
    """row: dict avec nom, commune. Retourne dict site_url, site_status, site_issues, email."""
    session = session or requests.Session()
    try:
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
    for path in ("/contact", "/mentions-legales"):
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
