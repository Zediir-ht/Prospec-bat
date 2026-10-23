# Prospec-bat

Prospection automatisée pour [zdrdev.fr](https://zdrdev.fr) auprès des artisans, commerçants, restaurateurs et entreprises du bâtiment d'Aveyron (12) et des départements voisins (48, 15, 46, 81, 82).
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
python -m prospec.cli suppress x@y.fr # désinscription (à faire à chaque "STOP" reçu)
```
Quotidien (cron, 9h en semaine) : `qualify -n 30 && run`.

## Cadre légal (B2B, CNIL)
Mail en rapport avec l'activité du destinataire, expéditeur identifié, mention de désinscription, liste de suppression respectée. Les entrepreneurs individuels ne sont contactés que sur une adresse professionnelle (jamais Gmail, Orange, etc.).
Renseigner `SENDER_LEGAL` (raison sociale, SIRET, adresse) avant tout envoi.

## Dashboard mobile
```bash
python -m prospec.web   # http://localhost:8000
```
Pages : Accueil (stats, mode d'envoi, « Préparer les mails du jour », désinscription), À valider (relire / modifier / envoyer / ignorer), Envoyés (marquer réponse ou refus). Prospection par email uniquement : les entreprises sans email public sont ignorées.
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

### Installation en une commande (Termux / Android)
```bash
pkg install -y git
git clone -b claude/prospection-batiment-aveyron-zojkz0 https://github.com/zediir-ht/prospec-bat.git
cd prospec-bat && ./install.sh
```
Le script installe les dépendances, pose 3 questions (mot de passe d'application Gmail, mentions légales, téléphone), génère les secrets, puis lance le dashboard sur http://localhost:8000.

## Réglages (.env)
- `DEPARTEMENTS` : par défaut `12,48,15,46,81,82` (Aveyron en priorité). Ajouter `30`, `34` pour élargir.
- `SECTEURS` : par défaut `batiment,alimentaire,restauration,artisanat,services,commerce`.
La recherche s'arrête dès que `DAILY_LIMIT` (10) mails exploitables sont réunis (adresses trouvées + brouillons en attente) : rien n'est cherché de plus tant que vous n'avez pas écoulé ceux-là. Les entreprises sont téléchargées au fur et à mesure (Aveyron d'abord), pas toutes d'un coup. `QUALIFY_PER_DAY` (150) limite le nombre d'entreprises testées par recherche.

## Rédaction des mails par Claude
Chaque mail est écrit par Claude pour l'entreprise visée (activité, commune, constat sur son site). Il n'y a pas de modèle fixe.
- **Avec une clé API** (`ANTHROPIC_API_KEY`) : « Préparer les mails du jour » écrit les mails tout seul.
- **Sans clé** : onglet **À rédiger** → *Copier la demande* → coller dans Claude (claude.ai) → coller sa réponse JSON → *Importer*. Les mails arrivent dans **À valider**.
Tout mail mentionnant un prix est refusé automatiquement.

## Sources d'adresses email
1. **Site de l'entreprise** : pages d'accueil, contact, mentions légales ; détecte aussi les adresses masquées (`[at]`, `&#64;`, `%40`, protection Cloudflare).
2. **OpenStreetMap** (`python -m prospec.cli osm`) : emails et sites web que les entreprises publient elles-mêmes, licence ODbL. Appariés à la base SIRENE par nom et code postal ; un site connu par OSM est lu directement, sans recherche web.
3. **Google Places** (facultatif, `GOOGLE_PLACES_KEY`) : trouve le site officiel de façon fiable.
Chaque mail indique d'où vient l'adresse (information exigée par le RGPD, art. 14) et propose de répondre STOP.
Règle absolue : aucune adresse n'est jamais devinée ni reconstituée (`info@`, `prenom.nom@`…). Un mail ne part que vers une adresse lue sur le site de l'entreprise ou publiée par elle dans OpenStreetMap ; toute autre origine est refusée (`mailer.assert_sourced`). Non utilisé non plus : annuaires dont les conditions interdisent l'extraction (Pages Jaunes, réseaux sociaux), listes achetées d'origine inconnue.

## Mode collecte (stock d'adresses)
Bouton **Lancer la collecte** du dashboard, ou `python -m prospec.cli collect -n 1000` : teste les entreprises sans s'arrêter à 10, en téléchargeant de nouvelles entreprises au fur et à mesure, et remplit un stock d'adresses. Les envois restent limités à `DAILY_LIMIT` par jour. Bouton **Arrêter** pour interrompre. Compter plusieurs heures pour 1000 entreprises : téléphone branché, Termux en « batterie sans restriction ».

## Vitesse
La recherche teste `WORKERS` (20) entreprises en parallèle : la lecture des sites se fait en même temps, seule la recherche web (DuckDuckGo) est espacée de `SEARCH_INTERVAL` (1 s) pour ne pas être bloquée, et ralentit d'elle-même si le moteur refuse des requêtes. Les entreprises dont le site est connu par OpenStreetMap ne passent pas par la recherche web. Avec Google Places (`GOOGLE_PLACES_KEY`), on peut baisser `SEARCH_INTERVAL` à 0.1.

## Recherche par enseigne et par métier
- Chaque entreprise est cherchée sous son **enseigne** (« Plomberie du Rouergue ») puis sous son nom légal (« SARL DUPONT ET FILS »).
- `python -m prospec.cli discover -n 20` (lancé aussi par la collecte et « Préparer les mails du jour ») cherche « métier + commune » (« plomberie et chauffage Rodez ») et rattache les sites trouvés aux entreprises SIRENE : par le **SIREN/SIRET** affiché dans les mentions légales (certain), sinon par le nom dans l'adresse du site s'il ne désigne qu'une entreprise de la commune.
