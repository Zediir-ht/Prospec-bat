#!/bin/sh
# Dashboard en arrière-plan (démarrage du téléphone, mises à jour).
#   ./server.sh start | stop | restart | status | log
cd "$(dirname "$0")" || exit 1
PORT="${PORT:-8000}"
PIDF=data/server.pid
LOG=data/server.log
mkdir -p data

running() { [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; }

start() {
  if running; then
    echo "Le dashboard tourne déjà : http://localhost:$PORT"
    return 0
  fi
  if [ ! -f .env ]; then
    echo "Fichier .env absent : lancez d'abord ./install.sh"
    return 1
  fi
  python -c "import flask, requests, dns" 2>/dev/null || pip install requests flask dnspython || return 1
  # Termux : empêche Android d'endormir le programme
  command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock
  # journal limité : on repart d'un fichier neuf au-delà de 1 Mo
  if [ -f "$LOG" ] && [ "$(wc -c < "$LOG")" -gt 1000000 ]; then mv "$LOG" "$LOG.old"; fi
  echo "--- démarrage $(date '+%d/%m %H:%M') ---" >> "$LOG"
  nohup python -m prospec.web >> "$LOG" 2>&1 &
  echo $! > "$PIDF"
  sleep 2
  if running; then
    echo "Dashboard lancé en arrière-plan : http://localhost:$PORT"
  else
    echo "Le dashboard n'a pas démarré. Dernières lignes du journal :"
    tail -n 15 "$LOG"
    return 1
  fi
}

stop() {
  if running; then
    kill "$(cat "$PIDF")"
    i=0
    while running && [ $i -lt 10 ]; do sleep 1; i=$((i + 1)); done
    running && kill -9 "$(cat "$PIDF")" 2>/dev/null
    echo "Dashboard arrêté."
  else
    echo "Le dashboard ne tournait pas."
  fi
  rm -f "$PIDF"
}

case "${1:-start}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) if running; then echo "En marche : http://localhost:$PORT"; else echo "Arrêté."; fi ;;
  log) tail -n 40 "$LOG" ;;
  *) echo "Usage : ./server.sh start | stop | restart | status | log"; exit 1 ;;
esac
