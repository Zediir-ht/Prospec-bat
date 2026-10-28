# Graph Report - Prospec-bat  (2026-10-28)

## Corpus Check
- 31 files · ~23,678 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 471 nodes · 1119 edges · 21 communities (19 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6ae15ada`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- web.py
- Vérification du domaine (DNS)
- Commandes en ligne et orchestration
- Rédaction des mails et configuration
- Lecture des réponses Gmail
- Envoi et relances
- Base de données et tests du dashboard
- osm.py
- dnscheck.py
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- post
- env
- Interface et mascotte Bati
- run_cleanup
- cron
- start_inbox_poll
- frdate
- Dashboard mobile (Flask)

## God Nodes (most connected - your core abstractions)
1. `connect()` - 43 edges
2. `env()` - 26 edges
3. `process()` - 21 edges
4. `index()` - 21 edges
5. `login()` - 17 edges
6. `send_now()` - 16 edges
7. `connect()` - 16 edges
8. `cmd_run()` - 14 edges
9. `add()` - 14 edges
10. `qualify_batch()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `send_now()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/cli.py → README.md
- `draft_action()` --implements--> `Mode review : rien ne part sans validation`  [INFERRED]
  prospec/web.py → README.md
- `qualify_batch()` --implements--> `Recherche en parallèle (WORKERS) et cadence de recherche web`  [INFERRED]
  prospec/cli.py → README.md
- `send_followup_now()` --implements--> `Relances dans le même fil (J+7, une seule)`  [INFERRED]
  prospec/cli.py → README.md
- `is_suppressed()` --implements--> `Cadre légal B2B (CNIL)`  [INFERRED]
  prospec/db.py → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline de prospection (source, qualification, rédaction, envoi)** — prospec_sourcing, prospec_qualify, prospec_mailer, prospec_cli [INFERRED 0.85]
- **Chaîne de contrôle des adresses avant envoi** — prospec_emails, prospec_dnscheck, prospec_mailer_assert_sourced, prospec_db_is_suppressed [INFERRED 0.85]
- **Suivi après envoi (réponses, relances, pipeline, notifications)** — prospec_inbox, prospec_notify, prospec_cli_send_followup_now, prospec_web_pipeline_action [INFERRED 0.85]

## Communities (21 total, 2 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.16
Nodes (9): close_connection(), collect_now(), guard(), _run_collect(), run_now(), start_job(), status(), stop_send() (+1 more)

### Community 1 - "Vérification du domaine (DNS)"
Cohesion: 0.05
Nodes (42): inspect(), match_site(), next_queries(), run(), check(), clean_database(), diagnose(), extract() (+34 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.07
Nodes (29): apply_result(), cmd_clean(), cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run() (+21 more)

### Community 3 - "Rédaction des mails et configuration"
Cohesion: 0.08
Nodes (24): sender(), batch_followup_prompt(), batch_prompt(), build_message(), check_mail(), claude_mail(), compose(), deliver() (+16 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.12
Nodes (22): is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date(), process() (+14 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.08
Nodes (30): check_can_send(), send_followup_now(), send_now(), due_followups(), first_send_date(), in_suppressed(), log_send(), now() (+22 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.12
Nodes (23): connect(), migrate(), _run_send_all(), con(), con(), client(), login(), test_collect_auto_toggle_and_daily_preempts() (+15 more)

### Community 7 - "osm.py"
Cohesion: 0.12
Nodes (14): notify(), company_names(), distinctive(), fetch_dept(), match(), norm_spaces(), parse_element(), refresh() (+6 more)

### Community 8 - "dnscheck.py"
Cohesion: 0.09
Nodes (9): domain_status(), email_ok(), make_resolver(), Vérification du domaine (enregistrement MX), dnspython (>=2.4), pytest (>=8), isolated(), test_dns_check_survives_missing_resolv_conf() (+1 more)

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.13
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "test_prospec.py"
Cohesion: 0.09
Nodes (22): enseigne_of(), fetch_naf(), metier_for(), parse_result(), pool_size(), source(), Recherche par enseigne et par métier + ville, _cf() (+14 more)

### Community 13 - "post"
Cohesion: 0.21
Nodes (14): set_setting(), parse_batch(), check_inbox(), connect(), draft_action(), import_followups(), import_mails(), mark() (+6 more)

### Community 14 - "env"
Cohesion: 0.17
Nodes (13): env(), get_setting(), send_mode(), collect_auto(), due_followups(), hud_counts(), index(), page() (+5 more)

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.47
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 16 - "run_cleanup"
Cohesion: 0.25
Nodes (6): clean_now(), run_cleanup(), send_all(), start_cleanup_once(), start_send(), Envoi groupé « Tout envoyer » sans quota

### Community 17 - "cron"
Cohesion: 0.33
Nodes (4): cron(), health(), login(), manifest()

### Community 18 - "start_inbox_poll"
Cohesion: 0.29
Nodes (4): collect_progress(), start_collect_loop(), loop(), start_inbox_poll()

### Community 20 - "Dashboard mobile (Flask)"
Cohesion: 0.50
Nodes (4): Dashboard mobile (Flask), Déploiement Docker et disque persistant, Mode review : rien ne part sans validation, gunicorn (>=22)

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)`, `gunicorn (>=22)`, `requests (>=2.31)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 138 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `Vérification du domaine (DNS)`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `osm.py`, `test_prospec.py`, `post`, `run_cleanup`, `start_inbox_poll`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **What connects `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Vérification du domaine (DNS)` be split into smaller, more focused modules?**
  _Cohesion score 0.05194805194805195 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `env` to `web.py`, `Vérification du domaine (DNS)`, `Commandes en ligne et orchestration`, `Rédaction des mails et configuration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `osm.py`, `Installation et démarrage Termux`, `cron`, `start_inbox_poll`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.07400555041628122 - nodes in this community are weakly interconnected._
- **Should `Rédaction des mails et configuration` be split into smaller, more focused modules?**
  _Cohesion score 0.08250355618776671 - nodes in this community are weakly interconnected._
- **Should `Lecture des réponses Gmail` be split into smaller, more focused modules?**
  _Cohesion score 0.11553030303030302 - nodes in this community are weakly interconnected._