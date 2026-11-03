# Graph Report - Prospec-bat  (2026-11-03)

## Corpus Check
- 31 files · ~26,143 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 496 nodes · 1194 edges · 15 communities (14 shown, 1 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d7777e70`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- web.py
- Commandes en ligne et orchestration
- Rédaction des mails et configuration
- Lecture des réponses Gmail
- Envoi et relances
- Base de données et tests du dashboard
- re
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- test_prospec.py
- Interface et mascotte Bati
- next_to_write
- draft_action

## God Nodes (most connected - your core abstractions)
1. `connect()` - 47 edges
2. `env()` - 29 edges
3. `index()` - 23 edges
4. `process()` - 21 edges
5. `login()` - 18 edges
6. `connect()` - 17 edges
7. `send_now()` - 16 edges
8. `cmd_run()` - 15 edges
9. `qualify_company()` - 15 edges
10. `add()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `draft_action()` --implements--> `Mode review : rien ne part sans validation`  [INFERRED]
  prospec/web.py → README.md
- `send_all()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/web.py → README.md
- `qualify_batch()` --implements--> `Recherche en parallèle (WORKERS) et cadence de recherche web`  [INFERRED]
  prospec/cli.py → README.md
- `send_followup_now()` --implements--> `Relances dans le même fil (J+7, une seule)`  [INFERRED]
  prospec/cli.py → README.md
- `send_now()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/cli.py → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline de prospection (source, qualification, rédaction, envoi)** — prospec_sourcing, prospec_qualify, prospec_mailer, prospec_cli [INFERRED 0.85]
- **Chaîne de contrôle des adresses avant envoi** — prospec_emails, prospec_dnscheck, prospec_mailer_assert_sourced, prospec_db_is_suppressed [INFERRED 0.85]
- **Suivi après envoi (réponses, relances, pipeline, notifications)** — prospec_inbox, prospec_notify, prospec_cli_send_followup_now, prospec_web_pipeline_action [INFERRED 0.85]

## Communities (15 total, 1 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.05
Nodes (50): get_setting(), set_setting(), parse_batch(), check_inbox(), clean_now(), close_connection(), collect_auto(), collect_now() (+42 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.08
Nodes (28): cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source(), cmd_stats() (+20 more)

### Community 3 - "Rédaction des mails et configuration"
Cohesion: 0.07
Nodes (25): sender(), batch_followup_prompt(), batch_prompt(), build_message(), check_mail(), deliver(), describe(), facebook_message() (+17 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.08
Nodes (27): is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date(), process() (+19 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.09
Nodes (29): contact(), remember_message(), send_followup_now(), send_now(), due_followups(), first_send_date(), log_send(), now() (+21 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.12
Nodes (24): connect(), migrate(), _run_send_all(), con(), test_qualify_runs_in_parallel(), client(), login(), test_collect_auto_toggle_and_daily_preempts() (+16 more)

### Community 8 - "re"
Cohesion: 0.05
Nodes (32): apply_result(), cmd_clean(), domain_status(), email_ok(), make_resolver(), check(), clean_database(), diagnose() (+24 more)

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.15
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "test_prospec.py"
Cohesion: 0.13
Nodes (14): enseigne_of(), fetch_naf(), metier_for(), next_refresh(), parse_result(), pool_size(), refresh_days(), refresh_if_due() (+6 more)

### Community 13 - "test_prospec.py"
Cohesion: 0.06
Nodes (45): inspect(), match_site(), next_queries(), run(), company_names(), distinctive(), match(), norm_spaces() (+37 more)

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.47
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 17 - "next_to_write"
Cohesion: 0.18
Nodes (8): check_can_send(), next_to_write(), ei_blocked(), in_suppressed(), suppressed_set(), assert_sourced(), test_ei_free_mail_setting(), test_never_send_to_unsourced_address()

### Community 18 - "draft_action"
Cohesion: 0.29
Nodes (5): Dashboard mobile (Flask), Déploiement Docker et disque persistant, Mode review : rien ne part sans validation, Prospec-bat (projet de prospection pour zdrdev.fr), gunicorn (>=22)

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `flask (>=3.0)`, `requests (>=2.31)`, `Suivi des prospects (de la réponse au client)`, `gunicorn (>=22)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 147 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `re`, `test_prospec.py`, `test_prospec.py`, `next_to_write`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **What connects `PATH`, `flask (>=3.0)`, `requests (>=2.31)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05369369369369369 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `Commandes en ligne et orchestration` to `web.py`, `Rédaction des mails et configuration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `test_prospec.py`, `test_prospec.py`, `next_to_write`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.0782608695652174 - nodes in this community are weakly interconnected._
- **Should `Rédaction des mails et configuration` be split into smaller, more focused modules?**
  _Cohesion score 0.06852497096399536 - nodes in this community are weakly interconnected._
- **Should `Lecture des réponses Gmail` be split into smaller, more focused modules?**
  _Cohesion score 0.07777777777777778 - nodes in this community are weakly interconnected._