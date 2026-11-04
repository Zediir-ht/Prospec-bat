# Graph Report - Prospec-bat  (2026-11-04)

## Corpus Check
- 32 files · ~29,507 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 547 nodes · 1321 edges · 25 communities (22 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 60 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3e5f3619`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- web.py
- post
- Commandes en ligne et orchestration
- mailer.py
- Lecture des réponses Gmail
- Envoi et relances
- Base de données et tests du dashboard
- index
- search_urls
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- osm.py
- sourcing.py
- Interface et mascotte Bati
- next_to_write
- qualify.py
- draft_action
- run_cleanup
- collect_progress
- discovery.py
- dnscheck.py
- frdate
- FakeSMTP

## God Nodes (most connected - your core abstractions)
1. `connect()` - 53 edges
2. `env()` - 32 edges
3. `index()` - 26 edges
4. `process()` - 21 edges
5. `login()` - 21 edges
6. `connect()` - 20 edges
7. `next_to_write()` - 17 edges
8. `send_now()` - 16 edges
9. `cmd_run()` - 15 edges
10. `main()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `send_now()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/cli.py → README.md
- `qualify_batch()` --implements--> `Recherche en parallèle (WORKERS) et cadence de recherche web`  [INFERRED]
  prospec/cli.py → README.md
- `is_suppressed()` --implements--> `Cadre légal B2B (CNIL)`  [INFERRED]
  prospec/db.py → README.md
- `batch_followup_prompt()` --implements--> `Relances dans le même fil (J+7, une seule)`  [INFERRED]
  prospec/mailer.py → README.md
- `check_mail()` --implements--> `Angle : maquette de site gratuite, aucun prix`  [EXTRACTED]
  prospec/mailer.py → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline de prospection (source, qualification, rédaction, envoi)** — prospec_sourcing, prospec_qualify, prospec_mailer, prospec_cli [INFERRED 0.85]
- **Chaîne de contrôle des adresses avant envoi** — prospec_emails, prospec_dnscheck, prospec_mailer_assert_sourced, prospec_db_is_suppressed [INFERRED 0.85]
- **Suivi après envoi (réponses, relances, pipeline, notifications)** — prospec_inbox, prospec_notify, prospec_cli_send_followup_now, prospec_web_pipeline_action [INFERRED 0.85]

## Communities (25 total, 3 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.13
Nodes (12): close_connection(), collect_now(), cron(), guard(), health(), login(), manifest(), _run_collect() (+4 more)

### Community 1 - "post"
Cohesion: 0.12
Nodes (20): reset_drafts(), set_setting(), suppress(), check_inbox(), clear_drafts(), connect(), import_followups(), mark() (+12 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.09
Nodes (24): cmd_bounces(), cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_reset_drafts(), cmd_run() (+16 more)

### Community 3 - "mailer.py"
Cohesion: 0.06
Nodes (31): env(), sender(), batch_followup_prompt(), batch_prompt(), build_message(), check_mail(), claude_mail(), compose() (+23 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.08
Nodes (23): is_suppressed(), check(), decode(), find_company(), fresh_text(), imap_date(), process(), references() (+15 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.08
Nodes (31): contact(), remember_message(), send_followup_now(), send_now(), due_followups(), first_send_date(), log_send(), now() (+23 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.11
Nodes (27): connect(), migrate(), _run_send_all(), con(), test_qualify_runs_in_parallel(), client(), login(), test_clear_ready_mails() (+19 more)

### Community 7 - "index"
Cohesion: 0.17
Nodes (12): get_setting(), send_mode(), collect_auto(), due_followups(), hud_counts(), index(), page(), pipeline_rows() (+4 more)

### Community 8 - "search_urls"
Cohesion: 0.40
Nodes (4): search_feedback(), search_urls(), throttle_search(), test_search_throttle_spaces_requests()

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.15
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "test_prospec.py"
Cohesion: 0.14
Nodes (13): decode_cloudflare(), extract_emails(), _cf(), test_discovery_links_sites_by_siren_and_name(), test_emails(), test_extract_emails_obfuscated(), test_metier_for_other_sectors(), test_migration_marks_old_emails_as_site() (+5 more)

### Community 13 - "osm.py"
Cohesion: 0.14
Nodes (15): company_names(), distinctive(), fetch_dept(), match(), norm_spaces(), parse_element(), refresh(), same_company() (+7 more)

### Community 14 - "sourcing.py"
Cohesion: 0.15
Nodes (12): enseigne_of(), fetch_naf(), metier_for(), next_refresh(), parse_result(), pool_size(), refresh_days(), refresh_if_due() (+4 more)

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.47
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 16 - "next_to_write"
Cohesion: 0.08
Nodes (17): check_can_send(), held_back(), next_to_write(), ei_blocked(), contacted_emails(), in_suppressed(), purge_drafts(), suppressed_set() (+9 more)

### Community 17 - "qualify.py"
Cohesion: 0.11
Nodes (11): analyse_html(), best_email(), deobfuscate(), name_tokens(), pick_site(), places_site(), qualify_company(), Sources d'adresses email (site, OpenStreetMap, Google Places) (+3 more)

### Community 18 - "draft_action"
Cohesion: 0.40
Nodes (5): draft_action(), Dashboard mobile (Flask), Déploiement Docker et disque persistant, Mode review : rien ne part sans validation, gunicorn (>=22)

### Community 19 - "run_cleanup"
Cohesion: 0.25
Nodes (6): clean_now(), run_cleanup(), send_all(), start_cleanup_once(), start_send(), Envoi groupé « Tout envoyer » sans quota

### Community 20 - "collect_progress"
Cohesion: 0.22
Nodes (6): collect_progress(), start_collect_loop(), loop(), start_inbox_poll(), loop(), Notifications de réponse (Termux, ntfy.sh)

### Community 21 - "discovery.py"
Cohesion: 0.22
Nodes (7): inspect(), match_site(), next_queries(), run(), fetch(), norm(), thread_session()

### Community 22 - "dnscheck.py"
Cohesion: 0.05
Nodes (34): apply_result(), cmd_clean(), domain_status(), email_ok(), mailbox_status(), make_resolver(), _mx_hosts(), _rcpt() (+26 more)

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)`, `gunicorn (>=22)`, `dnspython (>=2.4)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 171 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `post`, `Commandes en ligne et orchestration`, `Envoi et relances`, `test_prospec.py`, `osm.py`, `sourcing.py`, `next_to_write`, `run_cleanup`, `collect_progress`, `dnscheck.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **What connects `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1341991341991342 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `mailer.py` to `web.py`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `index`, `search_urls`, `osm.py`, `sourcing.py`, `next_to_write`, `qualify.py`, `collect_progress`, `discovery.py`, `dnscheck.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Should `post` be split into smaller, more focused modules?**
  _Cohesion score 0.12333333333333334 - nodes in this community are weakly interconnected._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.09176788124156546 - nodes in this community are weakly interconnected._
- **Should `mailer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06274509803921569 - nodes in this community are weakly interconnected._