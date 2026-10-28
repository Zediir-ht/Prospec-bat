# Graph Report - Prospec-bat  (2026-10-28)

## Corpus Check
- 31 files · ~22,898 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 462 nodes · 1085 edges · 14 communities (13 shown, 1 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 55 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4cee7148`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Dashboard web (Flask)
- Vérification du domaine (DNS)
- Commandes en ligne et orchestration
- Rédaction des mails et configuration
- Lecture des réponses Gmail
- Envoi et relances
- Base de données et tests du dashboard
- Recherche et validation des adresses
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- Statistiques de réponse
- Interface et mascotte Bati

## God Nodes (most connected - your core abstractions)
1. `connect()` - 40 edges
2. `env()` - 26 edges
3. `process()` - 21 edges
4. `index()` - 19 edges
5. `send_now()` - 16 edges
6. `login()` - 15 edges
7. `cmd_run()` - 14 edges
8. `connect()` - 14 edges
9. `add()` - 14 edges
10. `qualify_batch()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `send_all()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/web.py → README.md
- `qualify_batch()` --implements--> `Recherche en parallèle (WORKERS) et cadence de recherche web`  [INFERRED]
  prospec/cli.py → README.md
- `send_followup_now()` --implements--> `Relances dans le même fil (J+7, une seule)`  [INFERRED]
  prospec/cli.py → README.md
- `send_now()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/cli.py → README.md
- `is_suppressed()` --implements--> `Cadre légal B2B (CNIL)`  [INFERRED]
  prospec/db.py → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline de prospection (source, qualification, rédaction, envoi)** — prospec_sourcing, prospec_qualify, prospec_mailer, prospec_cli [INFERRED 0.85]
- **Chaîne de contrôle des adresses avant envoi** — prospec_emails, prospec_dnscheck, prospec_mailer_assert_sourced, prospec_db_is_suppressed [INFERRED 0.85]
- **Suivi après envoi (réponses, relances, pipeline, notifications)** — prospec_inbox, prospec_notify, prospec_cli_send_followup_now, prospec_web_pipeline_action [INFERRED 0.85]

## Communities (14 total, 1 thin omitted)

### Community 0 - "Dashboard web (Flask)"
Cohesion: 0.05
Nodes (50): env(), get_setting(), send_mode(), set_setting(), check_inbox(), clean_now(), close_connection(), collect_now() (+42 more)

### Community 1 - "Vérification du domaine (DNS)"
Cohesion: 0.05
Nodes (31): apply_result(), cmd_clean(), domain_status(), email_ok(), make_resolver(), check(), clean_database(), diagnose() (+23 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.09
Nodes (24): cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source(), cmd_stats() (+16 more)

### Community 3 - "Rédaction des mails et configuration"
Cohesion: 0.09
Nodes (22): sender(), batch_followup_prompt(), batch_prompt(), check_mail(), claude_mail(), compose(), deliver(), describe() (+14 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.12
Nodes (22): is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date(), process() (+14 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.09
Nodes (32): check_can_send(), contact(), remember_message(), send_followup_now(), send_now(), due_followups(), first_send_date(), log_send() (+24 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.12
Nodes (22): connect(), migrate(), _run_send_all(), con(), con(), test_qualify_runs_in_parallel(), client(), login() (+14 more)

### Community 7 - "Recherche et validation des adresses"
Cohesion: 0.06
Nodes (32): inspect(), match_site(), next_queries(), run(), notify(), company_names(), distinctive(), fetch_dept() (+24 more)

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.15
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "test_prospec.py"
Cohesion: 0.07
Nodes (26): decode_cloudflare(), extract_emails(), enseigne_of(), fetch_naf(), metier_for(), parse_result(), pool_size(), source() (+18 more)

### Community 13 - "Statistiques de réponse"
Cohesion: 0.29
Nodes (3): compute(), issue_labels(), Statistiques de réponse

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.38
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)`, `gunicorn (>=22)`, `dnspython (>=2.4)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 136 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `Dashboard web (Flask)`, `Vérification du domaine (DNS)`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Recherche et validation des adresses`, `test_prospec.py`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **What connects `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Dashboard web (Flask)` be split into smaller, more focused modules?**
  _Cohesion score 0.0532724505327245 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `Dashboard web (Flask)` to `Commandes en ligne et orchestration`, `Rédaction des mails et configuration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `Recherche et validation des adresses`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `Vérification du domaine (DNS)` be split into smaller, more focused modules?**
  _Cohesion score 0.05288207297726071 - nodes in this community are weakly interconnected._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.09041835357624832 - nodes in this community are weakly interconnected._
- **Should `Rédaction des mails et configuration` be split into smaller, more focused modules?**
  _Cohesion score 0.08708708708708708 - nodes in this community are weakly interconnected._