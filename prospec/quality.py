"""Qualité des adresses d'après les retours en erreur déjà constatés : quels types d'adresses sont introuvables."""
import re
from datetime import datetime

from . import config

CONTACTED = ("sent", "followed_up", "replied", "refused", "bounced")
SOURCES = {"site": "site de l'entreprise", "osm": "OpenStreetMap"}


def address_class(row):
    """Type d'adresse : origine · domaine de l'entreprise ou messagerie perso · état du site."""
    email = (row["email"] or "").lower()
    kind = "messagerie perso" if email.rsplit("@", 1)[-1] in config.FREE_MAIL_DOMAINS else "domaine de l'entreprise"
    if row["site_status"] == "none":
        site = "sans site"
    else:
        m = re.search(r"mise à jour affichée : (\d{4})", row["site_issues"] or "")
        site = "site ancien" if m and datetime.now().year - int(m.group(1)) >= 5 else "site actuel"
    return f"{SOURCES.get(row['email_source'], 'autre origine')} · {kind} · {site}"


def bounce_table(con):
    """[(type d'adresse, mails partis, en erreur, taux %, mis de côté)] pour les types déjà envoyés, du pire au meilleur."""
    counts = {}
    for r in con.execute("SELECT status, email, email_source, site_status, site_issues FROM companies "
                         f"WHERE contacted_at IS NOT NULL AND email IS NOT NULL AND status IN {CONTACTED}"):
        c = counts.setdefault(address_class(r), [0, 0])
        c[0] += 1
        c[1] += r["status"] == "bounced"
    limit, minimum = float(config.env("BOUNCE_LIMIT", "20")), int(config.env("BOUNCE_MIN_SENT", "10"))
    lines = [(k, v[0], v[1], round(100 * v[1] / v[0]), v[0] >= minimum and 100 * v[1] / v[0] >= limit)
             for k, v in counts.items()]
    return sorted(lines, key=lambda x: (-x[3], -x[1]))


def risky_classes(con):
    """Types d'adresses qui reviennent trop souvent en erreur (BOUNCE_LIMIT % à partir de BOUNCE_MIN_SENT mails) :
    elles ne sont plus proposées à la rédaction. ALLOW_RISKY=1 pour tout garder."""
    if config.env("ALLOW_RISKY", "0") == "1":
        return set()
    return {line[0] for line in bounce_table(con) if line[4]}
