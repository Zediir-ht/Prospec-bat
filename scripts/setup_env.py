"""Crée le fichier .env : génère les secrets, ne pose que les questions nécessaires."""
import getpass
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"

if env_path.exists() and "--force" not in sys.argv:
    print(".env existe déjà : rien à faire (relancez avec --force pour le refaire).")
    sys.exit(0)

print("Configuration de Prospec Bat (3 questions)\n")
print("1/3 Mot de passe d'application Gmail (16 lettres).")
print("    À créer sur myaccount.google.com > Sécurité > Validation en 2 étapes > Mots de passe d'application.")
gmail = getpass.getpass("    Mot de passe d'application : ").replace(" ", "").strip()
print("\n2/3 Mentions légales ajoutées en bas des mails (raison sociale, SIRET, adresse).")
legal = input("    Ex : ZDR Dev - SIRET 123 456 789 00012 - 1 rue X, 12000 Rodez\n    > ").strip()
print("\n3/3 Numéro de téléphone affiché dans la signature (Entrée pour ignorer).")
phone = input("    > ").strip()

password = secrets.token_urlsafe(9)
values = {
    "SENDER_FIRSTNAME": "Corentin",
    "SENDER_LASTNAME": "MAYRAND",
    "SENDER_EMAIL": "corentin.mayrand@gmail.com",
    "SENDER_WEBSITE": "https://zdrdev.fr",
    "SENDER_PHONE": phone,
    "SENDER_LEGAL": legal,
    "GMAIL_APP_PASSWORD": gmail,
    "ANTHROPIC_API_KEY": "",
    "SEND_MODE": "review",
    "DAILY_LIMIT": "10",
    "FOLLOWUP_DAYS": "7",
    "DASHBOARD_PASSWORD": password,
    "DASHBOARD_SECRET": secrets.token_hex(24),
    "CRON_TOKEN": secrets.token_hex(16),
    "QUALIFY_PER_DAY": "150",
}
env_path.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n", encoding="utf-8")
env_path.chmod(0o600)
print(f"\n.env créé. Mot de passe du dashboard : {password}")
print("Notez-le : il vous sera demandé à chaque connexion (modifiable dans .env).\n")
