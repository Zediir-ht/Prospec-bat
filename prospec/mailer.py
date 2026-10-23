"""Rédaction des mails par Claude (API ou collage manuel) et dépôt en brouillon / envoi via Gmail."""
import imaplib
import json
import re
import smtplib
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from . import config

MODEL = "claude-haiku-5-5"

ANGLES = {
    "none": "L'entreprise n'a pas de site internet que l'on trouve en ligne.",
    "outdated": "L'entreprise a un site, mais il a des défauts : {issues}.",
    "ok": "L'entreprise a un site correct.",
}

SYSTEM = """Tu rédiges un mail de prospection à froid, en français, pour Corentin Mayrand, créateur de sites web (zdrdev.fr), à destination d'une entreprise locale d'Aveyron ou des départements voisins (artisan, commerçant, restaurateur, bâtiment, services).
Règles strictes :
- 4 à 6 phrases, ton direct, courtois, vouvoiement, aucun jargon, pas de ton publicitaire.
- Commence par "Bonjour" suivi du prénom du dirigeant s'il est fourni, sinon "Bonjour,".
- Mentionne le métier et la commune, et UN constat précis fourni (sans l'exagérer ni l'inventer).
- Bénéfice concret : être trouvé par les clients de la région qui cherchent leur activité sur internet depuis leur téléphone.
- Propose de préparer une maquette gratuite de leur site, sans engagement, et demande si ça les intéresse.
- N'indique AUCUN prix, tarif ou montant.
- Ne mets ni signature ni formule de désinscription : elles sont ajoutées automatiquement.
Les informations sur l'entreprise sont fournies en JSON."""

FORMAT_SINGLE = "\nRéponds en deux parties séparées par un saut de ligne : la première ligne est l'objet du mail (court, sans majuscules abusives), puis le corps."


def followup_mail(c):
    salut = f"Bonjour {c['dirigeant'].split()[0]}," if c.get("dirigeant") else "Bonjour,"
    body = (
        f"{salut}\n\nJe me permets de revenir vers vous suite à mon message de la semaine dernière. "
        f"Ma proposition reste la même : une maquette gratuite de votre site, sans engagement.\n\n"
        f"Si ce n'est pas le bon moment, aucun souci, il vous suffit de me le dire."
    )
    return f"Re : Un site pour {c['nom']} ?", body


def describe(c):
    angle = ANGLES.get(c["site_status"], "").format(issues=c.get("site_issues", ""))
    return {
        "siren": c["siren"], "entreprise": c.get("enseigne") or c["nom"],
        "raison_sociale": c["nom"], "commune": c["commune"], "activite": c["metier"],
        "dirigeant": c.get("dirigeant") or "inconnu", "constat": angle,
    }


def claude_mail(c):
    """Rédige un mail via l'API Claude (nécessite ANTHROPIC_API_KEY). Retourne (objet, corps)."""
    import requests

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": config.env("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01"},
        json={"model": MODEL, "max_tokens": 600, "system": SYSTEM + FORMAT_SINGLE,
              "messages": [{"role": "user", "content": json.dumps(describe(c), ensure_ascii=False)}]},
        timeout=60,
    )
    resp.raise_for_status()
    subject, _, body = resp.json()["content"][0]["text"].strip().partition("\n")
    return check_mail(subject.strip().strip('"'), body.strip())


FORBIDDEN = ("€", "euro", "tarif", "prix", "devis gratuit à partir")


def check_mail(subject, body):
    text = f"{subject}\n{body}".lower()
    if not subject or len(body) < 80:
        raise ValueError("mail vide ou trop court")
    if any(w in text for w in FORBIDDEN):
        raise ValueError("le mail mentionne un prix")
    return subject, body


def compose(c):
    """Mail rédigé par Claude pour cette entreprise, ou None si la rédaction automatique est indisponible."""
    if not config.env("ANTHROPIC_API_KEY"):
        return None
    try:
        return claude_mail(c)
    except Exception as exc:
        print(f"  ! rédaction impossible pour {c['nom']} ({exc}), mail non préparé")
        return None


def batch_prompt(companies):
    """Demande à coller dans Claude (claude.ai) pour rédiger plusieurs mails d'un coup."""
    data = json.dumps([describe(c) for c in companies], ensure_ascii=False, indent=1)
    return (
        SYSTEM
        + "\n\nTu reçois ci-dessous une liste d'entreprises. Rédige un mail DIFFÉRENT et personnalisé pour chacune."
        + " Réponds uniquement avec un tableau JSON, sans aucun autre texte, de la forme :"
        + ' [{"siren": "...", "subject": "objet", "body": "corps du mail"}]'
        + "\nDans le JSON, l'objet est dans \"subject\" (pas de ligne séparée) et les retours à la ligne du corps s'écrivent \\n."
        + "\n\nEntreprises :\n" + data
    )


def parse_batch(text, allowed):
    """Lit la réponse de Claude. Retourne (mails valides {siren: (objet, corps)}, liste d'erreurs)."""
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return {}, ["aucun tableau JSON trouvé dans la réponse"]
    try:
        items = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        return {}, [f"JSON invalide : {exc}"]
    ok, errors = {}, []
    for it in items if isinstance(items, list) else []:
        siren = str(it.get("siren", "")) if isinstance(it, dict) else ""
        if siren not in allowed:
            errors.append(f"entreprise inconnue ou déjà traitée : {siren or '?'}")
            continue
        try:
            ok[siren] = check_mail(str(it.get("subject", "")).strip(), str(it.get("body", "")).strip())
        except ValueError as exc:
            errors.append(f"{allowed[siren]} : {exc}")
    return ok, errors


SOURCES = {"site": "sur le site web de votre entreprise", "osm": "dans OpenStreetMap, où elle est publiée pour votre entreprise"}


def assert_sourced(row):
    """Refuse tout envoi vers une adresse dont l'origine n'est pas connue : jamais d'adresse devinée."""
    if not row["email"] or row["email_source"] not in SOURCES:
        raise ValueError(f"adresse non sourcée pour {row['nom']} : envoi refusé")


def format_phone(tel):
    """« 0632915377 » ou « +33632915377 » -> « 06 32 91 53 77 »."""
    digits = re.sub(r"\D", "", tel or "")
    if digits.startswith("33") and len(digits) == 11:
        digits = "0" + digits[2:]
    if len(digits) == 10:
        return " ".join(digits[i:i + 2] for i in range(0, 10, 2))
    return (tel or "").strip()


def signature(source=None):
    s = config.sender()
    lines = ["", "Cordialement,", "", f"{s['prenom']} {s['nom']}", "Création de sites web en Aveyron"]
    if s["site"]:
        lines.append(f"Site : {s['site']}")
    if s["tel"]:
        lines.append(f"Tél. : {format_phone(s['tel'])}")
    lines.append(f"Mail : {s['email']}")
    lines += [
        "",
        "--",
        "Vous recevez ce message à titre professionnel"
        + (f" : j'ai trouvé votre adresse {SOURCES[source]}." if source in SOURCES else ".")
        + " Si ce n'est pas pertinent pour vous, répondez simplement STOP : je ne vous écrirai plus.",
    ]
    if s["legal"]:
        lines.append(s["legal"])
    return "\n".join(lines)


def build_message(to, subject, body, source=None):
    s = config.sender()
    m = EmailMessage()
    m["From"] = f"{s['prenom']} {s['nom']} <{s['email']}>"
    m["To"] = to
    m["Subject"] = subject
    m["Date"] = formatdate(localtime=True)
    m["Message-ID"] = make_msgid(domain=s["email"].split("@")[-1])
    m["List-Unsubscribe"] = f"<mailto:{s['email']}?subject=STOP>"
    m.set_content(body + "\n" + signature(source))
    return m


def save_draft(msg):
    s = config.sender()
    with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
        imap.login(s["email"], config.env("GMAIL_APP_PASSWORD"))
        imap.append("[Gmail]/Drafts", "\\Draft", imaplib.Time2Internaldate(time.time()), msg.as_bytes())


def send(msg):
    s = config.sender()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(s["email"], config.env("GMAIL_APP_PASSWORD"))
        smtp.send_message(msg)


def deliver(msg, mode):
    (send if mode == "send" else save_draft)(msg)
