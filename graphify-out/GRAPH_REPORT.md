# Graph Report - Prospec-bat  (2026-11-04)

## Corpus Check
- 32 files · ~28,148 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 529 nodes · 1278 edges · 31 communities (25 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `71597c58`
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
- test_dns_check_survives_missing_resolv_conf
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- sourcing.py
- Démarrage de session (hook)
- qualify.py
- collect_progress
- Interface et mascotte Bati
- run_cleanup
- test_prospec.py
- draft_action
- test_emails.py
- apply_result
- dnscheck.py
- emails.py
- frdate
- mailer.py
- pytest
- diagnose
- FakeSMTP
- build_message
- facebook_message
- test_claude_mail_via_http

## God Nodes (most connected - your core abstractions)
1. `connect()` - 49 edges
2. `env()` - 32 edges
3. `index()` - 25 edges
4. `process()` - 21 edges
5. `login()` - 18 edges
6. `connect()` - 17 edges
7. `send_now()` - 16 edges
8. `next_to_write()` - 15 edges
9. `cmd_run()` - 15 edges
10. `mailbox_status()` - 15 edges

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

## Communities (31 total, 6 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.13
Nodes (12): close_connection(), collect_now(), cron(), guard(), health(), login(), manifest(), _run_collect() (+4 more)

### Community 1 - "post"
Cohesion: 0.19
Nodes (16): now(), set_setting(), check_inbox(), connect(), followup_action(), import_followups(), import_mails(), mark() (+8 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.06
Nodes (35): cmd_bounces(), cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source() (+27 more)

### Community 3 - "parse_batch"
Cohesion: 0.17
Nodes (11): batch_followup_prompt(), batch_prompt(), check_mail(), _objects(), parse_batch(), Rédaction des mails par Claude (API ou copier-coller), Rédiger sans limite : copie de toutes les demandes, lots, test_batch_followup_prompt_and_import() (+3 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.10
Nodes (25): sender(), is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date() (+17 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.07
Nodes (32): contact(), remember_message(), send_followup_now(), send_now(), due_followups(), first_send_date(), in_suppressed(), log_send() (+24 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.12
Nodes (24): connect(), migrate(), _run_send_all(), con(), con(), client(), login(), test_collect_auto_toggle_and_daily_preempts() (+16 more)

### Community 7 - "index"
Cohesion: 0.17
Nodes (12): get_setting(), send_mode(), collect_auto(), due_followups(), hud_counts(), index(), page(), pipeline_rows() (+4 more)

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.14
Nodes (8): install-boot.sh script, install.sh script, Démarrage automatique sous Termux (Termux:Boot), running(), server.sh script, start(), stop(), start.sh script

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "sourcing.py"
Cohesion: 0.09
Nodes (16): notify(), enseigne_of(), fetch_naf(), metier_for(), next_refresh(), parse_result(), pool_size(), refresh_days() (+8 more)

### Community 13 - "qualify.py"
Cohesion: 0.06
Nodes (34): inspect(), match_site(), next_queries(), run(), company_names(), distinctive(), match(), norm_spaces() (+26 more)

### Community 14 - "collect_progress"
Cohesion: 0.25
Nodes (5): collect_progress(), start_collect_loop(), loop(), start_inbox_poll(), Notifications de réponse (Termux, ntfy.sh)

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.38
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 16 - "run_cleanup"
Cohesion: 0.29
Nodes (5): clean_now(), run_cleanup(), send_all(), start_cleanup_once(), start_send()

### Community 17 - "test_prospec.py"
Cohesion: 0.12
Nodes (13): assert_sourced(), decode_cloudflare(), extract_emails(), _cf(), test_emails(), test_extract_emails_obfuscated(), test_metier_for_other_sectors(), test_migration_marks_old_emails_as_site() (+5 more)

### Community 18 - "draft_action"
Cohesion: 0.40
Nodes (5): draft_action(), Dashboard mobile (Flask), Déploiement Docker et disque persistant, Mode review : rien ne part sans validation, gunicorn (>=22)

### Community 19 - "test_emails.py"
Cohesion: 0.29
Nodes (8): best_email(), add(), test_best_email_ignores_agency(), test_clean_database(), test_cleanup_button_and_report(), test_last_defense_before_sending(), test_related_domain(), test_search_discards_bad_and_shared_addresses()

### Community 20 - "apply_result"
Cohesion: 0.16
Nodes (8): apply_result(), check_can_send(), email_ok(), check(), test_check_rejects_garbage(), test_domain_status_with_fake_resolver(), test_apply_result_keeps_facebook(), test_unknown_mailbox_blocks_address_and_send()

### Community 21 - "dnscheck.py"
Cohesion: 0.14
Nodes (8): domain_status(), mailbox_status(), make_resolver(), _mx_hosts(), _rcpt(), Vérification du domaine (enregistrement MX), dnspython (>=2.4), test_mailbox_probe()

### Community 22 - "emails.py"
Cohesion: 0.28
Nodes (6): extract(), host_of(), norm(), related(), repair(), test_repair_without_inventing()

### Community 24 - "mailer.py"
Cohesion: 0.25
Nodes (5): claude_mail(), compose(), describe(), prompt_parts(), send()

### Community 26 - "diagnose"
Cohesion: 0.29
Nodes (5): cmd_clean(), clean_database(), diagnose(), shared_by_others(), Qualité des adresses (validation, nettoyage, adresses partagées)

### Community 28 - "build_message"
Cohesion: 0.33
Nodes (6): build_message(), format_phone(), signature(), test_signature_has_contact_details(), test_signature_has_optout_and_no_price(), test_signature_mentions_email_source()

### Community 29 - "facebook_message"
Cohesion: 0.40
Nodes (3): facebook_message(), messenger_link(), test_facebook_message_tone()

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)`, `requests (>=2.31)`, `gunicorn (>=22)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 165 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `post`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `sourcing.py`, `qualify.py`, `collect_progress`, `run_cleanup`, `test_prospec.py`, `test_emails.py`, `apply_result`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **What connects `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1341991341991342 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `Commandes en ligne et orchestration` to `web.py`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `index`, `sourcing.py`, `qualify.py`, `collect_progress`, `dnscheck.py`, `mailer.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.06390977443609022 - nodes in this community are weakly interconnected._
- **Should `Lecture des réponses Gmail` be split into smaller, more focused modules?**
  _Cohesion score 0.09957325746799431 - nodes in this community are weakly interconnected._
- **Should `Envoi et relances` be split into smaller, more focused modules?**
  _Cohesion score 0.06845513413506013 - nodes in this community are weakly interconnected._