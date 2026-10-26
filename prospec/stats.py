"""Statistiques de réponse : quels métiers, communes, constats et jours donnent des réponses."""
from collections import defaultdict
from datetime import datetime

CONTACTED = ("sent", "followed_up", "replied", "refused", "bounced")
DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
ISSUES = [("HTTPS", "Site non sécurisé"), ("téléphones", "Pas adapté au mobile"), ("ancien", "Site ancien"),
          ("ne répond pas", "Site en panne"), ("obsolète", "Technologie obsolète")]


def issue_labels(site_status, site_issues):
    if site_status == "none":
        return ["Pas de site"]
    labels = [label for key, label in ISSUES if key in (site_issues or "")]
    return labels or ["Site à refaire"]


def compute(con):
    """Retourne {"total": {...}, "groups": [(titre, [ligne, ...]), ...]}. Une ligne : label, sent, replied, stop, rate.
    Les mails revenus en erreur ne comptent pas : ils n'ont jamais été reçus."""
    rows = con.execute(
        f"SELECT status, metier, commune, site_status, site_issues, email_source, contacted_at FROM companies "
        f"WHERE contacted_at IS NOT NULL AND status IN {CONTACTED}").fetchall()
    rows = [r for r in rows if r["status"] != "bounced"]
    groups = {t: defaultdict(lambda: [0, 0, 0]) for t in ("Constat sur le site", "Métier", "Commune", "Jour d'envoi", "Origine de l'adresse")}

    def add(title, label, status):
        g = groups[title][label]
        g[0] += 1
        g[1] += status == "replied"
        g[2] += status == "refused"

    for r in rows:
        for label in issue_labels(r["site_status"], r["site_issues"]):
            add("Constat sur le site", label, r["status"])
        add("Métier", r["metier"] or "autre", r["status"])
        add("Commune", r["commune"] or "inconnue", r["status"])
        try:
            add("Jour d'envoi", DAYS[datetime.fromisoformat(r["contacted_at"]).weekday()], r["status"])
        except ValueError:
            pass
        add("Origine de l'adresse", {"site": "Site de l'entreprise", "osm": "OpenStreetMap"}.get(r["email_source"], "Autre"), r["status"])
    out = []
    for title, g in groups.items():
        lines = [{"label": k, "sent": v[0], "replied": v[1], "stop": v[2], "rate": round(100 * v[1] / v[0]) if v[0] else 0}
                 for k, v in g.items()]
        lines.sort(key=lambda x: (-x["rate"], -x["sent"]) if title == "Jour d'envoi" else (-x["sent"], -x["rate"]))
        if title == "Jour d'envoi":
            lines.sort(key=lambda x: DAYS.index(x["label"]))
        out.append((title, lines[:8]))
    replied = sum(r["status"] == "replied" for r in rows)
    stop = sum(r["status"] == "refused" for r in rows)
    bounced = con.execute("SELECT COUNT(*) FROM companies WHERE status='bounced'").fetchone()[0]
    return {"total": {"sent": len(rows), "replied": replied, "stop": stop, "bounced": bounced,
                      "rate": round(100 * replied / len(rows)) if rows else 0}, "groups": out}
