#!/bin/bash
# SessionStart (sessions cloud) : prépare l'environnement et met le graphe de connaissances sous les yeux de Claude.
# Idempotent. Pas de « set -e » : une étape qui échoue ne doit jamais empêcher la session de démarrer.
set -uo pipefail

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
export PATH="$HOME/.local/bin:$PATH"

# 1. Dépendances du projet (de quoi lancer les tests : python -m pytest -q)
pip install -q -r requirements.txt >/dev/null 2>&1 || echo "(!) installation des dépendances Python incomplète"

# 2. Graphify : installation si absent, compétence /graphify, puis mise à jour du graphe (code seul, sans IA)
if ! command -v graphify >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then
    uv tool install graphifyy -q >/dev/null 2>&1
  else
    pip install -q graphifyy >/dev/null 2>&1
  fi
fi
if command -v graphify >/dev/null 2>&1; then
  graphify install >/dev/null 2>&1
  graphify update . >/dev/null 2>&1 || echo "(!) mise à jour du graphe impossible : le graphe versionné est utilisé tel quel"
else
  echo "(!) Graphify n'a pas pu être installé : le graphe versionné (graphify-out/) reste lisible, mais pas interrogeable."
fi

# 3. Ce que Claude lit au démarrage (la sortie de ce script est ajoutée au contexte de la session)
if [ -f graphify-out/GRAPH_REPORT.md ]; then
  echo "=== GRAPHE DE CONNAISSANCES DE PROSPEC-BAT (graphify-out/GRAPH_REPORT.md) ==="
  echo "Lis ce résumé avant de commencer. Pour une question sur le code : graphify query \"...\", graphify path \"A\" \"B\", graphify explain \"X\"."
  echo "Après avoir modifié du code : graphify update ."
  echo
  sed -n '1,70p' graphify-out/GRAPH_REPORT.md
  echo
  echo "(Rapport complet : graphify-out/GRAPH_REPORT.md)"
else
  echo "Aucun graphe de connaissances dans graphify-out/ : lance /graphify . pour le construire."
fi
exit 0
