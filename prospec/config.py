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


# Aveyron en premier (traité en priorité), puis les départements limitrophes.
# Ajouter "30" (Gard) ou "34" (Hérault) dans DEPARTEMENTS (.env) pour élargir davantage.
DEPARTEMENTS = [d.strip() for d in env("DEPARTEMENTS", "12,48,15,46,81,82").split(",") if d.strip()]

# Codes NAF du bâtiment (construction, 41 / 42 / 43)
NAF_BATIMENT = [
    "41.20A", "41.20B", "43.11Z", "43.12A", "43.12B", "43.13Z", "43.21A", "43.21B",
    "43.22A", "43.22B", "43.29A", "43.29B", "43.31Z", "43.32A", "43.32B", "43.32C",
    "43.33Z", "43.34Z", "43.39Z", "43.91A", "43.91B", "43.99A", "43.99B", "43.99C",
    "43.99D", "43.99E",
]

# Autres secteurs : code NAF -> libellé tel qu'on le chercherait sur internet (« boulangerie Rodez »)
SECTEURS = {
    "alimentaire": {
        "10.13B": "charcuterie", "10.71A": "boulangerie", "10.71B": "boulangerie", "10.71C": "boulangerie",
        "10.71D": "pâtisserie", "10.82Z": "chocolaterie", "47.21Z": "primeur", "47.22Z": "boucherie",
        "47.23Z": "poissonnerie", "47.24Z": "boulangerie-pâtisserie", "47.25Z": "cave à vins", "47.29Z": "épicerie",
    },
    "restauration": {
        "56.10A": "restaurant", "56.10B": "restaurant", "56.10C": "restauration rapide", "56.21Z": "traiteur",
        "56.30Z": "bar", "55.10Z": "hôtel", "55.20Z": "gîte et hébergement", "55.30Z": "camping",
    },
    "artisanat": {
        "16.23Z": "charpentier", "16.29Z": "artisan du bois", "31.09A": "fabricant de meubles", "31.09B": "fabricant de meubles",
        "23.41Z": "céramiste", "25.50A": "forgeron", "25.50B": "coutellerie", "25.62A": "mécanique de précision",
        "25.62B": "mécanique de précision", "32.12Z": "bijoutier", "32.13Z": "créateur de bijoux", "18.12Z": "imprimerie",
        "95.23Z": "cordonnier", "95.25Z": "horloger", "95.29Z": "réparation", "96.01A": "pressing", "96.01B": "pressing",
        "74.20Z": "photographe", "81.30Z": "paysagiste", "90.03A": "artiste", "90.03B": "artiste",
    },
    "services": {
        "96.02A": "coiffeur", "96.02B": "institut de beauté", "96.04Z": "bien-être et spa", "96.09Z": "services à la personne",
        "93.13Z": "salle de sport", "45.11Z": "concessionnaire automobile", "45.20A": "garage automobile",
        "45.20B": "garage automobile", "45.31Z": "pièces auto", "45.40Z": "garage moto",
    },
    "commerce": {
        "47.41Z": "informatique", "47.51Z": "textile", "47.52A": "quincaillerie", "47.52B": "bricolage",
        "47.53Z": "décoration", "47.54Z": "électroménager", "47.59A": "magasin de meubles", "47.59B": "décoration",
        "47.61Z": "librairie", "47.62Z": "presse et papeterie", "47.64Z": "magasin de sport", "47.65Z": "magasin de jouets",
        "47.71Z": "boutique de vêtements", "47.72A": "magasin de chaussures", "47.72B": "maroquinerie",
        "47.75Z": "parfumerie", "47.76Z": "fleuriste", "47.77Z": "bijouterie", "47.78A": "opticien",
        "47.78C": "boutique", "47.79Z": "brocante",
    },
}
ACTIVE_SECTEURS = [x.strip() for x in env("SECTEURS", "batiment,alimentaire,restauration,artisanat,services,commerce").split(",") if x.strip()]

NAF_METIERS = {}
for _name in ACTIVE_SECTEURS:
    NAF_METIERS.update(SECTEURS.get(_name, {}))
NAF_CODES = (NAF_BATIMENT if "batiment" in ACTIVE_SECTEURS else []) + list(NAF_METIERS)

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

# Entrepreneurs individuels (nature juridique 1000) : contactés uniquement sur une adresse
# professionnelle (nom de domaine de l'entreprise), jamais sur une messagerie personnelle.
FREE_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "orange.fr", "wanadoo.fr", "hotmail.com", "hotmail.fr", "outlook.com",
    "outlook.fr", "live.fr", "live.com", "yahoo.fr", "yahoo.com", "free.fr", "sfr.fr", "neuf.fr",
    "laposte.net", "icloud.com", "me.com", "bbox.fr", "numericable.fr", "aol.com", "msn.com",
}


def sender():
    return {
        "prenom": env("SENDER_FIRSTNAME", "Corentin"),
        "nom": env("SENDER_LASTNAME", "MAYRAND"),
        "email": env("SENDER_EMAIL", "corentin.mayrand@gmail.com"),
        "site": env("SENDER_WEBSITE", "https://zdrdev.fr"),
        "tel": env("SENDER_PHONE"),
        "legal": env("SENDER_LEGAL"),
    }
