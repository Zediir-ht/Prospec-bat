# Graph Report - Prospec-bat  (2026-10-28)

## Corpus Check
- 31 files · ~25,624 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 491 nodes · 1177 edges · 20 communities (18 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fabebba5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- web.py
- discovery.py
- Commandes en ligne et orchestration
- Rédaction des mails et configuration
- Lecture des réponses Gmail
- Envoi et relances
- Base de données et tests du dashboard
- run_cleanup
- re
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- qualify.py
- db.py
- Interface et mascotte Bati
- post
- next_to_write
- draft_action
- frdate

## God Nodes (most connected - your core abstractions)
1. `connect()` - 46 edges
2. `env()` - 27 edges
3. `index()` - 23 edges
4. `process()` - 21 edges
5. `login()` - 18 edges
6. `connect()` - 17 edges
7. `send_now()` - 16 edges
8. `qualify_company()` - 15 edges
9. `cmd_run()` - 14 edges
10. `add()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `send_all()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/web.py → README.md
- `qualify_batch()` --implements--> `Recherche en parallèle (WORKERS) et cadence de recherche web`  [INFERRED]
  prospec/cli.py → README.md
- `send_now()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
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

## Communities (20 total, 2 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.13
Nodes (12): close_connection(), collect_now(), cron(), guard(), health(), hud_counts(), manifest(), _run_collect() (+4 more)

### Community 1 - "discovery.py"
Cohesion: 0.09
Nodes (16): inspect(), match_site(), next_queries(), run(), notify(), company_names(), distinctive(), fetch_dept() (+8 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.06
Nodes (34): check_can_send(), cmd_clean(), cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run() (+26 more)

### Community 3 - "Rédaction des mails et configuration"
Cohesion: 0.07
Nodes (25): sender(), batch_followup_prompt(), batch_prompt(), build_message(), check_mail(), claude_mail(), compose(), deliver() (+17 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.12
Nodes (22): is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date(), process() (+14 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.09
Nodes (26): send_now(), due_followups(), first_send_date(), sent_today(), compute(), issue_labels(), sent_today(), Envoi groupé « Tout envoyer » sans quota (+18 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.14
Nodes (23): connect(), migrate(), _run_send_all(), test_qualify_runs_in_parallel(), client(), login(), test_collect_auto_toggle_and_daily_preempts(), test_collect_progress() (+15 more)

### Community 7 - "run_cleanup"
Cohesion: 0.15
Nodes (10): clean_now(), run_cleanup(), send_all(), start_cleanup_once(), start_collect_loop(), loop(), start_inbox_poll(), loop() (+2 more)

### Community 8 - "re"
Cohesion: 0.07
Nodes (19): apply_result(), domain_status(), email_ok(), make_resolver(), Vérification du domaine (enregistrement MX), dnspython (>=2.4), pytest (>=8), isolated() (+11 more)

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.15
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "test_prospec.py"
Cohesion: 0.09
Nodes (22): enseigne_of(), fetch_naf(), metier_for(), next_refresh(), parse_result(), pool_size(), refresh_days(), refresh_if_due() (+14 more)

### Community 13 - "qualify.py"
Cohesion: 0.06
Nodes (35): check(), clean_database(), diagnose(), extract(), host_of(), norm(), related(), repair() (+27 more)

### Community 14 - "db.py"
Cohesion: 0.17
Nodes (13): target(), env(), get_setting(), send_mode(), collect_auto(), due_followups(), index(), login() (+5 more)

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.38
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 16 - "post"
Cohesion: 0.20
Nodes (14): now(), set_setting(), check_inbox(), connect(), followup_action(), mark(), pipeline_action(), set_mode() (+6 more)

### Community 17 - "next_to_write"
Cohesion: 0.22
Nodes (6): next_to_write(), in_suppressed(), suppressed_set(), parse_batch(), import_followups(), import_mails()

### Community 18 - "draft_action"
Cohesion: 0.40
Nodes (5): draft_action(), Dashboard mobile (Flask), Déploiement Docker et disque persistant, Mode review : rien ne part sans validation, gunicorn (>=22)

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)`, `gunicorn (>=22)`, `requests (>=2.31)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 145 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `run_cleanup`, `re`, `test_prospec.py`, `qualify.py`, `db.py`, `post`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **What connects `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12554112554112554 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `db.py` to `web.py`, `discovery.py`, `Commandes en ligne et orchestration`, `Rédaction des mails et configuration`, `Lecture des réponses Gmail`, `Base de données et tests du dashboard`, `run_cleanup`, `test_prospec.py`, `qualify.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `discovery.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08636977058029689 - nodes in this community are weakly interconnected._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.06313497822931785 - nodes in this community are weakly interconnected._
- **Should `Rédaction des mails et configuration` be split into smaller, more focused modules?**
  _Cohesion score 0.07084785133565621 - nodes in this community are weakly interconnected._