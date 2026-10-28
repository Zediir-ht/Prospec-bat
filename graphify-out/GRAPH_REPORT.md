# Graph Report - Prospec-bat  (2026-10-28)

## Corpus Check
- 31 files · ~23,324 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 468 nodes · 1111 edges · 14 communities (13 shown, 1 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `14f73a4d`
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
- discovery.py
- dnscheck.py
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- Interface et mascotte Bati

## God Nodes (most connected - your core abstractions)
1. `connect()` - 42 edges
2. `env()` - 26 edges
3. `process()` - 21 edges
4. `index()` - 20 edges
5. `send_now()` - 16 edges
6. `connect()` - 16 edges
7. `login()` - 16 edges
8. `cmd_run()` - 14 edges
9. `add()` - 14 edges
10. `qualify_batch()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `send_all()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/web.py → README.md
- `qualify_batch()` --implements--> `Recherche en parallèle (WORKERS) et cadence de recherche web`  [INFERRED]
  prospec/cli.py → README.md
- `send_now()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/cli.py → README.md
- `is_suppressed()` --implements--> `Cadre légal B2B (CNIL)`  [INFERRED]
  prospec/db.py → README.md
- `check_mail()` --implements--> `Angle : maquette de site gratuite, aucun prix`  [EXTRACTED]
  prospec/mailer.py → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline de prospection (source, qualification, rédaction, envoi)** — prospec_sourcing, prospec_qualify, prospec_mailer, prospec_cli [INFERRED 0.85]
- **Chaîne de contrôle des adresses avant envoi** — prospec_emails, prospec_dnscheck, prospec_mailer_assert_sourced, prospec_db_is_suppressed [INFERRED 0.85]
- **Suivi après envoi (réponses, relances, pipeline, notifications)** — prospec_inbox, prospec_notify, prospec_cli_send_followup_now, prospec_web_pipeline_action [INFERRED 0.85]

## Communities (14 total, 1 thin omitted)

### Community 0 - "Dashboard web (Flask)"
Cohesion: 0.05
Nodes (54): env(), get_setting(), send_mode(), set_setting(), check_inbox(), clean_now(), close_connection(), collect_auto() (+46 more)

### Community 1 - "Vérification du domaine (DNS)"
Cohesion: 0.06
Nodes (36): apply_result(), cmd_clean(), email_ok(), check(), clean_database(), diagnose(), extract(), host_of() (+28 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.10
Nodes (22): cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source(), cmd_stats() (+14 more)

### Community 3 - "Rédaction des mails et configuration"
Cohesion: 0.06
Nodes (34): check_can_send(), contact(), remember_message(), send_followup_now(), send_now(), sender(), log_send(), now() (+26 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.12
Nodes (22): is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date(), process() (+14 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.09
Nodes (24): due_followups(), first_send_date(), in_suppressed(), migrate(), sent_today(), suppressed_set(), compute(), issue_labels() (+16 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.13
Nodes (22): connect(), _run_send_all(), con(), con(), test_qualify_runs_in_parallel(), client(), login(), test_collect_auto_toggle_and_daily_preempts() (+14 more)

### Community 7 - "discovery.py"
Cohesion: 0.10
Nodes (20): inspect(), match_site(), next_queries(), run(), company_names(), distinctive(), fetch_dept(), match() (+12 more)

### Community 8 - "dnscheck.py"
Cohesion: 0.12
Nodes (6): domain_status(), make_resolver(), Vérification du domaine (enregistrement MX), dnspython (>=2.4), test_dns_check_survives_missing_resolv_conf(), test_domain_status_with_fake_resolver()

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.09
Nodes (11): install-boot.sh script, install.sh script, notify(), Démarrage automatique sous Termux (Termux:Boot), Notifications de réponse (Termux, ntfy.sh), running(), server.sh script, start() (+3 more)

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "test_prospec.py"
Cohesion: 0.07
Nodes (26): enseigne_of(), fetch_naf(), metier_for(), parse_result(), pool_size(), source(), Recherche par enseigne et par métier + ville, pytest (>=8) (+18 more)

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.38
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)`, `gunicorn (>=22)`, `requests (>=2.31)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 137 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `Dashboard web (Flask)`, `Vérification du domaine (DNS)`, `Commandes en ligne et orchestration`, `Rédaction des mails et configuration`, `Lecture des réponses Gmail`, `Envoi et relances`, `discovery.py`, `test_prospec.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **What connects `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Dashboard web (Flask)` be split into smaller, more focused modules?**
  _Cohesion score 0.052614052614052616 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `Dashboard web (Flask)` to `Vérification du domaine (DNS)`, `Commandes en ligne et orchestration`, `Rédaction des mails et configuration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `discovery.py`, `Installation et démarrage Termux`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `Vérification du domaine (DNS)` be split into smaller, more focused modules?**
  _Cohesion score 0.059907834101382486 - nodes in this community are weakly interconnected._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.10420168067226891 - nodes in this community are weakly interconnected._
- **Should `Rédaction des mails et configuration` be split into smaller, more focused modules?**
  _Cohesion score 0.0632996632996633 - nodes in this community are weakly interconnected._