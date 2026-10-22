# Prospec-bat

Prospection automatisée pour [zdrdev.fr](https://zdrdev.fr) auprès des entreprises du bâtiment d'Aveyron (12).
Angle : **maquette de site gratuite**, aucun prix dans les mails. 10 mails/jour.

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env   # renseigner GMAIL_APP_PASSWORD, SENDER_LEGAL, (ANTHROPIC_API_KEY)
```

## Utilisation
```bash
python -m prospec.cli source          # 1x : liste des entreprises du 12 (API Recherche d'entreprises)
python -m prospec.cli qualify -n 30   # détecte site / état / email de contact
python -m prospec.cli run             # brouillons Gmail (SEND_MODE=draft) ou envoi (SEND_MODE=send), 10/jour
python -m prospec.cli stats
python -m prospec.cli export-calls    # entreprises ciblées mais sans email -> data/a_appeler.csv
python -m prospec.cli suppress x@y.fr # désinscription (à faire à chaque "STOP" reçu)
```
Quotidien (cron, 9h en semaine) : `qualify -n 30 && run`.

## Cadre légal (B2B, CNIL)
Mail en rapport avec l'activité du destinataire, expéditeur identifié, mention de désinscription, liste de suppression respectée. Les entrepreneurs individuels sont exclus par défaut (`config.py`).
Renseigner `SENDER_LEGAL` (raison sociale, SIRET, adresse) avant tout envoi.
