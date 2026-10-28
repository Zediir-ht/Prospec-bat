# Graph Report - Prospec-bat  (2026-10-28)

## Corpus Check
- 31 files · ~22,528 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 460 nodes · 1080 edges · 15 communities (14 shown, 1 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 55 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `687ddb4a`
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
- Règles : adresses sourcées et cadre légal
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- Sourcing SIRENE et notifications
- Démarrage de session (hook)
- Statistiques de réponse
- Interface et mascotte Bati

## God Nodes (most connected - your core abstractions)
1. `connect()` - 39 edges
2. `env()` - 26 edges
3. `process()` - 21 edges
4. `index()` - 19 edges
5. `send_now()` - 16 edges
6. `cmd_run()` - 14 edges
7. `connect()` - 14 edges
8. `add()` - 14 edges
9. `qualify_batch()` - 13 edges
10. `send_followup_now()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `send_now()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/cli.py → README.md
- `qualify_batch()` --implements--> `Recherche en parallèle (WORKERS) et cadence de recherche web`  [INFERRED]
  prospec/cli.py → README.md
- `cmd_suppress()` --implements--> `Cadre légal B2B (CNIL)`  [INFERRED]
  prospec/cli.py → README.md
- `is_suppressed()` --implements--> `Cadre légal B2B (CNIL)`  [INFERRED]
  prospec/db.py → README.md
- `batch_followup_prompt()` --implements--> `Relances dans le même fil (J+7, une seule)`  [INFERRED]
  prospec/mailer.py → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline de prospection (source, qualification, rédaction, envoi)** — prospec_sourcing, prospec_qualify, prospec_mailer, prospec_cli [INFERRED 0.85]
- **Chaîne de contrôle des adresses avant envoi** — prospec_emails, prospec_dnscheck, prospec_mailer_assert_sourced, prospec_db_is_suppressed [INFERRED 0.85]
- **Suivi après envoi (réponses, relances, pipeline, notifications)** — prospec_inbox, prospec_notify, prospec_cli_send_followup_now, prospec_web_pipeline_action [INFERRED 0.85]

## Communities (15 total, 1 thin omitted)

### Community 0 - "Dashboard web (Flask)"
Cohesion: 0.05
Nodes (47): set_setting(), suppress(), check_inbox(), clean_now(), close_connection(), collect_now(), connect(), cron() (+39 more)

### Community 1 - "Vérification du domaine (DNS)"
Cohesion: 0.06
Nodes (21): cmd_clean(), domain_status(), email_ok(), make_resolver(), clean_database(), Qualité des adresses (validation, nettoyage, adresses partagées), Vérification du domaine (enregistrement MX), dnspython (>=2.4) (+13 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.08
Nodes (30): apply_result(), cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source() (+22 more)

### Community 3 - "Rédaction des mails et configuration"
Cohesion: 0.09
Nodes (22): sender(), batch_followup_prompt(), batch_prompt(), build_message(), check_mail(), claude_mail(), deliver(), describe() (+14 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.12
Nodes (20): is_suppressed(), check(), decode(), find_company(), fresh_text(), imap_date(), process(), references() (+12 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.09
Nodes (30): check_can_send(), contact(), remember_message(), send_followup_now(), send_now(), due_followups(), first_send_date(), in_suppressed() (+22 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.07
Nodes (36): connect(), migrate(), parse_element(), _run_send_all(), _cf(), test_analyse_html(), test_claude_mail_via_http(), test_discovery_links_sites_by_siren_and_name() (+28 more)

### Community 7 - "Recherche et validation des adresses"
Cohesion: 0.06
Nodes (36): inspect(), match_site(), next_queries(), run(), check(), diagnose(), extract(), host_of() (+28 more)

### Community 8 - "Règles : adresses sourcées et cadre légal"
Cohesion: 0.25
Nodes (4): assert_sourced(), Prospec-bat (projet de prospection pour zdrdev.fr), Sources d'adresses email (site, OpenStreetMap, Google Places), test_never_send_to_unsourced_address()

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.15
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "Sourcing SIRENE et notifications"
Cohesion: 0.11
Nodes (13): notify(), enseigne_of(), fetch_naf(), metier_for(), parse_result(), pool_size(), source(), start_inbox_poll() (+5 more)

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

- **Why does `connect()` connect `Base de données et tests du dashboard` to `Dashboard web (Flask)`, `Vérification du domaine (DNS)`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Règles : adresses sourcées et cadre légal`, `Sourcing SIRENE et notifications`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **What connects `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Dashboard web (Flask)` be split into smaller, more focused modules?**
  _Cohesion score 0.05267778753292362 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `Commandes en ligne et orchestration` to `Dashboard web (Flask)`, `Rédaction des mails et configuration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `Recherche et validation des adresses`, `Sourcing SIRENE et notifications`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `Vérification du domaine (DNS)` be split into smaller, more focused modules?**
  _Cohesion score 0.06341463414634146 - nodes in this community are weakly interconnected._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.08181818181818182 - nodes in this community are weakly interconnected._
- **Should `Rédaction des mails et configuration` be split into smaller, more focused modules?**
  _Cohesion score 0.08677098150782361 - nodes in this community are weakly interconnected._