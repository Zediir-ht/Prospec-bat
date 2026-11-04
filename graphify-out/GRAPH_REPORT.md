# Graph Report - Prospec-bat  (2026-11-04)

## Corpus Check
- 32 files · ~28,735 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 534 nodes · 1291 edges · 31 communities (27 shown, 4 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `20e33aa2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- web.py
- post
- Commandes en ligne et orchestration
- parse_batch
- Lecture des réponses Gmail
- Envoi et relances
- Base de données et tests du dashboard
- index
- email_ok
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- sourcing.py
- Démarrage de session (hook)
- qualify.py
- run_cleanup
- Interface et mascotte Bati
- batch_followup_prompt
- test_prospec.py
- Prospec-bat (projet de prospection pour zdrdev.fr)
- test_emails.py
- apply_result
- dnscheck.py
- emails.py
- frdate
- check_mail
- pytest
- clean_database
- FakeSMTP
- build_message
- facebook_message
- start_job

## God Nodes (most connected - your core abstractions)
1. `connect()` - 50 edges
2. `env()` - 32 edges
3. `index()` - 25 edges
4. `process()` - 21 edges
5. `connect()` - 19 edges
6. `login()` - 19 edges
7. `send_now()` - 16 edges
8. `next_to_write()` - 15 edges
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
- `cmd_suppress()` --implements--> `Cadre légal B2B (CNIL)`  [INFERRED]
  prospec/cli.py → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline de prospection (source, qualification, rédaction, envoi)** — prospec_sourcing, prospec_qualify, prospec_mailer, prospec_cli [INFERRED 0.85]
- **Chaîne de contrôle des adresses avant envoi** — prospec_emails, prospec_dnscheck, prospec_mailer_assert_sourced, prospec_db_is_suppressed [INFERRED 0.85]
- **Suivi après envoi (réponses, relances, pipeline, notifications)** — prospec_inbox, prospec_notify, prospec_cli_send_followup_now, prospec_web_pipeline_action [INFERRED 0.85]

## Communities (31 total, 4 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.13
Nodes (10): close_connection(), cron(), guard(), health(), login(), manifest(), send_all(), start_send() (+2 more)

### Community 1 - "post"
Cohesion: 0.15
Nodes (17): set_setting(), check_inbox(), connect(), draft_action(), import_followups(), mark(), pipeline_action(), set_mode() (+9 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.06
Nodes (38): check_can_send(), cmd_bounces(), cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run() (+30 more)

### Community 3 - "parse_batch"
Cohesion: 0.21
Nodes (8): batch_prompt(), _objects(), parse_batch(), import_mails(), Rédaction des mails par Claude (API ou copier-coller), Rédiger sans limite : copie de toutes les demandes, lots, test_batch_prompt_and_parse(), test_parse_batch_tolerates_truncated_or_bracketless_text()

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.10
Nodes (24): sender(), is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date() (+16 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.08
Nodes (32): send_followup_now(), send_now(), due_followups(), first_send_date(), in_suppressed(), log_send(), now(), sent_today() (+24 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.12
Nodes (25): connect(), migrate(), _run_send_all(), con(), con(), client(), login(), test_collect_auto_toggle_and_daily_preempts() (+17 more)

### Community 7 - "index"
Cohesion: 0.17
Nodes (12): get_setting(), send_mode(), collect_auto(), due_followups(), hud_counts(), index(), page(), pipeline_rows() (+4 more)

### Community 8 - "email_ok"
Cohesion: 0.18
Nodes (5): domain_status(), email_ok(), Vérification du domaine (enregistrement MX), test_dns_check_survives_missing_resolv_conf(), test_domain_status_with_fake_resolver()

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.13
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "sourcing.py"
Cohesion: 0.15
Nodes (13): enseigne_of(), fetch_naf(), metier_for(), next_refresh(), parse_result(), pool_size(), refresh_days(), refresh_if_due() (+5 more)

### Community 13 - "qualify.py"
Cohesion: 0.05
Nodes (36): inspect(), match_site(), next_queries(), run(), notify(), company_names(), distinctive(), fetch_dept() (+28 more)

### Community 14 - "run_cleanup"
Cohesion: 0.15
Nodes (9): clean_now(), collect_progress(), run_cleanup(), start_cleanup_once(), start_collect_loop(), loop(), start_inbox_poll(), loop() (+1 more)

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.38
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 16 - "batch_followup_prompt"
Cohesion: 0.25
Nodes (5): batch_followup_prompt(), describe(), followup_mail(), prompt_parts(), Relances dans le même fil (J+7, une seule)

### Community 17 - "test_prospec.py"
Cohesion: 0.13
Nodes (13): decode_cloudflare(), extract_emails(), _cf(), test_emails(), test_extract_emails_obfuscated(), test_migration_marks_old_emails_as_site(), test_osm_matches_on_enseigne(), test_parallel_stops_near_target() (+5 more)

### Community 18 - "Prospec-bat (projet de prospection pour zdrdev.fr)"
Cohesion: 0.33
Nodes (4): Dashboard mobile (Flask), Déploiement Docker et disque persistant, Prospec-bat (projet de prospection pour zdrdev.fr), gunicorn (>=22)

### Community 19 - "test_emails.py"
Cohesion: 0.29
Nodes (8): best_email(), add(), test_best_email_ignores_agency(), test_clean_database(), test_cleanup_button_and_report(), test_last_defense_before_sending(), test_related_domain(), test_search_discards_bad_and_shared_addresses()

### Community 20 - "apply_result"
Cohesion: 0.22
Nodes (6): apply_result(), check(), diagnose(), shared_by_others(), test_check_rejects_garbage(), test_apply_result_keeps_facebook()

### Community 21 - "dnscheck.py"
Cohesion: 0.16
Nodes (6): mailbox_status(), make_resolver(), _mx_hosts(), _rcpt(), dnspython (>=2.4), test_mailbox_probe()

### Community 22 - "emails.py"
Cohesion: 0.28
Nodes (6): extract(), host_of(), norm(), related(), repair(), test_repair_without_inventing()

### Community 24 - "check_mail"
Cohesion: 0.20
Nodes (6): check_mail(), claude_mail(), compose(), test_check_mail_rejects_price(), test_claude_mail_via_http(), test_price_check_only_flags_whole_words()

### Community 26 - "clean_database"
Cohesion: 0.67
Nodes (3): cmd_clean(), clean_database(), Qualité des adresses (validation, nettoyage, adresses partagées)

### Community 28 - "build_message"
Cohesion: 0.27
Nodes (7): build_message(), deliver(), format_phone(), signature(), test_signature_has_contact_details(), test_signature_has_optout_and_no_price(), test_signature_mentions_email_source()

### Community 29 - "facebook_message"
Cohesion: 0.40
Nodes (3): facebook_message(), messenger_link(), test_facebook_message_tone()

### Community 30 - "start_job"
Cohesion: 0.67
Nodes (4): collect_now(), _run_collect(), run_now(), start_job()

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)`, `requests (>=2.31)`, `gunicorn (>=22)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 166 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `post`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `sourcing.py`, `qualify.py`, `run_cleanup`, `test_prospec.py`, `test_emails.py`, `apply_result`, `start_job`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **What connects `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13157894736842105 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `Commandes en ligne et orchestration` to `web.py`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `index`, `Installation et démarrage Termux`, `sourcing.py`, `qualify.py`, `run_cleanup`, `dnscheck.py`, `check_mail`, `start_job`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.05952380952380952 - nodes in this community are weakly interconnected._
- **Should `Lecture des réponses Gmail` be split into smaller, more focused modules?**
  _Cohesion score 0.1021021021021021 - nodes in this community are weakly interconnected._
- **Should `Envoi et relances` be split into smaller, more focused modules?**
  _Cohesion score 0.07676767676767676 - nodes in this community are weakly interconnected._