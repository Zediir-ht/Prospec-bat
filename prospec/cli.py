"""Usage : python -m prospec.cli {source|qualify|run|suppress EMAIL|stats}"""
import argparse
import random
import sys
import time

from . import config, db, mailer, qualify, sourcing


def cmd_source(con, _):
    print(f"{sourcing.source(con)} nouvelles entreprises ajoutées")


def cmd_qualify(con, args):
    rows = con.execute("SELECT * FROM companies WHERE status='new' ORDER BY RANDOM() LIMIT ?", (args.n,)).fetchall()
    for row in rows:
        res = qualify.qualify_company(dict(row))
        if res["site_status"] == "ok":
            status = "skip"  # site correct : hors cible
        elif res["site_status"] == "unknown":
            continue  # réessayé plus tard
        elif res["email"]:
            status = "qualified"
        else:
            status = "no_email"  # cible pertinente mais aucun email public trouvé : ignorée
        con.execute(
            "UPDATE companies SET site_url=?, site_status=?, site_issues=?, email=?, status=? WHERE siren=?",
            (res["site_url"], res["site_status"], res["site_issues"], res["email"], status, row["siren"]),
        )
        con.commit()
        print(f"{row['nom']} ({row['commune']}) -> {res['site_status']} / {res['email']} / {status}")
        time.sleep(random.uniform(1, 3))


def contact(con, row, subject, body, mode, followup=False):
    if mode != "review":  # en mode review, l'envoi se fait depuis le dashboard
        mailer.deliver(mailer.build_message(row["email"], subject, body), mode)
    ts = db.now()
    if followup:
        con.execute("UPDATE companies SET status='followed_up', followup_at=? WHERE siren=?", (ts, row["siren"]))
    else:
        con.execute(
            "UPDATE companies SET status=?, subject=?, body=?, contacted_at=? WHERE siren=?",
            ("sent" if mode == "send" else "drafted", subject, body, ts, row["siren"]),
        )
    con.commit()


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
    # 2. nouveaux contacts : les entreprises sans site d'abord
    rows = con.execute(
        "SELECT * FROM companies WHERE status='qualified' ORDER BY (site_status='none') DESC, RANDOM()"
    ).fetchall()
    for row in rows:
        if done >= limit:
            break
        if db.is_suppressed(con, row["email"]):
            con.execute("UPDATE companies SET status='refused' WHERE siren=?", (row["siren"],))
            continue
        subject, body = mailer.compose(dict(row))
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
    q = sub.add_parser("qualify"); q.add_argument("-n", type=int, default=30)
    sub.add_parser("run")
    s = sub.add_parser("suppress"); s.add_argument("email")
    sub.add_parser("stats")
    args = p.parse_args()
    con = db.connect()
    {"source": cmd_source, "qualify": cmd_qualify, "run": cmd_run, "suppress": cmd_suppress,
     "stats": cmd_stats}[args.cmd](con, args)


if __name__ == "__main__":
    main()
