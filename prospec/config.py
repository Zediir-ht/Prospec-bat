import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "prospec.db"


def _load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()


def env(name, default=""):
    return os.environ.get(name, default)


DEPARTEMENT = "12"  # Aveyron

# Codes NAF du bâtiment (construction, 41 / 42 / 43)
NAF_CODES = [
    "41.20A", "41.20B", "43.11Z", "43.12A", "43.12B", "43.13Z", "43.21A", "43.21B",
    "43.22A", "43.22B", "43.29A", "43.29B", "43.31Z", "43.32A", "43.32B", "43.32C",
    "43.33Z", "43.34Z", "43.39Z", "43.91A", "43.91B", "43.99A", "43.99B", "43.99C",
    "43.99D", "43.99E",
]

# Libellé du métier utilisé dans les mails, par préfixe NAF
METIERS = {
    "41.20": "construction",
    "43.11": "démolition",
    "43.12": "terrassement",
    "43.13": "forage",
    "43.21": "électricité",
    "43.22": "plomberie et chauffage",
    "43.29": "installation et isolation",
    "43.31": "plâtrerie",
    "43.32": "menuiserie",
    "43.33": "carrelage et revêtements",
    "43.34": "peinture et vitrerie",
    "43.39": "finitions",
    "43.91": "couverture et charpente",
    "43.99": "maçonnerie et gros œuvre",
}

# Les entrepreneurs individuels sont exclus par défaut (prudence CNIL)
EXCLURE_ENTREPRENEURS_INDIVIDUELS = True


def sender():
    return {
        "prenom": env("SENDER_FIRSTNAME", "Corentin"),
        "nom": env("SENDER_LASTNAME", "MAYRAND"),
        "email": env("SENDER_EMAIL", "corentin.mayrand@gmail.com"),
        "site": env("SENDER_WEBSITE", "https://zdrdev.fr"),
        "tel": env("SENDER_PHONE"),
        "legal": env("SENDER_LEGAL"),
    }
