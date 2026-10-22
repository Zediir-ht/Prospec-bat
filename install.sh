#!/bin/sh
# Installation complète sur Termux (Android) : ./install.sh
cd "$(dirname "$0")" || exit 1

if command -v pkg >/dev/null 2>&1; then
  pkg install -y python nano
fi
python -c "import flask, requests" 2>/dev/null || pip install requests flask || exit 1
python scripts/setup_env.py || exit 1
echo "Installation terminée. Lancement du dashboard..."
exec ./start.sh
