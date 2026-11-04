# Graph Report - Prospec-bat  (2026-11-04)

## Corpus Check
- 32 files · ~28,987 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 538 nodes · 1300 edges · 25 communities (21 shown, 4 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b11f6659`
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
- email_ok
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- sourcing.py
- Démarrage de session (hook)
- qualify.py
- run_cleanup
- Interface et mascotte Bati
- next_to_write
- mailbox_status
- draft_action
- assert_sourced
- check_can_send
- dnscheck.py
- emails.py
- frdate
- pytest

## God Nodes (most connected - your core abstractions)
1. `connect()` - 51 edges
2. `env()` - 32 edges
3. `index()` - 25 edges
4. `process()` - 21 edges
5. `connect()` - 19 edges
6. `login()` - 19 edges
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

## Communities (25 total, 4 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.13
Nodes (12): close_connection(), collect_now(), cron(), guard(), health(), login(), manifest(), _run_collect() (+4 more)

### Community 1 - "post"
Cohesion: 0.16
Nodes (16): now(), connect(), followup_action(), mark(), pipeline_action(), send_all(), set_mode(), social_action() (+8 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.08
Nodes (25): cmd_bounces(), cmd_collect(), cmd_discover(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source(), cmd_stats() (+17 more)

### Community 3 - "mailer.py"
Cohesion: 0.06
Nodes (28): batch_followup_prompt(), batch_prompt(), build_message(), check_mail(), claude_mail(), compose(), deliver(), describe() (+20 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.10
Nodes (28): cmd_inbox(), sender(), is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text() (+20 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.08
Nodes (28): send_followup_now(), send_now(), due_followups(), first_send_date(), in_suppressed(), log_send(), sent_today(), suppressed_set() (+20 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.12
Nodes (26): connect(), migrate(), _run_send_all(), con(), test_source_stops_when_pool_is_enough(), fake_fetch(), client(), login() (+18 more)

### Community 7 - "index"
Cohesion: 0.16
Nodes (14): env(), get_setting(), send_mode(), collect_auto(), due_followups(), hud_counts(), import_followups(), index() (+6 more)

### Community 8 - "email_ok"
Cohesion: 0.18
Nodes (5): domain_status(), email_ok(), Vérification du domaine (enregistrement MX), test_dns_check_survives_missing_resolv_conf(), test_domain_status_with_fake_resolver()

### Community 9 - "Installation et démarrage Termux"
Cohesion: 0.09
Nodes (11): install-boot.sh script, install.sh script, notify(), Démarrage automatique sous Termux (Termux:Boot), Notifications de réponse (Termux, ntfy.sh), running(), server.sh script, start() (+3 more)

### Community 10 - "Consignes de session (CLAUDE.md)"
Cohesion: 0.50
Nodes (3): Au début de chaque session, graphify, Prospec-bat

### Community 11 - "sourcing.py"
Cohesion: 0.08
Nodes (22): set_setting(), enseigne_of(), fetch_naf(), metier_for(), next_refresh(), parse_result(), pool_size(), refresh_days() (+14 more)

### Community 13 - "qualify.py"
Cohesion: 0.06
Nodes (38): inspect(), match_site(), next_queries(), run(), company_names(), distinctive(), fetch_dept(), match() (+30 more)

### Community 14 - "run_cleanup"
Cohesion: 0.18
Nodes (7): clean_now(), collect_progress(), run_cleanup(), start_cleanup_once(), start_collect_loop(), loop(), start_inbox_poll()

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.38
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 16 - "next_to_write"
Cohesion: 0.19
Nodes (7): held_back(), next_to_write(), address_class(), bounce_table(), risky_classes(), import_mails(), test_risky_address_types_are_held_back()

### Community 17 - "mailbox_status"
Cohesion: 0.29
Nodes (4): mailbox_status(), _rcpt(), send(), test_mailbox_probe()

### Community 18 - "draft_action"
Cohesion: 0.40
Nodes (5): draft_action(), Dashboard mobile (Flask), Déploiement Docker et disque persistant, Mode review : rien ne part sans validation, gunicorn (>=22)

### Community 20 - "check_can_send"
Cohesion: 0.18
Nodes (8): apply_result(), check_can_send(), ei_blocked(), contacted_emails(), test_apply_result_keeps_facebook(), test_ei_free_mail_setting(), test_never_write_or_send_twice_to_the_same_address(), test_unknown_mailbox_blocks_address_and_send()

### Community 21 - "dnscheck.py"
Cohesion: 0.22
Nodes (3): make_resolver(), _mx_hosts(), dnspython (>=2.4)

### Community 22 - "emails.py"
Cohesion: 0.09
Nodes (22): cmd_clean(), check(), clean_database(), diagnose(), extract(), host_of(), norm(), related() (+14 more)

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)`, `requests (>=2.31)`, `gunicorn (>=22)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 168 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `post`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `sourcing.py`, `qualify.py`, `run_cleanup`, `next_to_write`, `assert_sourced`, `check_can_send`, `emails.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **What connects `PATH`, `flask (>=3.0)`, `Suivi des prospects (de la réponse au client)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1341991341991342 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `index` to `web.py`, `Commandes en ligne et orchestration`, `mailer.py`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `Installation et démarrage Termux`, `sourcing.py`, `qualify.py`, `run_cleanup`, `next_to_write`, `mailbox_status`, `check_can_send`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.08305647840531562 - nodes in this community are weakly interconnected._
- **Should `mailer.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0647342995169082 - nodes in this community are weakly interconnected._
- **Should `Lecture des réponses Gmail` be split into smaller, more focused modules?**
  _Cohesion score 0.10128205128205128 - nodes in this community are weakly interconnected._