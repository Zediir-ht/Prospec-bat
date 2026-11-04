# Graph Report - Prospec-bat  (2026-11-04)

## Corpus Check
- 32 files · ~29,302 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 542 nodes · 1309 edges · 31 communities (24 shown, 7 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a2ee27ea`
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
- qualify.py
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- osm.py
- set_setting
- Interface et mascotte Bati
- next_to_write
- qualify_company
- draft_action
- assert_sourced
- check_can_send
- discovery.py
- dnscheck.py
- frdate
- re
- FakeSMTP
- cron
- apply_result
- contacted_emails
- best_email
- test_claude_mail_via_http

## God Nodes (most connected - your core abstractions)
1. `connect()` - 52 edges
2. `env()` - 32 edges
3. `index()` - 26 edges
4. `process()` - 21 edges
5. `login()` - 20 edges
6. `connect()` - 19 edges
7. `next_to_write()` - 17 edges
8. `send_now()` - 16 edges
9. `cmd_run()` - 15 edges
10. `mailbox_status()` - 15 edges

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

## Communities (31 total, 7 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.12
Nodes (15): clean_now(), close_connection(), collect_now(), guard(), run_cleanup(), _run_collect(), run_now(), send_all() (+7 more)

### Community 1 - "post"
Cohesion: 0.17
Nodes (15): check_inbox(), connect(), import_followups(), import_mails(), mark(), pipeline_action(), set_mode(), social_action() (+7 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.06
Nodes (34): cmd_bounces(), cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source() (+26 more)

### Community 3 - "mailer.py"
Cohesion: 0.08
Nodes (28): env(), sender(), batch_followup_prompt(), batch_prompt(), check_mail(), claude_mail(), compose(), describe() (+20 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.07
Nodes (27): is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date(), process() (+19 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.08
Nodes (32): contact(), remember_message(), send_followup_now(), send_now(), due_followups(), first_send_date(), log_send(), now() (+24 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.14
Nodes (24): connect(), migrate(), _run_send_all(), client(), login(), test_collect_auto_toggle_and_daily_preempts(), test_collect_progress(), test_company_names_are_escaped() (+16 more)

### Community 7 - "index"
Cohesion: 0.17
Nodes (12): get_setting(), send_mode(), collect_auto(), due_followups(), hud_counts(), index(), page(), pipeline_rows() (+4 more)

### Community 8 - "qualify.py"
Cohesion: 0.16
Nodes (9): decode_cloudflare(), deobfuscate(), extract_emails(), search_feedback(), search_urls(), throttle_search(), requests (>=2.31), test_emails() (+1 more)

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.15
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "test_prospec.py"
Cohesion: 0.15
Nodes (12): _cf(), test_extract_emails_obfuscated(), test_migration_marks_old_emails_as_site(), test_osm_matches_on_enseigne(), test_parallel_stops_near_target(), test_pick_site_skips_directories(), test_qualify_keeps_osm_email(), test_qualify_runs_in_parallel() (+4 more)

### Community 13 - "osm.py"
Cohesion: 0.18
Nodes (12): match_site(), company_names(), distinctive(), fetch_dept(), match(), norm_spaces(), parse_element(), same_company() (+4 more)

### Community 14 - "set_setting"
Cohesion: 0.33
Nodes (6): set_setting(), next_refresh(), refresh_days(), refresh_if_due(), collect_progress(), test_sourcing_refresh_after_full_round()

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.47
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 16 - "next_to_write"
Cohesion: 0.15
Nodes (5): held_back(), address_class(), bounce_table(), risky_classes(), test_risky_address_types_are_held_back()

### Community 17 - "qualify_company"
Cohesion: 0.17
Nodes (9): analyse_html(), facebook_page(), norm(), pick_facebook(), pick_site(), places_site(), qualify_company(), test_analyse_html() (+1 more)

### Community 18 - "draft_action"
Cohesion: 0.40
Nodes (5): draft_action(), Dashboard mobile (Flask), Déploiement Docker et disque persistant, Mode review : rien ne part sans validation, gunicorn (>=22)

### Community 20 - "check_can_send"
Cohesion: 0.21
Nodes (7): check_can_send(), next_to_write(), ei_blocked(), in_suppressed(), suppressed_set(), test_ei_free_mail_setting(), test_never_write_or_send_twice_to_the_same_address()

### Community 21 - "discovery.py"
Cohesion: 0.21
Nodes (6): inspect(), next_queries(), run(), fetch(), thread_session(), test_discovery_links_sites_by_siren_and_name()

### Community 22 - "dnscheck.py"
Cohesion: 0.05
Nodes (25): cmd_clean(), domain_status(), email_ok(), mailbox_status(), make_resolver(), _mx_hosts(), _rcpt(), clean_database() (+17 more)

### Community 24 - "re"
Cohesion: 0.26
Nodes (7): extract(), host_of(), norm(), related(), repair(), name_tokens(), test_repair_without_inventing()

### Community 26 - "cron"
Cohesion: 0.33
Nodes (4): cron(), health(), login(), manifest()

### Community 27 - "apply_result"
Cohesion: 0.29
Nodes (5): apply_result(), check(), test_check_rejects_garbage(), test_apply_result_keeps_facebook(), test_unknown_mailbox_blocks_address_and_send()

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)`, `requests (>=2.31)`, `gunicorn (>=22)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 170 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `post`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `test_prospec.py`, `osm.py`, `set_setting`, `next_to_write`, `assert_sourced`, `check_can_send`, `discovery.py`, `dnscheck.py`, `apply_result`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **What connects `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11692307692307692 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `mailer.py` to `web.py`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `index`, `qualify.py`, `osm.py`, `set_setting`, `next_to_write`, `qualify_company`, `check_can_send`, `discovery.py`, `dnscheck.py`, `cron`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.06328320802005012 - nodes in this community are weakly interconnected._
- **Should `mailer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0753045404208195 - nodes in this community are weakly interconnected._
- **Should `Lecture des réponses Gmail` be split into smaller, more focused modules?**
  _Cohesion score 0.07400555041628122 - nodes in this community are weakly interconnected._