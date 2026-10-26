#!/bin/sh
# Lance le dashboard Prospec Bat (Termux ou Linux) : ./start.sh
cd "$(dirname "$0")" || exit 1

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Fichier .env créé. Renseignez-le (nano .env) puis relancez ./start.sh"
  exit 1
fi

# Le dashboard tourne déjà en arrière-plan (démarrage automatique) : inutile d'en lancer un second
if [ -f data/server.pid ] && kill -0 "$(cat data/server.pid)" 2>/dev/null; then
  echo "Le dashboard tourne déjà en arrière-plan : http://localhost:${PORT:-8000}"
  echo "Après une mise à jour : ./server.sh restart"
  exit 0
fi

# Installe les dépendances nécessaires au dashboard si besoin
python -c "import flask, requests, dns" 2>/dev/null || pip install requests flask dnspython || exit 1

# Termux : empêche Android d'endormir le programme
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock

PORT="${PORT:-8000}"
echo "Dashboard : http://localhost:$PORT  (Ctrl+C pour arrêter)"
exec python -m prospec.web
