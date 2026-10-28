"""Interface du dashboard : styles, icônes, gabarits et scripts (aucune logique métier ici)."""
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

# Icônes au trait (24 px, couleur du texte)
_PATHS = {
    "home": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v10h13V10"/><path d="M10 20v-5h4v5"/>',
    "write": '<path d="M4 20h4.5L19.5 9 15 4.5 4 15.5z"/><path d="m13.5 6 4.5 4.5"/>',
    "send": '<rect x="3" y="5" width="18" height="14" rx="3.5"/><path d="m3.5 7.5 8.5 6 8.5-6"/>',
    "followup": '<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20.5 4v5h-5"/>',
    "more": '<circle cx="5" cy="12" r="1.6" fill="currentColor"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/><circle cx="19" cy="12" r="1.6" fill="currentColor"/>',
    "sent": '<path d="M3 13.5h5l1.5 3h5l1.5-3h5"/><path d="M5.5 5h13L21 13.5V19H3v-5.5z"/>',
    "pipeline": '<path d="M5 21V4h12l-2.5 4.5L17 13H5"/>',
    "stats": '<path d="M5 20v-8M11 20V5M17 20v-5"/><path d="M3 20h18"/>',
    "save": '<path d="M5 4h11.5L20 7.5V20H5z"/><path d="M8.5 4v5h7V4M8.5 20v-6h8v6"/>',
    "skip": '<path d="m6.5 6.5 11 11M17.5 6.5l-11 11"/>',
    "chevron": '<path d="m7 10 5 5 5-5"/>',
}


def icon(name, size=24):
    return (f'<svg class="i" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_PATHS[name]}</svg>')


# Navigation : 4 onglets principaux dans la barre du bas, le reste dans « Plus »
MAIN_TABS = [("home", "Accueil", "home"), ("write", "Rédiger", "write"), ("drafts", "Valider", "send"), ("followups", "Relancer", "followup")]
MORE_TABS = [("sent", "Envoyés", "sent", "Mails partis et réponses reçues"),
             ("pipeline", "Suivi", "pipeline", "Prospects qui ont répondu, jusqu'au client"),
             ("stats", "Stats", "stats", "Ce qui donne le plus de réponses")]

CSS = r"""
/* Monde de jeu lumineux : fond blanc à pois, formes bombées, 4 couleurs franches.
   Colonne unique de 560 px, en-tête compact collant en haut, barre d'onglets fixe en bas. */
:root{--bg:#ffffff;--dot:#eef3ff;--ink:#1d2a5c;--mut:#5d6894;--line:#1d3d8f;
--red:#ff3b3b;--red2:#c81e2b;--blue:#2f7bff;--blue2:#1b4fc4;--yellow:#ffc61a;--yellow2:#d99300;--green:#2ec95c;--green2:#16913b;
--sky:#e6f2ff;--card:#ffffff;--soft:#f4f7ff;--tabh:74px;
--display:"Fredoka","Baloo 2",ui-rounded,system-ui,sans-serif;--body:"Nunito",ui-rounded,system-ui,sans-serif;color-scheme:light}
*{box-sizing:border-box}
html{min-height:100%;background-color:var(--bg);background-image:radial-gradient(var(--dot) 18%,transparent 20%),radial-gradient(var(--dot) 18%,transparent 20%);
background-size:34px 34px;background-position:0 0,17px 17px}
body{margin:0;min-height:100vh;color:var(--ink);font:16px/1.5 var(--body);-webkit-tap-highlight-color:transparent;
padding:0 max(16px,env(safe-area-inset-right,0px)) calc(var(--tabh) + 24px + env(safe-area-inset-bottom,0px)) max(16px,env(safe-area-inset-left,0px))}
body.guest{padding-bottom:24px}
.wrap{max-width:560px;margin:0 auto;position:relative;z-index:1}
.cloud{position:fixed;z-index:0;top:110px;left:0;width:90px;height:30px;border-radius:30px;background:#fff;pointer-events:none;box-shadow:0 0 0 3px #d6e6ff;animation:drift 70s linear infinite;will-change:transform}
.cloud::before,.cloud::after{content:"";position:absolute;background:#fff;border-radius:50%;box-shadow:0 -3px 0 0 #d6e6ff}
.cloud::before{width:40px;height:40px;left:12px;top:-20px}.cloud::after{width:30px;height:30px;left:44px;top:-14px}
.cloud.c2{top:52%;animation-duration:95s;animation-delay:-40s}
@keyframes drift{from{transform:translateX(-130px)}to{transform:translateX(110vw)}}

/* En-tête collant, qui se réduit au défilement */
.top{position:fixed;top:0;left:0;right:0;z-index:20;margin:0;will-change:transform;padding:calc(10px + env(safe-area-inset-top,0px)) max(16px,env(safe-area-inset-right,0px)) 10px max(16px,env(safe-area-inset-left,0px));
background:#fff;transition:transform .28s cubic-bezier(.2,.8,.2,1),box-shadow .28s}
.wrap{padding-top:var(--toph,96px)}
.top .in,.top h1,.top .hud,.top h1 small,.chip .t{transition:transform .28s cubic-bezier(.2,.8,.2,1),opacity .2s}
.top .in{max-width:560px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:10px}
.top.mini{transform:translateY(calc(-1 * var(--shift,26px)));box-shadow:0 3px 0 #d6e2ff}
.top.mini .in{transform:translateY(calc(var(--shift,26px) * .5))}
.top.mini h1{transform:scale(.78);transform-origin:left center}.top.mini h1 small{opacity:0}
.top.mini .hud{transform:scale(.8);transform-origin:right center}.top.mini .chip .t,.top.mini .chip .lbl{opacity:0}
.chip b,.chip .lbl{transition:transform .28s cubic-bezier(.2,.8,.2,1),opacity .2s}.top.mini .chip b{transform:translateY(-8px) scale(1.15)}
h1{font:700 27px/1 var(--display);min-width:0;margin:0;letter-spacing:.5px;display:flex;gap:1px;flex-wrap:wrap;align-items:baseline}
h1 .word{display:flex;gap:1px;flex-wrap:nowrap;white-space:nowrap}
h1 .word>span{display:inline-block;-webkit-text-stroke:2px var(--line);paint-order:stroke fill;text-shadow:0 3px 0 var(--line);animation:wave 3.2s ease-in-out 2}
h1 .l0{color:var(--red)}h1 .l1{color:var(--blue)}h1 .l2{color:var(--yellow)}h1 .l3{color:var(--green)}h1 .sp{width:8px}
@keyframes wave{0%,85%,100%{transform:translateY(0)}92%{transform:translateY(-5px)}}
h1 small{display:block;width:100%;font:700 11px/1 var(--display);color:var(--blue);letter-spacing:3px;margin-top:7px;-webkit-text-stroke:0;text-shadow:none;animation:none}
.hud{display:flex;gap:7px;flex:none}
.chip{display:flex;flex-direction:column;align-items:center;min-width:56px;padding:5px 9px 6px;border-radius:15px;background:#fff;box-shadow:0 0 0 2.5px var(--line),0 3px 0 2.5px var(--line);
font:700 9.5px/1 var(--display);color:var(--mut);letter-spacing:.4px;text-transform:uppercase}
.chip b{font:700 17px/1.15 var(--display);color:var(--ink);margin-top:2px;font-variant-numeric:tabular-nums;text-transform:none;letter-spacing:0}
.chip.r b{color:var(--red)}.chip .lbl{display:flex;gap:4px;align-items:center}
.bump{animation:bump .6s cubic-bezier(.3,1.8,.5,1)}
@keyframes bump{0%{transform:scale(1)}40%{transform:scale(1.35)}100%{transform:scale(1)}}
.coin{display:inline-block;width:15px;height:15px;border-radius:50%;flex:none;background:radial-gradient(circle at 38% 32%,#fff6c2 0 16%,var(--yellow) 18% 58%,var(--yellow2) 60%);
box-shadow:0 0 0 2px var(--line);animation:spin 1.8s ease-in-out infinite}
@keyframes spin{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.15)}}

/* Blocs */
.block{background:var(--card);border-radius:24px;padding:18px;margin:0 0 18px;position:relative;box-shadow:0 0 0 3px var(--line),0 7px 0 3px var(--line)}
.block h2{font:700 19px/1.2 var(--display);margin:0 0 10px;color:var(--ink);display:flex;align-items:center;gap:10px;text-wrap:balance}
.block h2::before{content:"";width:14px;height:14px;border-radius:50%;background:var(--c,var(--blue));box-shadow:0 0 0 3px var(--line);flex:none}
.wrap>.block:first-child,.wrap>form:first-child,.wrap>.swipe:first-child{margin-top:8px}
.mut{color:var(--mut);font-size:15px}p{margin:0 0 6px}
.tag{display:inline-block;font:700 13px/1 var(--display);padding:6px 11px;border-radius:999px;background:var(--sky);color:var(--blue2);margin:2px 6px 2px 0;box-shadow:inset 0 0 0 2px #c9dcff}
.tag.good{background:#dcf8e4;color:var(--green2);box-shadow:inset 0 0 0 2px #a8ebbb}.tag.hot{background:#ffe4e4;color:var(--red2);box-shadow:inset 0 0 0 2px #ffc2c2}.tag.warm{background:#fff3cc;color:#8a5d00;box-shadow:inset 0 0 0 2px #ffe08a}
input,textarea,select{width:100%;min-width:0;padding:12px 14px;border:0;border-radius:16px;background:var(--soft);color:var(--ink);font:16px/1.5 var(--body);box-shadow:inset 0 0 0 2.5px #c9d3f0}
input:focus,textarea:focus,select:focus{outline:none;box-shadow:inset 0 0 0 3px var(--blue),0 0 0 4px #2f7bff33}
textarea{min-height:220px;margin-top:10px;resize:vertical}
.row{display:flex;gap:12px;flex-wrap:wrap;margin-top:14px;align-items:center}
.actions{display:flex;gap:12px;margin-top:14px;align-items:center}.actions .grow{flex:1;min-width:0}
a{color:var(--blue2);font-weight:700}
pre{white-space:pre-wrap;font:700 14px/1.5 var(--display);margin:12px 0 0;color:var(--blue2)}
pre.sig{font:600 14px/1.45 var(--body);color:var(--mut);background:var(--soft);border-radius:16px;padding:12px 14px;margin:0}
.quote{font:600 15px/1.45 var(--body);color:var(--ink);background:var(--soft);border-radius:16px;padding:11px 14px;margin:10px 0 0;border-left:5px solid var(--green)}
.log{white-space:pre-wrap;font:700 15px/1.5 var(--display);color:var(--blue2);margin:12px 0 0}

/* Boutons */
button,.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;font:700 16px/1.1 var(--display);padding:13px 20px 14px;border:0;border-radius:999px;cursor:pointer;color:#fff;text-decoration:none;
background:var(--blue);box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--blue2),inset 0 3px 0 #fff5;transition:transform .1s,box-shadow .1s}
button:active,.btn:active{transform:translateY(4px);box-shadow:0 0 0 3px var(--line),0 1px 0 3px var(--blue2)}
button:focus-visible,.btn:focus-visible,.tabbar a:focus-visible,.tabbar button:focus-visible,summary:focus-visible{outline:3px solid var(--yellow);outline-offset:4px}
button[disabled]{opacity:.7;cursor:wait}
.ok{background:var(--green);box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--green2),inset 0 3px 0 #fff5}
.ok:active{box-shadow:0 0 0 3px var(--line),0 1px 0 3px var(--green2)}
.ko{background:var(--red);box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--red2),inset 0 3px 0 #fff5}
.ko:active{box-shadow:0 0 0 3px var(--line),0 1px 0 3px var(--red2)}
.gh{background:#fff;color:var(--ink);box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--line)}
.big{font-size:18px;padding:17px 20px 18px;width:100%;background:var(--yellow);color:var(--ink);box-shadow:0 0 0 3px var(--line),0 6px 0 3px var(--yellow2),inset 0 4px 0 #fff8}
.big.ok{background:var(--green);color:#fff;box-shadow:0 0 0 3px var(--line),0 6px 0 3px var(--green2),inset 0 4px 0 #fff6}
.ib{width:50px;height:50px;padding:0;flex:none}
.ib.gh{color:var(--ink)}.ib.ko{color:#fff}
.small{font-size:14px;padding:9px 14px 10px}
.link{background:none;box-shadow:none;color:var(--mut);padding:8px 4px;font-size:14px;text-decoration:underline}
.link:active{transform:none;box-shadow:none}
button.armed{background:var(--yellow)!important;color:var(--ink)!important;box-shadow:0 0 0 3px var(--line),0 5px 0 3px var(--yellow2)!important}

/* Accueil */
.hero{background:linear-gradient(180deg,var(--sky),#fff 75%)}
.stripe{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0 0 18px}
.mini-stat{background:#fff;border-radius:18px;padding:10px 8px 9px;text-align:center;box-shadow:0 0 0 2.5px var(--line),0 4px 0 2.5px var(--line)}
a.mini-stat{display:block;text-decoration:none;transition:transform .12s}a.mini-stat:active{transform:translateY(3px)}a.mini-stat:focus-visible{outline:3px solid var(--c);outline-offset:2px}
.mini-stat b{display:block;font:700 22px/1.1 var(--display);color:var(--c);font-variant-numeric:tabular-nums}
.mini-stat span{display:block;font:700 12px/1.2 var(--display);color:var(--mut);margin-top:3px}
.quest .bar{display:grid;grid-template-columns:repeat(var(--n),1fr);gap:5px;margin-top:10px;padding:5px;border-radius:999px;background:#fff;box-shadow:inset 0 0 0 3px var(--line)}
.quest .bar i{height:16px;border-radius:999px;background:var(--soft)}
.quest .bar i.on{background:radial-gradient(circle at 35% 30%,#fff6c2 0 14%,var(--yellow) 16% 60%,var(--yellow2));box-shadow:inset 0 -3px 0 #0002;animation:pop .55s cubic-bezier(.3,1.8,.5,1) both}
@keyframes pop{0%{transform:scale(.2)}100%{transform:none}}
.quest p{margin:0;font:700 15px/1.4 var(--display);color:var(--mut)}.quest p b{color:var(--ink);font-size:22px}

/* Blocs repliables */
details>summary{list-style:none;cursor:pointer}details>summary::-webkit-details-marker{display:none}
.fold>summary{display:flex;align-items:center;justify-content:space-between;gap:10px;font:700 17px/1.2 var(--display)}
.fold>summary .i{transition:transform .2s;color:var(--mut)}.fold[open]>summary .i{transform:rotate(180deg)}
.fold[open]>summary{margin-bottom:12px}

/* Cartes de mail : repliées, s'ouvrent d'un tap, se balaient */
.swipe{position:relative;margin:0 0 18px;touch-action:pan-y}
.swipe-bg{position:absolute;inset:0;border-radius:24px;display:flex;align-items:center;justify-content:space-between;padding:0 22px;font:700 17px/1 var(--display);color:#fff;opacity:0;transition:opacity .15s}
.swipe-bg .go{color:var(--green2)}.swipe-bg .no{color:var(--red2)}
.swipe.r .swipe-bg{opacity:1;background:#dcf8e4}.swipe.l .swipe-bg{opacity:1;background:#ffe4e4}
.swipe.r .no,.swipe.l .go{visibility:hidden}
.swipe>.card{margin:0;transition:transform .25s cubic-bezier(.2,.9,.3,1.2)}
.swipe.drag>.card{transition:none}
.swipe.gone>.card{transition:transform .3s ease-in,opacity .3s;opacity:0}
.card>summary{display:block}
.card .head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}
.card .head h2{margin:0 0 8px}
.card .head .i{color:var(--mut);margin-top:2px;flex:none;transition:transform .2s}.card[open] .head .i{transform:rotate(180deg)}
.card .subj{font:700 15.5px/1.35 var(--display);margin:8px 0 2px}
.card .prev{color:var(--mut);font-size:14.5px;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card[open] .prev,.card[open] .subj{display:none}
.card form{margin-top:12px}
.lots{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}.lots .lot{flex:1 1 130px}
.more{text-align:center;margin:-4px 0 18px}
.hint{font:700 13px/1.35 var(--display);color:var(--mut);text-align:center;margin:-6px 0 14px}

/* Suivi : frise des étapes */
.stepper{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;margin:14px 0 4px;position:relative}
.stepper::before{content:"";position:absolute;left:12%;right:12%;top:17px;height:5px;border-radius:5px;background:#d6dcf0}
.step{flex-direction:column;gap:5px;background:none;box-shadow:none;color:var(--mut);padding:0;font:700 12.5px/1.15 var(--display);position:relative;z-index:1}
.step:active{transform:none;box-shadow:none}
.step .dot{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:#fff;box-shadow:0 0 0 3px #c9d3f0;color:var(--mut);font-size:15px}
.step.done .dot{background:var(--green);box-shadow:0 0 0 3px var(--line);color:#fff}
.step.cur .dot{background:var(--yellow);box-shadow:0 0 0 3px var(--line),0 0 0 7px #ffc61a55;color:var(--ink)}
.step.done,.step.cur{color:var(--ink)}
.lost .step .dot{background:#fff;box-shadow:0 0 0 3px #c9d3f0;color:var(--mut)}

/* Stats */
.best{background:linear-gradient(180deg,#e3fbea,#fff 80%)}
.best ul{list-style:none;margin:6px 0 0;padding:0;display:grid;gap:8px}
.best li{display:flex;justify-content:space-between;gap:10px;align-items:baseline;font:700 15px/1.3 var(--display)}
.best li .k{color:var(--mut);font-size:13px;display:block}.best li .v{color:var(--green2);font-size:20px;white-space:nowrap}
.bars{margin:12px 0 0}.bars .l{display:flex;justify-content:space-between;gap:10px;font:700 14px/1.3 var(--display)}
.bars .t{height:14px;border-radius:999px;background:var(--soft);box-shadow:inset 0 0 0 2px #c9d3f0;margin-top:5px;overflow:hidden}
.bars .t i{display:block;height:100%;border-radius:999px;background:var(--green)}
.few{margin:0 0 0 6px!important;padding:3px 7px!important;font-size:11.5px!important}

/* Bati */
.bot{display:inline-block;width:44px;height:52px;background:{{bot}} center/contain no-repeat;flex:none}
.runner{height:76px;position:relative;margin-top:14px;overflow:hidden;border-radius:18px;background:linear-gradient(180deg,var(--sky),#fff)}
.runner::after{content:"";position:absolute;left:0;right:0;bottom:0;height:16px;border-radius:16px 16px 0 0;background:var(--green);box-shadow:inset 0 3px 0 #ffffff66}
.runner .bot{position:absolute;left:0;bottom:12px;animation:run 6s linear infinite,hop .5s ease-in-out infinite}
@keyframes run{from{transform:translateX(-50px)}to{transform:translateX(560px)}}
@keyframes hop{0%,100%{margin-bottom:0}50%{margin-bottom:14px}}
.idle{display:flex;gap:14px;align-items:center}.idle .bot{animation:hop 2.4s ease-in-out infinite}
.ground{height:44px;margin:30px calc(-1 * max(16px,env(safe-area-inset-left,0px))) 0;position:relative;
background:radial-gradient(ellipse 130px 44px at 18% 100%,var(--green) 98%,transparent),radial-gradient(ellipse 170px 56px at 62% 100%,#5fdc85 98%,transparent),
radial-gradient(ellipse 120px 40px at 96% 100%,var(--green) 98%,transparent)}

/* Barre d'onglets fixe en bas */
.tabbar{position:fixed;left:0;right:0;bottom:0;z-index:30;display:flex;justify-content:center;
padding:8px max(10px,env(safe-area-inset-right,0px)) calc(8px + env(safe-area-inset-bottom,0px)) max(10px,env(safe-area-inset-left,0px));
background:#fff;box-shadow:0 -3px 0 var(--line)}
.tabbar .in{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:4px;width:100%;max-width:560px}
.tabbar a,.tabbar button{display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 2px 5px;border-radius:16px;background:none;box-shadow:none;
color:var(--mut);text-decoration:none;font:700 12px/1 var(--display);position:relative;min-height:56px;justify-content:center}
.tabbar a:active,.tabbar button:active{transform:scale(.94);box-shadow:none}
.tabbar .on{color:var(--red2);background:#ffe9e9}
.tabbar .on .i{transform:translateY(-1px)}
.tabbar .n{position:absolute;top:2px;left:calc(50% + 6px);min-width:20px;height:20px;padding:0 5px;border-radius:999px;background:var(--yellow);color:var(--ink);
font:700 11.5px/20px var(--display);box-shadow:0 0 0 2px var(--line);text-align:center}
.sheet{position:fixed;inset:0;z-index:40}
.sheet-back{position:absolute;inset:0;background:#1d2a5c66;animation:fade .2s}
.sheet-panel{position:absolute;left:0;right:0;bottom:0;margin:0 auto;max-width:560px;background:#fff;border-radius:26px 26px 0 0;box-shadow:0 -3px 0 3px var(--line);
padding:12px max(16px,env(safe-area-inset-right,0px)) calc(18px + env(safe-area-inset-bottom,0px)) max(16px,env(safe-area-inset-left,0px));animation:up .25s cubic-bezier(.2,.9,.3,1.1)}
.sheet-panel::before{content:"";display:block;width:44px;height:5px;border-radius:5px;background:#c9d3f0;margin:0 auto 12px}
.sheet a{display:flex;align-items:center;gap:14px;padding:12px 10px;border-radius:18px;text-decoration:none;color:var(--ink)}
.sheet a+a{margin-top:4px}.sheet a.on{background:#ffe9e9}
.sheet a .ic{width:46px;height:46px;border-radius:15px;display:grid;place-items:center;background:var(--sky);color:var(--blue2);box-shadow:0 0 0 2.5px var(--line);flex:none}
.sheet a b{display:block;font:700 17px/1.2 var(--display)}.sheet a span.d{display:block;font-size:13.5px;color:var(--mut)}
.sheet a .n{margin-left:auto;min-width:24px;padding:3px 7px;border-radius:999px;background:var(--yellow);font:700 13px/1.2 var(--display);text-align:center;box-shadow:0 0 0 2px var(--line)}
@keyframes up{from{transform:translateY(100%)}to{transform:none}}@keyframes fade{from{opacity:0}}

/* Notifications et effets */
.toast{position:fixed;left:50%;bottom:calc(var(--tabh) + 18px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:35;width:max-content;max-width:min(520px,calc(100% - 32px));
display:flex;gap:10px;align-items:center;background:var(--ink);color:#fff;font:700 15px/1.35 var(--display);padding:12px 18px;border-radius:20px;
box-shadow:0 0 0 3px #fff,0 6px 0 3px var(--line);animation:toastin .35s cubic-bezier(.2,.9,.3,1.3) both}
body.guest .toast{bottom:20px}
.toast.out{animation:toastout .3s ease-in both}
@keyframes toastin{from{transform:translate(-50%,30px);opacity:0}}@keyframes toastout{to{transform:translate(-50%,30px);opacity:0}}
.fx{position:fixed;inset:0;pointer-events:none;z-index:50;overflow:hidden}
.fx i{position:absolute;display:block}
.fx .c{width:22px;height:22px;border-radius:50%;background:radial-gradient(circle at 38% 32%,#fff6c2 0 16%,var(--yellow) 18% 58%,var(--yellow2) 60%);box-shadow:0 0 0 2.5px var(--line);
animation:coin 1.1s cubic-bezier(.2,.7,.4,1) both}
@keyframes coin{0%{transform:translate(0,0) scale(.3);opacity:0}15%{opacity:1}60%{transform:translate(var(--x),-170px) scale(1)}100%{transform:translate(var(--x),-120px) scale(.8);opacity:0}}
.fx .f{width:10px;height:16px;border-radius:3px;top:-20px;animation:fall var(--d) linear both}
@keyframes fall{to{transform:translate(var(--x),110vh) rotate(var(--r))}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}.fx{display:none}}
"""

PAGE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#ffffff">
<link rel="manifest" href="/manifest.json"><link rel="icon" href="/static/icon-192.png"><link rel="apple-touch-icon" href="/static/icon-192.png">
<title>Prospec Bat</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@400;600;700&display=swap">
<style>{{css|safe}}</style></head>
<body class="{{'' if session.get('ok') else 'guest'}}"><i class="cloud c1"></i><i class="cloud c2"></i>
<header class="top" id="top"><div class="in">
<h1><span class="word">{% for ch in "PROSPEC BAT" %}{% if ch == " " %}<span class="sp"></span>{% else %}<span class="l{{loop.index0 % 4}}" style="animation-delay:{{loop.index0*90}}ms">{{ch}}</span>{% endif %}{% endfor %}</span><small>MONDE 12 · AVEYRON</small></h1>
{% if session.get('ok') and hud %}<div class="hud"><span class="chip"><span class="t">Envoyés</span><b id="hud-sent">{{hud.sent}}</b></span>
<span class="chip r"><span class="lbl"><i class="coin"></i><span class="t">Réponses</span></span><b>{{hud.replied}}</b></span></div>{% endif %}
</div></header>
<main class="wrap">{{body|safe}}<div class="ground" aria-hidden="true"></div></main>
{% if msg %}<div class="toast" id="toast" role="status"><i class="coin"></i><span>{{msg}}</span></div>{% endif %}
{% if session.get('ok') %}
<nav class="tabbar" aria-label="Navigation"><div class="in">
{% for k,l,ic in main_tabs %}<a href="{{url_for('index',tab=k)}}" class="{{'on' if tab==k}}"{% if tab==k %} aria-current="page"{% endif %}>{{icon(ic)|safe}}{{l}}{% if counts.get(k) %}<span class="n">{{counts[k]}}</span>{% endif %}</a>{% endfor %}
<button type="button" id="morebtn" class="{{'on' if tab in more_keys}}" aria-haspopup="dialog" aria-expanded="false">{{icon('more')|safe}}Plus{% if more_count %}<span class="n">{{more_count}}</span>{% endif %}</button>
</div></nav>
<div class="sheet" id="sheet" hidden role="dialog" aria-label="Plus d'onglets"><div class="sheet-back" data-close></div><div class="sheet-panel">
{% for k,l,ic,d in more_tabs %}<a href="{{url_for('index',tab=k)}}" class="{{'on' if tab==k}}"><span class="ic">{{icon(ic)|safe}}</span><span><b>{{l}}</b><span class="d">{{d}}</span></span>{% if counts.get(k) %}<span class="n">{{counts[k]}}</span>{% endif %}</a>{% endfor %}
</div></div>{% endif %}
<div class="fx" id="fx" aria-hidden="true"></div>
<script>
(function(){
/* En-tête compact au défilement */
var top=document.getElementById("top"),mini=false,tick=false,root=document.documentElement;
function measure(){var was=top.classList.contains("mini");top.classList.remove("mini");var h=top.offsetHeight;if(was)top.classList.add("mini");
root.style.setProperty("--toph",h+"px");root.style.setProperty("--shift",Math.max(0,h-62)+"px")}
measure();window.addEventListener("resize",measure);if(document.fonts)document.fonts.ready.then(measure);
/* hystérésis : se réduit après 70 px, ne revient qu'en dessous de 20 px */
function onScroll(){if(tick)return;tick=true;requestAnimationFrame(function(){tick=false;var y=window.scrollY;
if(!mini&&y>70){mini=true;top.classList.add("mini")}else if(mini&&y<20){mini=false;top.classList.remove("mini")}})}
window.addEventListener("scroll",onScroll,{passive:true});onScroll();
/* Après une action (formulaire), on revient au même endroit, avec la même carte ouverte */
function tabOf(q){return new URLSearchParams(q).get("tab")||"home"}
document.addEventListener("submit",function(e){try{var d=e.target.closest("[id^=c]");
sessionStorage.setItem("pb-pos",JSON.stringify({u:tabOf(location.search),y:window.scrollY,open:d&&d.tagName==="DETAILS"&&d.open?d.id:null}))}catch(x){}},true);
try{var pos=JSON.parse(sessionStorage.getItem("pb-pos")||"null");sessionStorage.removeItem("pb-pos");
if(pos&&pos.u===tabOf(location.search)){if(pos.open){var od=document.getElementById(pos.open);if(od)od.open=true}window.scrollTo(0,pos.y)}}catch(x){}
/* Progression d'une recherche ou d'un envoi : mise à jour sans recharger la page */
var live=document.querySelector("[data-live]");
if(live){var kind=live.getAttribute("data-live"),logEl=live.querySelector("[data-log]");
var poll=setInterval(function(){fetch("/status",{cache:"no-store"}).then(function(r){return r.json()}).then(function(s){var st=s[kind];
if(logEl&&st.log){logEl.hidden=false;logEl.textContent=st.log}
if(!st.running){clearInterval(poll);try{sessionStorage.setItem("pb-pos",JSON.stringify({u:tabOf(location.search),y:window.scrollY}))}catch(x){}location.reload()}}).catch(function(){})},3000)}
/* Notification qui disparaît seule */
var t=document.getElementById("toast");if(t){setTimeout(function(){t.classList.add("out");setTimeout(function(){t.remove()},400)},4500);t.addEventListener("click",function(){t.remove()})}
/* Panneau « Plus » */
var mb=document.getElementById("morebtn"),sh=document.getElementById("sheet");
if(mb&&sh){mb.addEventListener("click",function(){sh.hidden=false;mb.setAttribute("aria-expanded","true")});
sh.addEventListener("click",function(e){if(e.target.hasAttribute("data-close")){sh.hidden=true;mb.setAttribute("aria-expanded","false")}});
document.addEventListener("keydown",function(e){if(e.key==="Escape"&&!sh.hidden){sh.hidden=true;mb.setAttribute("aria-expanded","false")}})}
/* Confirmation dans la page : 1er appui -> le bouton demande confirmation, 2e appui -> action */
document.addEventListener("click",function(e){var b=e.target.closest("button[data-confirm]");if(!b)return;
if(b.dataset.armed!=="1"){e.preventDefault();b.dataset.armed="1";b.dataset.label=b.innerHTML;b.textContent=b.dataset.confirm;b.classList.add("armed");
setTimeout(function(){if(b.dataset.armed==="1"){b.dataset.armed="";b.innerHTML=b.dataset.label;b.classList.remove("armed")}},6000)}});
/* Copier une demande pour Claude */
document.addEventListener("click",function(e){var b=e.target.closest("button[data-copy]");if(!b)return;var src=document.querySelector(b.dataset.copy),ok=document.querySelector(b.dataset.done);
function done(){if(ok)ok.hidden=false}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(src.value).then(done,function(){src.hidden=false;src.select()})}else{src.hidden=false;src.select();document.execCommand("copy");done()}});
/* « Tout envoyer » emporte les modifications faites à l'écran */
var sa=document.getElementById("sendall");if(sa)sa.addEventListener("submit",function(){var f=this;
document.querySelectorAll("form[data-siren]").forEach(function(d){["subject","body"].forEach(function(k){
var i=document.createElement("input");i.type="hidden";i.name=k+"_"+d.dataset.siren;i.value=d.elements[k].value;f.appendChild(i)})})});
/* Balayer une carte : droite = envoyer, gauche = ignorer */
document.querySelectorAll(".swipe").forEach(function(w){var card=w.querySelector(".card"),x0=0,y0=0,dx=0,on=false,locked=false;
w.addEventListener("touchstart",function(e){if(card.open)return;x0=e.touches[0].clientX;y0=e.touches[0].clientY;dx=0;on=true;locked=false},{passive:true});
w.addEventListener("touchmove",function(e){if(!on)return;var x=e.touches[0].clientX-x0,y=e.touches[0].clientY-y0;
if(!locked){if(Math.abs(x)<12&&Math.abs(y)<12)return;if(Math.abs(y)>Math.abs(x)){on=false;return}locked=true;w.classList.add("drag")}
dx=x;card.style.transform="translateX("+dx+"px) rotate("+(dx/40)+"deg)";w.classList.toggle("r",dx>30);w.classList.toggle("l",dx<-30)},{passive:true});
w.addEventListener("touchend",function(){if(!on)return;on=false;w.classList.remove("drag");var lim=w.offsetWidth*.38;
if(locked&&Math.abs(dx)>lim){var act=dx>0?"send":"skip",btn=w.querySelector('button[name="act"][value="'+act+'"]');
w.classList.add("gone");card.style.transform="translateX("+(dx>0?120:-120)+"%) rotate("+(dx>0?8:-8)+"deg)";
setTimeout(function(){btn.form.requestSubmit?btn.form.requestSubmit(btn):btn.form.submit()},280)}
else{card.style.transform="";w.classList.remove("r","l")}});});
/* Effets : pièces quand un mail part, confettis pour un nouveau client */
var fx="{{fx}}",layer=document.getElementById("fx"),reduce=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;
if(fx&&!reduce){var tb=document.querySelector(".tabbar"),by=window.innerHeight-((tb?tb.offsetHeight:0)+40);
if(fx==="coins"){for(var i=0;i<9;i++){var c=document.createElement("i");c.className="c";c.style.left=(window.innerWidth/2-11)+"px";c.style.top=by+"px";
c.style.setProperty("--x",((i-4)*34)+"px");c.style.animationDelay=(i*45)+"ms";layer.appendChild(c)}
var hs=document.getElementById("hud-sent");if(hs)setTimeout(function(){hs.classList.add("bump")},500)}
if(fx==="confetti"){var cols=["#ff3b3b","#2f7bff","#ffc61a","#2ec95c","#1d3d8f"];for(var j=0;j<70;j++){var f=document.createElement("i");f.className="f";
f.style.left=(Math.random()*100)+"vw";f.style.background=cols[j%5];f.style.setProperty("--x",(Math.random()*120-60)+"px");f.style.setProperty("--r",(Math.random()*900-450)+"deg");
f.style.setProperty("--d",(1.8+Math.random()*1.6)+"s");f.style.animationDelay=(Math.random()*.6)+"s";layer.appendChild(f)}}
setTimeout(function(){layer.innerHTML=""},4000)}
})();
</script></body></html>"""

LOGIN = r"""<div class="block" style="margin-top:12px"><h2>Appuyez sur Start</h2><form method="post"><label class="mut" for="pw">Mot de passe</label>
<input type="password" name="pw" id="pw" autofocus autocomplete="current-password" style="margin-top:6px">
{% if err %}<p style="color:var(--red2);font-weight:700;margin-top:8px">Mot de passe incorrect</p>{% endif %}<div class="row"><button class="ok">▶ Start</button></div></form></div>"""

HOME = r"""<div class="block hero" style="--c:var(--red)"{% if running %} data-live="job"{% endif %}><h2>Mails du jour</h2>
<form method="post" action="{{url_for('run_now')}}"><button class="big" {{'disabled' if running}}>{{'⏳ En cours…' if running else '▶ Préparer les mails du jour'}}</button></form>
{% if running %}<div class="runner" aria-hidden="true"><i class="bot"></i></div>
<form method="post" action="{{url_for('stop_job')}}"><div class="row"><button class="ko small">■ Arrêter</button></div></form>{% endif %}
<p class="log" data-log{% if not log %} hidden{% endif %}>{{log}}</p></div>
<div class="stripe">{% for label,n,c,tab in stats %}{% if tab %}<a class="mini-stat" style="--c:var({{c}})" href="{{url_for('index', tab=tab)}}"><b>{{n}}</b><span>{{label}}</span></a>{% else %}<div class="mini-stat" style="--c:var({{c}})"><b>{{n}}</b><span>{{label}}</span></div>{% endif %}{% endfor %}</div>
<div class="block quest" style="--n:{{limit}};--c:var(--yellow)"><h2>Objectif du jour</h2>
<p><b>{{today}}</b> mail{{'s' if today > 1}} envoyé{{'s' if today > 1}} aujourd'hui · objectif {{limit}}</p>
<div class="bar">{% for i in range(limit) %}<i class="{{'on' if i < today}}" style="animation-delay:{{i*60}}ms"></i>{% endfor %}</div></div>
<div class="block" style="--c:var(--green)"><h2>Mode collecte</h2><p class="mut">Teste un grand nombre d'entreprises pour remplir le stock d'adresses. Ça peut durer des heures : laissez le téléphone branché.</p>
<div class="row">{% if running %}<span class="mut">Une recherche est déjà en cours.</span>{% else %}<form method="post" action="{{url_for('collect_now')}}"><button class="ok">★ Lancer la collecte</button></form>{% endif %}</div></div>
<details class="block fold"><summary><span>Réglages <span class="mut" style="font-size:14px">· mode {{modes|selectattr(0,"equalto",mode)|map(attribute=1)|first}}</span></span> {{icon('chevron')|safe}}</summary>
<form method="post" action="{{url_for('set_mode')}}"><label class="mut" for="mode">Mode d'envoi. En mode Review, aucun mail ne part sans votre bouton Envoyer.</label>
<select name="mode" id="mode" onchange="this.form.submit()" style="margin-top:8px">
{% for k,l in modes %}<option value="{{k}}" {{'selected' if k==mode}}>{{l}}</option>{% endfor %}</select></form>
<form method="post" action="{{url_for('clean_now')}}" style="margin-top:18px"><span class="mut">Adresses invalides : fichiers, adresses d'agences web, domaines inexistants, doublons.</span>
<div class="row" style="margin-top:8px"><button class="gh small"{% if cleaning %} disabled{% endif %}>{{'⏳ Nettoyage…' if cleaning else '🧹 Nettoyer les adresses'}}</button></div>
{% if clean_last %}<p class="mut" style="margin-top:8px;font-size:14px">Dernier nettoyage : {{clean_last[0]}} · {{clean_last[1]}} adresse(s) retirée(s)</p>{% endif %}</form>
<form method="post" action="{{url_for('stop')}}" style="margin-top:18px"><label class="mut" for="stopmail">Désinscription : quelqu'un a répondu STOP</label>
<input type="email" name="email" id="stopmail" placeholder="email@entreprise.fr" required style="margin-top:8px"><div class="row"><button class="ko small">Ne plus contacter</button></div></form>
</details>"""

SITE = "{{ {'none':'pas de site','outdated':'site à refaire'}.get(c.site_status,c.site_status) }}"

SIGNATURE = r"""<details class="block fold"><summary>Signature ajoutée à chaque mail {{icon('chevron')|safe}}</summary>
<pre class="sig">{{sig('site')}}</pre><p class="mut" style="margin-top:8px">La phrase sur l'origine de l'adresse s'adapte à chaque mail (site de l'entreprise ou OpenStreetMap).</p></details>"""

DRAFT = r"""{% if sending or send_log %}<div class="block" style="--c:var(--green)"{% if sending %} data-live="send"{% endif %}><h2>Envoi groupé</h2>
<p class="log" style="margin:0" data-log>{{send_log}}</p>{% if sending %}<div class="runner" aria-hidden="true"><i class="bot"></i></div>
<form method="post" action="{{url_for('stop_send')}}"><div class="row"><button class="ko small">■ Arrêter l'envoi</button></div></form>{% endif %}</div>{% endif %}
{% if rows and not sending %}<div class="block" style="--c:var(--green)"><h2>{{total}} mails prêts</h2>
<p class="mut">Envoie les {{total}} mails, avec vos modifications à l'écran, espacés de quelques secondes.</p>
<form method="post" action="{{url_for('send_all')}}" id="sendall"><div class="row"><button class="big ok" data-confirm="Appuyez encore pour confirmer l'envoi de {{total}} mail(s)">✉ Tout envoyer ({{total}})</button></div></form></div>
<p class="hint">Touchez un mail pour le modifier. Glissez-le vers la droite pour l'envoyer, vers la gauche pour l'ignorer.</p>""" + SIGNATURE + r"""{% endif %}
{% for c in rows %}<div class="swipe"><div class="swipe-bg" aria-hidden="true"><span class="go">✉ Envoyer</span><span class="no">Ignorer ✕</span></div>
<details class="block card" id="c{{c.siren}}"><summary><div class="head"><h2>{{c.enseigne or c.nom}}</h2>{{icon('chevron')|safe}}</div>
<span class="tag">{{c.commune}}</span><span class="tag">{{c.metier}}</span><span class="tag {{'hot' if c.site_status=='none' else 'warm'}}">""" + SITE + r"""</span>
<p class="subj">{{c.subject}}</p><p class="prev">{{c.body}}</p></summary>
<form method="post" action="{{url_for('draft_action',siren=c.siren)}}" data-siren="{{c.siren}}">
<div class="mut">{{c.email}}{% if c.site_url %} · <a href="{{c.site_url}}" target="_blank" rel="noopener">voir le site</a>{% endif %}</div>
<input name="subject" aria-label="Objet" value="{{c.subject}}" style="margin-top:10px"><textarea name="body" aria-label="Message">{{c.body}}</textarea>
<div class="actions"><button name="act" value="send" class="ok grow" data-confirm="Confirmer l'envoi à {{c.email}}">✉ Envoyer</button>
<button name="act" value="save" class="gh ib" aria-label="Enregistrer" title="Enregistrer">{{icon('save')|safe}}</button>
<button name="act" value="skip" class="ko ib" aria-label="Ignorer" title="Ignorer">{{icon('skip')|safe}}</button></div></form></details></div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Aucun mail en attente. Passez par « Rédiger », ou lancez « Préparer les mails du jour » depuis l'accueil.</span></div>{% endfor %}
{% if total > rows|length %}<div class="more"><a class="btn gh small" href="{{url_for('index', tab="drafts", n=n + 30)}}">Afficher {{[30, total - rows|length]|min}} de plus <span class="mut" style="font-size:13px">({{total - rows|length}} restant{{'s' if total - rows|length > 1}})</span></a></div>{% endif %}"""

WRITE = r"""{% if auto %}<div class="block"><h2>Rédaction automatique</h2><p class="mut">Claude écrit chaque mail via la clé API quand vous appuyez sur « Préparer les mails du jour ».</p></div>
{% else %}<div class="block"><h2>{{n}} entreprise{{'s' if n > 1}} prête{{'s' if n > 1}}</h2>
<p class="mut">1. Copiez la demande.<br>2. Collez-la dans une conversation avec Claude (claude.ai).<br>3. Collez sa réponse ci-dessous.</p>
{% if n %}<div class="row"><button class="big" type="button" id="copyall">⧉ Copier toutes les demandes ({{n}})</button></div>
<p class="mut" id="copied" hidden style="margin-top:10px">Copié. Collez-la maintenant dans Claude.</p>
{% if n > 40 %}<p class="mut" style="margin-top:10px">Au-delà d'environ 40 mails, Claude peut couper sa réponse en route. Dans ce cas, utilisez les lots ci-dessous.</p>{% endif %}{% endif %}</div>
{% if n > 1 %}<details class="block fold"><summary>Copier par lots {{icon('chevron')|safe}}</summary>
<label class="mut" for="lotsize">Taille d'un lot</label>
<select id="lotsize" style="margin-top:6px"><option value="10">10 mails</option><option value="20">20 mails</option><option value="30" selected>30 mails</option><option value="50">50 mails</option><option value="100">100 mails</option></select>
<div class="lots" id="lots"></div></details>{% endif %}
<form class="block" style="--c:var(--green)" method="post" action="{{url_for('import_mails')}}"><h2>Réponse de Claude</h2>
<textarea name="text" aria-label="Réponse de Claude" placeholder="Collez ici le tableau JSON écrit par Claude" required style="min-height:150px"></textarea>
<p class="mut" style="margin-top:8px">Vous pouvez coller plusieurs réponses à la suite, ou en importer une par lot : les mails déjà importés ne sont pas refaits.</p>
<div class="row"><button class="ok">⬇ Importer les mails</button></div></form>
<script type="application/json" id="pdata">{{pdata|tojson}}</script>
<script>
(function(){var el=document.getElementById("pdata");if(!el)return;var d=JSON.parse(el.textContent),N=d.companies.length;
function build(a,b){return d.intro+"\n\nEntreprises :\n"+JSON.stringify(d.companies.slice(a,b),null,1)}
function copy(text,done){function fallback(){var t=document.createElement("textarea");t.value=text;t.setAttribute("readonly","");t.style.cssText="position:fixed;top:0;left:0;width:1px;height:1px;opacity:0";
document.body.appendChild(t);t.select();t.setSelectionRange(0,text.length);var ok=false;try{ok=document.execCommand("copy")}catch(e){}t.remove();done(ok)}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){done(true)},fallback)}else fallback()}
function say(ok,msg){var c=document.getElementById("copied");if(!c)return;c.hidden=false;c.textContent=ok?msg:"Copie impossible : ouvrez Réglages Chrome > Paramètres du site, ou copiez à la main."}
var all=document.getElementById("copyall");if(all)all.addEventListener("click",function(){copy(build(0,N),function(ok){say(ok,"Copié : les "+N+" demandes. Collez-les dans Claude.")})});
var box=document.getElementById("lots"),size=document.getElementById("lotsize");
function lots(){if(!box)return;var k=parseInt(size.value,10),h="";for(var a=0;a<N;a+=k){var b=Math.min(a+k,N);h+='<button type="button" class="small lot" data-a="'+a+'" data-b="'+b+'">⧉ Lot '+(a/k+1)+' <span style="opacity:.85">· '+(a+1)+(b-a>1?"–"+b:"")+'</span></button>'}box.innerHTML=h}
if(size){size.addEventListener("change",lots);lots();box.addEventListener("click",function(e){var b=e.target.closest(".lot");if(!b)return;var a=+b.dataset.a,z=+b.dataset.b;
copy(build(a,z),function(ok){say(ok,"Lot copié ("+(a+1)+" à "+z+"). Collez-le dans Claude.");if(ok){b.classList.add("ok");b.textContent="✓ Copié · "+(a+1)+"–"+z}})})}
})();
</script>{% endif %}"""

SENT = r"""<form class="block" style="--c:var(--blue)" method="post" action="{{url_for('check_inbox')}}"><h2>Réponses</h2>
<p class="mut">Lit votre boîte Gmail (sans rien modifier) : réponses, demandes STOP et adresses en erreur sont reconnues toutes seules.</p>
<div class="row"><button>📬 Vérifier les réponses</button></div></form>
{% for c in rows %}<div class="block" style="--c:var({{ {'replied':'--green','refused':'--red','bounced':'--red'}.get(c.status,'--blue') }})"><h2>{{c.enseigne or c.nom}}</h2>
<span class="tag {{ {'replied':'good','refused':'hot','bounced':'hot','followed_up':'warm'}.get(c.status,'') }}">{{ {'sent':'envoyé','followed_up':'relancé','replied':'a répondu','refused':'STOP / refus','bounced':'adresse en erreur'}.get(c.status,c.status) }}</span>
<div class="mut" style="margin-top:6px">{{c.email}} · envoyé le {{c.contacted_at|frdate}}{% if c.reply_at %} · réponse le {{c.reply_at|frdate}}{% endif %}</div>
{% if c.reply_snippet %}<p class="quote">« {{c.reply_snippet}} »</p>{% endif %}
{% if c.status in ('sent','followed_up') %}<form method="post" action="{{url_for('mark',siren=c.siren)}}"><div class="row">
<button name="s" value="replied" class="ok small">★ A répondu</button><button name="s" value="refused" class="ko small">Refus</button></div></form>{% endif %}</div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Rien d'envoyé pour l'instant.</span></div>{% endfor %}
{% if total > rows|length %}<div class="more"><a class="btn gh small" href="{{url_for('index', tab="sent", n=n + 30)}}">Afficher {{[30, total - rows|length]|min}} de plus <span class="mut" style="font-size:13px">({{total - rows|length}} restant{{'s' if total - rows|length > 1}})</span></a></div>{% endif %}"""

FOLLOW = r"""<div class="block" style="--c:var(--yellow)"><h2>{{total}} à relancer</h2>
<p class="mut">Sans réponse depuis {{days}} jours. Une seule relance par entreprise, dans le même fil que votre premier mail.</p></div>
{% if rows %}<details class="block fold"><summary>Faire écrire les relances par Claude {{icon('chevron')|safe}}</summary>
<button class="small" type="button" data-copy="#fprompt" data-done="#fcopied">⧉ Copier la demande</button>
<textarea id="fprompt" readonly hidden>{{prompt}}</textarea><p class="mut" id="fcopied" hidden style="margin-top:10px">Copié. Collez-la dans Claude, puis sa réponse ci-dessous.</p>
<form method="post" action="{{url_for('import_followups')}}"><textarea name="text" aria-label="Réponse de Claude" placeholder="Collez ici le tableau JSON écrit par Claude" style="min-height:90px"></textarea>
<div class="row"><button class="ok small">⬇ Importer les relances</button></div></form></details>
<p class="hint">Touchez une relance pour la modifier. Glissez vers la droite pour l'envoyer, vers la gauche pour ne pas relancer.</p>""" + SIGNATURE + r"""{% endif %}
{% for c in rows %}<div class="swipe"><div class="swipe-bg" aria-hidden="true"><span class="go">✉ Relancer</span><span class="no">Pas de relance ✕</span></div>
<details class="block card" id="c{{c.siren}}"><summary><div class="head"><h2>{{c.enseigne or c.nom}}</h2>{{icon('chevron')|safe}}</div>
<span class="tag">{{c.commune}}</span><span class="tag warm">premier mail le {{c.contacted_at|frdate}}</span>
<p class="subj">{{c.f_subject}}</p><p class="prev">{{c.f_body}}</p></summary>
<form method="post" action="{{url_for('followup_action',siren=c.siren)}}"><div class="mut">{{c.email}}</div>
<input name="subject" aria-label="Objet" value="{{c.f_subject}}" style="margin-top:10px"><textarea name="body" aria-label="Message" style="min-height:170px">{{c.f_body}}</textarea>
<div class="actions"><button name="act" value="send" class="ok grow" data-confirm="Confirmer la relance à {{c.email}}">✉ Relancer</button>
<button name="act" value="save" class="gh ib" aria-label="Enregistrer" title="Enregistrer">{{icon('save')|safe}}</button>
<button name="act" value="skip" class="ko ib" aria-label="Ne pas relancer" title="Ne pas relancer">{{icon('skip')|safe}}</button></div></form></details></div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Aucune relance à faire. Les mails sans réponse après {{days}} jours apparaîtront ici.</span></div>{% endfor %}
{% if total > rows|length %}<div class="more"><a class="btn gh small" href="{{url_for('index', tab="followups", n=n + 30)}}">Afficher {{[30, total - rows|length]|min}} de plus <span class="mut" style="font-size:13px">({{total - rows|length}} restant{{'s' if total - rows|length > 1}})</span></a></div>{% endif %}"""

STEPS = [("replied", "Réponse"), ("mockup", "Maquette"), ("meeting", "Rendez-vous"), ("client", "Client")]

PIPE = r"""<div class="block" style="--c:var(--green)"><h2>Suivi des prospects</h2>
<p class="mut">Touchez une étape pour faire avancer un prospect. Notes et rappels sont dans chaque carte.</p></div>
{% for c in rows %}{% set cur = steps_keys.index(c.stage_key) if c.stage_key in steps_keys else -1 %}
<div class="block{{' lost' if c.stage_key=='lost'}}" id="c{{c.siren}}" style="--c:var({{ {'client':'--green','lost':'--red','meeting':'--yellow','mockup':'--blue'}.get(c.stage_key,'--red') }})">
<h2>{{c.enseigne or c.nom}}</h2><span class="tag {{ {'client':'good','lost':'hot','meeting':'warm'}.get(c.stage_key,'') }}">{{stage_names[c.stage_key]}}</span>
<span class="tag">{{c.commune}}</span>{% if c.due %}<span class="tag hot">Rappel : {{c.reminder|frshort}}</span>{% elif c.reminder %}<span class="tag warm">Rappel le {{c.reminder|frshort}}</span>{% endif %}
<div class="mut" style="margin-top:6px"><a href="mailto:{{c.email}}">{{c.email}}</a></div>
{% if c.reply_snippet %}<p class="quote">« {{c.reply_snippet}} »</p>{% endif %}
<form method="post" action="{{url_for('pipeline_action',siren=c.siren)}}">
<div class="stepper" role="group" aria-label="Étape">{% for k,l in steps %}<button name="stage" value="{{k}}" class="step{{' done' if loop.index0 < cur or c.stage_key == 'client'}}{{' cur' if loop.index0 == cur and c.stage_key != 'client'}}"{% if loop.index0 == cur %} aria-current="step"{% endif %}><span class="dot">{{'✓' if loop.index0 < cur or c.stage_key == 'client' else loop.index}}</span>{{l}}</button>{% endfor %}</div>
{% if c.stage_key != 'lost' %}<div style="text-align:right"><button name="stage" value="lost" class="link">Marquer comme perdu</button></div>{% endif %}
<details class="fold" style="margin-top:6px"{% if c.due %} open{% endif %}><summary>Note et rappel{% if c.notes %} · 1 note{% endif %} {{icon('chevron')|safe}}</summary>
<textarea name="notes" aria-label="Notes" placeholder="Notes (ce qui a été dit, ce qu'il faut faire…)" style="min-height:90px;margin-top:0">{{c.notes or ''}}</textarea>
<label class="mut" for="r{{c.siren}}" style="display:block;margin-top:10px">Me le rappeler le :</label>
<div class="actions" style="margin-top:4px"><input type="date" id="r{{c.siren}}" name="reminder" value="{{c.reminder or ''}}" class="grow">
<button name="stage" value="keep" class="gh ib" aria-label="Enregistrer" title="Enregistrer">{{icon('save')|safe}}</button></div></details></form></div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">Personne à suivre pour l'instant. Les réponses apparaissent ici dès que quelqu'un répond.</span></div>{% endfor %}
{% if total > rows|length %}<div class="more"><a class="btn gh small" href="{{url_for('index', tab="pipeline", n=n + 30)}}">Afficher {{[30, total - rows|length]|min}} de plus <span class="mut" style="font-size:13px">({{total - rows|length}} restant{{'s' if total - rows|length > 1}})</span></a></div>{% endif %}"""

STATS = r"""<div class="block best" style="--c:var(--green)"><h2>Ce qui marche le mieux</h2>
{% if insights %}<ul>{% for title, l in insights %}<li><span><span class="k">{{title}}</span>{{l.label}}</span><span class="v">{{l.rate}} %<span class="mut" style="font-size:13px"> ({{l.replied}}/{{l.sent}})</span></span></li>{% endfor %}</ul>
{% else %}<p class="mut">Encore trop peu d'envois pour conclure : il faut au moins 5 mails reçus dans une catégorie.</p>{% endif %}</div>
<div class="stripe">{% for label,n,c in tiles %}<div class="mini-stat" style="--c:var({{c}})"><b>{{n}}</b><span>{{label}}</span></div>{% endfor %}</div>
{% if not data.total.sent %}<div class="block idle"><i class="bot"></i><span class="mut">Pas encore de statistiques : elles apparaissent après vos premiers envois.</span></div>{% endif %}
{% for title, lines in data.groups if lines %}<details class="block fold"{% if loop.first %} open{% endif %}><summary>{{title}} {{icon('chevron')|safe}}</summary>
{% for l in lines %}<div class="bars"><div class="l"><span>{{l.label}}{% if l.sent < 5 %} <span class="tag few">peu de données</span>{% endif %}</span>
<span class="mut" style="white-space:nowrap">{{l.replied}}/{{l.sent}} · {{l.rate}} %</span></div><div class="t"><i style="width:{{[l.rate,3]|max}}%"></i></div></div>{% endfor %}</details>{% endfor %}
<p class="mut" style="text-align:center">Taux de réponse = réponses / mails reçus. Les adresses en erreur ne comptent pas.</p>"""


LIST = r"""<div class="block" style="--c:var({{color}})"><h2>{{title}} <span class="mut">({{total}})</span></h2>
<div class="row"><a class="btn gh small" href="{{url_for('index')}}">← Accueil</a>{% if kind == 'stock' and total %}<a class="btn small" href="{{url_for('index', tab='write')}}">✎ Rédiger</a>{% endif %}</div></div>
{% for c in rows %}<div class="block" style="--c:var({{color}})"><h2>{{c.enseigne or c.nom}}</h2>
<span class="tag">{{c.metier or c.naf}}</span><span class="tag">{{c.commune}}</span>{% if kind == 'stock' %}<span class="tag {{'warm' if c.site_status in ('none','outdated')}}">{{ {'none':'sans site','outdated':'site ancien','ok':'site correct'}.get(c.site_status,'site ?') }}</span>{% endif %}
<div class="mut" style="margin-top:6px">{{c.email}}{% if kind == 'stock' %} · source : {{ {'site':'site web','osm':'OpenStreetMap'}.get(c.email_source,c.email_source) }}{% elif c.reply_at %} · le {{c.reply_at|frdate}}{% elif c.contacted_at %} · envoyé le {{c.contacted_at|frdate}}{% endif %}</div>
{% if c.reply_snippet %}<p class="quote">« {{c.reply_snippet}} »</p>{% endif %}</div>
{% else %}<div class="block idle"><i class="bot"></i><span class="mut">{{empty}}</span></div>{% endfor %}
{% if total > rows|length %}<div class="more"><a class="btn gh small" href="{{url_for('index', tab=kind, n=n + 30)}}">Afficher {{[30, total - rows|length]|min}} de plus <span class="mut" style="font-size:13px">({{total - rows|length}} restant{{'s' if total - rows|length > 1}})</span></a></div>{% endif %}"""
