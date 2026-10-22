"""Rédaction des mails (Claude ou modèle fixe) et dépôt en brouillon / envoi via Gmail."""
import imaplib
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

SYSTEM = """Tu rédiges un mail de prospection à froid, en français, pour Corentin Mayrand, créateur de sites web (zdrdev.fr), à destination d'une entreprise du bâtiment d'Aveyron.
Règles strictes :
- 4 à 6 phrases, ton direct, courtois, vouvoiement, aucun jargon, pas de ton publicitaire.
- Commence par "Bonjour" suivi du prénom du dirigeant s'il est fourni, sinon "Bonjour,".
- Mentionne le métier et la commune, et UN constat précis fourni (sans l'exagérer ni l'inventer).
- Bénéfice concret : être trouvé par les particuliers du secteur qui cherchent leur métier sur internet.
- Propose de préparer une maquette gratuite de leur site, sans engagement, et demande si ça les intéresse.
- N'indique AUCUN prix, tarif ou montant.
- Ne mets ni signature ni formule de désinscription : elles sont ajoutées automatiquement.
Réponds en deux parties séparées par une ligne vide : la première ligne est l'objet du mail (court, sans majuscules abusives), puis le corps."""


def fallback_mail(c):
    salut = f"Bonjour {c['dirigeant'].split()[0]}," if c.get("dirigeant") else "Bonjour,"
    if c["site_status"] == "none":
        constat = f"En cherchant « {c['metier']} {c['commune']} » sur internet, je n'ai pas trouvé de site pour {c['nom']}."
    else:
        constat = f"En regardant le site de {c['nom']}, j'ai remarqué que {c['site_issues'].split(';')[0].strip()}."
    body = (
        f"{salut}\n\n{constat} Aujourd'hui, la plupart des particuliers de {c['commune']} et des environs "
        f"cherchent d'abord un professionnel du bâtiment sur leur téléphone avant d'appeler.\n\n"
        f"Je crée des sites web pour les artisans et entreprises du bâtiment de l'Aveyron. "
        f"Je peux vous préparer une maquette gratuite de votre site, sans engagement, pour que vous voyiez le résultat concrètement.\n\n"
        f"Est-ce que cela vous intéresserait ?"
    )
    return f"Un site pour {c['nom']} ?", body


def followup_mail(c):
    salut = f"Bonjour {c['dirigeant'].split()[0]}," if c.get("dirigeant") else "Bonjour,"
    body = (
        f"{salut}\n\nJe me permets de revenir vers vous suite à mon message de la semaine dernière. "
        f"Ma proposition reste la même : une maquette gratuite de votre site, sans engagement.\n\n"
        f"Si ce n'est pas le bon moment, aucun souci, il vous suffit de me le dire."
    )
    return f"Re : Un site pour {c['nom']} ?", body


def claude_mail(c):
    import anthropic

    client = anthropic.Anthropic()
    angle = ANGLES.get(c["site_status"], "").format(issues=c.get("site_issues", ""))
    user = (
        f"Entreprise : {c['nom']}\nCommune : {c['commune']}\nMétier : {c['metier']}\n"
        f"Dirigeant : {c.get('dirigeant') or 'inconnu'}\nConstat : {angle}"
    )
    msg = client.messages.create(model=MODEL, max_tokens=600, system=SYSTEM, messages=[{"role": "user", "content": user}])
    text = msg.content[0].text.strip()
    subject, _, body = text.partition("\n")
    return subject.strip().strip('"'), body.strip()


def compose(c):
    if config.env("ANTHROPIC_API_KEY"):
        try:
            return claude_mail(c)
        except Exception as exc:  # repli sur le modèle fixe plutôt que de bloquer la journée
            print(f"  ! Claude indisponible ({exc}), modèle fixe utilisé")
    return fallback_mail(c)


def signature():
    s = config.sender()
    lines = ["", "Cordialement,", f"{s['prenom']} {s['nom']}", f"Création de sites web - {s['site']}"]
    if s["tel"]:
        lines.append(s["tel"])
    lines += [
        "",
        "--",
        "Vous recevez ce message à titre professionnel. Si ce n'est pas pertinent pour vous, "
        "répondez simplement STOP : je ne vous écrirai plus.",
    ]
    if s["legal"]:
        lines.append(s["legal"])
    return "\n".join(lines)


def build_message(to, subject, body):
    s = config.sender()
    m = EmailMessage()
    m["From"] = f"{s['prenom']} {s['nom']} <{s['email']}>"
    m["To"] = to
    m["Subject"] = subject
    m["Date"] = formatdate(localtime=True)
    m["Message-ID"] = make_msgid(domain=s["email"].split("@")[-1])
    m["List-Unsubscribe"] = f"<mailto:{s['email']}?subject=STOP>"
    m.set_content(body + "\n" + signature())
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
