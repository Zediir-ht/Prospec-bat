"""Lecture de la boîte Gmail, sans rien y modifier : réponses, demandes de désinscription et mails revenus
en erreur. Une réponse est rattachée à l'entreprise par le fil du mail envoyé (Message-ID), sinon par
l'adresse de l'expéditeur, sinon par son nom de domaine."""
import email
import imaplib
import re
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.utils import getaddresses, parseaddr

from . import config, db
from .qualify import EMAIL_RE

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CONTACTED = ("sent", "followed_up")
STOP_RE = re.compile(
    r"\bstop\b|d[ée]sinscri|d[ée]sabonn|ne (?:plus )?(?:me|nous) (?:plus )?(?:contacter|[ée]crire|solliciter|envoyer)"
    r"|pas int[ée]ress|retirez|supprimez (?:mon|notre|cette) adresse|merci de ne plus", re.I)
QUOTE_RE = re.compile(r"^\s*(?:>|Le .{3,120}a [ée]crit|On .{3,120}wrote|-{3,}\s*(?:Original|Message)|De\s*:|From\s*:|Envoy[ée] de mon)", re.M)
AUTO_SUBJECT_RE = re.compile(r"absen|out of office|r[ée]ponse automatique|automatic reply|auto(?:matic)?[- ]?reply|cong[ée]s", re.I)
BOUNCE_SENDERS = ("mailer-daemon", "postmaster")


def imap_date(d):
    """Date au format IMAP (mois en anglais, quelle que soit la langue du téléphone)."""
    return f"{d.day:02d}-{MONTHS[d.month - 1]}-{d.year}"


def decode(value):
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:
        return value or ""


def text_of(msg):
    """Texte brut du message (partie texte, sinon HTML sans balises)."""
    plain, html = [], []
    for part in msg.walk() if msg.is_multipart() else [msg]:
        if part.get_content_maintype() == "multipart" or part.get("Content-Disposition", "").startswith("attachment"):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        ctype = part.get_content_type()
        if ctype == "text/plain":
            plain.append(text)
        elif ctype == "text/html":
            html.append(re.sub(r"<[^>]+>", " ", text))
        elif ctype in ("message/delivery-status", "text/rfc822-headers"):
            plain.append(text)
    return "\n".join(plain or html)


def fresh_text(text):
    """La réponse elle-même, sans le message d'origine cité en dessous."""
    m = QUOTE_RE.search(text)
    return (text[: m.start()] if m else text).strip()


def references(msg, text=""):
    raw = " ".join(" ".join(msg.get_all(h, [])) for h in ("In-Reply-To", "References"))
    return set(re.findall(r"<[^<>\s]+@[^<>\s]+>", raw + " " + text))


def find_company(con, refs, addresses):
    for ref in refs:
        row = con.execute("SELECT * FROM companies WHERE instr(COALESCE(message_ids,''), ?) > 0", (ref,)).fetchone()
        if row:
            return row
    for addr in addresses:
        row = con.execute("SELECT * FROM companies WHERE lower(email)=? ORDER BY contacted_at DESC", (addr,)).fetchone()
        if row:
            return row
    for addr in addresses:  # même entreprise, autre boîte (patron@ au lieu de contact@)
        domain = addr.split("@")[-1]
        if domain in config.FREE_MAIL_DOMAINS:
            continue
        rows = con.execute("SELECT * FROM companies WHERE lower(email) LIKE ? AND status IN ('sent','followed_up')",
                           ("%@" + domain,)).fetchall()
        if len(rows) == 1:
            return rows[0]
    return None


def process(con, msg):
    """Analyse un message reçu. Retourne 'replied', 'stop', 'bounced', ou None (sans rapport / ignoré)."""
    sender = parseaddr(msg.get("From", ""))[1].lower()
    me = config.sender()["email"].lower()
    if not sender or sender == me:
        return None
    text = text_of(msg)
    is_bounce = sender.split("@")[0] in BOUNCE_SENDERS or msg.get_content_type() == "multipart/report"
    if is_bounce:
        failed = [a.lower() for a in msg.get_all("X-Failed-Recipients", [])] + [e.lower() for e in EMAIL_RE.findall(text)]
        row = find_company(con, references(msg, text), [a for a in failed if a != me and a.split("@")[0] not in BOUNCE_SENDERS])
        if not row or row["status"] not in CONTACTED:
            return None
        con.execute("UPDATE companies SET status='bounced' WHERE siren=?", (row["siren"],))
        con.execute("INSERT OR IGNORE INTO suppression(email) VALUES (?)", (row["email"].lower(),))
        con.commit()
        return "bounced"
    auto = msg.get("Auto-Submitted", "no").lower() != "no" or AUTO_SUBJECT_RE.search(decode(msg.get("Subject")))
    if auto:
        return None  # message d'absence : ce n'est pas une réponse
    addresses = [sender] + [a.lower() for _, a in getaddresses(msg.get_all("Reply-To", []))]
    row = find_company(con, references(msg), addresses)
    if not row or row["status"] not in CONTACTED:
        return None
    reply = fresh_text(text)
    snippet = re.sub(r"\s+", " ", reply)[:300]
    if STOP_RE.search(reply):
        con.execute("UPDATE companies SET reply_at=?, reply_snippet=? WHERE siren=?", (db.now(), snippet, row["siren"]))
        db.suppress(con, row["email"])  # passe aussi l'entreprise en « refus »
        return "stop"
    con.execute("UPDATE companies SET status='replied', reply_at=?, reply_snippet=? WHERE siren=?",
                (db.now(), snippet, row["siren"]))
    con.commit()
    return "replied"


def check(con, days=None):
    """Lit les messages reçus depuis `days` jours (INBOX_DAYS, 45 par défaut), une seule fois chacun.
    Retourne le nombre de réponses, de désinscriptions et d'erreurs détectées."""
    s = config.sender()
    days = days or int(config.env("INBOX_DAYS", "45"))
    counts = {"replied": 0, "stop": 0, "bounced": 0}
    with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
        imap.login(s["email"], config.env("GMAIL_APP_PASSWORD"))
        imap.select("INBOX", readonly=True)  # lecture seule : rien n'est marqué comme lu
        _, data = imap.uid("search", None, f"(SINCE {imap_date(datetime.now() - timedelta(days=days))})")
        seen = {r[0] for r in con.execute("SELECT uid FROM inbox_seen")}
        for uid in (data[0] or b"").split():
            uid = uid.decode()
            if uid in seen:
                continue
            _, parts = imap.uid("fetch", uid, "(BODY.PEEK[])")
            raw = next((p[1] for p in parts if isinstance(p, tuple)), None)
            if raw:
                kind = process(con, email.message_from_bytes(raw))
                if kind:
                    counts[kind] += 1
            con.execute("INSERT OR IGNORE INTO inbox_seen(uid) VALUES (?)", (uid,))
            con.commit()
    return counts


def summary(counts):
    parts = [f"{counts['replied']} réponse(s)", f"{counts['stop']} désinscription(s)", f"{counts['bounced']} adresse(s) en erreur"]
    return "Boîte mail vérifiée : " + ", ".join(parts) + "."
