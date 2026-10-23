"""Dashboard mobile : valider les mails du jour, voir les stats, gérer les désinscriptions."""
import hmac
import threading
from urllib.parse import quote_plus

from flask import Flask, abort, jsonify, redirect, render_template_string, request, session, url_for

from . import cli, config, db, mailer

app = Flask(__name__)
app.secret_key = config.env("DASHBOARD_SECRET") or config.env("DASHBOARD_PASSWORD", "change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30)

_job = {"running": False, "log": ""}

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--tx:#1b1f24;--mut:#667085;--ac:#1d6feb;--ok:#12805c;--ko:#c0362c;--bd:#e4e7ec}
@media(prefers-color-scheme:dark){:root{--bg:#0f1318;--card:#181d24;--tx:#e8ecf1;--mut:#98a2b3;--bd:#2a313b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.45 system-ui,sans-serif;padding:0 16px 80px}
header{display:flex;justify-content:space-between;align-items:center;padding:14px 0}h1{font-size:19px;margin:0}
nav{display:flex;gap:8px;margin-bottom:14px;overflow-x:auto}nav a{padding:8px 14px;border-radius:999px;background:var(--card);border:1px solid var(--bd);color:var(--tx);text-decoration:none;white-space:nowrap;font-size:14px}
nav a.on{background:var(--ac);color:#fff;border-color:var(--ac)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px;margin-bottom:12px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.stat b{font-size:26px;display:block}.stat span{color:var(--mut);font-size:13px}
.mut{color:var(--mut);font-size:13px}.tag{display:inline-block;font-size:12px;padding:2px 8px;border-radius:999px;background:var(--bg);border:1px solid var(--bd)}
input,textarea,select{width:100%;padding:10px;border-radius:8px;border:1px solid var(--bd);background:var(--bg);color:var(--tx);font:inherit}
textarea{min-height:200px}button,.btn{display:inline-block;padding:11px 16px;border:0;border-radius:8px;background:var(--ac);color:#fff;font:inherit;font-weight:600;text-decoration:none;cursor:pointer}
.btn.ok{background:var(--ok)}.btn.ko{background:var(--ko)}.btn.gh{background:var(--bg);color:var(--tx);border:1px solid var(--bd)}.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
pre{white-space:pre-wrap;font:inherit;margin:8px 0}
"""

PAGE = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#1d6feb">
<link rel="manifest" href="/manifest.json"><title>Prospec Bat</title><style>{{css}}</style></head><body>
<header><h1>Prospec Bat</h1><span class="mut">{{mode_label}}</span></header>
{% if msg %}<div class="card">{{msg}}</div>{% endif %}
{% if session.get('ok') %}<nav>
{% for k,l in tabs %}<a href="{{url_for('index',tab=k)}}" class="{{'on' if tab==k}}">{{l}}</a>{% endfor %}</nav>{% endif %}
{{body|safe}}</body></html>"""

LOGIN = """<div class="card"><form method="post"><p>Mot de passe</p><input type="password" name="pw" autofocus autocomplete="current-password">
{% if err %}<p style="color:var(--ko)">Mot de passe incorrect</p>{% endif %}<div class="row"><button>Entrer</button></div></form></div>"""

HOME = """<div class="grid">
{% for label,n in stats %}<div class="card stat"><b>{{n}}</b><span>{{label}}</span></div>{% endfor %}</div>
<div class="card"><b>Mode d'envoi</b><form method="post" action="{{url_for('set_mode')}}"><select name="mode" onchange="this.form.submit()">
{% for k,l in modes %}<option value="{{k}}" {{'selected' if k==mode}}>{{l}}</option>{% endfor %}</select></form>
<p class="mut">review = vous validez chaque mail ici avant envoi.</p></div>
<div class="card"><form method="post" action="{{url_for('run_now')}}"><button {{'disabled' if running}}>{{'En cours…' if running else 'Préparer les mails du jour'}}</button></form>
<pre class="mut">{{log}}</pre></div>
<div class="card"><form method="post" action="{{url_for('stop')}}"><b>Désinscription</b><p class="mut">Quelqu'un a répondu STOP :</p>
<input type="email" name="email" placeholder="email@entreprise.fr" required><div class="row"><button class="ko">Ne plus contacter</button></div></form></div>"""

DRAFT = """{% for c in rows %}<div class="card"><b>{{c.nom}}</b> <span class="tag">{{c.commune}}</span> <span class="tag">{{c.metier}}</span>
<div class="mut">{{c.email}} · {{ {'none':'pas de site','outdated':'site à refaire'}.get(c.site_status,c.site_status) }}{% if c.site_url %} · <a href="{{c.site_url}}" target="_blank" rel="noopener">voir le site</a>{% endif %}</div>
<form method="post" action="{{url_for('draft_action',siren=c.siren)}}"><input name="subject" value="{{c.subject}}"><br><br>
<textarea name="body">{{c.body}}</textarea><div class="row">
<button name="act" value="send" class="btn ok" onclick="return confirm('Envoyer ce mail à {{c.email}} ?')">Envoyer</button>
<button name="act" value="save" class="btn gh">Enregistrer</button><button name="act" value="skip" class="btn ko">Ignorer</button></div></form></div>
{% else %}<div class="card mut">Aucun mail en attente. Lancez « Préparer les mails du jour » depuis l'accueil.</div>{% endfor %}"""

WRITE = """{% if auto %}<div class="card"><b>Rédaction automatique active</b><p class="mut">Claude écrit chaque mail via la clé API quand vous appuyez sur « Préparer les mails du jour ».</p></div>
{% else %}<div class="card"><b>{{n}} entreprises prêtes à recevoir un mail</b>
<p class="mut">1. Copiez la demande.<br>2. Collez-la dans une conversation avec Claude (claude.ai).<br>3. Collez sa réponse ci-dessous.</p>
{% if batch %}<div class="row"><button class="btn pri" id="copy" type="button">Copier la demande ({{batch|length}} entreprises)</button></div>
<textarea id="prompt" readonly hidden>{{prompt}}</textarea><p class="mut" id="copied" hidden>Copié. Collez-la maintenant dans Claude.</p>{% endif %}</div>
<form class="card" method="post" action="{{url_for('import_mails')}}"><b>Réponse de Claude</b>
<textarea name="text" placeholder="Collez ici le tableau JSON écrit par Claude" required></textarea>
<div class="row"><button class="btn ok">Importer les mails</button></div></form>
<script>document.getElementById("copy")&&document.getElementById("copy").addEventListener("click",function(){var t=document.getElementById("prompt");
function done(){document.getElementById("copied").hidden=false}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t.value).then(done,function(){t.hidden=false;t.select()})}else{t.hidden=false;t.select();document.execCommand("copy");done()}});</script>{% endif %}"""

SENT = """{% for c in rows %}<div class="card"><b>{{c.nom}}</b> <span class="tag">{{c.status}}</span>
<div class="mut">{{c.email}} · {{c.contacted_at}}</div>
<form method="post" action="{{url_for('mark',siren=c.siren)}}"><div class="row">
<button name="s" value="replied" class="btn ok">A répondu</button><button name="s" value="refused" class="btn ko">Refus</button></div></form></div>
{% else %}<div class="card mut">Rien d'envoyé pour l'instant.</div>{% endfor %}"""

TABS = [("home", "Accueil"), ("write", "À rédiger"), ("drafts", "À valider"), ("sent", "Envoyés")]
MODES = [("review", "Review (je valide ici)"), ("draft", "Brouillons Gmail"), ("send", "Envoi direct")]


def page(body, tab="home", con=None):
    mode = db.send_mode(con) if con else ""
    return render_template_string(PAGE, css=CSS, body=body, tab=tab, tabs=TABS, mode_label=dict(MODES).get(mode, ""),
                                  msg=session.pop("msg", ""))


def connect():
    return db.connect()


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
    return page(render_template_string(LOGIN, err=err))


@app.route("/health")
def health():
    return "ok"


@app.route("/manifest.json")
def manifest():
    return jsonify(name="Prospec Bat", short_name="Prospec", start_url="/", display="standalone",
                   background_color="#1d6feb", theme_color="#1d6feb",
                   icons=[{"src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%231d6feb'/%3E%3Ctext x='32' y='44' font-size='34' text-anchor='middle' fill='white'%3EP%3C/text%3E%3C/svg%3E",
                           "sizes": "any", "type": "image/svg+xml"}])


@app.route("/")
def index():
    tab = request.args.get("tab", "home")
    con = connect()
    if tab == "drafts":
        rows = con.execute("SELECT * FROM companies WHERE status='drafted' ORDER BY contacted_at").fetchall()
        body = render_template_string(DRAFT, rows=rows)
    elif tab == "write":
        batch = cli.next_to_write(con)[: int(config.env("DAILY_LIMIT", "10"))]
        body = render_template_string(
            WRITE, auto=bool(config.env("ANTHROPIC_API_KEY")), n=len(cli.next_to_write(con)), batch=batch,
            prompt=mailer.batch_prompt([dict(r) for r in batch]) if batch else "")
    elif tab == "sent":
        rows = con.execute("SELECT * FROM companies WHERE status IN ('sent','followed_up') ORDER BY contacted_at DESC LIMIT 100").fetchall()
        body = render_template_string(SENT, rows=rows)
    else:
        tab = "home"
        counts = {r["status"]: r["n"] for r in con.execute("SELECT status, COUNT(*) n FROM companies GROUP BY status")}
        stats = [("entreprises en base", sum(counts.values())), ("à valider", counts.get("drafted", 0)),
                 ("envoyés", counts.get("sent", 0) + counts.get("followed_up", 0)), ("réponses", counts.get("replied", 0)),
                 ("sans email (ignorées)", counts.get("no_email", 0)), ("refus", counts.get("refused", 0))]
        body = render_template_string(HOME, stats=stats, modes=MODES, mode=db.send_mode(con), running=_job["running"], log=_job["log"])
    return page(body, tab, con)


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
    elif act in ("save", "send"):
        con.execute("UPDATE companies SET subject=?, body=? WHERE siren=?", (subject, body, siren))
        if act == "send":
            if db.is_suppressed(con, row["email"]):
                abort(409, "Adresse désinscrite")
            mailer.send(mailer.build_message(row["email"], subject, body))
            con.execute("UPDATE companies SET status='sent', contacted_at=? WHERE siren=?", (db.now(), siren))
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


@app.post("/mark/<siren>")
def mark(siren):
    s = request.form.get("s")
    if s in ("replied", "refused"):
        con = connect()
        con.execute("UPDATE companies SET status=? WHERE siren=?", (s, siren))
        con.commit()
    return redirect(url_for("index", tab="sent"))


@app.post("/stop")
def stop():
    email = request.form.get("email", "").strip()
    if email:
        db.suppress(connect(), email)
    return redirect(url_for("index"))


def _run_daily():
    class A:  # arguments équivalents à la ligne de commande
        n = int(config.env("QUALIFY_PER_DAY", "30"))
    con = db.connect()
    try:
        _job["log"] = "Récupération des entreprises…"
        cli.cmd_source(con, A)
        _job["log"] = "Qualification des entreprises…"
        cli.cmd_qualify(con, A)
        _job["log"] = "Rédaction des mails…"
        cli.cmd_run(con, A)
        _job["log"] = ("Terminé : voir « À valider »." if config.env("ANTHROPIC_API_KEY")
                       else "Terminé : passez à « À rédiger » pour faire écrire les mails par Claude.")
    except Exception as exc:
        _job["log"] = f"Erreur : {exc}"
    finally:
        _job["running"] = False


def start_job():
    if _job["running"]:
        return False
    _job["running"] = True
    threading.Thread(target=_run_daily, daemon=True).start()
    return True


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(config.env("PORT", "8000")))
