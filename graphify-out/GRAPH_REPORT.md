# Graph Report - Prospec-bat  (2026-11-04)

## Corpus Check
- 32 files · ~27,933 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 527 nodes · 1273 edges · 26 communities (23 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d42e19e3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- web.py
- post
- Commandes en ligne et orchestration
- Rédaction des mails et configuration
- Lecture des réponses Gmail
- Envoi et relances
- Base de données et tests du dashboard
- index
- email_ok
- Installation et démarrage Termux
- Consignes de session (CLAUDE.md)
- test_prospec.py
- Démarrage de session (hook)
- qualify.py
- collect_progress
- Interface et mascotte Bati
- run_cleanup
- next_to_write
- draft_action
- test_emails.py
- apply_result
- dnscheck.py
- emails.py
- frdate
- extract
- pytest

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
10. `qualify_company()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `send_all()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/web.py → README.md
- `qualify_batch()` --implements--> `Recherche en parallèle (WORKERS) et cadence de recherche web`  [INFERRED]
  prospec/cli.py → README.md
- `send_now()` --implements--> `Envoi groupé « Tout envoyer » sans quota`  [INFERRED]
  prospec/cli.py → README.md
- `is_suppressed()` --implements--> `Cadre légal B2B (CNIL)`  [INFERRED]
  prospec/db.py → README.md
- `domain_status()` --implements--> `Vérification du domaine (enregistrement MX)`  [INFERRED]
  prospec/dnscheck.py → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pipeline de prospection (source, qualification, rédaction, envoi)** — prospec_sourcing, prospec_qualify, prospec_mailer, prospec_cli [INFERRED 0.85]
- **Chaîne de contrôle des adresses avant envoi** — prospec_emails, prospec_dnscheck, prospec_mailer_assert_sourced, prospec_db_is_suppressed [INFERRED 0.85]
- **Suivi après envoi (réponses, relances, pipeline, notifications)** — prospec_inbox, prospec_notify, prospec_cli_send_followup_now, prospec_web_pipeline_action [INFERRED 0.85]

## Communities (26 total, 3 thin omitted)

### Community 0 - "web.py"
Cohesion: 0.13
Nodes (12): close_connection(), collect_now(), cron(), guard(), health(), login(), manifest(), _run_collect() (+4 more)

### Community 1 - "post"
Cohesion: 0.19
Nodes (16): now(), set_setting(), check_inbox(), connect(), followup_action(), import_followups(), import_mails(), mark() (+8 more)

### Community 2 - "Commandes en ligne et orchestration"
Cohesion: 0.07
Nodes (33): cmd_clean(), cmd_collect(), cmd_discover(), cmd_inbox(), cmd_osm(), cmd_qualify(), cmd_run(), cmd_source() (+25 more)

### Community 3 - "Rédaction des mails et configuration"
Cohesion: 0.07
Nodes (28): env(), sender(), batch_followup_prompt(), batch_prompt(), build_message(), check_mail(), claude_mail(), compose() (+20 more)

### Community 4 - "Lecture des réponses Gmail"
Cohesion: 0.13
Nodes (21): is_suppressed(), suppress(), check(), decode(), find_company(), fresh_text(), imap_date(), process() (+13 more)

### Community 5 - "Envoi et relances"
Cohesion: 0.09
Nodes (26): send_now(), due_followups(), first_send_date(), migrate(), sent_today(), compute(), issue_labels(), Envoi groupé « Tout envoyer » sans quota (+18 more)

### Community 6 - "Base de données et tests du dashboard"
Cohesion: 0.15
Nodes (22): connect(), _run_send_all(), con(), client(), login(), test_collect_auto_toggle_and_daily_preempts(), test_collect_progress(), test_company_names_are_escaped() (+14 more)

### Community 7 - "index"
Cohesion: 0.17
Nodes (12): get_setting(), send_mode(), collect_auto(), due_followups(), hud_counts(), index(), page(), pipeline_rows() (+4 more)

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
Cohesion: 0.06
Nodes (26): decode_cloudflare(), extract_emails(), enseigne_of(), fetch_naf(), metier_for(), next_refresh(), parse_result(), pool_size() (+18 more)

### Community 13 - "qualify.py"
Cohesion: 0.05
Nodes (36): inspect(), match_site(), next_queries(), run(), notify(), company_names(), distinctive(), fetch_dept() (+28 more)

### Community 14 - "collect_progress"
Cohesion: 0.22
Nodes (6): collect_progress(), start_collect_loop(), loop(), start_inbox_poll(), loop(), Notifications de réponse (Termux, ntfy.sh)

### Community 15 - "Interface et mascotte Bati"
Cohesion: 0.38
Nodes (3): Bati, la mascotte robot (icône 192 px), Bati, la mascotte robot (icône 512 px), Interface : barre d'onglets, cartes balayables, effets

### Community 16 - "run_cleanup"
Cohesion: 0.29
Nodes (5): clean_now(), run_cleanup(), send_all(), start_cleanup_once(), start_send()

### Community 17 - "next_to_write"
Cohesion: 0.11
Nodes (14): check_can_send(), held_back(), next_to_write(), ei_blocked(), in_suppressed(), suppressed_set(), assert_sourced(), address_class() (+6 more)

### Community 18 - "draft_action"
Cohesion: 0.40
Nodes (5): draft_action(), Dashboard mobile (Flask), Déploiement Docker et disque persistant, Mode review : rien ne part sans validation, gunicorn (>=22)

### Community 19 - "test_emails.py"
Cohesion: 0.25
Nodes (8): best_email(), add(), con(), test_best_email_ignores_agency(), test_clean_database(), test_cleanup_button_and_report(), test_last_defense_before_sending(), test_search_discards_bad_and_shared_addresses()

### Community 20 - "apply_result"
Cohesion: 0.22
Nodes (6): apply_result(), check(), diagnose(), shared_by_others(), test_check_rejects_garbage(), test_apply_result_keeps_facebook()

### Community 21 - "dnscheck.py"
Cohesion: 0.16
Nodes (6): mailbox_status(), make_resolver(), _mx_hosts(), _rcpt(), dnspython (>=2.4), test_mailbox_probe()

### Community 22 - "emails.py"
Cohesion: 0.24
Nodes (7): clean_database(), host_of(), norm(), related(), Qualité des adresses (validation, nettoyage, adresses partagées), Vérification du domaine (enregistrement MX), test_related_domain()

### Community 24 - "extract"
Cohesion: 0.50
Nodes (3): extract(), repair(), test_repair_without_inventing()

## Knowledge Gaps
- **8 isolated node(s):** `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)`, `requests (>=2.31)`, `gunicorn (>=22)` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 164 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Base de données et tests du dashboard` to `web.py`, `post`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `test_prospec.py`, `qualify.py`, `collect_progress`, `run_cleanup`, `next_to_write`, `test_emails.py`, `apply_result`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **What connects `PATH`, `Suivi des prospects (de la réponse au client)`, `flask (>=3.0)` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `web.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1341991341991342 - nodes in this community are weakly interconnected._
- **Why does `env()` connect `Rédaction des mails et configuration` to `web.py`, `Commandes en ligne et orchestration`, `Lecture des réponses Gmail`, `Envoi et relances`, `Base de données et tests du dashboard`, `index`, `test_prospec.py`, `qualify.py`, `collect_progress`, `next_to_write`, `dnscheck.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Should `Commandes en ligne et orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.06787330316742081 - nodes in this community are weakly interconnected._
- **Should `Rédaction des mails et configuration` be split into smaller, more focused modules?**
  _Cohesion score 0.07474747474747474 - nodes in this community are weakly interconnected._
- **Should `Lecture des réponses Gmail` be split into smaller, more focused modules?**
  _Cohesion score 0.12701612903225806 - nodes in this community are weakly interconnected._