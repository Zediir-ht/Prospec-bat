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

## Dashboard mobile
```bash
python -m prospec.web   # http://localhost:8000
```
Pages : Accueil (stats, mode d'envoi, « Préparer les mails du jour », désinscription), À valider (relire / modifier / envoyer / ignorer), Envoyés (marquer réponse ou refus), À appeler.
Sur le téléphone : ouvrir l'URL dans Chrome > menu > « Ajouter à l'écran d'accueil ».

Mode `review` (défaut) : les mails sont rédigés mais **rien ne part** tant que vous n'appuyez pas sur *Envoyer*.

### Déploiement (Docker)
```bash
docker build -t prospec .
docker run -d --restart=always -p 80:8000 --env-file .env -v prospec-data:/app/data prospec
```
Il faut un disque persistant (`/app/data` contient la base SQLite) : un petit VPS (OVH, Hetzner...) ou Fly.io / Railway avec volume. Évitez les offres gratuites sans disque persistant (Render gratuit) : la base serait effacée.
Passer en HTTPS (Caddy ou le certificat du fournisseur) puisque l'on saisit un mot de passe.

Déclenchement quotidien : créer un job gratuit sur cron-job.org qui appelle `https://VOTRE-URL/cron/<CRON_TOKEN>` chaque matin en semaine.

### Lancement rapide (Termux / Linux)
```bash
./start.sh   # puis ouvrir http://localhost:8000
```
