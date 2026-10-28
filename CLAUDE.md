# Prospec-bat

Outil de prospection par email (Aveyron et départements voisins) pour zdrdev.fr : sourcing SIRENE, recherche d'adresses, rédaction par Claude, envoi, suivi, dashboard mobile (Flask + SQLite). Voir `README.md`.
Tests : `python -m pytest -q`. Branche de travail : `claude/prospection-batiment-aveyron-zojkz0`.

## Au début de chaque session
Lis le graphe de connaissances **avant de commencer** : `graphify-out/GRAPH_REPORT.md` (le résumé s'affiche aussi au démarrage de la session, via `.claude/hooks/session-start.sh`). Pour une question sur le code, interroge le graphe (`graphify query "..."`) avant de chercher dans les fichiers.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
