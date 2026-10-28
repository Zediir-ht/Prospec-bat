# Graph Report - Prospec-bat  (2026-10-28)

## Corpus Check
- 31 files · ~23,932 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 477 nodes · 1141 edges · 14 communities (13 shown, 1 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1964de71`
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
- notify.py
- re
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- Interface et mascotte Bati

## God Nodes (most connected - your core abstractions)
1. `connect()` - 44 edges
2. `env()` - 27 edges
3. `process()` - 21 edges
4. `index()` - 21 edges
5. `login()` - 17 edges
6. `send_now()` - 16 edges
7. `connect()` - 16 edges
8. `cmd_run()` - 14 edges
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

### Community 0 - "web.py"
Cohesion: 0.05
Nodes (53): get_setting(), send_mode(), set_setting(), parse_batch(), check_inbox(), clean_now(), close_connection(), collect_auto() (+45 more)

### Community 1 - "Vérification du domaine (DNS)"
Cohesion: 0.06
Nodes (34): env(), inspect(), match_site(), next_queries(), run(), company_names(), distinctive(), fetch_dept() (+26 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.07
Nodes (31): cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source(), cmd_stats() (+23 more)

### Community 3 - "Rédaction des mails et configuration"
Cohesion: 0.07
Nodes (24): batch_followup_prompt(), batch_prompt(), build_message(), check_mail(), claude_mail(), compose(), deliver(), describe() (+16 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.12
Nodes (22): sender(), is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date() (+14 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.08
Nodes (29): check_can_send(), send_followup_now(), send_now(), due_followups(), first_send_date(), in_suppressed(), log_send(), now() (+21 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.12
Nodes (23): connect(), migrate(), _run_send_all(), con(), con(), client(), login(), test_collect_auto_toggle_and_daily_preempts() (+15 more)

### Community 7 - "notify.py"
Cohesion: 0.20
Nodes (5): notify(), start_inbox_poll(), loop(), Notifications de réponse (Termux, ntfy.sh), test_notify_channels()

### Community 8 - "re"
Cohesion: 0.06
Nodes (29): apply_result(), cmd_clean(), domain_status(), email_ok(), make_resolver(), check(), clean_database(), diagnose() (+21 more)

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.15
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "test_prospec.py"
Cohesion: 0.08
Nodes (25): enseigne_of(), fetch_naf(), metier_for(), next_refresh(), parse_result(), pool_size(), refresh_days(), refresh_if_due() (+17 more)

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.47
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `flask (>=3.0)`, `requests (>=2.31)`, `Suivi des prospects (de la réponse au client)`, `gunicorn (>=22)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 140 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `Vérification du domaine (DNS)`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `notify.py`, `re`, `test_prospec.py`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **What connects `PATH`, `flask (>=3.0)`, `requests (>=2.31)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05126452494873548 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `Vérification du domaine (DNS)` to `web.py`, `Commandes en ligne et orchestration`, `Rédaction des mails et configuration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `notify.py`, `test_prospec.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Should `Vérification du domaine (DNS)` be split into smaller, more focused modules?**
  _Cohesion score 0.061057692307692306 - nodes in this community are weakly interconnected._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.06887755102040816 - nodes in this community are weakly interconnected._
- **Should `Rédaction des mails et configuration` be split into smaller, more focused modules?**
  _Cohesion score 0.07073170731707316 - nodes in this community are weakly interconnected._