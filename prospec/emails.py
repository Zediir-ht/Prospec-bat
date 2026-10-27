"""Validation des adresses email : débris de code, adresses factices, domaines sans rapport avec l'entreprise.
Aucune adresse n'est jamais devinée : on ne fait que rejeter les mauvaises ou réparer celles qui sont collées à du texte."""
import re
import unicodedata

from . import config

# Extensions de domaine courantes. Une extension inconnue (« png », « frTél », « jsx ») rend l'adresse suspecte.
KNOWN_TLDS = set("""fr com net org eu info biz io co be ch de es it uk nl lu pt at pl se no dk fi ie us ca re pm yt gp mq gf nc pf wf tf
bzh paris alsace corsica pro shop store site online tech app dev xyz cloud agency studio design photo art club cafe bar restaurant
immo immobilier auto garage hotel tours voyage fitness yoga bio vin wine beer pizza coffee boutique services solutions
company email group center city land world life love one top win vip fun live news media tv me cc ws name mobi asia tel
ac ad ae ag al am ao ar as au aw ax az ba bb bd bf bg bh bi bj bm bn bo br bs bt bw by bz cd cf cg ci ck cl cm cn cr cu cv cw cy cz
dj dm do dz ec ee eg er et fj fk fm fo ga gd ge gg gh gi gl gm gn gq gr gt gu gw gy hk hn hr ht hu id il im in iq ir is je jm jo jp
ke kg kh ki km kn kp kr kw ky kz la lb lc li lk lr ls lt lv ly ma mc md mg mh mk ml mm mn mo mp mr ms mt mu mv mw mx my mz na ne nf
ng ni np nr nu nz om pa pe pg ph pk pn pr ps pw py qa ro rs ru rw sa sb sc sd sg sh si sk sl sm sn so sr st sv sy sz tc td tg th tj
tk tl tm tn to tr tt tw tz ua ug uy uz va vc ve vg vi vn vu ws ye za zm zw""".split())

FILE_EXT = set("png jpg jpeg gif webp svg css js json xml ico pdf woff woff2 ttf eot mp4 mp3 zip html htm php txt map avif".split())
REPAIRABLE = ("com", "net", "org", "info", "bzh", "fr", "eu", "be", "ch", "de", "es", "it")  # seules extensions réparées

# Adresses qui ne sont pas celles de l'entreprise
BAD_LOCALS = {"noreply", "no-reply", "donotreply", "do-not-reply", "mailer-daemon", "postmaster", "abuse", "hostmaster", "webmaster",
              "root", "nobody", "unsubscribe", "bounce", "bounces", "email", "mail", "nom", "prenom", "name", "user", "username",
              "example", "exemple", "test", "votre", "votreemail", "adresse", "youremail", "yourname", "john.doe", "jane.doe",
              "nom.prenom", "prenom.nom", "xxx", "xxxx", "monadresse", "mon.email", "moi"}
BAD_DOMAINS = {"example.com", "example.org", "example.net", "example.fr", "domain.com", "domaine.com", "domaine.fr", "mondomaine.fr",
               "monsite.fr", "monsite.com", "nomdomaine.fr", "votredomaine.fr", "votresite.fr", "yourdomain.com", "yoursite.com",
               "email.com", "email.fr", "mail.com", "test.com", "test.fr", "sample.com", "site.com", "societe.fr", "entreprise.fr",
               "wix.com", "wixpress.com", "wixsite.com", "sentry.io", "wordpress.com", "wordpress.org", "w3.org", "schema.org",
               "google.com", "facebook.com", "instagram.com", "gravatar.com", "cloudflare.com", "jimdo.com", "squarespace.com",
               "shopify.com", "weebly.com", "webador.fr", "godaddy.com", "mailchimp.com", "sendinblue.com", "brevo.com", "ovh.com",
               "ovh.net", "ovhcloud.com", "gandi.net", "ionos.fr", "ionos.com", "one.com", "o2switch.fr", "hostinger.com",
               "pagesjaunes.fr", "societe.com", "pappers.fr", "cnil.fr", "gouv.fr", "service-public.fr", "legifrance.gouv.fr"}

LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
LOCAL_RE = re.compile(r"^[a-z0-9][a-z0-9._%+-]*$")
CANDIDATE_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s)


def repair(raw):
    """Répare les débris fréquents sans rien inventer : \\u003e collé au début, numéro de téléphone collé,
    extension suivie de texte (« …@site.frTel » -> « …@site.fr »). Retourne l'adresse en minuscules."""
    e = raw.strip().lower().strip(".,;:!?)>]}\"'")
    e = re.sub(r"^(?:u003[ce]|u0022|u0027|u0026|x3[ce]|%3[ce]|%20)+", "", e)
    e = re.sub(r"^\d{8,}(?=[a-z])", "", e)  # numéro de téléphone collé devant l'adresse
    local, _, domain = e.rpartition("@")
    labels = domain.split(".")
    last = labels[-1] if labels else ""
    raw_last = raw.strip().strip(".,;:!?)>]}\"'").rsplit(".", 1)[-1]  # casse d'origine : « frTel » = texte collé
    if last and last not in KNOWN_TLDS and last not in FILE_EXT:
        for tld in sorted(REPAIRABLE, key=len, reverse=True):  # « frtel » -> « fr » : texte collé derrière l'extension
            extra = len(last) - len(tld)
            glued = len(raw_last) > len(tld) and raw_last[len(tld)].isupper()
            if last.startswith(tld) and (extra >= 2 or (extra == 1 and glued)):
                labels[-1] = tld
                break
    return f"{local}@{'.'.join(labels)}"


def check(email):
    """(True, "") si l'adresse est plausible, sinon (False, raison). Ne regarde que l'adresse elle-même."""
    e = (email or "").strip().lower()
    if e.count("@") != 1 or len(e) > 254:
        return False, "format invalide"
    local, domain = e.split("@")
    if not local or len(local) > 64 or ".." in local or local.endswith(".") or not LOCAL_RE.match(local):
        return False, "partie locale invalide"
    if "%" in local or re.fullmatch(r"[0-9a-f]{20,}", local):
        return False, "débris de code"
    if local in BAD_LOCALS or re.match(r"^(?:no[-_.]?reply|do[-_.]?not[-_.]?reply|mailer[-_.]?daemon)", local):
        return False, "adresse automatique ou factice"
    labels = domain.split(".")
    if len(labels) < 2 or not all(LABEL_RE.match(x) for x in labels):
        return False, "domaine invalide"
    if labels[-1] not in KNOWN_TLDS:
        return False, f"extension inconnue (.{labels[-1]})"
    if domain in BAD_DOMAINS or any(domain.endswith("." + d) for d in BAD_DOMAINS if d.count(".") == 1 and d not in ("gouv.fr",)):
        return False, "domaine d'un service tiers"
    return True, ""


def extract(text):
    """Toutes les adresses plausibles du texte, réparées, sans doublon."""
    found = []
    for raw in CANDIDATE_RE.findall(text):
        e = repair(raw)
        if check(e)[0] and e not in found:
            found.append(e)
    return found


def host_of(url):
    h = re.sub(r"^https?://", "", (url or "").lower()).split("/")[0].split(":")[0]
    return h[4:] if h.startswith("www.") else h


def related(email, site_url, names=()):
    """Cette adresse appartient-elle bien à l'entreprise ? Oui si son domaine est celui du site, ressemble au nom de
    l'entreprise, ou si c'est une messagerie grand public (Gmail, Orange…) que beaucoup d'artisans utilisent.
    Non pour l'adresse d'une agence web, d'un hébergeur ou d'une autre société citée sur la page."""
    domain = email.rsplit("@", 1)[-1].lower()
    if domain in config.FREE_MAIL_DOMAINS:
        return True
    site = host_of(site_url)
    if site and (domain == site or domain.endswith("." + site) or site.endswith("." + domain)):
        return True
    base = norm(domain.rsplit(".", 1)[0])
    for name in names:
        for token in re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", (name or "").lower()).encode("ascii", "ignore").decode()):
            if len(token) >= 4 and token in base:
                return True
    return False


def shared_by_others(con, email, siren):
    """Une même adresse sur plusieurs entreprises est presque toujours celle d'une agence ou d'un groupe."""
    n = con.execute("SELECT COUNT(*) FROM companies WHERE lower(email)=? AND siren<>?", (email.lower(), siren)).fetchone()[0]
    return n >= 2


def diagnose(con, row, check_dns=False, counts=None):
    """Raison pour laquelle l'adresse d'une entreprise est à écarter, ou '' si elle est correcte.
    `counts` : nombre d'entreprises par adresse, calculé une fois avant le nettoyage."""
    email = row["email"]
    ok, why = check(email)
    if not ok:
        return why
    if row["email_source"] in (None, "site") and row["site_url"] and not related(email, row["site_url"], (row["nom"], row["enseigne"])):
        return "adresse d'un autre domaine que le site (agence, hébergeur…)"
    shared = (counts[email.lower()] >= 3) if counts is not None else shared_by_others(con, email, row["siren"])
    if shared:
        return "même adresse sur plusieurs entreprises"
    if check_dns:
        from . import dnscheck
        if not dnscheck.email_ok(email):
            return "le domaine ne reçoit pas de courrier"
    return ""


def clean_database(con, check_dns=True, progress=None):
    """Passe en revue les adresses des entreprises pas encore contactées et retire celles qui sont invalides.
    Retourne [(entreprise, adresse, raison), ...]. Les mails déjà envoyés ne sont pas touchés."""
    rows = con.execute("SELECT * FROM companies WHERE email IS NOT NULL AND status IN ('new','qualified','drafted','no_email')").fetchall()
    removed = []
    counts = {}
    for (e,) in con.execute("SELECT lower(email) FROM companies WHERE email IS NOT NULL"):
        counts[e] = counts.get(e, 0) + 1
    for i, row in enumerate(rows):
        why = diagnose(con, row, check_dns=check_dns, counts=counts)
        if why:
            con.execute("UPDATE companies SET email=NULL, email_source=NULL, status='no_email', subject=NULL, body=NULL WHERE siren=?", (row["siren"],))
            removed.append((row["enseigne"] or row["nom"], row["email"], why))
        if progress and i % 50 == 0:
            progress(i, len(rows))
    con.commit()
    return removed
