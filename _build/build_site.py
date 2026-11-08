"""Genera il sito statico di Quanto Manca.

Uso, dalla cartella Website:
    python3 _build/build_site.py

Le date delle feste si calcolano da oggi (ora italiana): rilanciandolo dopo una festa,
titoli e testi passano all'anno successivo. Il conto alla rovescia vero e proprio
gira nel browser, nel fuso orario di chi visita.
"""

import datetime as dt
import html
import json
import os
import random
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
from holidays import HOLIDAYS  # noqa: E402

# ---------- Configurazione ----------

BASE = "https://quantomanca.github.io/"
APP_NAME = "Quanto Manca"
# Link alla scheda App Store, per esempio "https://apps.apple.com/it/app/quanto-manca/id1234567890".
# Finché è None il sito mostra "Presto su App Store".
APP_STORE_URL = "https://apps.apple.com/it/app/quanto-manca-countdown-feste/id6830202016"
SUPPORT_EMAIL = "supporto.quantomanca@gmail.com"
AUTHOR = "Antonio Rossi"
VERSION = "4"  # cambia per forzare il ricaricamento di CSS e JS

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(SITE)
TODAY = dt.datetime.now(ZoneInfo("Europe/Rome")).date()

WEEKDAYS = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MONTHS = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
          "settembre", "ottobre", "novembre", "dicembre"]

e = html.escape


# ---------- Date ----------

def easter(y):
    a, b, c = y % 19, y // 100, y % 100
    d, ee, f = b // 4, b % 4, (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * ee + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(y, month, day)


def occurrence(rule, year):
    kind = rule[0]
    if kind == "fixed":
        return dt.date(year, rule[1], rule[2])
    if kind == "easter":
        return easter(year) + dt.timedelta(days=rule[1])
    if kind == "nth":
        first = dt.date(year, rule[1], 1)
        offset = (rule[2] - first.weekday()) % 7
        return first + dt.timedelta(days=offset + 7 * (rule[3] - 1))
    raise ValueError(rule)


def upcoming(rule, count=1, today=TODAY):
    out, year = [], today.year - 1
    while len(out) < count:
        d = occurrence(rule, year)
        if d >= today:
            out.append(d)
        year += 1
    return out


def js_rule(rule):
    return ":".join(str(x) for x in rule)


def long_date(d, year=True):
    s = f"{WEEKDAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]}"
    return f"{s} {d.year}" if year else s


def short_date(d):
    return f"{WEEKDAYS[d.weekday()][:3]} {d.day} {MONTHS[d.month - 1][:3]}"


# ---------- Dati derivati ----------

for h in HOLIDAYS:
    h["url"] = f"quanto-manca-{h['prep']}-{h['id']}/"
    h["to"] = f"{h['prep']} {h['name']}"          # "a Natale", "alla Befana"
    h["next"] = upcoming(h["rule"], 6)
    h["year"] = h["next"][0].year
    h["og"] = f"assets/og/{h['id']}.jpg"
    h["icon_src"] = f"assets/icons/{h['id']}.png"

ORDERED = sorted(HOLIDAYS, key=lambda h: h["next"][0])
CHRISTMAS = next(h for h in HOLIDAYS if h["id"] == "natale")


def load_quotes():
    """Una selezione di citazioni brevi dall'app; se il progetto non c'è (per esempio su GitHub) riusa quella salvata."""
    saved = os.path.join(SITE, "_build", "quotes.json")
    source = os.path.join(PROJECT, "Shared", "DailyQuotes.json")
    if os.path.exists(source):
        quotes = [q for q in json.load(open(source, encoding="utf-8")) if 30 <= len(q["text"]) <= 120]
        seen, picked = set(), []
        for q in sorted(quotes, key=lambda q: random.Random(q["text"]).random()):
            if q["author"] not in seen:
                seen.add(q["author"])
                picked.append(q)
            if len(picked) == 40:
                break
        with open(saved, "w", encoding="utf-8") as f:
            json.dump(picked, f, ensure_ascii=False, indent=1)
    return json.load(open(saved, encoding="utf-8"))


QUOTES = load_quotes()


# ---------- Pezzi comuni ----------

ICON_STORE = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="3" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 18.5h4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'


def store_button(extra=""):
    if APP_STORE_URL:
        return f'<a class="btn btn-primary {extra}" href="{e(APP_STORE_URL)}">{ICON_STORE}Scarica gratis su App Store</a>'
    return f'<span class="btn btn-soon {extra}" role="note">{ICON_STORE}<span><small>Per iPhone</small>Presto su App Store</span></span>'


def head(title, description, path, og_image, og_alt, jsonld, extra=""):
    url = BASE + path
    smart_banner = ""
    if APP_STORE_URL and "/id" in APP_STORE_URL:
        app_id = APP_STORE_URL.rsplit("/id", 1)[1].split("?")[0]
        smart_banner = f'\n<meta name="apple-itunes-app" content="app-id={e(app_id)}">'
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in jsonld)
    return f"""<!doctype html>
<html lang="it" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="author" content="{AUTHOR}">
<meta name="theme-color" content="#0A1433">{smart_banner}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{APP_NAME}">
<meta property="og:locale" content="it_IT">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{BASE}{og_image}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/assets/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="stylesheet" href="/assets/site.css?v={VERSION}">
<script src="/assets/site.js?v={VERSION}" defer></script>
{ld}{extra}
</head>
<body>
<a class="skip" href="#contenuto">Vai al contenuto</a>
"""


def header(current=""):
    def link(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{href}"{cur}>{label}</a>'
    return f"""<header class="site-header">
<div class="wrap">
<a class="logo" href="/" aria-label="{APP_NAME}, pagina iniziale"><img src="/assets/icons/app-64.png" alt="" width="34" height="34">{APP_NAME}</a>
<nav class="site-nav" aria-label="Principale">
{link("/#feste", "Feste", "feste")}
{link("/#app", "L'app", "app")}
{link("/#avvento", "Avvento", "avvento")}
{link("/supporto.html", "Supporto", "supporto")}
<a class="nav-cta" href="/#scarica">Scarica</a>
</nav>
</div>
</header>
"""


def footer():
    items = "\n".join(f'<li><a href="/{h["url"]}">Quanto manca {e(h["to"])}</a></li>' for h in HOLIDAYS)
    return f"""<footer class="site-footer">
<div class="wrap">
<div class="footer-grid">
<div>
<a class="logo" href="/"><img src="/assets/icons/app-64.png" alt="" width="34" height="34" loading="lazy">{APP_NAME}</a>
<p style="margin-top:14px">Il conto alla rovescia per le tue feste, con sfondi animati, suoni, calendario dell'Avvento e widget per iPhone.</p>
</div>
<div>
<h2>Conti alla rovescia</h2>
<ul class="footer-cols">
{items}
</ul>
</div>
<div>
<h2>Informazioni</h2>
<ul>
<li><a href="/supporto.html">Supporto e domande</a></li>
<li><a href="/privacy.html">Privacy</a></li>
<li><a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></li>
</ul>
</div>
</div>
<div class="copy"><span>© {TODAY.year} {AUTHOR}</span><span>iPhone, App Store e iOS sono marchi di Apple Inc.</span></div>
</div>
</footer>
</body>
</html>
"""


def countdown_block(rule, caption_html=""):
    return f"""<div class="countdown" role="timer" aria-live="off">
<div class="unit"><span class="num" data-u="d">–</span><span class="lbl">giorni</span></div>
<div class="unit"><span class="num" data-u="h">–</span><span class="lbl">ore</span></div>
<div class="unit"><span class="num" data-u="m">–</span><span class="lbl">minuti</span></div>
<div class="unit"><span class="num" data-u="s">–</span><span class="lbl">secondi</span></div>
</div>{caption_html}"""


def style_vars(h):
    c = h["colors"]
    return f"--c1:{c[0]};--c2:{c[1]};--c3:{c[2]};--accent:{h['accent']}"


def holiday_card(h, first=False):
    d = h["next"][0]
    days = (d - TODAY).days
    days_txt = "Oggi" if days == 0 else str(days)
    lbl = "" if days == 0 else ("giorno" if days == 1 else "giorni")
    return f"""<a class="holiday-card{' is-next' if first else ''}" href="/{h['url']}" style="{style_vars(h)}" data-rule="{js_rule(h['rule'])}">
<img src="/{h['icon_src']}" alt="" width="54" height="54" loading="lazy">
<span class="hc-days" data-days-to="{js_rule(h['rule'])}"><span data-n>{days_txt}</span><small data-l>{lbl}</small></span>
<span class="hc-name">{e(h['name'])}</span>
<span class="hc-date" data-date-of="{js_rule(h['rule'])}">{short_date(d)}</span>
<span class="hc-badge"{'' if first else ' hidden'}>La prossima</span>
</a>"""


def faq_html(items):
    return "\n".join(
        f"<details><summary>{e(q)}</summary><div><p>{a}</p></div></details>" for q, a in items
    )


def faq_jsonld(items):
    import re
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}}
            for q, a in items
        ],
    }


def write(path, content):
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("✓", path)


# ---------- Home ----------

SCENE_TITLES = [
    "Camino acceso", "Notte di neve", "Luci sull'albero", "Il volo della slitta", "Pupazzo nella bufera",
    "Aurora boreale", "Angolo accogliente", "Slitta sul bosco", "Luci di festa", "Rametto dorato",
    "Albero incantato", "Mercatino", "Fuochi sulla città", "Brindisi", "Mezzanotte", "Volo della Befana",
    "Calze sul camino", "Pioggia di cuori", "Notte di rose", "Coriandoli", "Maschere", "Prato in fiore",
    "Caccia alle uova", "Giardino fiorito", "Tramonto", "Spiaggia al tramonto", "Fuochi sul mare",
    "Luna stregata", "Campo di zucche", "Notte stellata", "Palloncini",
]

ADVENT_ORNAMENTS = ["⭐️", "🔔", "🎁", "❄️", "🕯️", "🍪", "🦌", "🧦", "🎀", "🍬", "☃️", "🌟",
                    "🎄", "🧸", "🍊", "🪵", "🎶", "🛷", "🥨", "📯", "🕊️", "🌰", "💫", "🎅"]

HOME_FAQ = [
    ("Quanto Manca è gratis?",
     "Sì. L'app si scarica gratis e la prossima festa in calendario è sempre sbloccata. Le altre feste si sbloccano con un breve video facoltativo, valido fino al giorno della festa. Con <strong>Quanto Manca Plus</strong>, a 0,99 € una volta sola, togli la pubblicità e sblocchi tutto per sempre."),
    ("Su quali dispositivi funziona?",
     "Su iPhone con iOS 17 o successivo, con i widget per la schermata Home e per il blocco schermo."),
    ("Il conto alla rovescia usa il mio fuso orario?",
     "Sì: il conto alla rovescia arriva alla mezzanotte del giorno di festa nel fuso orario del tuo iPhone, ovunque ti trovi. Lo stesso vale per i conti alla rovescia di questo sito."),
    ("Posso creare un countdown per il mio compleanno?",
     "Sì, con la tua festa personalizzata: scegli nome, data e, se vuoi, l'orario preciso, poi icona e colori. Può ripetersi ogni anno, perfetta per compleanni e anniversari."),
    ("Posso usare le mie foto come sfondo?",
     "Sì: puoi scegliere fino a 10 foto oppure un intero album di Foto, e decidere se far ruotare i tuoi sfondi, quelli dell'app o tutti insieme. Le foto restano sul tuo iPhone."),
    ("Perché non sento la musica?",
     "Quanto Manca rispetta l'interruttore silenzioso dell'iPhone: disattiva la modalità silenziosa e alza il volume. Musica e suoni si possono anche regolare dalle impostazioni dell'app."),
]


def home():
    quotes_json = json.dumps(QUOTES, ensure_ascii=False)
    demo = [{"id": h["id"], "name": h["name"], "emoji": h["emoji"], "rule": js_rule(h["rule"]),
             "colors": h["colors"], "accent": h["accent"], "scene": h["scene"]} for h in ORDERED]
    nat = CHRISTMAS
    nat_d = nat["next"][0]
    cards = "\n".join(holiday_card(h, i == 0) for i, h in enumerate(ORDERED))
    chips = "\n".join(
        f'<button type="button" data-demo="{h["id"]}" aria-pressed="{str(i == 0).lower()}" aria-label="{e(h["name"])}">{h["emoji"]}</button>'
        for i, h in enumerate(ORDERED))
    first = ORDERED[0]
    tiles = [("snow", CHRISTMAS, "Notte di neve", "Neve, vento d'inverno e campane lontane"),
             ("fireworks", HOLIDAYS[1], "Fuochi sulla città", "Ogni scoppio si sente quando esplode"),
             ("hearts", HOLIDAYS[3], "Pioggia di cuori", "Battito del cuore e un bacio"),
             ("halloween", HOLIDAYS[9], "Luna stregata", "Gufi, pipistrelli e porte che cigolano")]
    tiles_html = "\n".join(
        f'<figure class="scene-tile reveal" style="{style_vars(h)}"><canvas data-scene="{s}" data-accent="{h["accent"]}" aria-hidden="true"></canvas>'
        f'<figcaption>{e(t)}<span>{e(sub)}</span></figcaption></figure>'
        for s, h, t, sub in tiles)
    scene_chips = "\n".join(f"<li>{e(t)}</li>" for t in SCENE_TITLES)
    icon_names = [("app", "Natale")] + [(h["id"], h["name"]) for h in HOLIDAYS if h["id"] != "natale"]
    icons = "\n".join(
        f'<figure><img src="/assets/icons/{i if i != "app" else "natale"}.png" alt="Icona {e(n)}" width="92" height="92" loading="lazy"><figcaption>{e(n)}</figcaption></figure>'
        for i, n in icon_names)
    doors = []
    for n in range(1, 25):
        orn = ADVENT_ORNAMENTS[n - 1]
        if n <= 9:
            cls, txt = ("open gold" if n == 4 else "open"), orn
            if n == 4:
                cls, txt = "gold", orn
        elif n == 10:
            cls, txt = "today", str(n)
        else:
            cls, txt = "", str(n)
        doors.append(f'<div class="door {cls}" data-n="{n}" data-ornament="{orn}">{txt}</div>')
    doors = "\n".join(doors)
    q0 = QUOTES[0]

    faq = HOME_FAQ + [
        ("Dove si scarica Quanto Manca?",
         "Quanto Manca è disponibile gratis su App Store per iPhone con iOS 17 o successivo: cerca «Quanto Manca» o usa il pulsante qui sopra.") if APP_STORE_URL else
        ("Quando esce Quanto Manca?",
         "Quanto Manca è in arrivo su App Store per iPhone, in tempo per il conto alla rovescia di Natale."),
    ]

    app_ld = {
        "@context": "https://schema.org",
        "@type": "MobileApplication",
        "name": APP_NAME,
        "description": "Conto alla rovescia per Natale e tutte le feste, con sfondi animati e suoni, calendario dell'Avvento, frase del giorno e widget per la Home e il blocco schermo.",
        "operatingSystem": "iOS 17.0 o successivo",
        "applicationCategory": "LifestyleApplication",
        "inLanguage": "it",
        "image": BASE + "icon.png",
        "url": BASE,
        "author": {"@type": "Person", "name": AUTHOR},
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
    }
    if APP_STORE_URL:
        app_ld["downloadUrl"] = APP_STORE_URL
        app_ld["installUrl"] = APP_STORE_URL
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": APP_NAME, "url": BASE, "inLanguage": "it-IT"}

    page = head(
        "Quanto Manca – Il countdown per Natale e le feste, per iPhone",
        "Quanto manca a Natale? Il conto alla rovescia live per Natale e le tue feste, con sfondi animati, calendario dell'Avvento e widget per iPhone.",
        "", "assets/og/home.jpg", "Quanto Manca, il conto alla rovescia per le tue feste",
        [site_ld, app_ld, faq_jsonld(faq)],
    )
    page += header()
    page += f"""<main id="contenuto">
<section class="hero">
<div class="wrap">
<div>
<p class="eyebrow"><span class="dot"></span>App per iPhone · Gratis</p>
<h1>Il conto alla rovescia <span class="hl">per tutte le tue feste</span></h1>
<p class="lead">{APP_NAME} ti dice in ogni momento quanto manca a Natale, Capodanno, Pasqua, Halloween e ai giorni che contano per te. Con sfondi animati che si sentono, il calendario dell'Avvento e i widget per la Home e il blocco schermo.</p>
<div class="btn-row" id="scarica">{store_button()}<a class="btn btn-ghost" href="#feste">Tutte le feste</a></div>
<div class="hero-card" data-countdown="{js_rule(nat['rule'])}" style="--accent:#F2C261">
<div class="hero-card-title"><span>🎄 Mancano a Natale <span data-next-year>{nat_d.year}</span></span><a href="/{nat['url']}">Countdown di Natale →</a></div>
{countdown_block(nat['rule'])}
<p class="countdown-today">Buon Natale! 🎄</p>
</div>
</div>
<div class="hero-visual">
<div class="phone" data-phone data-countdown="{js_rule(first['rule'])}" style="{style_vars(first)}">
<div class="phone-screen">
<canvas data-scene="{first['scene']}" data-accent="{first['accent']}" aria-hidden="true"></canvas>
<div class="phone-ui" aria-hidden="true">
<div class="phone-status"><span>9:41</span><span class="island"></span><span class="bars"><i style="height:5px"></i><i style="height:7px"></i><i style="height:9px"></i><i style="height:11px"></i></span></div>
<div class="phone-brand"><img src="/assets/icons/app-64.png" alt="" width="20" height="20">{APP_NAME}</div>
<div class="phone-holiday"><span class="em" data-demo-emoji>{first['emoji']}</span><span data-demo-name>{e(first['name'])}</span></div>
<div class="phone-days" data-u="d">–</div>
<div class="phone-days-lbl">giorni</div>
<div class="phone-hms"><span data-u="h">00</span>:<span data-u="m">00</span>:<span data-u="s">00</span></div>
<div class="phone-bar"><i data-progress></i></div>
<div class="phone-quote"><b>Frase del giorno</b>Tocca per scoprirla ✨</div>
</div>
</div>
</div>
<div class="demo-chips" role="group" aria-label="Prova le feste">
{chips}
</div>
<p class="demo-caption">Tocca una festa per vederla nell'app</p>
</div>
</div>
</section>

<section class="section" id="feste">
<div class="wrap">
<div class="section-head reveal">
<p class="eyebrow"><span class="dot"></span>In ordine di arrivo</p>
<h2>Dieci feste, più la tua</h2>
<p>Quando una festa passa, il conto riparte da capo e la successiva è subito pronta. Tocca una festa per il suo conto alla rovescia, con storia, tradizioni e le date dei prossimi anni.</p>
</div>
<div class="holiday-grid" data-sort>
{cards}
<a class="holiday-card custom" href="#tua-festa">
<span style="font-size:40px;line-height:1;margin-bottom:auto">⭐️</span>
<span class="hc-name">La tua festa</span>
<span class="hc-date">Compleanni, anniversari, partenze</span>
</a>
</div>
</div>
</section>

<section class="section" id="app">
<div class="wrap">
<div class="section-head reveal">
<p class="eyebrow"><span class="dot"></span>Sfondi animati</p>
<h2>Sfondi che si muovono. E che si sentono.</h2>
<p>Più di trenta scene disegnate e animate, che cambiano da sole. Ognuna ha i suoi suoni: il fuoco che scoppietta nel camino, le campanelle della slitta che ti passa sopra la testa, la risata di Babbo Natale, i fuochi di Capodanno, le onde e i gabbiani di Ferragosto. E sotto, la musica delle feste.</p>
</div>
<div class="scene-tiles">
{tiles_html}
</div>
<ul class="chips reveal" aria-label="Alcuni degli sfondi">
{scene_chips}
</ul>
</div>
</section>

<section class="section" id="widget">
<div class="wrap split">
<div class="reveal">
<p class="eyebrow"><span class="dot"></span>Widget</p>
<h2>Sempre sotto gli occhi, anche senza aprire l'app</h2>
<p class="lead">Metti il conto alla rovescia sulla schermata Home o sul blocco schermo, in tre dimensioni e sei temi.</p>
<ul class="checks">
<li><strong>Interattivi:</strong> cambi tema o passi da giorni e ore a settimane e «nanne» con un tocco, direttamente dal widget.</li>
<li><strong>Frase del giorno</strong> anche sul blocco schermo, ogni mattina diversa.</li>
<li><strong>Calendario dell'Avvento</strong> in un widget, con la casella di oggi in evidenza.</li>
</ul>
</div>
<div class="widget-stage reveal" data-countdown="{js_rule(nat['rule'])}">
<div class="wall wall-home" aria-hidden="true">
<div class="home-grid">
<div class="w w-small"><span class="w-name">🎄 Natale</span><span class="w-days" data-days-left>–</span><span class="w-lbl">giorni</span></div>
<div class="app-dot"></div><div class="app-dot"></div><div class="app-dot"></div><div class="app-dot"></div>
<div class="w w-medium"><div><span class="w-name">🎄 Natale</span><div class="w-days" data-days-left>–</div><span class="w-lbl">giorni</span></div><div class="w-right"><div class="w-quote">«E quindi uscimmo a riveder le stelle.»</div><div class="w-bar"><i data-progress></i></div><div class="w-buttons"><span>🎨</span><span>⏱️</span></div></div></div>
<div class="app-dot"></div><div class="app-dot"></div><div class="app-dot"></div><div class="app-dot"></div>
</div>
<span class="wall-title">Schermata Home</span>
</div>
<div class="wall wall-lock" aria-hidden="true">
<div class="date">{long_date(TODAY, year=False).capitalize()}</div>
<div class="time">9:41</div>
<div class="lock-widgets">
<div class="lw lw-circle"><span><b data-days-left>–</b><small>giorni</small></span></div>
<div class="lw lw-rect">🎄 Natale<div class="big"><span data-days-left>–</span> giorni</div><div class="w-bar"><i data-progress></i></div></div>
</div>
<div class="lw lock-quote">«Oggi è sempre ancora.»<br><span style="opacity:.75;font-weight:600">Antonio Machado</span></div>
<span class="wall-title">Blocco schermo</span>
</div>
</div>
</div>
</section>

<section class="section" id="avvento">
<div class="wrap split reverse">
<div class="reveal">
<p class="eyebrow"><span class="dot"></span>Dal 1 al 24 dicembre</p>
<h2>Il calendario dell'Avvento</h2>
<p class="lead">Una casella al giorno, da aprire con un tocco: tradizioni di Natale, idee da fare in famiglia e ricette delle feste.</p>
<ul class="checks">
<li>Ogni casella regala una <strong>decorazione per il tuo albero</strong>, che a Natale diventa uno sfondo tutto tuo da condividere.</li>
<li>Un <strong>promemoria alle 8</strong> ti ricorda di aprire la casella del giorno.</li>
<li>Hai perso un giorno? Le caselle si possono recuperare fino a Natale.</li>
</ul>
</div>
<div class="advent reveal" data-advent aria-label="Esempio di calendario dell'Avvento" role="img">
{doors}
</div>
</div>
</section>

<section class="section" id="frase">
<div class="wrap split">
<div class="reveal">
<p class="eyebrow"><span class="dot"></span>Ogni giorno</p>
<h2>Una frase da scoprire</h2>
<p class="lead">Più di 800 citazioni di 142 grandi autori, da Dante a Emily Dickinson, da Seneca a Pirandello. Sempre con autore e opera, e mai la stessa per due anni.</p>
</div>
<figure class="quote-card reveal" data-quote>
<p class="q-label">La frase di oggi</p>
<blockquote data-q-text style="white-space:pre-line">{e(q0['text'].replace(' / ', chr(10)))}</blockquote>
<figcaption><span data-q-author>{e(q0['author'])}</span><cite data-q-source>{e(q0['source'])}</cite></figcaption>
</figure>
</div>
</section>

<section class="section" id="tua-festa">
<div class="wrap split reverse">
<div class="reveal">
<p class="eyebrow"><span class="dot"></span>Personalizza</p>
<h2>E poi c'è la tua festa</h2>
<p class="lead">Un compleanno, un anniversario, la laurea, le vacanze: dai un nome al tuo giorno, scegli data e orario, icona e colori. Se vuoi, si ripete ogni anno.</p>
<ul class="checks">
<li><strong>Le tue foto come sfondi animati</strong>, fino a 10, oppure un intero album di Foto che si aggiorna da solo.</li>
<li><strong>Dieci icone</strong> per l'app, una per ogni festa.</li>
<li><strong>Sei temi</strong> per i widget, dai colori della festa al rosso Natale.</li>
</ul>
</div>
<div class="reveal" style="display:grid;gap:22px">
<div class="custom-demo"><span class="em">🎂</span><div><div class="t">Compleanno di Giulia</div><div class="d">Ogni anno · 14 marzo</div></div><div class="n" data-days-to="fixed:3:14"><span data-n>–</span><small data-l>giorni</small></div></div>
<div class="icon-row">
{icons}
</div>
</div>
</div>
</section>

<section class="section" id="plus">
<div class="wrap">
<div class="section-head reveal">
<p class="eyebrow"><span class="dot"></span>Prezzi</p>
<h2>Gratis. O tutto, per meno di un euro.</h2>
<p>Niente banner e niente annunci a sorpresa: i video partono solo quando scegli tu di guardarli.</p>
</div>
<div class="plans">
<div class="plan reveal">
<h3>Gratis <span class="price">0 €</span></h3>
<ul class="checks">
<li>Conto alla rovescia, sfondi, suoni, widget e frase del giorno</li>
<li>La <strong>prossima festa</strong> in calendario sempre sbloccata</li>
<li>Le altre feste con un breve video, fino al giorno della festa</li>
<li>Calendario dell'Avvento e la tua festa personalizzata</li>
</ul>
</div>
<div class="plan plus reveal">
<h3>{APP_NAME} Plus <span class="price">0,99 € <small>una volta</small></span></h3>
<ul class="checks">
<li><strong>Niente pubblicità</strong>, mai</li>
<li>Tutte le feste <strong>sempre sbloccate</strong></li>
<li>La tua festa modificabile quando vuoi, anche nella data</li>
<li>Caselle dell'Avvento perse e decorazioni d'oro gratis</li>
<li>Pagamento unico, nessun abbonamento</li>
</ul>
</div>
</div>
</div>
</section>

<section class="section" id="domande">
<div class="wrap">
<div class="section-head reveal"><h2>Domande frequenti</h2></div>
<div class="faq">
{faq_html(faq)}
</div>
</div>
</section>

<section class="section">
<div class="wrap">
<div class="cta-band reveal">
<img src="/assets/icons/natale.png" alt="" width="96" height="96" loading="lazy">
<h2>Il conto alla rovescia comincia adesso</h2>
<p>{APP_NAME} è gratis per iPhone. Natale arriva prima di quanto pensi.</p>
<div class="btn-row">{store_button()}</div>
</div>
</div>
</section>
</main>
<script type="application/json" id="qm-holidays">{json.dumps(demo, ensure_ascii=False)}</script>
<script type="application/json" id="qm-quotes">{quotes_json}</script>
"""
    page += footer()
    write("index.html", page)


# ---------- Pagine delle feste ----------

def holiday_page(h):
    d0 = h["next"][0]
    d1 = h["next"][1]
    name, to, y = h["name"], h["to"], h["year"]
    faq = [
        (f"Quanti giorni mancano {to}?",
         f"{name} {y} cade {long_date(d0, year=False)}. Il conto alla rovescia in cima alla pagina mostra in tempo reale i giorni, le ore, i minuti e i secondi che mancano, calcolati nel tuo fuso orario."),
        (f"Quando cade {name} {d1.year}?",
         f"{name} {d1.year} cade {long_date(d1, year=False)} {d1.year}."),
    ] + list(h["faq"]) + [
        (f"Posso vedere quanto manca {to} sull'iPhone?",
         f"Sì, con l'app gratuita {APP_NAME}: aggiungi il widget alla schermata Home o al blocco schermo e vedi i giorni che mancano {to} senza aprire l'app."),
    ]
    rows = "\n".join(
        f"<tr><td>{d.year}</td><td>{d.day} {MONTHS[d.month - 1]}</td><td>{WEEKDAYS[d.weekday()]}</td></tr>" for d in h["next"][:6])
    story = "\n".join(f"<p>{e(p)}</p>" for p in h["story"])
    others = [o for o in ORDERED if o is not h]
    cards = "\n".join(holiday_card(o) for o in others)

    title = f"Quanto manca {to} {y}? Conto alla rovescia live"
    if len(title) > 60:
        title = f"Quanto manca {to} {y}? Countdown live"
    desc = (f"Quanti giorni mancano {to}? {name} {y} cade {long_date(d0, year=False)}: "
            f"conto alla rovescia live in giorni, ore, minuti e secondi.")
    if len(desc) <= 135:
        desc += " Storia e tradizioni."
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": APP_NAME, "item": BASE},
            {"@type": "ListItem", "position": 2, "name": f"Quanto manca {to}", "item": BASE + h["url"]},
        ],
    }
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": BASE + h["url"],
        "inLanguage": "it-IT",
        "isPartOf": {"@type": "WebSite", "name": APP_NAME, "url": BASE},
    }
    page = head(title, desc, h["url"], h["og"], f"Quanto manca {to}?", [crumbs, webpage, faq_jsonld(faq)])
    page += header("feste")
    page += f"""<main id="contenuto">
<section class="h-hero" style="{style_vars(h)}" data-countdown="{js_rule(h['rule'])}">
<canvas class="scene-bg" data-scene="{h['scene']}" data-accent="{h['accent']}" aria-hidden="true"></canvas>
<div class="wrap h-hero-grid">
<div>
<nav class="breadcrumb" aria-label="Percorso"><a href="/">{APP_NAME}</a><span aria-hidden="true">›</span><span>{e(name)}</span></nav>
<p class="eyebrow">{h['emoji']} Conto alla rovescia</p>
<h1>Quanto manca {e(to)} <span data-next-year>{y}</span>?</h1>
{countdown_block(h['rule'])}
<p class="countdown-today">{e(h['greeting'])} {h['emoji']}</p>
<p class="lead">{e(name)} <span data-next-year>{y}</span> cade <strong data-next-long>{long_date(d0)}</strong>. Il conto alla rovescia si aggiorna in tempo reale nel tuo fuso orario.</p>
</div>
<img class="h-hero-icon" src="/assets/icons/{h['id']}-lg.png" alt="Icona {e(name)} di {APP_NAME}" width="200" height="200">
</div>
</section>
<div class="wrap h-body">
<article class="prose">
<h2>{e(name)}: storia e tradizioni</h2>
{story}
<h2 style="margin-top:1.4em">Domande frequenti</h2>
<div class="faq">
{faq_html(faq)}
</div>
</article>
<aside class="side">
<div class="side-card">
<h2>Quando cade {e(name)}</h2>
<table class="dates">
<thead><tr><th>Anno</th><th>Data</th><th>Giorno</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>
<div class="app-card">
<img src="/{h['icon_src']}" alt="" width="60" height="60" loading="lazy">
<h2>Il countdown {e(to)} sul tuo iPhone</h2>
<p>Con {APP_NAME} hai il conto alla rovescia sempre sotto gli occhi: sfondi animati con i loro suoni, musica delle feste e widget per la Home e il blocco schermo.</p>
<div class="btn-row">{store_button()}</div>
</div>
</aside>
</div>
<section class="section">
<div class="wrap">
<div class="section-head"><h2>Le altre feste</h2><p>Quanto manca alle prossime feste, in ordine di arrivo.</p></div>
<div class="holiday-grid">
{cards}
</div>
</div>
</section>
</main>
"""
    page += footer()
    write(h["url"] + "index.html", page)


# ---------- Supporto, privacy, 404 ----------

SUPPORT_FAQ = [
    ("Perché una festa è bloccata?",
     "Nella versione gratuita la prossima festa in calendario è sempre disponibile. Le altre si sbloccano guardando un breve video, fino al giorno della festa, oppure tutte e per sempre con Quanto Manca Plus. Quando una festa passa, la successiva si sblocca da sola."),
    ("Ho comprato Plus su un altro iPhone.",
     "Apri le Impostazioni dell'app (l'icona in alto a destra) e tocca «Ripristina acquisti», con lo stesso Apple ID usato per l'acquisto."),
    ("Non sento la musica.",
     "Quanto Manca rispetta l'interruttore silenzioso dell'iPhone: disattiva la modalità silenziosa e alza il volume. Musica e suoni si attivano anche dalle impostazioni dell'app."),
    ("Come aggiungo i widget?",
     "Tieni premuto su uno spazio vuoto della schermata Home o del blocco schermo, tocca Modifica › Aggiungi widget e cerca Quanto Manca. Puoi scegliere tra il conto alla rovescia, la frase del giorno e il calendario dell'Avvento."),
    ("Il calendario dell'Avvento è chiuso.",
     "Le caselle si aprono dal 1 al 24 dicembre, una al giorno. Le caselle perse si possono recuperare fino al 25 dicembre."),
    ("Come uso un album di Foto come sfondo?",
     "Crea un album nell'app Foto, per esempio «Sfondi Quanto Manca», poi in Quanto Manca vai in Impostazioni › Le tue foto › Usa un album di Foto. Le foto che aggiungi all'album compaiono da sole."),
    ("Come cambio l'icona dell'app?",
     "In Impostazioni › Personalizza › Icona dell'app trovi dieci icone, una per ogni festa."),
    ("Come cambio le scelte sulla pubblicità?",
     "In Impostazioni › Privacy degli annunci puoi rivedere in qualsiasi momento il consenso dato al primo avvio."),
]


def support():
    page = head("Supporto – Quanto Manca",
                "Assistenza per Quanto Manca: risposte alle domande più frequenti su feste, widget, calendario dell'Avvento, Plus e foto, e contatti del supporto.",
                "supporto.html", "assets/og/home.jpg", "Quanto Manca, supporto", [faq_jsonld(SUPPORT_FAQ)])
    page += header("supporto")
    page += f"""<main id="contenuto" class="page">
<div class="wrap">
<p class="eyebrow"><span class="dot"></span>Supporto</p>
<h1>Come possiamo aiutarti?</h1>
<div class="card">
<p>Hai una domanda, un problema o un'idea per {APP_NAME}? Scrivici a <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>: di solito rispondiamo entro due giorni. Se puoi, indica il modello di iPhone e la versione di iOS.</p>
</div>
<h2>Domande frequenti</h2>
<div class="faq">
{faq_html(SUPPORT_FAQ)}
</div>
</div>
</main>
"""
    page += footer()
    write("supporto.html", page)


def privacy():
    page = head("Informativa sulla privacy – Quanto Manca",
                "Come Quanto Manca tratta i dati: cosa resta sul tuo iPhone, come funzionano la pubblicità di Google AdMob e gli acquisti, e quali sono i tuoi diritti.",
                "privacy.html", "assets/og/home.jpg", "Quanto Manca, privacy", [])
    page += header()
    page += f"""<main id="contenuto" class="page">
<div class="wrap">
<p class="eyebrow"><span class="dot"></span>Privacy</p>
<h1>Informativa sulla privacy</h1>
<p class="updated">Ultimo aggiornamento: 3 novembre 2026</p>

<div class="card">
<p>{APP_NAME} è un'app per iPhone sviluppata da {AUTHOR} (di seguito «noi»). Questa informativa spiega quali dati vengono trattati quando usi l'app e come puoi esercitare i tuoi diritti ai sensi del Regolamento (UE) 2016/679 (GDPR).</p>
</div>

<h2>Dati che restano sul tuo iPhone</h2>
<p>La festa scelta, la festa personalizzata, i progressi del calendario dell'Avvento, le impostazioni e le foto che scegli come sfondo vengono salvati solo sul tuo dispositivo. Non li riceviamo e non li inviamo a nessuno.</p>
<ul>
<li><strong>Foto:</strong> se scegli una foto o un album di Foto come sfondo, l'app legge quelle immagini solo per mostrarle sul tuo schermo. Le immagini non lasciano il dispositivo.</li>
<li><strong>Notifiche:</strong> i promemoria del calendario dell'Avvento sono notifiche locali, programmate sul tuo iPhone.</li>
</ul>

<h2>Pubblicità (Google AdMob)</h2>
<p>La versione gratuita mostra video pubblicitari facoltativi tramite Google AdMob, un servizio di Google Ireland Limited. Per mostrare gli annunci, misurarne l'efficacia e prevenire frodi, Google può raccogliere: identificatori del dispositivo, posizione approssimativa (dedotta dall'indirizzo IP), interazioni con gli annunci, dati di diagnostica e prestazioni.</p>
<p>Al primo avvio, nello Spazio economico europeo e nel Regno Unito, l'app ti chiede il consenso tramite la piattaforma di gestione del consenso di Google. Puoi cambiare scelta in qualsiasi momento da Impostazioni › Privacy degli annunci. {APP_NAME} non chiede il permesso di tracciamento di Apple: gli annunci non usano l'identificatore pubblicitario per tracciarti tra app e siti di altre aziende.</p>
<p>Come Google tratta i dati: <a href="https://policies.google.com/technologies/partner-sites">policies.google.com/technologies/partner-sites</a> e <a href="https://policies.google.com/privacy">policies.google.com/privacy</a>.</p>

<h2>Acquisti ({APP_NAME} Plus)</h2>
<p>Gli acquisti in-app sono gestiti interamente da Apple. Non riceviamo i tuoi dati di pagamento; Apple ci comunica solo che l'acquisto è valido.</p>

<h2>Questo sito</h2>
<p>Il sito è ospitato da GitHub Pages (GitHub, Inc.), che può registrare dati tecnici come l'indirizzo IP per motivi di sicurezza. Il sito non usa cookie, strumenti di analisi né caratteri o script di altri servizi.</p>

<h2>Minori</h2>
<p>{APP_NAME} è adatta a tutti ma non è rivolta specificamente ai bambini.</p>

<h2>Base giuridica e conservazione</h2>
<p>Il trattamento dei dati per la pubblicità si basa sul tuo consenso, che puoi revocare in qualsiasi momento. Noi non conserviamo dati personali; per i dati raccolti da Google valgono i tempi indicati nelle sue norme.</p>

<h2>I tuoi diritti</h2>
<p>Puoi chiedere accesso, rettifica, cancellazione, limitazione od opposizione al trattamento, e proporre reclamo al Garante per la protezione dei dati personali (<a href="https://www.garanteprivacy.it">garanteprivacy.it</a>). Per qualsiasi richiesta scrivi a <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>.</p>

<h2>Modifiche</h2>
<p>Se cambiamo questa informativa aggiorniamo la data in alto. Le modifiche importanti verranno segnalate anche nell'app.</p>
</div>
</main>
"""
    page += footer()
    write("privacy.html", page)


def not_found():
    cards = "\n".join(holiday_card(h, i == 0) for i, h in enumerate(ORDERED[:4]))
    page = head("Pagina non trovata – Quanto Manca", "Questa pagina non esiste. Torna al conto alla rovescia per le tue feste.",
                "404.html", "assets/og/home.jpg", APP_NAME, [], '\n<meta name="robots" content="noindex">')
    page = page.replace('<meta name="robots" content="index, follow, max-image-preview:large">\n', "")
    page += header()
    page += f"""<main id="contenuto" class="page">
<div class="wrap" style="max-width:var(--wrap)">
<p class="eyebrow"><span class="dot"></span>Errore 404</p>
<h1>Questa pagina non c'è più</h1>
<p class="lead">Ma le feste non scappano. Torna alla <a href="/">pagina iniziale</a> o scegli il prossimo conto alla rovescia.</p>
<div class="holiday-grid" style="margin-top:30px">
{cards}
</div>
</div>
</main>
"""
    page += footer()
    write("404.html", page)


def extras():
    urls = [""] + [h["url"] for h in ORDERED] + ["supporto.html", "privacy.html"]
    body = "\n".join(f"<url><loc>{BASE}{u}</loc></url>" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n")
    manifest = {
        "name": APP_NAME, "short_name": APP_NAME, "lang": "it", "start_url": "/", "display": "standalone",
        "background_color": "#050A1C", "theme_color": "#0A1433",
        "icons": [{"src": "/assets/icons/app-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/assets/icons/app-512.png", "sizes": "512x512", "type": "image/png"}],
    }
    write("site.webmanifest", json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    write(".nojekyll", "")
    # Elenco per lo script delle immagini di condivisione.
    spec = [{"id": "home", "title": "Quanto manca\nalle tue feste?", "colors": CHRISTMAS["colors"], "accent": CHRISTMAS["accent"], "icon": "Default"}]
    spec += [{"id": h["id"], "title": f"Quanto manca\n{h['to']}?", "colors": h["colors"], "accent": h["accent"], "icon": h["icon"]} for h in HOLIDAYS]
    write("_build/og_spec.json", json.dumps(spec, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    home()
    for h in HOLIDAYS:
        holiday_page(h)
    support()
    privacy()
    not_found()
    extras()
