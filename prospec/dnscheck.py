"""Vérifie qu'un nom de domaine peut recevoir du courrier (enregistrement MX), sans jamais deviner d'adresse."""
import random
import re
import smtplib
import socket
import threading
import time
from functools import lru_cache

from . import config

try:
    import dns.exception
    import dns.resolver
except ImportError:  # dnspython absent : on ne bloque rien
    dns = None


def make_resolver():
    """Résolveur DNS. Sur Android (Termux), /etc/resolv.conf n'existe pas : on utilise alors des DNS publics."""
    try:
        resolver = dns.resolver.Resolver()
    except Exception:
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = ["1.1.1.1", "8.8.8.8"]
    if not getattr(resolver, "nameservers", None):
        resolver.nameservers = ["1.1.1.1", "8.8.8.8"]
    resolver.lifetime, resolver.timeout = 5, 3
    return resolver


@lru_cache(maxsize=4096)
def domain_status(domain):
    """'ok', 'invalid' (le domaine n'existe pas ou n'accepte aucun courrier) ou 'unknown' (réseau, délai dépassé)."""
    if dns is None or not domain:
        return "unknown"
    try:
        resolver = make_resolver()
    except Exception:  # la vérification est un plus : elle ne doit jamais bloquer un envoi
        return "unknown"
    try:
        answers = resolver.resolve(domain, "MX")
        # MX « . » = le domaine déclare ne recevoir aucun courrier (RFC 7505)
        return "invalid" if all(str(a.exchange) == "." for a in answers) else "ok"
    except dns.resolver.NXDOMAIN:
        return "invalid"
    except dns.resolver.NoAnswer:  # pas de MX : le courrier va à l'adresse du domaine, s'il en a une
        try:
            resolver.resolve(domain, "A")
            return "ok"
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return "invalid"
        except Exception:
            return "unknown"
    except Exception:
        return "unknown"


def email_ok(email):
    """False seulement quand on est sûr que l'adresse ne peut pas recevoir de courrier."""
    return domain_status((email or "").rsplit("@", 1)[-1].strip().lower()) != "invalid"


# --- La boîte existe-t-elle ? Sonde SMTP (RCPT TO), sans jamais envoyer de mail ------------------------------
# Beaucoup de serveurs (Gmail, Orange, Free, OVH…) répondent « utilisateur inconnu » dès l'étape RCPT. Le port 25
# sortant est souvent bloqué sur téléphone : dans ce cas la sonde s'arrête 30 minutes et ne bloque rien.
UNKNOWN_USER_RE = re.compile(
    r"user unknown|unknown user|no such user|does not exist|doesn't exist|not exist|invalid (?:recipient|mailbox|address)"
    r"|recipient (?:rejected|not found|address rejected)|mailbox (?:unavailable|not found)|address rejected|no mailbox"
    r"|unrouteable|account.{0,30}(?:disabled|inactive|not found)|5\.1\.[01]\b|utilisateur inconnu|n'existe pas", re.I)
POLICY_RE = re.compile(r"spam|block|blacklist|blocklist|denied|policy|reputation|reverse dns|\brbl\b|not authorized|relay|5\.7\.", re.I)
_probe = {"blocked_until": 0.0, "slots": threading.Semaphore(4)}
_catchall = {}
_mailbox = {}


def _mx_hosts(domain):
    try:
        answers = make_resolver().resolve(domain, "MX")
        hosts = [str(a.exchange).rstrip(".") for a in sorted(answers, key=lambda a: a.preference)]
        return [h for h in hosts if h][:2]
    except Exception:
        return [domain]


def _rcpt(server, sender, rcpt):
    """(code, message) de la réponse à RCPT TO, ou None si le serveur n'a pas accepté la conversation."""
    code, _ = server.mail(sender)
    if code >= 400:
        return None
    return server.rcpt(rcpt)


def mailbox_status(email):
    """'ok' (boîte acceptée), 'invalid' (le serveur dit que la boîte n'existe pas) ou 'unknown' (port 25 bloqué,
    serveur qui accepte tout, refus pour une autre raison…). Désactivable avec SMTP_PROBE=0."""
    email = (email or "").strip().lower()
    if config.env("SMTP_PROBE", "1") == "0" or "@" not in email or dns is None:
        return "unknown"
    if email in _mailbox:
        return _mailbox[email]
    if time.monotonic() < _probe["blocked_until"]:
        return "unknown"
    domain = email.rsplit("@", 1)[-1]
    sender = config.sender()["email"] or "postmaster@localhost"
    helo = re.sub(r"^https?://|/.*$", "", config.sender()["site"] or "").replace("www.", "") or "localhost"
    result = "unknown"
    with _probe["slots"]:
        for host in _mx_hosts(domain):
            try:
                server = smtplib.SMTP(timeout=8, local_hostname=helo)
                server.connect(host, 25)
            except (OSError, smtplib.SMTPException):  # port 25 filtré ou serveur injoignable
                _probe["blocked_until"] = time.monotonic() + 1800
                return "unknown"
            try:
                server.ehlo_or_helo_if_needed()
                answer = _rcpt(server, sender, email)
                if answer is None:
                    continue
                code, msg = answer[0], (answer[1] or b"").decode("utf-8", "replace")
                if code in (250, 251):
                    if domain not in _catchall:  # le domaine accepte-t-il n'importe quoi ?
                        fake = _rcpt(server, sender, f"pb-{random.randrange(16 ** 10):010x}@{domain}")
                        _catchall[domain] = bool(fake and fake[0] in (250, 251))
                    result = "unknown" if _catchall[domain] else "ok"
                elif code in (550, 551, 553, 554) and UNKNOWN_USER_RE.search(msg) and not POLICY_RE.search(msg):
                    result = "invalid"
                break
            except (OSError, smtplib.SMTPException):
                continue
            finally:
                try:
                    server.close()
                except Exception:
                    pass
    if result != "unknown" or time.monotonic() >= _probe["blocked_until"]:
        _mailbox[email] = result
    return result
