"""Dashboard mobile : valider les mails du jour, voir les stats, gérer les désinscriptions."""
import hmac
import re
from datetime import datetime
import random
import threading
import time
from urllib.parse import quote_plus

from flask import Flask, abort, g, jsonify, redirect, render_template, request, session, url_for
from jinja2 import DictLoader

from . import cli, config, db, emails, inbox, mailer, sourcing, stats as statsmod

app = Flask(__name__)
app.secret_key = config.env("DASHBOARD_SECRET") or config.env("DASHBOARD_PASSWORD", "change-me")
app.config.update(MAX_FORM_MEMORY_SIZE=50_000_000, MAX_CONTENT_LENGTH=None, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30)

_job = {"running": False, "log": "", "stop": False, "kind": "", "next": None}
_send = {"running": False, "log": "", "stop": False}  # envoi groupé, indépendant des recherches
_clean = {"running": False}

from . import ui

# Gabarits compilés une seule fois (l'extension .html active l'échappement automatique)
TEMPLATES = ("PAGE", "LOGIN", "HOME", "DRAFT", "WRITE", "SENT", "FOLLOW", "PIPE", "STATS", "LIST", "SOCIAL")
app.jinja_loader = DictLoader({f"{name.lower()}.html": getattr(ui, name) for name in TEMPLATES})
PAGE_CSS = ui.CSS.replace("{{bot}}", ui.BOT)

MODES = [("review", "Review (je valide ici)"), ("draft", "Brouillons Gmail"), ("send", "Envoi direct")]
MODE_SHORT = {"review": "Review", "draft": "Gmail", "send": "Auto"}


def hud_counts(con):
    counts = {r["status"]: r["n"] for r in con.execute("SELECT status, COUNT(*) n FROM companies GROUP BY status")}
    return {"sent": counts.get("sent", 0) + counts.get("followed_up", 0) + counts.get("replied", 0) + counts.get("refused", 0),
            "replied": counts.get("replied", 0), "drafted": counts.get("drafted", 0)}


def collect_progress(con):
    """Avancement de la collecte : catégories SIRENE (département × activité) téléchargées et entreprises testées."""
    sourcing.refresh_if_due(con)  # nouveau passage dû : la collecte repart pour les entreprises créées depuis
    total = con.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    untested = con.execute("SELECT COUNT(*) FROM companies WHERE status='new'").fetchone()[0]
    found = con.execute("SELECT COUNT(*) FROM companies WHERE email_source IN ('site','osm')").fetchone()[0]
    cats = len(config.DEPARTEMENTS) * len(config.NAF_CODES)
    done = con.execute("SELECT COUNT(*) FROM sourced").fetchone()[0]
    pct = lambda a, b: round(100 * a / b) if b else 0
    return {"cats": cats, "cats_done": min(done, cats), "cats_pct": pct(done, cats), "total": total, "tested": total - untested,
            "tested_pct": pct(total - untested, total), "untested": untested, "found": found,
            "finished": done >= cats and untested == 0,
            "next_refresh": sourcing.next_refresh(con)}


SOCIAL_TODO = "status='no_email' AND facebook IS NOT NULL AND fb_done IS NULL"


def page(body, tab="home", con=None):
    mode = db.send_mode(con) if con else ""
    hud = hud_counts(con) if con else None
    counts = {}
    if con:
        counts = {"write": len(cli.next_to_write(con)), "drafts": hud["drafted"], "followups": len(due_followups(con)),
                  "pipeline": len(pipeline_todo(con)),
                  "social": con.execute(f"SELECT COUNT(*) FROM companies WHERE {SOCIAL_TODO}").fetchone()[0]}
    more_keys = [k for k, *_ in ui.MORE_TABS]
    return render_template(
        "page.html", css=PAGE_CSS, body=body, tab=tab, hud=hud, icon=ui.icon,
        main_tabs=ui.MAIN_TABS, more_tabs=ui.MORE_TABS, more_keys=more_keys, more_count=sum(counts.get(k, 0) for k in more_keys),
        mode_short=MODE_SHORT.get(mode, ""), counts=counts, msg=session.pop("msg", ""), fx=session.pop("fx", ""))


def render(template, **kw):
    """Gabarit d'onglet, avec les icônes et la signature à disposition."""
    return render_template(template, icon=ui.icon, sig=mailer.signature, **kw)


def sent_today(con):
    return db.sent_today(con)


STAGES = {"replied": "À recontacter", "mockup": "Maquette envoyée", "meeting": "Rendez-vous", "client": "Client", "lost": "Perdu"}


def due_followups(con):
    return db.due_followups(con, int(config.env("FOLLOWUP_DAYS", "7")))


def pipeline_rows(con):
    """Entreprises qui ont répondu, avec leur étape ; celles qui demandent une action d'abord."""
    today = datetime.now().strftime("%Y-%m-%d")
    out = []
    for r in con.execute("SELECT * FROM companies WHERE status='replied' ORDER BY COALESCE(reply_at, contacted_at) DESC").fetchall():
        c = dict(r)
        c["stage_key"] = c["stage"] if c["stage"] in STAGES else "replied"
        c["due"] = bool(c["reminder"]) and c["reminder"] <= today and c["stage_key"] not in ("client", "lost")
        out.append(c)
    order = {"replied": 0, "meeting": 1, "mockup": 2, "client": 3, "lost": 4}
    out.sort(key=lambda c: (not c["due"], order[c["stage_key"]]))
    return out


def pipeline_todo(con):
    return [c for c in pipeline_rows(con) if c["due"] or c["stage_key"] == "replied"]


@app.template_filter("frshort")
def frshort(value):
    """« 2026-10-28 » -> « 28/10 »."""
    v = value or ""
    return f"{v[8:10]}/{v[5:7]}" if len(v) >= 10 else v


@app.template_filter("frdate")
def frdate(value):
    """« 2026-10-23T13:37:00 » -> « 23/10 à 13:37 »."""
    v = value or ""
    return f"{v[8:10]}/{v[5:7]} à {v[11:16]}" if len(v) >= 16 else v


def connect():
    """Une seule connexion par requête, refermée à la fin."""
    if "con" not in g:
        g.con = db.connect()
    return g.con


@app.teardown_appcontext
def close_connection(exc):
    con = g.pop("con", None)
    if con is not None:
        con.close()


PAGE_SIZE = 30
LISTS = {"replies": ("Réponses", "--green", "Aucune réponse pour l'instant."),
         "refused": ("Refus", "--red", "Aucun refus."),
         "stock": ("Adresses en stock", "--green", "Aucune adresse prête : lancez le mode collecte.")}


def shown():
    """Nombre d'éléments affichés dans une liste (« Afficher plus » ajoute PAGE_SIZE)."""
    try:
        return max(PAGE_SIZE, min(int(request.args.get("n", PAGE_SIZE)), 2000))
    except ValueError:
        return PAGE_SIZE


@app.before_request
def guard():
    if request.endpoint in ("login", "manifest", "cron", "health", "static"):
        return
    if not session.get("ok"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    pw = config.env("DASHBOARD_PASSWORD")
    err = False
    if request.method == "POST":
        if pw and hmac.compare_digest(request.form.get("pw", ""), pw):
            session.permanent, session["ok"] = True, True
            return redirect(url_for("index"))
        err = True
    return page(render_template("login.html", err=err))


@app.route("/health")
def health():
    return "ok"


@app.route("/manifest.json")
def manifest():
    return jsonify(name="Prospec Bat", short_name="Prospec", start_url="/", display="standalone",
                   background_color="#ffffff", theme_color="#ffffff",
                   icons=[{"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
                          {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}])


@app.route("/")
def index():
    tab = request.args.get("tab", "home")
    con = connect()
    if tab == "drafts":
        total = con.execute("SELECT COUNT(*) FROM companies WHERE status='drafted'").fetchone()[0]
        rows = con.execute("SELECT * FROM companies WHERE status='drafted' ORDER BY contacted_at LIMIT ?", (shown(),)).fetchall()
        body = render("draft.html", rows=rows, total=total, n=shown(), sending=_send["running"], send_log=_send["log"])
    elif tab == "write":
        ready = cli.next_to_write(con)
        intro, items = mailer.prompt_parts([dict(r) for r in ready])
        body = render("write.html", auto=bool(config.env("ANTHROPIC_API_KEY")), n=len(ready), pdata={"intro": intro, "companies": items})
    elif tab == "followups":
        due = due_followups(con)
        all_rows = [dict(r) for r in due]  # la demande à Claude contient toutes les relances, pas seulement celles affichées
        for c in all_rows:
            c["f_subject"], c["f_body"] = (c["followup_subject"], c["followup_body"]) if c["followup_body"] else mailer.followup_mail(c)
        rows = all_rows[:shown()]
        body = render(
            "follow.html", rows=rows, total=len(due), n=shown(), days=config.env("FOLLOWUP_DAYS", "7"),
            prompt=mailer.batch_followup_prompt([dict(r, f_subject=r["f_subject"]) for r in all_rows]) if all_rows else "")
    elif tab == "pipeline":
        prows = pipeline_rows(con)
        body = render("pipe.html", rows=prows[:shown()], total=len(prows), n=shown(), stage_names=STAGES, steps=ui.STEPS, steps_keys=[k for k, _ in ui.STEPS])
    elif tab == "stats":
        data = statsmod.compute(con)
        t = data["total"]
        tiles = [("mails reçus", t["sent"], "--blue"), ("réponses", t["replied"], "--green"), ("taux de réponse", f"{t['rate']} %", "--yellow2"),
                 ("demandes STOP", t["stop"], "--red"), ("adresses en erreur", t["bounced"], "--red"),
                 ("clients", con.execute("SELECT COUNT(*) FROM companies WHERE stage='client'").fetchone()[0], "--green")]
        insights = []
        for title, lines in data["groups"]:  # meilleure ligne de chaque catégorie, à partir de 5 mails reçus
            solid = [l for l in lines if l["sent"] >= 5]
            if solid and title != "Origine de l'adresse":
                insights.append((title, max(solid, key=lambda l: (l["rate"], l["sent"]))))
        body = render("stats.html", data=data, tiles=tiles, insights=insights)
    elif tab == "social":
        total = con.execute(f"SELECT COUNT(*) FROM companies WHERE {SOCIAL_TODO}").fetchone()[0]
        rows = [dict(r, message=mailer.facebook_message(dict(r)), messenger=mailer.messenger_link(r["facebook"]))
                for r in con.execute(f"SELECT * FROM companies WHERE {SOCIAL_TODO} "
                                     "ORDER BY (code_postal LIKE '12%') DESC, siren LIMIT ?", (shown(),)).fetchall()]
        sent = con.execute("SELECT * FROM companies WHERE fb_done='sent' ORDER BY fb_sent_at DESC LIMIT 100").fetchall()
        body = render("social.html", rows=rows, total=total, n=shown(), sent=sent)
    elif tab in LISTS:
        title, color, empty = LISTS[tab]
        if tab == "stock":
            all_rows = cli.next_to_write(con)
            total, rows = len(all_rows), all_rows[:shown()]
        else:
            status = "replied" if tab == "replies" else "refused"
            total = con.execute("SELECT COUNT(*) FROM companies WHERE status=?", (status,)).fetchone()[0]
            rows = con.execute("SELECT * FROM companies WHERE status=? ORDER BY COALESCE(reply_at, contacted_at) DESC LIMIT ?",
                               (status, shown())).fetchall()
        body = render("list.html", kind=tab, title=title, color=color, empty=empty, rows=rows, total=total, n=shown())
    elif tab == "sent":
        where = ("status IN ('sent','followed_up','replied','bounced') OR (status='refused' AND contacted_at IS NOT NULL)")
        total = con.execute(f"SELECT COUNT(*) FROM companies WHERE {where}").fetchone()[0]
        rows = con.execute(
            f"SELECT * FROM companies WHERE {where} "
            "ORDER BY (status='replied' AND reply_at IS NOT NULL) DESC, COALESCE(reply_at, contacted_at) DESC LIMIT ?", (shown(),)).fetchall()
        body = render("sent.html", rows=rows, total=total, n=shown())
    else:
        tab = "home"
        counts = {r["status"]: r["n"] for r in con.execute("SELECT status, COUNT(*) n FROM companies GROUP BY status")}
        stats = [("entreprises", sum(counts.values()), "--blue", None), ("adresses en stock", len(cli.next_to_write(con)), "--green", "stock"),
                 ("à valider", counts.get("drafted", 0), "--yellow2", "drafts"), ("envoyés", counts.get("sent", 0) + counts.get("followed_up", 0), "--blue", "sent"),
                 ("réponses", counts.get("replied", 0), "--green", "replies"), ("refus", counts.get("refused", 0), "--red", "refused")]
        last = db.get_setting(con, "last_clean").split("|")
        body = render("home.html", clean_last=(frdate(last[0]), last[1]) if len(last) == 2 else None, cleaning=_clean["running"], stats=stats, modes=MODES, mode=db.send_mode(con), running=_job["running"], kind=_job["kind"], auto=collect_auto(con), progress=collect_progress(con), log=_job["log"],
                      limit=cli.target(), today=sent_today(con))
    return page(body, tab, con)


@app.get("/status")
def status():
    return jsonify(job={"running": _job["running"], "log": _job["log"]}, send={"running": _send["running"], "log": _send["log"]})


def run_cleanup():
    """Retire les adresses invalides (en arrière-plan, la vérification des domaines prend un moment)."""
    if _clean["running"]:
        return
    _clean["running"] = True
    try:
        con = db.connect()
        removed = emails.clean_database(con)
        for name, email, why in removed:
            print(f"adresse retirée : {name} <{email}> ({why})")
        db.set_setting(con, "last_clean", f"{db.now()}|{len(removed)}")
        db.set_setting(con, "emails_cleaned", "3")
    except Exception as exc:
        print(f"Nettoyage impossible : {exc}")
    finally:
        _clean["running"] = False


@app.post("/clean")
def clean_now():
    if _clean["running"]:
        session["msg"] = "Un nettoyage est déjà en cours."
    else:
        threading.Thread(target=run_cleanup, daemon=True).start()
        session["msg"] = "Nettoyage lancé. Le résultat s'affiche dans Réglages dans quelques instants."
    return redirect(url_for("index"))


@app.post("/mode")
def set_mode():
    mode = request.form.get("mode")
    if mode in dict(MODES):
        db.set_setting(connect(), "send_mode", mode)
    return redirect(url_for("index"))


@app.post("/draft/<siren>")
def draft_action(siren):
    con = connect()
    row = con.execute("SELECT * FROM companies WHERE siren=? AND status='drafted'", (siren,)).fetchone()
    if not row:
        abort(404)
    act, subject, body = request.form.get("act"), request.form.get("subject", ""), request.form.get("body", "")
    if act == "skip":
        con.execute("UPDATE companies SET status='skip' WHERE siren=?", (siren,))
        session["msg"] = f"{row['enseigne'] or row['nom']} ignorée."
    elif act in ("save", "send"):
        con.execute("UPDATE companies SET subject=?, body=? WHERE siren=?", (subject, body, siren))
        if act == "send":
            try:
                cli.send_now(con, row, subject, body)
                session["msg"], session["fx"] = f"Mail envoyé à {row['enseigne'] or row['nom']}.", "coins"
            except ValueError as exc:
                con.commit()
                session["msg"] = f"Envoi impossible : {exc}"
    con.commit()
    return redirect(url_for("index", tab="drafts"))


@app.post("/import")
def import_mails():
    con = connect()
    allowed = {r["siren"]: r["nom"] for r in cli.next_to_write(con)}
    ok, errors = mailer.parse_batch(request.form.get("text", ""), allowed)
    for siren, (subject, body) in ok.items():
        con.execute("UPDATE companies SET status='drafted', subject=?, body=?, contacted_at=? WHERE siren=?",
                    (subject, body, db.now(), siren))
    con.commit()
    msg = f"{len(ok)} mails importés dans « À valider »."
    if errors:
        msg += " Refusés : " + " ; ".join(errors[:5])
    session["msg"] = msg
    return redirect(url_for("index", tab="drafts" if ok else "write"))


@app.post("/inbox")
def check_inbox():
    try:
        session["msg"] = inbox.summary(inbox.check(connect()))
    except Exception as exc:
        session["msg"] = f"Impossible de lire la boîte Gmail : {exc}. Vérifiez GMAIL_APP_PASSWORD dans .env."
    return redirect(url_for("index", tab="sent"))


@app.post("/send-all")
def send_all():
    con = connect()
    rows = con.execute("SELECT * FROM companies WHERE status='drafted' ORDER BY contacted_at").fetchall()
    for r in rows:  # enregistre d'abord les modifications faites à l'écran
        subject, body = request.form.get(f"subject_{r['siren']}"), request.form.get(f"body_{r['siren']}")
        if subject is not None and body is not None:
            con.execute("UPDATE companies SET subject=?, body=? WHERE siren=?", (subject, body, r["siren"]))
    con.commit()
    if not start_send():
        session["msg"] = "Un envoi est déjà en cours."
    return redirect(url_for("index", tab="drafts"))


@app.post("/send/stop")
def stop_send():
    _send["stop"] = True
    _send["log"] = "Arrêt demandé : fin après le mail en cours…"
    return redirect(url_for("index", tab="drafts"))


def start_send():
    if _send["running"]:
        return False
    _send.update(running=True, stop=False, log="Préparation de l'envoi…")
    threading.Thread(target=_run_send_all, daemon=True).start()
    return True


def _run_send_all():
    sent, errors = 0, []
    try:
        con = db.connect()
        rows = con.execute("SELECT * FROM companies WHERE status='drafted' ORDER BY contacted_at").fetchall()
        if not rows:
            _send["log"] = "Aucun mail prêt à envoyer."
            return
        for i, row in enumerate(rows):
            if _send["stop"]:
                break
            if i:  # espace les envois : un envoi en rafale ressemble à du spam
                pause = random.uniform(*(float(x) for x in config.env("SEND_SPACING", "15,40").split(",")))
                _send["log"] = f"{sent}/{len(rows)} envoyé(s)… prochain dans {int(pause)} s"
                time.sleep(pause)
            try:
                cli.send_now(con, row, row["subject"], row["body"])
                sent += 1
                print(f"envoyé -> {row['email']}")
            except Exception as exc:
                errors.append(f"{row['enseigne'] or row['nom']} : {exc}")
                print(f"  ! échec d'envoi à {row['email']} : {exc}")
            _send["log"] = f"{sent}/{len(rows)} envoyé(s)…"
        _send["log"] = f"{sent} mail(s) envoyé(s)." + (" Erreurs : " + " ; ".join(errors) if errors else "")
    except Exception as exc:  # erreur imprévue : on l'affiche au lieu de s'arrêter en silence
        _send["log"] = f"Envoi interrompu après {sent} mail(s) : {exc}"
        print(f"  ! envoi groupé interrompu : {exc}")
    finally:
        _send["running"] = False


@app.post("/followup/<siren>")
def followup_action(siren):
    con = connect()
    row = con.execute("SELECT * FROM companies WHERE siren=? AND status='sent' AND followup_at IS NULL", (siren,)).fetchone()
    if not row:
        abort(404)
    act, subject, body = request.form.get("act"), request.form.get("subject", "").strip(), request.form.get("body", "").strip()
    if act == "skip":
        con.execute("UPDATE companies SET followup_at=? WHERE siren=?", (db.now(), siren))
    elif act in ("save", "send"):
        con.execute("UPDATE companies SET followup_subject=?, followup_body=? WHERE siren=?", (subject, body, siren))
        con.commit()
        if act == "send":
            row = con.execute("SELECT * FROM companies WHERE siren=?", (siren,)).fetchone()
            try:
                cli.send_followup_now(con, row, subject, body)
                session["msg"], session["fx"] = f"Relance envoyée à {row['enseigne'] or row['nom']}.", "coins"
            except ValueError as exc:
                session["msg"] = f"Relance impossible : {exc}"
    con.commit()
    return redirect(url_for("index", tab="followups"))


@app.post("/followups/import")
def import_followups():
    con = connect()
    allowed = {r["siren"]: r["nom"] for r in due_followups(con)}
    ok, errors = mailer.parse_batch(request.form.get("text", ""), allowed, min_len=40)
    for siren, (subject, body) in ok.items():
        con.execute("UPDATE companies SET followup_subject=?, followup_body=? WHERE siren=?", (subject, body, siren))
    con.commit()
    msg = f"{len(ok)} relance(s) importée(s)."
    if errors:
        msg += " Refusées : " + " ; ".join(errors[:5])
    session["msg"] = msg
    return redirect(url_for("index", tab="followups"))


@app.post("/pipeline/<siren>")
def pipeline_action(siren):
    con = connect()
    if not con.execute("SELECT 1 FROM companies WHERE siren=? AND status='replied'", (siren,)).fetchone():
        abort(404)
    stage = request.form.get("stage", "keep")
    reminder = request.form.get("reminder", "").strip()
    if reminder and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", reminder):
        reminder = ""
    con.execute("UPDATE companies SET notes=?, reminder=? WHERE siren=?", (request.form.get("notes", "").strip(), reminder or None, siren))
    if stage in STAGES:
        name = con.execute("SELECT COALESCE(NULLIF(enseigne,''), nom) FROM companies WHERE siren=?", (siren,)).fetchone()[0]
        con.execute("UPDATE companies SET stage=? WHERE siren=?", (None if stage == "replied" else stage, siren))
        if stage in ("client", "lost"):
            con.execute("UPDATE companies SET reminder=NULL WHERE siren=?", (siren,))
        if stage == "client":
            session["msg"], session["fx"] = f"🎉 {name} devient client !", "confetti"
        else:
            session["msg"] = f"{name} : {STAGES[stage].lower()}."
    elif stage == "keep":
        session["msg"] = "Note enregistrée."
    con.commit()
    return redirect(url_for("index", tab="pipeline"))


@app.post("/mark/<siren>")
def mark(siren):
    s = request.form.get("s")
    if s in ("replied", "refused"):
        con = connect()
        con.execute("UPDATE companies SET status=? WHERE siren=?", (s, siren))
        con.commit()
    return redirect(url_for("index", tab="sent"))


@app.post("/social/<siren>")
def social_action(siren):
    """Suivi des messages Facebook envoyés à la main."""
    s, con = request.form.get("s"), connect()
    if s == "sent":
        con.execute("UPDATE companies SET fb_done='sent', fb_sent_at=?, fb_message=? WHERE siren=?",
                    (db.now(), request.form.get("message", ""), siren))
        session["msg"] = "Message noté comme envoyé."
    elif s == "wrong":  # ce n'était pas la page de l'entreprise
        con.execute("UPDATE companies SET facebook=NULL WHERE siren=?", (siren,))
    elif s == "skip":
        con.execute("UPDATE companies SET fb_done='skip' WHERE siren=?", (siren,))
    elif s == "replied":
        con.execute("UPDATE companies SET status='replied', reply_at=?, reply_snippet=COALESCE(reply_snippet, 'Réponse sur Facebook') "
                    "WHERE siren=?", (db.now(), siren))
        session["msg"] = "Bravo ! L'entreprise passe dans le Suivi."
    elif s == "refused":
        con.execute("UPDATE companies SET status='refused', fb_done='refused' WHERE siren=?", (siren,))
    con.commit()
    return redirect(url_for("index", tab="social"))


@app.post("/stop")
def stop():
    email = request.form.get("email", "").strip()
    if email:
        db.suppress(connect(), email)
    return redirect(url_for("index"))


def _run_daily():
    class A:  # arguments équivalents à la ligne de commande
        n = int(config.env("QUALIFY_PER_DAY", "150"))
    con = db.connect()
    try:
        _job["log"] = "Lecture des réponses…"
        try:
            print(inbox.summary(inbox.check(con)))
        except Exception as exc:  # boîte inaccessible : on continue sans bloquer la journée
            print(f"Boîte Gmail inaccessible : {exc}")
        if cli.pending(con) < cli.target():  # sinon : déjà assez de mails, aucune recherche
            _job["log"] = "Récupération des entreprises…"
            cli.cmd_source(con, A)
            _job["log"] = "Emails publiés sur OpenStreetMap…"
            try:
                cli.cmd_osm(con, A)
            except Exception as exc:  # source facultative : on continue sans elle
                print(f"OpenStreetMap indisponible : {exc}")
            _job["log"] = "Recherche par métier et par ville…"
            try:
                cli.discovery.run(con, max_queries=5, stop=lambda: _job["stop"])
            except Exception as exc:
                print(f"Recherche par métier indisponible : {exc}")
            _job["log"] = "Recherche d'adresses email…"
            cli.qualify_batch(con, A.n, stop=lambda: _job["stop"], log=lambda t: _job.update(log=f"Recherche : {t}"))
        _job["log"] = "Rédaction des mails…"
        cli.cmd_run(con, A)
        _job["log"] = ("Terminé : voir « À valider »." if config.env("ANTHROPIC_API_KEY")
                       else "Terminé : passez à « À rédiger » pour faire écrire les mails par Claude.")
    except Exception as exc:
        _job["log"] = f"Erreur : {exc}"
    finally:
        _job["running"] = False


def _run_collect():
    class A:
        n = int(config.env("COLLECT_MAX", "1000"))
    con = db.connect()
    try:
        _job["log"] = "Collecte en cours…"
        tested, found = cli.cmd_collect(con, A, stop=lambda: _job["stop"], log=lambda t: _job.update(log=f"Collecte : {t}"))
        _job["log"] = f"Collecte terminée : {tested} entreprises testées, {found} adresses trouvées."
        return tested
    except Exception as exc:
        _job["log"] = f"Erreur : {exc}"
    finally:
        _job["running"] = False
        queued, _job["next"] = _job["next"], None
        if queued:  # « Préparer les mails du jour » demandé pendant la collecte : il passe maintenant
            start_job(queued)


def start_job(target=None):
    target = target or _run_daily
    if _job["running"]:
        if _job["kind"] == "collect" and target is _run_daily:  # la collecte cède la place aux mails du jour
            _job.update(stop=True, next=_run_daily, log="Collecte en pause : préparation des mails du jour…")
            return True
        return False
    _job.update(running=True, stop=False, kind="collect" if target is _run_collect else "daily")
    threading.Thread(target=target, daemon=True).start()
    return True


def collect_auto(con):
    return db.get_setting(con, "collect_auto", "1") == "1"


def start_collect_loop():
    """Collecte permanente : tant que le dashboard tourne et qu'elle est activée, relance la recherche
    d'adresses aussitôt, dès que rien d'autre ne tourne. Exceptions : 10 s après une erreur (réseau
    coupé), et plus rien une fois toutes les entreprises testées, pour ne pas tourner à vide."""

    def loop():
        time.sleep(10)
        while True:
            wait = 5  # collecte désactivée ou autre tâche en cours : on revérifie dans 5 s
            try:
                con = db.connect()
                if collect_auto(con) and not _job["running"] and not collect_progress(con)["finished"]:
                    _job.update(running=True, stop=False, kind="collect")
                    wait = 0 if _run_collect() is not None else 10
            except Exception as exc:
                print(f"Collecte permanente : {exc}")
                wait = 10
            time.sleep(wait)

    threading.Thread(target=loop, daemon=True).start()


@app.post("/collect")
def collect_now():
    start_job(_run_collect)
    return redirect(url_for("index"))


@app.post("/collect/auto")
def toggle_collect():
    con = connect()
    on = not collect_auto(con)
    db.set_setting(con, "collect_auto", "1" if on else "0")
    session["msg"] = "Collecte permanente activée." if on else "Collecte permanente désactivée."
    if not on and _job["kind"] == "collect":
        _job["stop"] = True
    return redirect(url_for("index"))


@app.post("/job/stop")
def stop_job():
    _job["stop"] = True
    if _job["kind"] == "collect":  # arrêter la collecte coupe aussi la collecte permanente
        db.set_setting(connect(), "collect_auto", "0")
    _job["log"] = "Arrêt demandé : fin après l'entreprise en cours…"
    return redirect(url_for("index"))


@app.post("/run")
def run_now():
    start_job()
    return redirect(url_for("index"))


@app.route("/cron/<token>", methods=["GET", "POST"])
def cron(token):
    """Appelé chaque matin par un service de cron gratuit (cron-job.org)."""
    expected = config.env("CRON_TOKEN")
    if not expected or not hmac.compare_digest(token, expected):
        abort(404)
    return jsonify(started=start_job())


def start_inbox_poll():
    """Vérifie la boîte Gmail toutes les INBOX_POLL_MINUTES minutes tant que le dashboard tourne : c'est ce qui
    déclenche les notifications de réponse sans avoir à ouvrir l'application (0 pour désactiver)."""
    minutes = int(config.env("INBOX_POLL_MINUTES", "15"))
    if minutes <= 0 or not config.env("GMAIL_APP_PASSWORD"):
        return

    def loop():
        time.sleep(30)
        while True:
            try:
                print(inbox.summary(inbox.check(db.connect())))
            except Exception as exc:
                print(f"Vérification de la boîte impossible : {exc}")
            time.sleep(minutes * 60)

    threading.Thread(target=loop, daemon=True).start()


def start_cleanup_once():
    """Une fois après chaque mise à jour des règles de validation : nettoie les adresses déjà en base."""
    if db.get_setting(db.connect(), "emails_cleaned") != "3":
        threading.Thread(target=run_cleanup, daemon=True).start()


if __name__ == "__main__":
    start_cleanup_once()
    start_inbox_poll()
    start_collect_loop()
    app.run(host="0.0.0.0", port=int(config.env("PORT", "8000")))
