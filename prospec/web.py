"""Dashboard mobile : valider les mails du jour, voir les stats, gérer les désinscriptions."""
import hmac
import threading
from urllib.parse import quote_plus

from flask import Flask, abort, jsonify, redirect, render_template_string, request, session, url_for

from . import cli, config, db, mailer

app = Flask(__name__)
app.secret_key = config.env("DASHBOARD_SECRET") or config.env("DASHBOARD_PASSWORD", "change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30)

_job = {"running": False, "log": "", "stop": False}

def _sprite(rows, palette, px=4):
    """Pixel art en CSS : une grille de caractères -> une liste de box-shadow."""
    shadows = [f"{x * px}px {y * px}px 0 {palette[ch]}" for y, line in enumerate(rows)
               for x, ch in enumerate(line) if ch in palette]
    return ",".join(shadows)


# « Bati », le petit robot de prospection (dessin original)
BOT = _sprite([
    "...cc...",
    ".gggggg.",
    ".gcggcg.",
    ".gggggg.",
    "..oooo..",
    ".oooooo.",
    ".o.oo.o.",
    "..b..b..",
], {"c": "#4de8ff", "g": "#d9d4ff", "o": "#ff8a3d", "b": "#2a2160"})

CSS = """
/* Monde 8 bits néon : ciel de nuit, blocs à bord pixel, pièces d'or ; colonne unique de 560px */
:root{--sky:#17113a;--sky2:#2b1b5e;--panel:#2a2160;--panel2:#352a78;--ink:#fff7e6;--mut:#b9b3e6;
--coin:#ffcc29;--coin2:#c98a00;--go:#2fd35f;--go2:#178a39;--brick:#e2552d;--brick2:#8f2c12;--neon:#4de8ff;--line:#0c0824;
--px:"Press Start 2P",ui-monospace,monospace;--body:"Chakra Petch",system-ui,sans-serif;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;color:var(--ink);font:16px/1.5 var(--body);padding:0 max(16px,env(safe-area-inset-right,0px)) 0 max(16px,env(safe-area-inset-left,0px))}
html{min-height:100%;background-color:var(--sky);background:radial-gradient(1px 1px at 12% 18%,#fff8 50%,transparent 51%),radial-gradient(1px 1px at 72% 9%,#fff9 50%,transparent 51%),
radial-gradient(2px 2px at 38% 42%,#4de8ff88 50%,transparent 51%),radial-gradient(1px 1px at 88% 61%,#fff7 50%,transparent 51%),
radial-gradient(1px 1px at 55% 77%,#fff6 50%,transparent 51%),linear-gradient(180deg,var(--sky) 0%,var(--sky2) 70%,#3a1f6e 100%)}
.wrap{max-width:560px;margin:0 auto;padding-block:max(12px,env(safe-area-inset-top,0px)) 0;position:relative;z-index:1}
.cloud{position:fixed;z-index:0;width:8px;height:8px;opacity:.18;animation:drift 60s linear infinite;pointer-events:none;
box-shadow:16px 0 #fff,24px 0 #fff,32px 0 #fff,8px 8px #fff,16px 8px #fff,24px 8px #fff,32px 8px #fff,40px 8px #fff,0 16px #fff,8px 16px #fff,16px 16px #fff,24px 16px #fff,32px 16px #fff,40px 16px #fff,48px 16px #fff}
.cloud.c2{top:38%;animation-duration:85s;animation-delay:-30s;transform:scale(1.4)}.cloud.c1{top:12%}
@keyframes drift{from{left:-80px}to{left:110%}}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 0 14px;flex-wrap:wrap}
h1{font:400 15px/1.3 var(--px);margin:0;letter-spacing:1px;text-shadow:2px 2px 0 var(--line),0 0 12px #4de8ff66}
h1 small{display:block;font-size:8px;color:var(--neon);letter-spacing:2px;margin-top:6px;text-shadow:none}
.hud{display:flex;gap:14px;font:400 9px/1 var(--px);color:var(--mut);align-items:center}
.hud b{display:block;color:var(--ink);font-size:11px;margin-top:5px;font-weight:400}
.coin{display:inline-block;width:14px;height:14px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#fff3b0 0 18%,var(--coin) 20% 60%,var(--coin2) 62%);
box-shadow:0 0 0 2px var(--line);animation:spin 1.6s steps(8) infinite;vertical-align:-2px}
@keyframes spin{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.15)}}
.block{background:var(--panel);border:0;padding:14px;margin-bottom:14px;position:relative;
box-shadow:0 -4px 0 0 var(--line),0 4px 0 0 var(--line),-4px 0 0 0 var(--line),4px 0 0 0 var(--line),inset 0 4px 0 0 #ffffff1a,inset 0 -4px 0 0 #00000040,8px 8px 0 0 #0c082499}
.block h2{font:400 10px/1.5 var(--px);margin:0 0 10px;color:var(--coin);letter-spacing:1px}
.quest .bar{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:4px;margin-top:10px}
.quest .bar i{height:16px;background:#0c0824;box-shadow:inset 0 0 0 2px #ffffff14}
.quest .bar i.on{background:linear-gradient(180deg,#ffe680,var(--coin) 55%,var(--coin2));box-shadow:inset 0 -3px 0 #0003;animation:pop .5s ease-out both}
@keyframes pop{0%{transform:translateY(6px) scale(.6)}60%{transform:translateY(-4px)}100%{transform:none}}
.quest p{margin:0;font:400 9px/1.6 var(--px);color:var(--mut)}
.quest p b{color:var(--ink);font-weight:400}
nav{display:flex;gap:10px;overflow-x:auto;padding:4px 4px 12px;margin:0 -4px 4px}
nav a{flex:none;font:400 9px/1 var(--px);color:var(--ink);text-decoration:none;padding:11px 12px;background:var(--panel2);
box-shadow:0 0 0 3px var(--line),inset 0 -4px 0 #0005;transition:transform .12s}
nav a.on{background:var(--go);color:var(--line);box-shadow:0 0 0 3px var(--line),inset 0 -4px 0 var(--go2),0 0 14px #2fd35f66}
nav a:active{transform:translateY(2px)}
nav a .n{display:inline-block;margin-left:6px;padding:3px 5px;background:var(--coin);color:var(--line)}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:16px}
@media (max-width:420px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.stat{margin:0;text-align:center;padding:14px 6px;cursor:default}
.stat b{display:block;font:400 18px/1 var(--px);color:var(--ink);font-variant-numeric:tabular-nums;text-shadow:2px 2px 0 var(--line)}
.stat span{display:block;margin-top:9px;font-size:13px;color:var(--mut);line-height:1.25}
.stat:nth-child(1) b{color:var(--neon)}.stat:nth-child(2) b,.stat:nth-child(5) b{color:var(--go)}.stat:nth-child(3) b,.stat:nth-child(4) b{color:var(--coin)}.stat:nth-child(6) b{color:var(--brick)}
.stat:hover,.stat:active{animation:bump .3s steps(3)}
@keyframes bump{50%{transform:translateY(-6px)}}
.mut{color:var(--mut);font-size:14px}
.tag{display:inline-block;font:400 8px/1 var(--px);padding:5px 6px;background:#0c0824;color:var(--neon);margin:2px 4px 2px 0;vertical-align:middle}
.tag.hot{color:var(--brick);}.tag.warm{color:var(--coin)}
input,textarea,select{width:100%;min-width:0;padding:11px;border:0;background:#0f0a2b;color:var(--ink);font:16px/1.5 var(--body);
box-shadow:inset 0 0 0 2px #ffffff22}
input:focus,textarea:focus,select:focus{outline:none;box-shadow:inset 0 0 0 2px var(--neon),0 0 12px #4de8ff55}
textarea{min-height:220px;margin-top:10px;resize:vertical}
.row{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px;align-items:center}
button,.btn{display:inline-block;font:400 10px/1.2 var(--px);letter-spacing:.5px;padding:13px 14px;border:0;cursor:pointer;color:var(--line);text-decoration:none;
background:var(--coin);box-shadow:0 0 0 3px var(--line),inset 0 -5px 0 var(--coin2),inset 0 3px 0 #fff6;transition:transform .08s}
button:active,.btn:active{transform:translateY(3px);box-shadow:0 0 0 3px var(--line),inset 0 -2px 0 var(--coin2)}
button:focus-visible,.btn:focus-visible,nav a:focus-visible{outline:3px solid var(--neon);outline-offset:4px}
button[disabled]{filter:grayscale(.7) brightness(.8);cursor:wait}
.btn.ok,button.ok{background:var(--go);box-shadow:0 0 0 3px var(--line),inset 0 -5px 0 var(--go2),inset 0 3px 0 #fff6}
.btn.ko,button.ko{background:var(--brick);color:var(--ink);box-shadow:0 0 0 3px var(--line),inset 0 -5px 0 var(--brick2),inset 0 3px 0 #fff4}
.btn.gh{background:var(--panel2);color:var(--ink);box-shadow:0 0 0 3px var(--line),inset 0 -5px 0 #0006}
.btn.big{font-size:11px;padding:16px 18px;width:100%;text-align:center}
pre{white-space:pre-wrap;font:400 9px/1.7 var(--px);margin:12px 0 0;color:var(--neon)}
a{color:var(--neon)}
.msg{background:var(--go2);color:var(--ink);font:400 9px/1.7 var(--px)}
.msg .coin{margin-right:8px;animation:spin .6s steps(8) 3,rise .9s ease-out both}
@keyframes rise{0%{transform:translateY(10px);opacity:0}100%{transform:none;opacity:1}}
.runner{height:50px;position:relative;margin-top:12px;overflow:hidden}
.runner::after{content:"";position:absolute;left:0;right:0;bottom:0;height:14px;background:repeating-linear-gradient(90deg,var(--brick) 0 30px,var(--brick2) 30px 32px);box-shadow:inset 0 3px 0 var(--go)}
.runner .bot{position:absolute;left:0;top:4px;width:4px;height:4px;box-shadow:{{bot}};animation:run 6s linear infinite,hop .4s steps(2) infinite}
@keyframes run{from{transform:translateX(-40px)}to{transform:translateX(560px)}}
@keyframes hop{50%{margin-top:-4px}}
.idle .bot{position:relative;display:inline-block;width:4px;height:4px;margin:0 36px 30px 0;box-shadow:{{bot}};vertical-align:top}
.ground{height:28px;margin:28px calc(-1 * max(16px,env(safe-area-inset-left,0px))) 0;background:repeating-linear-gradient(90deg,var(--brick) 0 30px,var(--brick2) 30px 32px),var(--brick);
box-shadow:inset 0 4px 0 var(--go),inset 0 8px 0 var(--go2)}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
"""

PAGE = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#17113a">
<link rel="manifest" href="/manifest.json"><title>Prospec Bat</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600&family=Press+Start+2P&display=swap">
<style>{{css|safe}}</style></head><body><i class="cloud c1"></i><i class="cloud c2"></i><div class="wrap">
<header><h1>PROSPEC BAT<small>MONDE 12 · AVEYRON</small></h1>
{% if session.get('ok') and hud %}<div class="hud"><span>ENVOYES<b>{{hud.sent}}</b></span><span><i class="coin"></i> REPONSES<b>{{hud.replied}}</b></span><span>MODE<b>{{mode_short}}</b></span></div>{% endif %}</header>
{% if msg %}<div class="block msg"><i class="coin"></i>{{msg}}</div>{% endif %}
{% if session.get('ok') %}<nav>
{% for k,l in tabs %}<a href="{{url_for('index',tab=k)}}" class="{{'on' if tab==k}}">{{l}}{% if counts and counts.get(k) %}<span class="n">{{counts[k]}}</span>{% endif %}</a>{% endfor %}</nav>{% endif %}
{{body|safe}}<div class="ground" aria-hidden="true"></div></div></body></html>"""

LOGIN = """<div class="block"><h2>APPUYEZ SUR START</h2><form method="post"><label class="mut" for="pw">Mot de passe</label>
<input type="password" name="pw" id="pw" autofocus autocomplete="current-password">
{% if err %}<p style="color:var(--brick)">Mot de passe incorrect</p>{% endif %}<div class="row"><button class="ok">▶ START</button></div></form></div>"""

HOME = """<div class="block quest" style="--n:{{limit}}"><h2>QUETE DU JOUR</h2>
<p><b>{{today}}</b> / {{limit}} mails envoyés aujourd'hui</p>
<div class="bar">{% for i in range(limit) %}<i class="{{'on' if i < today}}" style="animation-delay:{{i*60}}ms"></i>{% endfor %}</div></div>
<div class="grid">
{% for label,n in stats %}<div class="block stat"><b>{{n}}</b><span>{{label}}</span></div>{% endfor %}</div>
<div class="block"><h2>NIVEAU DU JOUR</h2><form method="post" action="{{url_for('run_now')}}">
<button class="btn big" {{'disabled' if running}}>{{'⏳ EN COURS…' if running else '▶ PREPARER LES MAILS DU JOUR'}}</button></form>
{% if running %}<div class="runner" aria-hidden="true"><i class="bot"></i></div>{% endif %}
<pre>{{log}}</pre></div>
<div class="block"><h2>MODE COLLECTE</h2><p class="mut">Teste un grand nombre d'entreprises pour remplir le stock d'adresses. Les envois restent limités à {{limit}} par jour. Ça peut durer des heures : laissez le téléphone branché.</p>
<div class="row">{% if running %}<form method="post" action="{{url_for('stop_job')}}"><button class="ko">■ ARRETER</button></form>
{% else %}<form method="post" action="{{url_for('collect_now')}}"><button class="ok">★ LANCER LA COLLECTE</button></form>{% endif %}</div></div>
{% if running %}<script>setTimeout(function(){location.reload()},15000)</script>{% endif %}
<div class="block"><h2>MODE D'ENVOI</h2><form method="post" action="{{url_for('set_mode')}}"><label class="mut" for="mode">En mode Review, aucun mail ne part sans votre bouton Envoyer.</label>
<select name="mode" id="mode" onchange="this.form.submit()" style="margin-top:8px">
{% for k,l in modes %}<option value="{{k}}" {{'selected' if k==mode}}>{{l}}</option>{% endfor %}</select></form></div>
<div class="block"><form method="post" action="{{url_for('stop')}}"><h2>DESINSCRIPTION</h2><label class="mut" for="stopmail">Quelqu'un a répondu STOP :</label>
<input type="email" name="email" id="stopmail" placeholder="email@entreprise.fr" required style="margin-top:8px"><div class="row"><button class="ko">NE PLUS CONTACTER</button></div></form></div>"""

SITE = "{{ {'none':'pas de site','outdated':'site à refaire'}.get(c.site_status,c.site_status) }}"

DRAFT = """{% for c in rows %}<div class="block"><h2>{{c.enseigne or c.nom}}</h2>
<span class="tag">{{c.commune}}</span><span class="tag">{{c.metier}}</span><span class="tag {{'hot' if c.site_status=='none' else 'warm'}}">""" + SITE + """</span>
<div class="mut" style="margin-top:6px">{{c.email}}{% if c.site_url %} · <a href="{{c.site_url}}" target="_blank" rel="noopener">voir le site</a>{% endif %}</div>
<form method="post" action="{{url_for('draft_action',siren=c.siren)}}"><input name="subject" aria-label="Objet" value="{{c.subject}}" style="margin-top:10px">
<textarea name="body" aria-label="Message">{{c.body}}</textarea><div class="row">
<button name="act" value="send" class="ok" onclick="return confirm('Envoyer ce mail à {{c.email}} ?')">✉ ENVOYER</button>
<button name="act" value="save" class="btn gh">ENREGISTRER</button><button name="act" value="skip" class="ko">IGNORER</button></div></form></div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Aucun mail en attente. Passez par « À rédiger », ou lancez « Préparer les mails du jour » depuis l'accueil.</span></div>{% endfor %}"""

WRITE = """{% if auto %}<div class="block"><h2>REDACTION AUTO</h2><p class="mut">Claude écrit chaque mail via la clé API quand vous appuyez sur « Préparer les mails du jour ».</p></div>
{% else %}<div class="block"><h2>{{n}} ENTREPRISES PRETES</h2>
<p class="mut">1. Copiez la demande.<br>2. Collez-la dans une conversation avec Claude (claude.ai).<br>3. Collez sa réponse ci-dessous.</p>
{% if batch %}<div class="row"><button class="btn" id="copy" type="button">⧉ Copier la demande ({{batch|length}} entreprises)</button></div>
<textarea id="prompt" readonly hidden>{{prompt}}</textarea><p class="mut" id="copied" hidden>Copié. Collez-la maintenant dans Claude.</p>{% endif %}</div>
<form class="block" method="post" action="{{url_for('import_mails')}}"><h2>REPONSE DE CLAUDE</h2>
<textarea name="text" aria-label="Réponse de Claude" placeholder="Collez ici le tableau JSON écrit par Claude" required></textarea>
<div class="row"><button class="ok">⬇ IMPORTER LES MAILS</button></div></form>
<script>document.getElementById("copy")&&document.getElementById("copy").addEventListener("click",function(){var t=document.getElementById("prompt");
function done(){document.getElementById("copied").hidden=false}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t.value).then(done,function(){t.hidden=false;t.select()})}else{t.hidden=false;t.select();document.execCommand("copy");done()}});</script>{% endif %}"""

SENT = """{% for c in rows %}<div class="block"><h2>{{c.enseigne or c.nom}}</h2><span class="tag {{'warm' if c.status=='followed_up'}}">{{ {'sent':'envoyé','followed_up':'relancé'}.get(c.status,c.status) }}</span>
<div class="mut" style="margin-top:6px">{{c.email}} · {{(c.contacted_at or '')[:16]|replace('T',' ')}}</div>
<form method="post" action="{{url_for('mark',siren=c.siren)}}"><div class="row">
<button name="s" value="replied" class="ok">★ A REPONDU</button><button name="s" value="refused" class="ko">REFUS</button></div></form></div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Rien d'envoyé pour l'instant.</span></div>{% endfor %}"""

TABS = [("home", "ACCUEIL"), ("write", "A REDIGER"), ("drafts", "A VALIDER"), ("sent", "ENVOYES")]
MODES = [("review", "Review (je valide ici)"), ("draft", "Brouillons Gmail"), ("send", "Envoi direct")]
MODE_SHORT = {"review": "REVIEW", "draft": "GMAIL", "send": "AUTO"}


def hud_counts(con):
    counts = {r["status"]: r["n"] for r in con.execute("SELECT status, COUNT(*) n FROM companies GROUP BY status")}
    return {"sent": counts.get("sent", 0) + counts.get("followed_up", 0) + counts.get("replied", 0) + counts.get("refused", 0),
            "replied": counts.get("replied", 0), "drafted": counts.get("drafted", 0)}


def page(body, tab="home", con=None):
    mode = db.send_mode(con) if con else ""
    hud = hud_counts(con) if con else None
    counts = {"write": len(cli.next_to_write(con)), "drafts": hud["drafted"]} if con else {}
    return render_template_string(PAGE, css=CSS.replace("{{bot}}", BOT), body=body, tab=tab, tabs=TABS, hud=hud,
                                  mode_short=MODE_SHORT.get(mode, ""), counts=counts, msg=session.pop("msg", ""))


def sent_today(con):
    return con.execute(
        "SELECT COUNT(*) FROM companies WHERE status IN ('sent','followed_up','replied','refused') "
        "AND substr(contacted_at, 1, 10) = date('now', 'localtime')").fetchone()[0]


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
                   background_color="#17113a", theme_color="#17113a",
                   icons=[{"src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%2317113a'/%3E%3Ccircle cx='32' cy='32' r='18' fill='%23ffcc29' stroke='%230c0824' stroke-width='5'/%3E%3Crect x='29' y='22' width='6' height='20' fill='%23c98a00'/%3E%3C/svg%3E",
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
        stats = [("entreprises en base", sum(counts.values())), ("adresses en stock", len(cli.next_to_write(con))),
                 ("à valider", counts.get("drafted", 0)), ("envoyés", counts.get("sent", 0) + counts.get("followed_up", 0)),
                 ("réponses", counts.get("replied", 0)), ("refus", counts.get("refused", 0))]
        body = render_template_string(HOME, stats=stats, modes=MODES, mode=db.send_mode(con), running=_job["running"], log=_job["log"], limit=cli.target(), today=min(sent_today(con), cli.target()))
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
            try:
                mailer.assert_sourced(row)
            except ValueError as exc:
                abort(409, str(exc))
            mailer.send(mailer.build_message(row["email"], subject, body, row["email_source"]))
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
        n = int(config.env("QUALIFY_PER_DAY", "150"))
    con = db.connect()
    try:
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
    except Exception as exc:
        _job["log"] = f"Erreur : {exc}"
    finally:
        _job["running"] = False


def start_job(target=None):
    if _job["running"]:
        return False
    _job.update(running=True, stop=False)
    threading.Thread(target=target or _run_daily, daemon=True).start()
    return True


@app.post("/collect")
def collect_now():
    start_job(_run_collect)
    return redirect(url_for("index"))


@app.post("/job/stop")
def stop_job():
    _job["stop"] = True
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(config.env("PORT", "8000")))
