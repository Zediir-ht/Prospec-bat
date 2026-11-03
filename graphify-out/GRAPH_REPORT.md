# Graph Report - Prospec-bat  (2026-11-03)

## Corpus Check
- 31 files · ~26,423 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 499 nodes · 1200 edges · 27 communities (24 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b3ae5019`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- web.py
- qualify.py
- Commandes en ligne et orchestration
- Rédaction des mails et configuration
- Lecture des réponses Gmail
- Envoi et relances
- Base de données et tests du dashboard
- osm.py
- email_ok
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- qualify_company
- notify.py
- Interface et mascotte Bati
- run
- next_to_write
- draft_action
- test_emails.py
- apply_result
- dnscheck.py
- emails.py
- search_urls
- extract
- pytest
- clean_database

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

## Communities (27 total, 3 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.05
Nodes (54): get_setting(), now(), send_mode(), set_setting(), next_refresh(), refresh_if_due(), check_inbox(), clean_now() (+46 more)

### Community 1 - "qualify.py"
Cohesion: 0.18
Nodes (5): inspect(), deobfuscate(), fetch(), thread_session(), requests (>=2.31)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.06
Nodes (39): cmd_clean(), cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source() (+31 more)

### Community 3 - "Rédaction des mails et configuration"
Cohesion: 0.07
Nodes (28): env(), sender(), batch_followup_prompt(), batch_prompt(), build_message(), check_mail(), claude_mail(), compose() (+20 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.11
Nodes (21): is_suppressed(), check(), decode(), find_company(), fresh_text(), imap_date(), process(), references() (+13 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.11
Nodes (23): send_now(), due_followups(), sent_today(), compute(), issue_labels(), Envoi groupé « Tout envoyer » sans quota, Statistiques de réponse, add() (+15 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.12
Nodes (25): connect(), first_send_date(), migrate(), suppress(), _run_send_all(), test_suppression(), client(), login() (+17 more)

### Community 7 - "osm.py"
Cohesion: 0.18
Nodes (9): company_names(), distinctive(), fetch_dept(), match(), norm_spaces(), refresh(), same_company(), same_name_and_place() (+1 more)

### Community 8 - "email_ok"
Cohesion: 0.20
Nodes (4): domain_status(), email_ok(), test_dns_check_survives_missing_resolv_conf(), test_domain_status_with_fake_resolver()

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.15
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "test_prospec.py"
Cohesion: 0.13
Nodes (11): decode_cloudflare(), extract_emails(), _cf(), test_check_mail_rejects_price(), test_claude_mail_via_http(), test_emails(), test_extract_emails_obfuscated(), test_migration_marks_old_emails_as_site() (+3 more)

### Community 13 - "qualify_company"
Cohesion: 0.14
Nodes (13): parse_element(), analyse_html(), facebook_page(), name_tokens(), pick_facebook(), pick_site(), places_site(), qualify_company() (+5 more)

### Community 14 - "notify.py"
Cohesion: 0.20
Nodes (5): notify(), start_inbox_poll(), loop(), Notifications de réponse (Termux, ntfy.sh), test_notify_channels()

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.47
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 16 - "run"
Cohesion: 0.22
Nodes (7): match_site(), next_queries(), run(), norm(), test_discovery_links_sites_by_siren_and_name(), test_source_stops_when_pool_is_enough(), fake_fetch()

### Community 17 - "next_to_write"
Cohesion: 0.19
Nodes (8): check_can_send(), next_to_write(), ei_blocked(), in_suppressed(), suppressed_set(), assert_sourced(), test_ei_free_mail_setting(), test_never_send_to_unsourced_address()

### Community 18 - "draft_action"
Cohesion: 0.29
Nodes (5): Dashboard mobile (Flask), Déploiement Docker et disque persistant, Mode review : rien ne part sans validation, Prospec-bat (projet de prospection pour zdrdev.fr), gunicorn (>=22)

### Community 19 - "test_emails.py"
Cohesion: 0.25
Nodes (8): best_email(), add(), con(), test_best_email_ignores_agency(), test_clean_database(), test_cleanup_button_and_report(), test_last_defense_before_sending(), test_search_discards_bad_and_shared_addresses()

### Community 20 - "apply_result"
Cohesion: 0.22
Nodes (6): apply_result(), check(), diagnose(), shared_by_others(), test_check_rejects_garbage(), test_apply_result_keeps_facebook()

### Community 22 - "emails.py"
Cohesion: 0.39
Nodes (4): host_of(), norm(), related(), test_related_domain()

### Community 23 - "search_urls"
Cohesion: 0.40
Nodes (4): search_feedback(), search_urls(), throttle_search(), test_search_throttle_spaces_requests()

### Community 24 - "extract"
Cohesion: 0.50
Nodes (3): extract(), repair(), test_repair_without_inventing()

### Community 26 - "clean_database"
Cohesion: 0.50
Nodes (3): clean_database(), Qualité des adresses (validation, nettoyage, adresses partagées), Vérification du domaine (enregistrement MX)

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)`, `requests (>=2.31)`, `gunicorn (>=22)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 148 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `test_prospec.py`, `qualify_company`, `notify.py`, `run`, `next_to_write`, `test_emails.py`, `apply_result`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **What connects `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05092592592592592 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `Rédaction des mails et configuration` to `web.py`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Base de données et tests du dashboard`, `osm.py`, `qualify_company`, `notify.py`, `run`, `next_to_write`, `search_urls`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.060451977401129946 - nodes in this community are weakly interconnected._
- **Should `Rédaction des mails et configuration` be split into smaller, more focused modules?**
  _Cohesion score 0.07439613526570048 - nodes in this community are weakly interconnected._
- **Should `Lecture des réponses Gmail` be split into smaller, more focused modules?**
  _Cohesion score 0.10634920634920635 - nodes in this community are weakly interconnected._