"""Dashboard mobile : valider les mails du jour, voir les stats, gérer les désinscriptions."""
import hmac
import re
from datetime import datetime
import random
import threading
import time
from urllib.parse import quote_plus

from flask import Flask, abort, jsonify, redirect, render_template_string, request, session, url_for

from . import cli, config, db, inbox, mailer, stats as statsmod

app = Flask(__name__)
app.secret_key = config.env("DASHBOARD_SECRET") or config.env("DASHBOARD_PASSWORD", "change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30)

_job = {"running": False, "log": "", "stop": False}
_send = {"running": False, "log": "", "stop": False}  # envoi groupé, indépendant des recherches

from urllib.parse import quote as _q

# « Bati », la mascotte de prospection (dessin original) : tête ronde bleue, corps rouge, antenne dorée
BOT_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 44 52'>"
           "<line x1='22' y1='9' x2='22' y2='3' stroke='#1d3d8f' stroke-width='3' stroke-linecap='round'/>"
           "<circle cx='22' cy='4' r='4' fill='#ffc61a' stroke='#1d3d8f' stroke-width='2'/>"
           "<rect x='5' y='9' width='34' height='24' rx='12' fill='#2f7bff' stroke='#1d3d8f' stroke-width='2.5'/>"
           "<rect x='11' y='14' width='22' height='13' rx='6.5' fill='#fff'/>"
           "<circle cx='17' cy='20.5' r='3' fill='#1d3d8f'/><circle cx='27' cy='20.5' r='3' fill='#1d3d8f'/>"
           "<circle cx='18' cy='19.5' r='1' fill='#fff'/><circle cx='28' cy='19.5' r='1' fill='#fff'/>"
           "<rect x='10' y='32' width='24' height='13' rx='6.5' fill='#ff3b3b' stroke='#1d3d8f' stroke-width='2.5'/>"
           "<circle cx='22' cy='38.5' r='2.6' fill='#ffc61a'/>"
           "<ellipse cx='15' cy='48' rx='5' ry='3.2' fill='#1d3d8f'/><ellipse cx='29' cy='48' rx='5' ry='3.2' fill='#1d3d8f'/></svg>")
BOT = "url(\"data:image/svg+xml," + _q(BOT_SVG) + "\")"

CSS = """
/* Monde de jeu lumineux : fond blanc à pois, formes bombées, 4 couleurs franches ; colonne unique de 560px */
:root{--bg:#ffffff;--dot:#eef3ff;--ink:#1d2a5c;--mut:#5d6894;--line:#1d3d8f;
--red:#ff3b3b;--red2:#c81e2b;--blue:#2f7bff;--blue2:#1b4fc4;--yellow:#ffc61a;--yellow2:#d99300;--green:#2ec95c;--green2:#16913b;
--sky:#e6f2ff;--card:#ffffff;--soft:#f4f7ff;
--display:"Fredoka","Baloo 2",ui-rounded,system-ui,sans-serif;--body:"Nunito",ui-rounded,system-ui,sans-serif;color-scheme:light}
*{box-sizing:border-box}
html{min-height:100%;background-color:var(--bg);background-image:radial-gradient(var(--dot) 18%,transparent 20%),radial-gradient(var(--dot) 18%,transparent 20%);
background-size:34px 34px;background-position:0 0,17px 17px}
body{margin:0;min-height:100vh;color:var(--ink);font:16px/1.5 var(--body);padding:0 max(16px,env(safe-area-inset-right,0px)) 0 max(16px,env(safe-area-inset-left,0px))}
.wrap{max-width:560px;margin:0 auto;padding-block:max(14px,env(safe-area-inset-top,0px)) 0;position:relative;z-index:1}
.cloud{position:fixed;z-index:0;top:70px;width:90px;height:30px;border-radius:30px;background:#fff;pointer-events:none;
box-shadow:0 0 0 3px #d6e6ff;animation:drift 70s linear infinite}
.cloud::before,.cloud::after{content:"";position:absolute;background:#fff;border-radius:50%;box-shadow:0 -3px 0 0 #d6e6ff}
.cloud::before{width:40px;height:40px;left:12px;top:-20px}.cloud::after{width:30px;height:30px;left:44px;top:-14px}
.cloud.c2{top:46%;animation-duration:95s;animation-delay:-40s;transform:scale(.8)}
@keyframes drift{from{left:-120px}to{left:110%}}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:6px 0 16px;flex-wrap:wrap}
h1{font:700 30px/1 var(--display);margin:0;letter-spacing:.5px;display:flex;gap:1px;flex-wrap:wrap;align-items:baseline}
h1 span{display:inline-block;-webkit-text-stroke:2px var(--line);paint-order:stroke fill;text-shadow:0 3px 0 var(--line);animation:wave 3.2s ease-in-out infinite}
h1 .l0{color:var(--red)}h1 .l1{color:var(--blue)}h1 .l2{color:var(--yellow)}h1 .l3{color:var(--green)}
h1 .sp{width:10px}
@keyframes wave{0%,85%,100%{transform:translateY(0)}92%{transform:translateY(-6px)}}
h1 small{display:block;width:100%;font:700 12px/1 var(--display);color:var(--blue);letter-spacing:3px;margin-top:8px;-webkit-text-stroke:0;text-shadow:none}
.hud{display:flex;gap:8px}
.hud span{display:flex;flex-direction:column;align-items:center;min-width:64px;padding:6px 10px 7px;border-radius:16px;background:#fff;
box-shadow:0 0 0 3px var(--line),0 4px 0 3px var(--line);font:700 10px/1 var(--display);color:var(--mut);letter-spacing:.5px}
.hud b{font:700 18px/1.1 var(--display);color:var(--ink);margin-top:3px;font-variant-numeric:tabular-nums}
.hud .r b{color:var(--red)}
.coin{display:inline-block;width:16px;height:16px;border-radius:50%;background:radial-gradient(circle at 38% 32%,#fff6c2 0 16%,var(--yellow) 18% 58%,var(--yellow2) 60%);
box-shadow:0 0 0 2px var(--line);animation:spin 1.8s ease-in-out infinite;vertical-align:-3px}
@keyframes spin{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.15)}}
.block{background:var(--card);border-radius:24px;padding:18px;margin-bottom:18px;position:relative;
box-shadow:0 0 0 3px var(--line),0 7px 0 3px var(--line)}
.block h2{font:700 19px/1.2 var(--display);margin:0 0 10px;color:var(--ink);display:flex;align-items:center;gap:10px}
.block h2::before{content:"";width:14px;height:14px;border-radius:50%;background:var(--c,var(--blue));box-shadow:0 0 0 3px var(--line);flex:none}
.quest{background:linear-gradient(180deg,var(--sky),#fff 70%)}
.quest h2{--c:var(--yellow)}
.quest .bar{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:6px;margin-top:12px;padding:6px;border-radius:999px;background:#fff;box-shadow:inset 0 0 0 3px var(--line)}
.quest .bar i{height:18px;border-radius:999px;background:var(--soft)}
.quest .bar i.on{background:radial-gradient(circle at 35% 30%,#fff6c2 0 14%,var(--yellow) 16% 60%,var(--yellow2));box-shadow:inset 0 -3px 0 #0002;animation:pop .55s cubic-bezier(.3,1.8,.5,1) both}
@keyframes pop{0%{transform:scale(.2)}100%{transform:none}}
.quest p{margin:0;font:700 15px/1.4 var(--display);color:var(--mut)}
.quest p b{color:var(--ink);font-size:22px}
nav{display:flex;gap:10px;overflow-x:auto;padding:4px 4px 16px;margin:0 -4px 2px}
nav a{flex:none;font:700 15px/1 var(--display);color:var(--ink);text-decoration:none;padding:11px 16px 12px;border-radius:999px;background:#fff;
box-shadow:0 0 0 3px var(--line),0 4px 0 3px var(--line);transition:transform .12s}
nav a.on{background:var(--red);color:#fff;box-shadow:0 0 0 3px var(--line),0 4px 0 3px var(--red2)}
nav a:active{transform:translateY(3px)}
nav a .n{display:inline-block;margin-left:7px;min-width:22px;padding:3px 6px;border-radius:999px;background:var(--yellow);color:var(--ink);text-align:center;box-shadow:0 0 0 2px var(--line)}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-bottom:20px}
@media (max-width:420px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.stat{margin:0;text-align:center;padding:16px 8px 14px;border-radius:22px;transition:transform .15s}
.stat b{display:inline-grid;place-items:center;min-width:58px;height:58px;padding:0 10px;border-radius:999px;font:700 26px/1 var(--display);color:#fff;
background:var(--c);box-shadow:0 0 0 3px var(--line),inset 0 -5px 0 #0003,inset 0 4px 0 #fff5;font-variant-numeric:tabular-nums}
.stat span{display:block;margin-top:10px;font:600 14px/1.25 var(--body);color:var(--mut)}
.stat:nth-child(1){--c:var(--blue)}.stat:nth-child(2){--c:var(--green)}.stat:nth-child(3){--c:var(--yellow)}
.stat:nth-child(3) b{color:var(--ink)}.stat:nth-child(4){--c:var(--blue)}.stat:nth-child(5){--c:var(--green)}.stat:nth-child(6){--c:var(--red)}
.stat:active,.stat:hover{transform:translateY(-4px) rotate(-1deg)}
.mut{color:var(--mut);font-size:15px}
.tag{display:inline-block;font:700 13px/1 var(--display);padding:6px 11px;border-radius:999px;background:var(--sky);color:var(--blue2);margin:2px 6px 2px 0;box-shadow:inset 0 0 0 2px #c9dcff}
.tag.good{background:#dcf8e4;color:var(--green2);box-shadow:inset 0 0 0 2px #a8ebbb}.tag.hot{background:#ffe4e4;color:var(--red2);box-shadow:inset 0 0 0 2px #ffc2c2}.tag.warm{background:#fff3cc;color:#8a5d00;box-shadow:inset 0 0 0 2px #ffe08a}
input,textarea,select{width:100%;min-width:0;padding:12px 14px;border:0;border-radius:16px;background:var(--soft);color:var(--ink);font:16px/1.5 var(--body);
box-shadow:inset 0 0 0 2.5px #c9d3f0}
input:focus,textarea:focus,select:focus{outline:none;box-shadow:inset 0 0 0 3px var(--blue),0 0 0 4px #2f7bff33}
textarea{min-height:220px;margin-top:10px;resize:vertical}
.row{display:flex;gap:12px;flex-wrap:wrap;margin-top:14px;align-items:center}
button,.btn{display:inline-block;font:700 16px/1.1 var(--display);padding:13px 20px 14px;border:0;border-radius:999px;cursor:pointer;color:#fff;text-decoration:none;
background:var(--blue);box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--blue2),inset 0 3px 0 #fff5;transition:transform .1s,box-shadow .1s}
button:active,.btn:active{transform:translateY(4px);box-shadow:0 0 0 3px var(--line),0 1px 0 3px var(--blue2)}
button:focus-visible,.btn:focus-visible,nav a:focus-visible{outline:3px solid var(--yellow);outline-offset:5px}
button[disabled]{opacity:.7;cursor:wait}
.btn.ok,button.ok{background:var(--green);box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--green2),inset 0 3px 0 #fff5}
.btn.ok:active,button.ok:active{box-shadow:0 0 0 3px var(--line),0 1px 0 3px var(--green2)}
.btn.ko,button.ko{background:var(--red);box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--red2),inset 0 3px 0 #fff5}
.btn.ko:active,button.ko:active{box-shadow:0 0 0 3px var(--line),0 1px 0 3px var(--red2)}
.btn.gh{background:#fff;color:var(--ink);box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--line)}
.btn.big{font-size:18px;padding:17px 20px 18px;width:100%;text-align:center;background:var(--yellow);color:var(--ink);box-shadow:0 0 0 3px var(--line),0 6px 0 3px var(--yellow2),inset 0 4px 0 #fff8}
pre.sig{font:600 14px/1.45 var(--body);color:var(--mut);background:var(--soft);border-radius:16px;padding:4px 14px 12px;margin:0}
.btn.big.ok{background:var(--green);color:#fff;box-shadow:0 0 0 3px var(--line),0 6px 0 3px var(--green2),inset 0 4px 0 #fff6}
button.armed{background:var(--yellow)!important;color:var(--ink)!important;box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--yellow2)!important}
.log{white-space:pre-wrap;font:700 15px/1.5 var(--display);color:var(--blue2);margin:0}
pre{white-space:pre-wrap;font:700 14px/1.5 var(--display);margin:12px 0 0;color:var(--blue2)}
a{color:var(--blue2);font-weight:700}
.msg{background:#e3fbea;font:700 15px/1.4 var(--display);display:flex;gap:10px;align-items:center}
.msg .coin{flex:none;animation:spin .7s ease-in-out 3,rise .9s cubic-bezier(.3,1.8,.5,1) both}
@keyframes rise{0%{transform:translateY(14px) scale(.4);opacity:0}100%{transform:none;opacity:1}}
.bot{display:inline-block;width:44px;height:52px;background:{{bot}} center/contain no-repeat}
.runner{height:76px;position:relative;margin-top:14px;overflow:hidden;border-radius:18px;background:linear-gradient(180deg,var(--sky),#fff)}
.runner::after{content:"";position:absolute;left:0;right:0;bottom:0;height:16px;border-radius:16px 16px 0 0;background:var(--green);box-shadow:inset 0 3px 0 #ffffff66}
.runner .bot{position:absolute;left:0;bottom:12px;animation:run 6s linear infinite,hop .5s ease-in-out infinite}
@keyframes run{from{transform:translateX(-50px)}to{transform:translateX(560px)}}
@keyframes hop{0%,100%{margin-bottom:0}50%{margin-bottom:14px}}
.idle{display:flex;gap:14px;align-items:center}.idle .bot{flex:none;animation:hop 2.4s ease-in-out infinite}
.ground{height:44px;margin:34px calc(-1 * max(16px,env(safe-area-inset-left,0px))) 0;position:relative;
background:radial-gradient(ellipse 130px 44px at 18% 100%,var(--green) 98%,transparent),radial-gradient(ellipse 170px 56px at 62% 100%,#5fdc85 98%,transparent),
radial-gradient(ellipse 120px 40px at 96% 100%,var(--green) 98%,transparent)}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
"""

PAGE = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#ffffff">
<link rel="manifest" href="/manifest.json"><title>Prospec Bat</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@400;600;700&display=swap">
<style>{{css|safe}}</style></head><body><i class="cloud c1"></i><i class="cloud c2"></i><div class="wrap">
<header><h1>{% for ch in "PROSPEC BAT" %}{% if ch == " " %}<span class="sp"></span>{% else %}<span class="l{{loop.index0 % 4}}" style="animation-delay:{{loop.index0*90}}ms">{{ch}}</span>{% endif %}{% endfor %}<small>MONDE 12 · AVEYRON</small></h1>
{% if session.get('ok') and hud %}<div class="hud"><span>ENVOYÉS<b>{{hud.sent}}</b></span><span class="r"><span style="all:unset;display:flex;gap:4px;align-items:center"><i class="coin"></i>RÉPONSES</span><b>{{hud.replied}}</b></span><span>MODE<b>{{mode_short}}</b></span></div>{% endif %}</header>
{% if msg %}<div class="block msg"><i class="coin"></i>{{msg}}</div>{% endif %}
{% if session.get('ok') %}<nav>
{% for k,l in tabs %}<a href="{{url_for('index',tab=k)}}" class="{{'on' if tab==k}}">{{l}}{% if counts and counts.get(k) %}<span class="n">{{counts[k]}}</span>{% endif %}</a>{% endfor %}</nav>{% endif %}
{{body|safe}}<div class="ground" aria-hidden="true"></div></div></body></html>"""

LOGIN = """<div class="block"><h2>Appuyez sur Start</h2><form method="post"><label class="mut" for="pw">Mot de passe</label>
<input type="password" name="pw" id="pw" autofocus autocomplete="current-password">
{% if err %}<p style="color:var(--brick)">Mot de passe incorrect</p>{% endif %}<div class="row"><button class="ok">▶ Start</button></div></form></div>"""

HOME = """<div class="block quest" style="--n:{{limit}}"><h2>Objectif du jour</h2>
<p><b>{{today}}</b> mail{{'s' if today > 1}} envoyé{{'s' if today > 1}} aujourd'hui · objectif {{limit}}</p>
<div class="bar">{% for i in range(limit) %}<i class="{{'on' if i < today}}" style="animation-delay:{{i*60}}ms"></i>{% endfor %}</div></div>
<div class="grid">
{% for label,n in stats %}<div class="block stat"><b>{{n}}</b><span>{{label}}</span></div>{% endfor %}</div>
<div class="block" style="--c:var(--red)"><h2>Mails du jour</h2><form method="post" action="{{url_for('run_now')}}">
<button class="btn big" {{'disabled' if running}}>{{'⏳ En cours…' if running else '▶ Préparer les mails du jour'}}</button></form>
{% if running %}<div class="runner" aria-hidden="true"><i class="bot"></i></div>{% endif %}
<pre>{{log}}</pre></div>
<div class="block" style="--c:var(--green)"><h2>Mode collecte</h2><p class="mut">Teste un grand nombre d'entreprises pour remplir le stock d'adresses. Les envois restent limités à {{limit}} par jour. Ça peut durer des heures : laissez le téléphone branché.</p>
<div class="row">{% if running %}<form method="post" action="{{url_for('stop_job')}}"><button class="ko">■ Arrêter</button></form>
{% else %}<form method="post" action="{{url_for('collect_now')}}"><button class="ok">★ Lancer la collecte</button></form>{% endif %}</div></div>
{% if running %}<script>setTimeout(function(){location.reload()},15000)</script>{% endif %}
<div class="block"><h2>Mode d'envoi</h2><form method="post" action="{{url_for('set_mode')}}"><label class="mut" for="mode">En mode Review, aucun mail ne part sans votre bouton Envoyer.</label>
<select name="mode" id="mode" onchange="this.form.submit()" style="margin-top:8px">
{% for k,l in modes %}<option value="{{k}}" {{'selected' if k==mode}}>{{l}}</option>{% endfor %}</select></form></div>
<div class="block" style="--c:var(--red)"><form method="post" action="{{url_for('stop')}}"><h2>Désinscription</h2><label class="mut" for="stopmail">Quelqu'un a répondu STOP :</label>
<input type="email" name="email" id="stopmail" placeholder="email@entreprise.fr" required style="margin-top:8px"><div class="row"><button class="ko">Ne plus contacter</button></div></form></div>"""

SITE = "{{ {'none':'pas de site','outdated':'site à refaire'}.get(c.site_status,c.site_status) }}"

DRAFT = """{% if sending or send_log %}<div class="block" style="--c:var(--green)"><h2>Envoi groupé</h2>
<p class="log">{{send_log}}</p>{% if sending %}<div class="runner" aria-hidden="true"><i class="bot"></i></div>
<form method="post" action="{{url_for('stop_send')}}"><div class="row"><button class="ko">■ Arrêter l'envoi</button></div></form>
<script>setTimeout(function(){location.reload()},8000)</script>{% endif %}</div>{% endif %}
{% if rows and not sending %}<div class="block" style="--c:var(--green)"><h2>{{rows|length}} mails prêts</h2>
<p class="mut">Envoie les {{rows|length}} mails, avec vos modifications à l'écran, espacés de quelques secondes.</p>
<form method="post" action="{{url_for('send_all')}}" id="sendall"><div class="row"><button class="btn big ok" data-confirm="Appuyez encore pour confirmer l'envoi de {{rows|length}} mail(s)">✉ Tout envoyer ({{rows|length}})</button></div></form></div>{% endif %}
<script>
/* Confirmation dans la page (les fenêtres de confirmation sont parfois bloquées par le navigateur) :
   1er appui -> le bouton demande confirmation, 2e appui -> envoi. */
document.addEventListener("click",function(e){var b=e.target.closest("button[data-confirm]");if(!b)return;
if(b.dataset.armed!=="1"){e.preventDefault();b.dataset.armed="1";b.dataset.label=b.textContent;b.textContent=b.dataset.confirm;b.classList.add("armed");
setTimeout(function(){if(b.dataset.armed==="1"){b.dataset.armed="";b.textContent=b.dataset.label;b.classList.remove("armed")}},6000)}});
var sa=document.getElementById("sendall");if(sa)sa.addEventListener("submit",function(){var f=this;
document.querySelectorAll("form[data-siren]").forEach(function(d){["subject","body"].forEach(function(k){
var i=document.createElement("input");i.type="hidden";i.name=k+"_"+d.dataset.siren;i.value=d.elements[k].value;f.appendChild(i)})})});
</script>
{% for c in rows %}<div class="block"><h2>{{c.enseigne or c.nom}}</h2>
<span class="tag">{{c.commune}}</span><span class="tag">{{c.metier}}</span><span class="tag {{'hot' if c.site_status=='none' else 'warm'}}">""" + SITE + """</span>
<div class="mut" style="margin-top:6px">{{c.email}}{% if c.site_url %} · <a href="{{c.site_url}}" target="_blank" rel="noopener">voir le site</a>{% endif %}</div>
<form method="post" action="{{url_for('draft_action',siren=c.siren)}}" data-siren="{{c.siren}}"><input name="subject" aria-label="Objet" value="{{c.subject}}" style="margin-top:10px">
<textarea name="body" aria-label="Message">{{c.body}}</textarea>
<p class="mut" style="margin:10px 0 4px">Ajouté automatiquement en bas du mail :</p><pre class="sig">{{sig(c.email_source)}}</pre><div class="row">
<button name="act" value="send" class="ok" data-confirm="Confirmer l'envoi à {{c.email}}">✉ Envoyer</button>
<button name="act" value="save" class="btn gh">Enregistrer</button><button name="act" value="skip" class="ko">Ignorer</button></div></form></div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Aucun mail en attente. Passez par « À rédiger », ou lancez « Préparer les mails du jour » depuis l'accueil.</span></div>{% endfor %}"""

WRITE = """{% if auto %}<div class="block"><h2>Rédaction automatique</h2><p class="mut">Claude écrit chaque mail via la clé API quand vous appuyez sur « Préparer les mails du jour ».</p></div>
{% else %}<div class="block"><h2>{{n}} entreprises prêtes</h2>
<p class="mut">1. Copiez la demande.<br>2. Collez-la dans une conversation avec Claude (claude.ai).<br>3. Collez sa réponse ci-dessous.</p>
{% if batch %}<div class="row"><button class="btn" id="copy" type="button">⧉ Copier la demande ({{batch|length}} entreprises)</button></div>
<textarea id="prompt" readonly hidden>{{prompt}}</textarea><p class="mut" id="copied" hidden>Copié. Collez-la maintenant dans Claude.</p>{% endif %}</div>
<form class="block" style="--c:var(--green)" method="post" action="{{url_for('import_mails')}}"><h2>Réponse de Claude</h2>
<textarea name="text" aria-label="Réponse de Claude" placeholder="Collez ici le tableau JSON écrit par Claude" required></textarea>
<div class="row"><button class="ok">⬇ Importer les mails</button></div></form>
<script>document.getElementById("copy")&&document.getElementById("copy").addEventListener("click",function(){var t=document.getElementById("prompt");
function done(){document.getElementById("copied").hidden=false}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t.value).then(done,function(){t.hidden=false;t.select()})}else{t.hidden=false;t.select();document.execCommand("copy");done()}});</script>{% endif %}"""

SENT = """<form class="block" style="--c:var(--blue)" method="post" action="{{url_for('check_inbox')}}"><h2>Réponses</h2>
<p class="mut">Lit votre boîte Gmail (sans rien modifier) : réponses, demandes STOP et adresses en erreur sont reconnues toutes seules.</p>
<div class="row"><button class="btn">📬 Vérifier les réponses</button></div></form>
{% for c in rows %}<div class="block" style="--c:var({{ {'replied':'--green','refused':'--red','bounced':'--red'}.get(c.status,'--blue') }})"><h2>{{c.enseigne or c.nom}}</h2>
<span class="tag {{ {'replied':'good','refused':'hot','bounced':'hot','followed_up':'warm'}.get(c.status,'') }}">{{ {'sent':'envoyé','followed_up':'relancé','replied':'a répondu','refused':'STOP / refus','bounced':'adresse en erreur'}.get(c.status,c.status) }}</span>
<div class="mut" style="margin-top:6px">{{c.email}} · envoyé le {{c.contacted_at|frdate}}{% if c.reply_at %} · réponse le {{c.reply_at|frdate}}{% endif %}</div>
{% if c.reply_snippet %}<pre class="sig" style="margin-top:10px;padding-top:12px">« {{c.reply_snippet}} »</pre>{% endif %}
{% if c.status in ('sent','followed_up') %}<form method="post" action="{{url_for('mark',siren=c.siren)}}"><div class="row">
<button name="s" value="replied" class="ok">★ A répondu</button><button name="s" value="refused" class="ko">Refus</button></div></form>{% endif %}</div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Rien d'envoyé pour l'instant.</span></div>{% endfor %}"""

FOLLOW = """<div class="block" style="--c:var(--yellow)"><h2>{{rows|length}} à relancer</h2>
<p class="mut">Sans réponse depuis {{days}} jours. Une seule relance par entreprise, dans le même fil que votre premier mail. Le texte est modifiable.</p>
{% if rows %}<div class="row"><button class="btn" id="copyf" type="button">⧉ Faire écrire les relances par Claude</button></div>
<textarea id="fprompt" readonly hidden>{{prompt}}</textarea><p class="mut" id="fcopied" hidden>Copié. Collez-la dans Claude, puis sa réponse ci-dessous.</p>
<form method="post" action="{{url_for('import_followups')}}"><textarea name="text" aria-label="Réponse de Claude" placeholder="Réponse de Claude (facultatif) : collez ici le tableau JSON" style="min-height:90px"></textarea>
<div class="row"><button class="ok">⬇ Importer les relances</button></div></form>{% endif %}
</div>
<script>var cf=document.getElementById("copyf");if(cf)cf.addEventListener("click",function(){var t=document.getElementById("fprompt");
function done(){document.getElementById("fcopied").hidden=false}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t.value).then(done,function(){t.hidden=false;t.select()})}else{t.hidden=false;t.select();document.execCommand("copy");done()}});
document.addEventListener("click",function(e){var b=e.target.closest("button[data-confirm]");if(!b)return;
if(b.dataset.armed!=="1"){e.preventDefault();b.dataset.armed="1";b.dataset.label=b.textContent;b.textContent=b.dataset.confirm;b.classList.add("armed");
setTimeout(function(){if(b.dataset.armed==="1"){b.dataset.armed="";b.textContent=b.dataset.label;b.classList.remove("armed")}},6000)}});</script>
{% for c in rows %}<div class="block"><h2>{{c.enseigne or c.nom}}</h2><span class="tag">{{c.commune}}</span><span class="tag warm">premier mail le {{c.contacted_at|frdate}}</span>
<div class="mut" style="margin-top:6px">{{c.email}}</div>
<form method="post" action="{{url_for('followup_action',siren=c.siren)}}"><input name="subject" aria-label="Objet" value="{{c.f_subject}}" style="margin-top:10px">
<textarea name="body" aria-label="Message" style="min-height:170px">{{c.f_body}}</textarea>
<p class="mut" style="margin:10px 0 4px">Ajouté automatiquement en bas du mail :</p><pre class="sig">{{sig(c.email_source)}}</pre>
<div class="row"><button name="act" value="send" class="ok" data-confirm="Confirmer la relance à {{c.email}}">✉ Relancer</button>
<button name="act" value="save" class="btn gh">Enregistrer</button><button name="act" value="skip" class="ko">Ne pas relancer</button></div></form></div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Aucune relance à faire. Les mails sans réponse après {{days}} jours apparaîtront ici.</span></div>{% endfor %}"""

PIPE = """<div class="block" style="--c:var(--green)"><h2>Suivi des prospects</h2>
<p class="mut">Les entreprises qui ont répondu, de la première réponse jusqu'au client. Ajoutez une note et une date de rappel.</p></div>
{% for c in rows %}<div class="block" style="--c:var({{ {'client':'--green','lost':'--red','meeting':'--yellow','mockup':'--blue'}.get(c.stage_key,'--red') }})">
<h2>{{c.enseigne or c.nom}}</h2><span class="tag {{ {'client':'good','lost':'hot','meeting':'warm'}.get(c.stage_key,'') }}">{{stage_names[c.stage_key]}}</span>
<span class="tag">{{c.commune}}</span>{% if c.due %}<span class="tag hot">Rappel : {{c.reminder|frshort}}</span>{% elif c.reminder %}<span class="tag warm">Rappel le {{c.reminder|frshort}}</span>{% endif %}
<div class="mut" style="margin-top:6px"><a href="mailto:{{c.email}}">{{c.email}}</a></div>
{% if c.reply_snippet %}<pre class="sig" style="margin-top:10px;padding-top:12px">« {{c.reply_snippet}} »</pre>{% endif %}
<form method="post" action="{{url_for('pipeline_action',siren=c.siren)}}">
<textarea name="notes" aria-label="Notes" placeholder="Notes (ce qui a été dit, ce qu'il faut faire…)" style="min-height:90px">{{c.notes or ''}}</textarea>
<label class="mut" for="r{{c.siren}}" style="display:block;margin-top:10px">Me le rappeler le :</label>
<input type="date" id="r{{c.siren}}" name="reminder" value="{{c.reminder or ''}}" style="margin-top:4px">
<div class="row"><button name="stage" value="mockup" class="btn">Maquette envoyée</button><button name="stage" value="meeting" class="btn">Rendez-vous</button>
<button name="stage" value="client" class="ok">★ Client</button><button name="stage" value="lost" class="ko">Perdu</button><button name="stage" value="keep" class="btn gh">Enregistrer</button></div></form></div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Personne à suivre pour l'instant. Les réponses apparaissent ici dès que quelqu'un répond.</span></div>{% endfor %}"""

STATS = """<div class="grid">
{% for label,n,c in tiles %}<div class="block stat" style="--c:var({{c}})"><b>{{n}}</b><span>{{label}}</span></div>{% endfor %}</div>
{% if not data.total.sent %}<div class="block idle"><i class="bot"></i><span class="mut">Pas encore de statistiques : elles apparaissent après vos premiers envois.</span></div>{% endif %}
{% for title, lines in data.groups if lines %}<div class="block" style="--c:var(--blue)"><h2>{{title}}</h2>
{% for l in lines %}<div style="margin:10px 0 0"><div style="display:flex;justify-content:space-between;gap:10px;font:700 14px/1.3 var(--display)"><span>{{l.label}}{% if l.sent < 5 %} <span class="tag" style="margin:0 0 0 4px;padding:3px 7px">peu de données</span>{% endif %}</span>
<span class="mut" style="white-space:nowrap">{{l.replied}}/{{l.sent}} · {{l.rate}} %</span></div>
<div style="height:14px;border-radius:999px;background:var(--soft);box-shadow:inset 0 0 0 2px #c9d3f0;margin-top:5px;overflow:hidden"><i style="display:block;height:100%;width:{{[l.rate,3]|max}}%;border-radius:999px;background:var(--green)"></i></div></div>{% endfor %}</div>{% endfor %}
<p class="mut" style="text-align:center">Taux de réponse = réponses / mails reçus. Les adresses en erreur ne comptent pas.</p>"""

TABS = [("home", "Accueil"), ("write", "À rédiger"), ("drafts", "À valider"), ("followups", "À relancer"),
        ("sent", "Envoyés"), ("pipeline", "Suivi"), ("stats", "Stats")]
MODES = [("review", "Review (je valide ici)"), ("draft", "Brouillons Gmail"), ("send", "Envoi direct")]
MODE_SHORT = {"review": "Review", "draft": "Gmail", "send": "Auto"}


def hud_counts(con):
    counts = {r["status"]: r["n"] for r in con.execute("SELECT status, COUNT(*) n FROM companies GROUP BY status")}
    return {"sent": counts.get("sent", 0) + counts.get("followed_up", 0) + counts.get("replied", 0) + counts.get("refused", 0),
            "replied": counts.get("replied", 0), "drafted": counts.get("drafted", 0)}


def page(body, tab="home", con=None):
    mode = db.send_mode(con) if con else ""
    hud = hud_counts(con) if con else None
    counts = {}
    if con:
        counts = {"write": len(cli.next_to_write(con)), "drafts": hud["drafted"], "followups": len(due_followups(con)),
                  "pipeline": len(pipeline_todo(con))}
    return render_template_string(PAGE, css=CSS.replace("{{bot}}", BOT), body=body, tab=tab, tabs=TABS, hud=hud,
                                  mode_short=MODE_SHORT.get(mode, ""), counts=counts, msg=session.pop("msg", ""))


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
                   background_color="#ffffff", theme_color="#ffffff",
                   icons=[{"src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='18' fill='%23ff3b3b'/%3E%3Ccircle cx='32' cy='32' r='17' fill='%23ffc61a' stroke='%231d3d8f' stroke-width='5'/%3E%3Crect x='29' y='22' width='6' height='20' rx='3' fill='%23d99300'/%3E%3C/svg%3E",
                           "sizes": "any", "type": "image/svg+xml"}])


@app.route("/")
def index():
    tab = request.args.get("tab", "home")
    con = connect()
    if tab == "drafts":
        rows = con.execute("SELECT * FROM companies WHERE status='drafted' ORDER BY contacted_at").fetchall()
        body = render_template_string(DRAFT, rows=rows, sig=mailer.signature, sending=_send["running"], send_log=_send["log"])
    elif tab == "write":
        batch = cli.next_to_write(con)[: int(config.env("DAILY_LIMIT", "10"))]
        body = render_template_string(
            WRITE, auto=bool(config.env("ANTHROPIC_API_KEY")), n=len(cli.next_to_write(con)), batch=batch,
            prompt=mailer.batch_prompt([dict(r) for r in batch]) if batch else "")
    elif tab == "followups":
        rows = []
        for r in due_followups(con):
            c = dict(r)
            c["f_subject"], c["f_body"] = (r["followup_subject"], r["followup_body"]) if r["followup_body"] else mailer.followup_mail(c)
            rows.append(c)
        body = render_template_string(
            FOLLOW, rows=rows, sig=mailer.signature, days=config.env("FOLLOWUP_DAYS", "7"),
            prompt=mailer.batch_followup_prompt([dict(r) for r in rows[:10]]) if rows else "")
    elif tab == "pipeline":
        body = render_template_string(PIPE, rows=pipeline_rows(con), stage_names=STAGES)
    elif tab == "stats":
        data = statsmod.compute(con)
        t = data["total"]
        tiles = [("mails reçus", t["sent"], "--blue"), ("réponses", t["replied"], "--green"), ("taux de réponse", f"{t['rate']} %", "--yellow"),
                 ("demandes STOP", t["stop"], "--red"), ("adresses en erreur", t["bounced"], "--red"),
                 ("clients", con.execute("SELECT COUNT(*) FROM companies WHERE stage='client'").fetchone()[0], "--green")]
        body = render_template_string(STATS, data=data, tiles=tiles)
    elif tab == "sent":
        rows = con.execute(
            "SELECT * FROM companies WHERE status IN ('sent','followed_up','replied','bounced') "
            "OR (status='refused' AND contacted_at IS NOT NULL) "
            "ORDER BY (status='replied' AND reply_at IS NOT NULL) DESC, COALESCE(reply_at, contacted_at) DESC LIMIT 150").fetchall()
        body = render_template_string(SENT, rows=rows)
    else:
        tab = "home"
        counts = {r["status"]: r["n"] for r in con.execute("SELECT status, COUNT(*) n FROM companies GROUP BY status")}
        stats = [("entreprises en base", sum(counts.values())), ("adresses en stock", len(cli.next_to_write(con))),
                 ("à valider", counts.get("drafted", 0)), ("envoyés", counts.get("sent", 0) + counts.get("followed_up", 0)),
                 ("réponses", counts.get("replied", 0)), ("refus", counts.get("refused", 0))]
        body = render_template_string(HOME, stats=stats, modes=MODES, mode=db.send_mode(con), running=_job["running"], log=_job["log"], limit=cli.target(), today=sent_today(con))
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
            try:
                cli.send_now(con, row, subject, body)
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
                session["msg"] = f"Relance envoyée à {row['enseigne'] or row['nom']}."
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
    if stage in STAGES and stage != "replied":
        con.execute("UPDATE companies SET stage=? WHERE siren=?", (stage, siren))
        if stage in ("client", "lost"):
            con.execute("UPDATE companies SET reminder=NULL WHERE siren=?", (siren,))
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


if __name__ == "__main__":
    start_inbox_poll()
    app.run(host="0.0.0.0", port=int(config.env("PORT", "8000")))
