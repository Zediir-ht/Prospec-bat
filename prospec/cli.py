"""Usage : python -m prospec.cli {source|osm|qualify [--all]|collect [-n N]|run|suppress EMAIL|stats}"""
import argparse
import random
import sys
import time

from . import config, db, mailer, osm, qualify, sourcing


def cmd_source(con, _):
    print(f"{sourcing.source(con)} nouvelles entreprises ajoutées")


def cmd_osm(con, _):
    print(f"{osm.refresh(con)} lieux OpenStreetMap avec email récupérés")
    print(f"{osm.match(con)} entreprises appariées")


def target():
    return int(config.env("DAILY_LIMIT", "10"))


def pending(con):
    """Mails exploitables en attente : entreprises avec email à rédiger + brouillons à valider."""
    drafted = con.execute("SELECT COUNT(*) FROM companies WHERE status='drafted'").fetchone()[0]
    return len(next_to_write(con)) + drafted


def qualify_batch(con, limit, until_target=True, stop=None, log=None, base=(0, 0)):
    """Teste jusqu'à `limit` entreprises. Avec until_target, s'arrête dès que `target()` mails exploitables
    sont réunis. `stop()` permet d'interrompre, `log(texte)` de suivre la progression.
    Retourne (entreprises testées, adresses trouvées)."""
    rows = con.execute("SELECT * FROM companies WHERE status='new' ORDER BY (code_postal LIKE '12%') DESC, RANDOM() LIMIT ?", (limit,)).fetchall()
    tested = found = 0
    for row in rows:
        if until_target and pending(con) >= target():
            print(f"Objectif atteint : {pending(con)} mails exploitables.")
            break
        if stop and stop():
            break
        res = qualify.qualify_company(dict(row))
        tested += 1
        if res["email"]:
            res["email_source"] = "site"
        elif row["email"]:  # email déjà connu par OpenStreetMap
            res["email"], res["email_source"] = row["email"], row["email_source"] or "osm"
        else:
            res["email_source"] = None
        if res["site_status"] == "ok":
            status = "skip"  # site correct : hors cible
        elif res["site_status"] == "unknown":
            continue  # réessayé plus tard
        elif res["email"] and row["nature_juridique"] == "1000" and res["email"].split("@")[-1] in config.FREE_MAIL_DOMAINS:
            status = "skip"  # entrepreneur individuel : pas de prospection sur une messagerie personnelle
        elif res["email"]:
            status = "qualified"
            found += 1
        else:
            status = "no_email"  # cible pertinente mais aucun email public trouvé : ignorée
        con.execute(
            "UPDATE companies SET site_url=?, site_status=?, site_issues=?, email=?, email_source=?, status=? WHERE siren=?",
            (res["site_url"], res["site_status"], res["site_issues"], res["email"], res["email_source"], status, row["siren"]),
        )
        con.commit()
        print(f"{row['nom']} ({row['commune']}) -> {res['site_status']} / {res['email']} / {status}")
        if log:
            log(f"{base[0] + tested} entreprises testées, {base[1] + found} adresses trouvées")
        time.sleep(random.uniform(1, 3))
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
        t, f = qualify_batch(con, min(args.n - tested, 100), until_target=False, stop=stop, log=log, base=(tested, found))
        if t == 0:
            break  # plus aucune entreprise à tester
        tested, found = tested + t, found + f
        if log:
            log(f"{tested} entreprises testées, {found} adresses trouvées")
    print(f"Collecte : {tested} entreprises testées, {found} adresses trouvées")
    return tested, found


def contact(con, row, subject, body, mode, followup=False):
    mailer.assert_sourced(row)
    if mode != "review":  # en mode review, l'envoi se fait depuis le dashboard
        mailer.deliver(mailer.build_message(row["email"], subject, body, row["email_source"]), mode)
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
    # 1. relances à J+7 (comptent dans le quota quotidien)
    if mode == "send":
        for row in db.due_followups(con, int(config.env("FOLLOWUP_DAYS", "7"))):
            if done >= limit:
                break
            if db.is_suppressed(con, row["email"]):
                continue
            subject, body = mailer.followup_mail(dict(row))
            contact(con, row, subject, body, mode, followup=True)
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
    sub.add_parser("run")
    s = sub.add_parser("suppress"); s.add_argument("email")
    sub.add_parser("stats")
    args = p.parse_args()
    con = db.connect()
    {"source": cmd_source, "osm": cmd_osm, "collect": cmd_collect, "qualify": cmd_qualify, "run": cmd_run, "suppress": cmd_suppress,
     "stats": cmd_stats}[args.cmd](con, args)


if __name__ == "__main__":
    main()
