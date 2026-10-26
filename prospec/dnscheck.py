"""Vérifie qu'un nom de domaine peut recevoir du courrier (enregistrement MX), sans jamais deviner d'adresse."""
from functools import lru_cache

try:
    import dns.exception
    import dns.resolver
except ImportError:  # dnspython absent : on ne bloque rien
    dns = None


@lru_cache(maxsize=4096)
def domain_status(domain):
    """'ok', 'invalid' (le domaine n'existe pas ou n'accepte aucun courrier) ou 'unknown' (réseau, délai dépassé)."""
    if dns is None or not domain:
        return "unknown"
    resolver = dns.resolver.Resolver()
    resolver.lifetime, resolver.timeout = 5, 3
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
