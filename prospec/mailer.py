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
Ton : chaleureux, simple et respectueux, comme un voisin sympa qui connaît la région. Le sourire vient de la légèreté du ton et, au plus, d'UN clin d'œil bienveillant sur le métier, la commune ou l'Aveyron, ou d'une petite autodérision de Corentin.
Interdit : plaisanter sur le site ou l'entreprise elle-même (ancienneté, défauts, absence de site), l'ironie, les sous-entendus, tout ce qui peut sembler moqueur, condescendant ou donneur de leçon. Le constat se dit simplement et gentiment, comme une observation utile, jamais comme un reproche : on reconnaît d'abord ce qui fonctionne (le travail, la réputation, la page déjà en place).
Règles strictes :
- 4 à 6 phrases courtes, vouvoiement, aucun jargon, pas de ton publicitaire ni de superlatifs.
- Commence par "Bonjour" suivi du prénom du dirigeant s'il est fourni, sinon "Bonjour,".
- Évite les formules toutes faites ("Je me permets de vous contacter", "Aujourd'hui, de nombreux clients…", "N'hésitez pas") : chaque mail doit avoir sa propre accroche et sa propre tournure.
- Mentionne le métier et la commune, et UN constat précis fourni (sans l'exagérer ni l'inventer).
- Bénéfice concret : être trouvé par les clients de la région qui cherchent leur activité sur internet depuis leur téléphone.
- Propose de préparer une maquette gratuite de leur site, sans engagement, et demande simplement si ça les intéresse.
- L'objet est court, sympathique et donne envie d'ouvrir (pas de majuscules abusives, pas de point d'exclamation en série).
- N'indique AUCUN prix, tarif ou montant.
- Ne mets ni signature ni formule de désinscription : elles sont ajoutées automatiquement.
Les informations sur l'entreprise sont fournies en JSON."""

FORMAT_SINGLE = "\nRéponds en deux parties séparées par un saut de ligne : la première ligne est l'objet du mail (court, sans majuscules abusives), puis le corps."


def followup_mail(c):
    """Relance par défaut (modifiable à l'écran), dans le même fil que le premier mail."""
    salut = f"Bonjour {c['dirigeant'].split()[0]}," if c.get("dirigeant") else "Bonjour,"
    body = (
        f"{salut}\n\nPetit retour vers vous, au cas où mon message de la semaine dernière aurait été noyé dans le courrier. "
        f"La proposition tient toujours : une maquette gratuite de votre site, sans engagement, juste pour voir ce que ça donnerait.\n\n"
        f"Si ce n'est pas le moment, aucun souci : un simple « non merci » et je vous laisse tranquille."
    )
    first = (c.get("subject") or "").strip()
    return (f"Re : {first}" if first else f"Re : Un site pour {c['nom']} ?"), body


FOLLOWUP_SYSTEM = """Tu rédiges une RELANCE courte, en français, pour Corentin Mayrand, créateur de sites web, à destination d'une entreprise
locale qui n'a pas répondu à son premier mail (fourni ci-dessous) il y a environ une semaine.
Règles strictes :
- 2 à 4 phrases, vouvoiement, ton jovial et léger avec une pointe d'humour bienveillant, jamais insistant, culpabilisant ni moqueur.
- Commence par "Bonjour" suivi du prénom du dirigeant s'il est fourni, sinon "Bonjour,".
- Ne répète pas le premier mail : rappelle simplement la maquette gratuite et sans engagement, avec un petit élément nouveau
  (une question simple, ou l'idée qu'un site se consulte surtout sur téléphone).
- Dis que ce n'est pas grave si ce n'est pas le moment.
- N'indique AUCUN prix, tarif ou montant. Ne mets ni signature ni formule de désinscription.
- L'objet commence par "Re : " suivi de l'objet du premier mail."""


def batch_followup_prompt(companies):
    """Demande à coller dans Claude (claude.ai) pour rédiger plusieurs relances d'un coup."""
    data = json.dumps([
        {**describe(c), "premier_mail_objet": c.get("subject") or "", "premier_mail_texte": c.get("body") or ""} for c in companies
    ], ensure_ascii=False, indent=1)
    return (
        FOLLOWUP_SYSTEM
        + "\n\nRédige une relance DIFFÉRENTE et personnalisée pour chacune des entreprises ci-dessous."
        + " Réponds uniquement avec un tableau JSON, sans aucun autre texte, de la forme :"
        + ' [{"siren": "...", "subject": "objet", "body": "corps de la relance"}]'
        + "\nLes retours à la ligne du corps s'écrivent \\n dans le JSON."
        + "\n\nEntreprises :\n" + data
    )


def facebook_message(c):
    """Message Facebook à envoyer à la main (copier-coller), sur le même ton que les mails. Trois tournures,
    choisies d'après le SIREN pour varier d'une entreprise à l'autre."""
    prenom = (c.get("dirigeant") or "").split()
    salut = f"Bonjour {prenom[0]}," if prenom else "Bonjour,"
    metier, commune = c.get("metier") or "votre activité", c.get("commune") or "dans le coin"
    issues = (c.get("site_issues") or "").split(";")[0].strip()
    if c.get("site_status") == "outdated" and issues:
        constat = f"En regardant votre site, j'ai remarqué un point qui pourrait être amélioré : {issues}."
        lead = "un site à jour aide les clients qui vous cherchent depuis leur téléphone à vous choisir"
    else:
        constat = f"En cherchant « {metier} {commune} », j'ai trouvé votre page Facebook… mais pas de site internet."
        lead = "tout le monde ne pense pas à fouiller Facebook pour trouver un pro"
    variants = [
        f"{salut}\n\nCorentin, créateur de sites internet en Aveyron (zdrdev.fr). {constat} Or {lead}, "
        f"et c'est souvent sur Google que tout commence.\n\nJe vous propose de vous préparer une maquette "
        f"gratuite de votre site, sans engagement : ça vous dirait d'y jeter un œil ?\n\nEt si ce n'est pas le moment, "
        f"un simple « non merci » suffit, promis je ne reviendrai pas frapper à la porte 😊",
        f"{salut}\n\nPetit message d'un voisin du web : je m'appelle Corentin et je crée des sites pour les pros du coin "
        f"(zdrdev.fr). {constat} Or {lead}.\n\nJe peux vous préparer une maquette gratuite, sans engagement, "
        f"pour voir ce que ça donnerait. Ça vous tente ?\n\nSi la réponse est non, aucun souci, je ne vous embêterai plus.",
        f"{salut}\n\nJe suis Corentin, je fabrique des sites internet pour les entreprises de l'Aveyron et d'à côté (zdrdev.fr). "
        f"{constat} Votre page fait déjà le travail auprès des habitués, mais {lead}.\n\nJe vous propose une maquette "
        f"gratuite de votre site, sans engagement, juste pour le plaisir des yeux. Ça vous intéresse ?\n\nUn « non merci » me va "
        f"très bien aussi, je ne relancerai pas.",
    ]
    return variants[int(re.sub(r"\D", "", c.get("siren") or "0") or 0) % len(variants)]


def messenger_link(page):
    """Lien qui ouvre directement la conversation Messenger avec la page, quand elle a un nom d'utilisateur."""
    slug = (page or "").rsplit("facebook.com/", 1)[-1]
    if not slug or "/" in slug or "?" in slug:
        return page
    return f"https://m.me/{slug}"


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


def check_mail(subject, body, min_len=80):
    text = f"{subject}\n{body}".lower()
    if not subject or len(body) < min_len:
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


BATCH_INTRO = (
    SYSTEM
    + "\n\nTu reçois ci-dessous une liste d'entreprises. Rédige un mail DIFFÉRENT et personnalisé pour chacune."
    + " Réponds uniquement avec un tableau JSON, sans aucun autre texte, de la forme :"
    + ' [{"siren": "...", "subject": "objet", "body": "corps du mail"}]'
    + "\nDans le JSON, l'objet est dans \"subject\" (pas de ligne séparée) et les retours à la ligne du corps s'écrivent \\n."
    + "\nIl doit y avoir exactement un élément par entreprise, dans le même ordre, sans en oublier."
)


def batch_prompt(companies):
    """Demande à coller dans Claude (claude.ai) pour rédiger plusieurs mails d'un coup."""
    data = json.dumps([describe(c) for c in companies], ensure_ascii=False, indent=1)
    return BATCH_INTRO + "\n\nEntreprises :\n" + data


def prompt_parts(companies):
    """(consigne, entreprises) : le dashboard assemble lui-même la demande de chaque lot, sans la répéter dans la page."""
    return BATCH_INTRO, [describe(c) for c in companies]


def parse_batch(text, allowed, min_len=80):
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
            ok[siren] = check_mail(str(it.get("subject", "")).strip(), str(it.get("body", "")).strip(), min_len)
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


def build_message(to, subject, body, source=None, thread_ids=None):
    s = config.sender()
    m = EmailMessage()
    m["From"] = f"{s['prenom']} {s['nom']} <{s['email']}>"
    m["To"] = to
    m["Subject"] = subject
    m["Date"] = formatdate(localtime=True)
    m["Message-ID"] = make_msgid(domain=s["email"].split("@")[-1])
    m["List-Unsubscribe"] = f"<mailto:{s['email']}?subject=STOP>"
    if thread_ids:  # relance : répond au premier mail, pour rester dans le même fil
        m["In-Reply-To"] = thread_ids[-1]
        m["References"] = " ".join(thread_ids)
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
