"""Usage : python -m prospec.cli {source|osm|discover [-n N]|inbox|qualify [--all]|collect [-n N]|run|suppress EMAIL|stats}"""
import argparse
import random
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from . import config, db, discovery, dnscheck, inbox, mailer, osm, qualify, sourcing


def cmd_source(con, _):
    print(f"{sourcing.source(con)} nouvelles entreprises ajoutées")


def cmd_osm(con, _):
    print(f"{osm.refresh(con)} lieux OpenStreetMap avec email récupérés")
    print(f"{osm.match(con)} entreprises appariées")


def cmd_discover(con, args):
    done, linked = discovery.run(con, max_queries=args.n)
    print(f"{done} recherches par métier et ville, {linked} sites rattachés à une entreprise")


def cmd_inbox(con, _):
    print(inbox.summary(inbox.check(con)))


def target():
    return int(config.env("DAILY_LIMIT", "10"))


def pending(con):
    """Mails exploitables en attente : entreprises avec email à rédiger + brouillons à valider."""
    drafted = con.execute("SELECT COUNT(*) FROM companies WHERE status='drafted'").fetchone()[0]
    return len(next_to_write(con)) + drafted


def apply_result(con, row, res):
    """Enregistre le résultat de la recherche pour une entreprise. Retourne le statut, ou None (à retenter)."""
    if res["email"]:
        res["email_source"] = "site"
    elif row["email"]:  # email déjà connu par OpenStreetMap
        res["email"], res["email_source"] = row["email"], row["email_source"] or "osm"
    else:
        res["email_source"] = None
    if res["email"] and not dnscheck.email_ok(res["email"]):
        print(f"  ! {res['email']} : le domaine ne reçoit pas de courrier, adresse écartée")
        res["email"], res["email_source"] = None, None
    if res["site_status"] == "ok":
        status = "skip"  # site correct : hors cible
    elif res["site_status"] == "unknown":
        return None  # recherche impossible pour l'instant : réessayé plus tard
    elif res["email"] and row["nature_juridique"] == "1000" and res["email"].split("@")[-1] in config.FREE_MAIL_DOMAINS:
        status = "skip"  # entrepreneur individuel : pas de prospection sur une messagerie personnelle
    elif res["email"]:
        status = "qualified"
    else:
        status = "no_email"  # cible pertinente mais aucun email public trouvé : ignorée
    con.execute(
        "UPDATE companies SET site_url=?, site_status=?, site_issues=?, email=?, email_source=?, status=? WHERE siren=?",
        (res["site_url"], res["site_status"], res["site_issues"], res["email"], res["email_source"], status, row["siren"]),
    )
    con.commit()
    print(f"{row['nom']} ({row['commune']}) -> {res['site_status']} / {res['email']} / {status}")
    return status


def qualify_batch(con, limit, until_target=True, stop=None, log=None, base=(0, 0), workers=None):
    """Teste jusqu'à `limit` entreprises avec `workers` recherches en parallèle (WORKERS, 20 par défaut).
    Avec until_target, s'arrête dès que `target()` mails exploitables sont réunis. `stop()` permet
    d'interrompre, `log(texte)` de suivre la progression. Retourne (entreprises testées, adresses trouvées).
    Les fils ne font que du réseau ; la base n'est écrite que par ce fil-ci."""
    workers = workers or int(config.env("WORKERS", "20"))
    rows = iter(con.execute(
        "SELECT * FROM companies WHERE status='new' ORDER BY (code_postal LIKE '12%') DESC, RANDOM() LIMIT ?", (limit,)
    ).fetchall())
    tested = found = 0

    def finished():
        if until_target and pending(con) >= target():
            print(f"Objectif atteint : {pending(con)} mails exploitables.")
            return True
        return bool(stop and stop())

    with ThreadPoolExecutor(max_workers=workers) as pool:
        running = {}

        def submit_next():
            row = next(rows, None)
            if row is not None:
                running[pool.submit(qualify.qualify_company, dict(row))] = row

        if not finished():
            for _ in range(workers):
                submit_next()
        while running:
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for fut in done:
                row = running.pop(fut)
                try:
                    res = fut.result()
                except Exception as exc:  # une entreprise en erreur ne bloque pas les autres
                    print(f"  ! {row['nom']} : {exc}")
                    continue
                tested += 1
                if apply_result(con, row, res) == "qualified":
                    found += 1
                if log:
                    log(f"{base[0] + tested} entreprises testées, {base[1] + found} adresses trouvées")
            if not finished():  # sinon : on laisse finir les recherches en cours sans en lancer d'autres
                for _ in done:
                    submit_next()
    return tested, found


def cmd_qualify(con, args):
    """Recherche du jour (s'arrête à `target()` mails), ou collecte sans limite avec --all."""
    qualify_batch(con, args.n, until_target=not getattr(args, "all", False))


def cmd_collect(con, args, stop=None, log=None):
    """Mode collecte : remplit le stock d'adresses sans s'arrêter à DAILY_LIMIT, jusqu'à args.n entreprises
    testées. Télécharge de nouvelles entreprises au fur et à mesure. Les envois restent limités à 10/jour."""
    tested = found = 0
    while tested < args.n and not (stop and stop()):
        sourcing.source(con, min_pool=300)
        try:
            osm.refresh(con)
            osm.match(con)
        except Exception as exc:  # source facultative : on continue sans elle
            print(f"OpenStreetMap indisponible : {exc}")
        discovery.run(con, max_queries=10, stop=stop, log=(lambda t: log(f"Collecte : {t}")) if log else None)
        t, f = qualify_batch(con, min(args.n - tested, 100), until_target=False, stop=stop, log=log, base=(tested, found))
        if t == 0:
            break  # plus aucune entreprise à tester
        tested, found = tested + t, found + f
        if log:
            log(f"{tested} entreprises testées, {found} adresses trouvées")
    print(f"Collecte : {tested} entreprises testées, {found} adresses trouvées")
    return tested, found


def check_can_send(con, row, subject, body):
    """Lève ValueError si ce mail ne doit pas partir (désinscrit, adresse non sourcée, domaine sans messagerie)."""
    if not (subject or "").strip() or not (body or "").strip():
        raise ValueError("l'objet ou le texte du mail est vide")
    if db.is_suppressed(con, row["email"]):
        raise ValueError(f"{row['email']} est désinscrite")
    mailer.assert_sourced(row)
    if not dnscheck.email_ok(row["email"]):
        raise ValueError(f"{row['email']} : le domaine ne reçoit pas de courrier")


def send_followup_now(con, row, subject, body):
    """Envoie la relance dans le fil du premier mail. Lève ValueError si elle ne doit pas partir."""
    check_can_send(con, row, subject, body)
    msg = mailer.build_message(row["email"], subject, body, row["email_source"], (row["message_ids"] or "").split())
    mailer.send(msg)
    remember_message(con, row["siren"], msg)
    con.execute("UPDATE companies SET status='followed_up', followup_at=?, followup_subject=?, followup_body=? WHERE siren=?",
                (db.now(), subject, body, row["siren"]))
    db.log_send(con, row["siren"], "followup")


def remember_message(con, siren, msg):
    """Garde l'identifiant du mail envoyé : les réponses le citent, ce qui permet de les reconnaître."""
    con.execute("UPDATE companies SET message_ids=TRIM(COALESCE(message_ids,'') || ' ' || ?) WHERE siren=?",
                (msg["Message-ID"], siren))


def send_now(con, row, subject, body):
    """Envoie tout de suite un mail validé (dashboard). Lève ValueError si l'adresse ne doit pas être contactée."""
    check_can_send(con, row, subject, body)
    msg = mailer.build_message(row["email"], subject, body, row["email_source"])
    mailer.send(msg)
    remember_message(con, row["siren"], msg)
    con.execute("UPDATE companies SET status='sent', subject=?, body=?, contacted_at=? WHERE siren=?",
                (subject, body, db.now(), row["siren"]))
    db.log_send(con, row["siren"], "first")


def contact(con, row, subject, body, mode, followup=False):
    mailer.assert_sourced(row)
    if mode != "review":  # en mode review, l'envoi se fait depuis le dashboard
        msg = mailer.build_message(row["email"], subject, body, row["email_source"])
        mailer.deliver(msg, mode)
        remember_message(con, row["siren"], msg)
        db.log_send(con, row["siren"], "followup" if followup else "first")
    ts = db.now()
    if followup:
        con.execute("UPDATE companies SET status='followed_up', followup_at=? WHERE siren=?", (ts, row["siren"]))
    else:
        con.execute(
            "UPDATE companies SET status=?, subject=?, body=?, contacted_at=? WHERE siren=?",
            ("sent" if mode == "send" else "drafted", subject, body, ts, row["siren"]),
        )
    con.commit()


def next_to_write(con):
    """Entreprises qualifiées, Aveyron d'abord, puis celles sans site ; exclut les désinscrits."""
    rows = con.execute(
        "SELECT * FROM companies WHERE status='qualified' AND email IS NOT NULL AND email_source IN ('site','osm') "
        "ORDER BY (code_postal LIKE '12%') DESC, (site_status='none') DESC, siren"
    ).fetchall()
    return [r for r in rows if not db.is_suppressed(con, r["email"])]


def cmd_run(con, args):
    mode, limit = db.send_mode(con), int(config.env("DAILY_LIMIT", "10"))
    if mode != "review" and not config.env("GMAIL_APP_PASSWORD"):
        sys.exit("GMAIL_APP_PASSWORD manquant dans .env")
    done = 0
    # 1. relances à J+7, uniquement en envoi direct :
    #    sinon elles passent par l'onglet « À relancer » du dashboard
    if mode == "send":
        for row in db.due_followups(con, int(config.env("FOLLOWUP_DAYS", "7"))):
            if done >= limit:
                break
            subject, body = (row["followup_subject"], row["followup_body"]) if row["followup_body"] else mailer.followup_mail(dict(row))
            try:
                send_followup_now(con, row, subject, body)
            except ValueError as exc:
                print(f"relance ignorée : {exc}")
                continue
            print(f"relance -> {row['nom']}")
            done += 1
            time.sleep(random.uniform(60, 240))
    # 2. nouveaux contacts : mails rédigés par Claude (API). Sans clé API, la rédaction se fait
    #    depuis l'onglet « À rédiger » du dashboard.
    if not config.env("ANTHROPIC_API_KEY"):
        print("Pas de clé API : rédigez les mails depuis l'onglet « À rédiger » du dashboard.")
        return
    for row in next_to_write(con):
        if done >= limit:
            break
        mail = mailer.compose(dict(row))
        if not mail:
            continue
        subject, body = mail
        contact(con, row, subject, body, mode)
        print(f"{mode} -> {row['nom']} <{row['email']}> : {subject}")
        done += 1
        if mode == "send":
            time.sleep(random.uniform(60, 240))  # échelonne les envois
    con.commit()
    print(f"{done} mails traités ({mode})")


def cmd_suppress(con, args):
    db.suppress(con, args.email)
    print(f"{args.email} ajouté à la liste de désinscription")


def cmd_stats(con, _):
    for r in con.execute("SELECT status, COUNT(*) n FROM companies GROUP BY status ORDER BY n DESC"):
        print(f"{r['status']:12} {r['n']}")


def main():
    p = argparse.ArgumentParser(prog="prospec")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("source")
    sub.add_parser("osm")
    q = sub.add_parser("qualify"); q.add_argument("-n", type=int, default=150)
    q.add_argument("--all", action="store_true", help="ne pas s'arrêter à DAILY_LIMIT")
    c = sub.add_parser("collect"); c.add_argument("-n", type=int, default=1000)
    d = sub.add_parser("discover"); d.add_argument("-n", type=int, default=20)
    sub.add_parser("inbox")
    sub.add_parser("run")
    s = sub.add_parser("suppress"); s.add_argument("email")
    sub.add_parser("stats")
    args = p.parse_args()
    con = db.connect()
    {"source": cmd_source, "osm": cmd_osm, "collect": cmd_collect, "discover": cmd_discover, "inbox": cmd_inbox, "qualify": cmd_qualify, "run": cmd_run, "suppress": cmd_suppress,
     "stats": cmd_stats}[args.cmd](con, args)


if __name__ == "__main__":
    main()
