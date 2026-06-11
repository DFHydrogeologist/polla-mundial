#!/usr/bin/env python3
"""
Rellena resultados.json con los marcadores reales de la fase de grupos del Mundial 2026.
Lo ejecuta automáticamente el GitHub Action; nadie edita resultados a mano.

Proveedor configurable por variable de entorno POLLA_PROVIDER:
  - "apifootball"   -> API-Football (api-sports.io). Requiere APIFOOTBALL_KEY.
  - "footballdata"  -> football-data.org.            Requiere FOOTBALLDATA_TOKEN.

Solo se cargan partidos FINALIZADOS (no marcadores en vivo), para que el ranking sea estable.
"""
import os, sys, json, unicodedata, datetime, urllib.request

PROVIDER = os.environ.get("POLLA_PROVIDER", "apifootball").lower()
OUT = os.path.join(os.path.dirname(__file__), "..", "resultados.json")

FIXTURE = [
  {
    "grupo": "A",
    "local": "México",
    "visitante": "Sudáfrica"
  },
  {
    "grupo": "A",
    "local": "Corea del Sur",
    "visitante": "Chequia"
  },
  {
    "grupo": "A",
    "local": "Chequia",
    "visitante": "Sudáfrica"
  },
  {
    "grupo": "A",
    "local": "México",
    "visitante": "Corea del Sur"
  },
  {
    "grupo": "A",
    "local": "Chequia",
    "visitante": "México"
  },
  {
    "grupo": "A",
    "local": "Sudáfrica",
    "visitante": "Corea del Sur"
  },
  {
    "grupo": "B",
    "local": "Canadá",
    "visitante": "Bosnia y Herzegovina"
  },
  {
    "grupo": "B",
    "local": "Qatar",
    "visitante": "Suiza"
  },
  {
    "grupo": "B",
    "local": "Suiza",
    "visitante": "Bosnia y Herzegovina"
  },
  {
    "grupo": "B",
    "local": "Canadá",
    "visitante": "Qatar"
  },
  {
    "grupo": "B",
    "local": "Suiza",
    "visitante": "Canadá"
  },
  {
    "grupo": "B",
    "local": "Bosnia y Herzegovina",
    "visitante": "Qatar"
  },
  {
    "grupo": "C",
    "local": "Brasil",
    "visitante": "Marruecos"
  },
  {
    "grupo": "C",
    "local": "Haití",
    "visitante": "Escocia"
  },
  {
    "grupo": "C",
    "local": "Escocia",
    "visitante": "Marruecos"
  },
  {
    "grupo": "C",
    "local": "Brasil",
    "visitante": "Haití"
  },
  {
    "grupo": "C",
    "local": "Escocia",
    "visitante": "Brasil"
  },
  {
    "grupo": "C",
    "local": "Marruecos",
    "visitante": "Haití"
  },
  {
    "grupo": "D",
    "local": "Estados Unidos",
    "visitante": "Paraguay"
  },
  {
    "grupo": "D",
    "local": "Australia",
    "visitante": "Turquía"
  },
  {
    "grupo": "D",
    "local": "Estados Unidos",
    "visitante": "Australia"
  },
  {
    "grupo": "D",
    "local": "Turquía",
    "visitante": "Paraguay"
  },
  {
    "grupo": "D",
    "local": "Turquía",
    "visitante": "Estados Unidos"
  },
  {
    "grupo": "D",
    "local": "Paraguay",
    "visitante": "Australia"
  },
  {
    "grupo": "E",
    "local": "Alemania",
    "visitante": "Curazao"
  },
  {
    "grupo": "E",
    "local": "Costa de Marfil",
    "visitante": "Ecuador"
  },
  {
    "grupo": "E",
    "local": "Alemania",
    "visitante": "Costa de Marfil"
  },
  {
    "grupo": "E",
    "local": "Ecuador",
    "visitante": "Curazao"
  },
  {
    "grupo": "E",
    "local": "Ecuador",
    "visitante": "Alemania"
  },
  {
    "grupo": "E",
    "local": "Curazao",
    "visitante": "Costa de Marfil"
  },
  {
    "grupo": "F",
    "local": "Países Bajos",
    "visitante": "Japón"
  },
  {
    "grupo": "F",
    "local": "Suecia",
    "visitante": "Túnez"
  },
  {
    "grupo": "F",
    "local": "Países Bajos",
    "visitante": "Suecia"
  },
  {
    "grupo": "F",
    "local": "Túnez",
    "visitante": "Japón"
  },
  {
    "grupo": "F",
    "local": "Japón",
    "visitante": "Suecia"
  },
  {
    "grupo": "F",
    "local": "Túnez",
    "visitante": "Países Bajos"
  },
  {
    "grupo": "G",
    "local": "Bélgica",
    "visitante": "Egipto"
  },
  {
    "grupo": "G",
    "local": "Irán",
    "visitante": "Nueva Zelanda"
  },
  {
    "grupo": "G",
    "local": "Bélgica",
    "visitante": "Irán"
  },
  {
    "grupo": "G",
    "local": "Nueva Zelanda",
    "visitante": "Egipto"
  },
  {
    "grupo": "G",
    "local": "Egipto",
    "visitante": "Irán"
  },
  {
    "grupo": "G",
    "local": "Nueva Zelanda",
    "visitante": "Bélgica"
  },
  {
    "grupo": "H",
    "local": "España",
    "visitante": "Cabo Verde"
  },
  {
    "grupo": "H",
    "local": "Arabia Saudita",
    "visitante": "Uruguay"
  },
  {
    "grupo": "H",
    "local": "España",
    "visitante": "Arabia Saudita"
  },
  {
    "grupo": "H",
    "local": "Uruguay",
    "visitante": "Cabo Verde"
  },
  {
    "grupo": "H",
    "local": "Cabo Verde",
    "visitante": "Arabia Saudita"
  },
  {
    "grupo": "H",
    "local": "Uruguay",
    "visitante": "España"
  },
  {
    "grupo": "I",
    "local": "Francia",
    "visitante": "Senegal"
  },
  {
    "grupo": "I",
    "local": "Iraq",
    "visitante": "Noruega"
  },
  {
    "grupo": "I",
    "local": "Francia",
    "visitante": "Iraq"
  },
  {
    "grupo": "I",
    "local": "Noruega",
    "visitante": "Senegal"
  },
  {
    "grupo": "I",
    "local": "Noruega",
    "visitante": "Francia"
  },
  {
    "grupo": "I",
    "local": "Senegal",
    "visitante": "Iraq"
  },
  {
    "grupo": "J",
    "local": "Argentina",
    "visitante": "Argelia"
  },
  {
    "grupo": "J",
    "local": "Austria",
    "visitante": "Jordania"
  },
  {
    "grupo": "J",
    "local": "Argentina",
    "visitante": "Austria"
  },
  {
    "grupo": "J",
    "local": "Jordania",
    "visitante": "Argelia"
  },
  {
    "grupo": "J",
    "local": "Argelia",
    "visitante": "Austria"
  },
  {
    "grupo": "J",
    "local": "Jordania",
    "visitante": "Argentina"
  },
  {
    "grupo": "K",
    "local": "Portugal",
    "visitante": "DR Congo"
  },
  {
    "grupo": "K",
    "local": "Uzbekistán",
    "visitante": "Colombia"
  },
  {
    "grupo": "K",
    "local": "Portugal",
    "visitante": "Uzbekistán"
  },
  {
    "grupo": "K",
    "local": "Colombia",
    "visitante": "DR Congo"
  },
  {
    "grupo": "K",
    "local": "Colombia",
    "visitante": "Portugal"
  },
  {
    "grupo": "K",
    "local": "DR Congo",
    "visitante": "Uzbekistán"
  },
  {
    "grupo": "L",
    "local": "Inglaterra",
    "visitante": "Croacia"
  },
  {
    "grupo": "L",
    "local": "Ghana",
    "visitante": "Panamá"
  },
  {
    "grupo": "L",
    "local": "Inglaterra",
    "visitante": "Ghana"
  },
  {
    "grupo": "L",
    "local": "Panamá",
    "visitante": "Croacia"
  },
  {
    "grupo": "L",
    "local": "Panamá",
    "visitante": "Inglaterra"
  },
  {
    "grupo": "L",
    "local": "Croacia",
    "visitante": "Ghana"
  }
]

ALIASES = {
  "México": [
    "Mexico"
  ],
  "Sudáfrica": [
    "South Africa"
  ],
  "Corea del Sur": [
    "South Korea",
    "Korea Republic"
  ],
  "Chequia": [
    "Czech Republic",
    "Czechia",
    "Czech-Republic"
  ],
  "Canadá": [
    "Canada"
  ],
  "Suiza": [
    "Switzerland"
  ],
  "Qatar": [
    "Qatar",
    "Catar"
  ],
  "Bosnia y Herzegovina": [
    "Bosnia and Herzegovina",
    "Bosnia & Herzegovina",
    "Bosnia"
  ],
  "Brasil": [
    "Brazil"
  ],
  "Marruecos": [
    "Morocco"
  ],
  "Haití": [
    "Haiti"
  ],
  "Escocia": [
    "Scotland"
  ],
  "Estados Unidos": [
    "USA",
    "United States",
    "United States of America"
  ],
  "Paraguay": [
    "Paraguay"
  ],
  "Australia": [
    "Australia"
  ],
  "Turquía": [
    "Turkey",
    "Turkiye",
    "Türkiye"
  ],
  "Alemania": [
    "Germany"
  ],
  "Curazao": [
    "Curacao",
    "Curaçao"
  ],
  "Costa de Marfil": [
    "Ivory Coast",
    "Cote d'Ivoire",
    "Côte d'Ivoire"
  ],
  "Ecuador": [
    "Ecuador"
  ],
  "Países Bajos": [
    "Netherlands",
    "Holland"
  ],
  "Japón": [
    "Japan"
  ],
  "Túnez": [
    "Tunisia"
  ],
  "Suecia": [
    "Sweden"
  ],
  "Bélgica": [
    "Belgium"
  ],
  "Egipto": [
    "Egypt"
  ],
  "Irán": [
    "Iran",
    "Iran, Islamic Republic of"
  ],
  "Nueva Zelanda": [
    "New Zealand"
  ],
  "España": [
    "Spain"
  ],
  "Cabo Verde": [
    "Cape Verde Islands",
    "Cape Verde",
    "Cabo Verde"
  ],
  "Arabia Saudita": [
    "Saudi Arabia"
  ],
  "Uruguay": [
    "Uruguay"
  ],
  "Francia": [
    "France"
  ],
  "Senegal": [
    "Senegal"
  ],
  "Noruega": [
    "Norway"
  ],
  "Iraq": [
    "Iraq",
    "Iraq Republic"
  ],
  "Argentina": [
    "Argentina"
  ],
  "Argelia": [
    "Algeria"
  ],
  "Austria": [
    "Austria"
  ],
  "Jordania": [
    "Jordan"
  ],
  "Portugal": [
    "Portugal"
  ],
  "Colombia": [
    "Colombia"
  ],
  "Uzbekistán": [
    "Uzbekistan"
  ],
  "DR Congo": [
    "DR Congo",
    "Congo DR",
    "Democratic Republic of Congo",
    "DR-Congo"
  ],
  "Inglaterra": [
    "England"
  ],
  "Croacia": [
    "Croatia"
  ],
  "Ghana": [
    "Ghana"
  ],
  "Panamá": [
    "Panama"
  ]
}

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii","ignore").decode()
    return "".join(c for c in s.lower() if c.isalnum())

# nombre-normalizado (cualquier alias o el propio ES) -> nombre ES canónico
LOOKUP = {}
for es, al in ALIASES.items():
    for name in [es] + al:
        LOOKUP[norm(name)] = es

# alias extra para variantes que usan ESPN / football-data
EXTRA = {
 "Corea del Sur":["Korea Republic","Korea, South"],
 "Bosnia y Herzegovina":["Bosnia-Herzegovina","Bosnia Herzegovina"],
 "Irán":["IR Iran"], "Estados Unidos":["United States"],
 "Costa de Marfil":["Cote dIvoire","Ivory Coast"], "Curazao":["Curacao"],
 "Chequia":["Czechia"], "Cabo Verde":["Cabo Verde","Cape Verde"],
 "Turquía":["Turkiye","Turkey"], "DR Congo":["Congo DR","DR Congo","Congo RD","Democratic Republic of Congo","RD Congo"],
}
for es, al in EXTRA.items():
    for name in al:
        LOOKUP[norm(name)] = es

def to_es(api_name):
    return LOOKUP.get(norm(api_name))

def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())

def _ventana_dias(antes=3, despues=1, fmt="%Y-%m-%d"):
    hoy = datetime.datetime.now(datetime.timezone.utc).date()
    return ((hoy - datetime.timedelta(days=antes)).strftime(fmt),
            (hoy + datetime.timedelta(days=despues)).strftime(fmt))

def fetch_espn():
    # ESPN: público, sin key, suele traer marcadores al instante.
    d1, d2 = _ventana_dias(fmt="%Y%m%d")
    url = (f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/"
           f"scoreboard?dates={d1}-{d2}&limit=200")
    data = http_get(url)
    events = data.get("events", []) or []
    print(f"[diag] ESPN · ventana {d1}-{d2} · eventos recibidos: {len(events)}")
    out = []
    for ev in events:
        comp = (ev.get("competitions") or [{}])[0]
        done = (((ev.get("status") or {}).get("type") or {}).get("completed")) is True
        if not done:
            continue
        home = away = None; gh = ga = None
        for c in comp.get("competitors", []):
            nm = (c.get("team") or {}).get("displayName") or (c.get("team") or {}).get("name")
            sc = c.get("score")
            try: sc = int(sc)
            except (TypeError, ValueError): sc = None
            if c.get("homeAway") == "home": home, gh = nm, sc
            elif c.get("homeAway") == "away": away, ga = nm, sc
        if home and away and gh is not None and ga is not None:
            out.append((home, away, gh, ga))
    print(f"[diag] ESPN · finalizados con marcador: {len(out)}")
    return out

def fetch_apifootball():
    key = os.environ["APIFOOTBALL_KEY"]
    url = "https://v3.football.api-sports.io/fixtures?league=1&season=2026"
    data = http_get(url, {"x-apisports-key": key})
    resp = data.get("response", []) or []
    errs = data.get("errors")
    print(f"[diag] API-Football · fixtures recibidos: {len(resp)} · results={data.get('results')} · errors={errs}")
    if errs:   # API-Football devuelve errores aquí (key inválida, plan sin esta liga, etc.)
        print("[diag] >>> La API devolvió un error. Revisa la key o si tu plan incluye el Mundial (league=1).")
    out = []
    for it in resp:
        st = (it.get("fixture",{}).get("status",{}) or {}).get("short","")
        if st not in ("FT","AET","PEN"):     # solo finalizados
            continue
        h = it["teams"]["home"]["name"]; a = it["teams"]["away"]["name"]
        gh = it["goals"]["home"]; ga = it["goals"]["away"]
        if gh is None or ga is None: continue
        out.append((h, a, int(gh), int(ga)))
    print(f"[diag] de esos, finalizados con marcador: {len(out)}")
    return out

def fetch_footballdata():
    tok = os.environ["FOOTBALLDATA_TOKEN"]
    # /v4/matches sin fecha devuelve solo el día actual (UTC). Pedimos una ventana
    # de varios días para no perder partidos según el huso horario. El merge en main()
    # acumula, así que esta ventana móvil + las corridas cada 30 min cubren todo.
    hoy = datetime.datetime.now(datetime.timezone.utc).date()
    desde = (hoy - datetime.timedelta(days=3)).isoformat()
    hasta = (hoy + datetime.timedelta(days=1)).isoformat()
    url = (f"https://api.football-data.org/v4/matches"
           f"?dateFrom={desde}&dateTo={hasta}&status=FINISHED")
    data = http_get(url, {"X-Auth-Token": tok})
    matches = data.get("matches", []) or []
    print(f"[diag] football-data.org · ventana {desde}..{hasta} · FINISHED recibidos: {len(matches)}")
    # detalle de lo que llega (para ver competencia, equipos y marcador)
    for m in matches[:40]:
        comp = (m.get("competition") or {}).get("code") or (m.get("competition") or {}).get("name","?")
        ft = m.get("score",{}).get("fullTime",{})
        print(f"[diag]   [{comp}] {m['homeTeam'].get('name')} {ft.get('home')}-{ft.get('away')} {m['awayTeam'].get('name')}")
    out = []
    for m in matches:
        h = m["homeTeam"]["name"]; a = m["awayTeam"]["name"]
        ft = m.get("score",{}).get("fullTime",{})
        gh, ga = ft.get("home"), ft.get("away")
        if gh is None or ga is None: continue
        out.append((h, a, int(gh), int(ga)))
    print(f"[diag] de esos, con marcador válido: {len(out)}")
    return out

def main():
    # Fuentes a intentar, en orden de prioridad. La primera que entregue un
    # marcador válido para un partido, gana. ESPN va primero (gratis y rápido).
    fuentes = [("ESPN", fetch_espn)]
    if os.environ.get("FOOTBALLDATA_TOKEN"):
        fuentes.append(("football-data.org", fetch_footballdata))
    if os.environ.get("APIFOOTBALL_KEY"):
        fuentes.append(("API-Football", fetch_apifootball))

    by_pair = {}            # (local_es, visitante_es) -> (gl, gv)
    fuente_de = {}          # (local_es, visitante_es) -> nombre de la fuente que lo aportó
    unmatched = []
    aportes = {}            # cuántos partidos aportó cada fuente

    for nombre, fn in fuentes:
        try:
            results = fn()
        except Exception as e:
            print(f"[diag] {nombre} falló: {e}")
            continue
        n = 0
        for h, a, gh, ga in results:
            eh, ea = to_es(h), to_es(a)
            if not eh or not ea:
                unmatched.append((nombre, h, a)); continue
            if (eh, ea) in by_pair:        # ya lo aportó una fuente de mayor prioridad
                continue
            by_pair[(eh, ea)] = (gh, ga)
            by_pair[(ea, eh)] = (ga, gh)   # por si la fuente invierte local/visitante
            fuente_de[(eh, ea)] = nombre
            n += 1
        aportes[nombre] = n

    # Partir del resultados.json existente para NO perder partidos de días previos
    prev = [[None, None] for _ in FIXTURE]
    try:
        with open(OUT, encoding="utf-8") as fp:
            old = json.load(fp)
        oa = old.get("real") if isinstance(old, dict) else old
        if isinstance(oa, list) and len(oa) == len(FIXTURE):
            prev = [[x[0] if x and x[0] is not None else None,
                     x[1] if x and x[1] is not None else None] for x in oa]
    except Exception:
        pass

    real = []; nuevos = 0; total_con_dato = 0
    for i, f in enumerate(FIXTURE):
        key = (f["local"], f["visitante"])
        if key in by_pair:
            gl, gv = by_pair[key]
            if prev[i][0] is None and prev[i][1] is None:
                nuevos += 1
                print(f"[diag] NUEVO: {f['local']} {gl}-{gv} {f['visitante']}  (fuente: {fuente_de.get(key,'?')})")
            real.append([gl, gv])
        else:
            real.append(prev[i])
        if real[i][0] is not None and real[i][1] is not None:
            total_con_dato += 1

    activas = [n for n in aportes]
    payload = {
        "source": " + ".join(activas) if activas else "sin fuente",
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "real": real,
    }
    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=0)

    print("[resumen] aportes por fuente:", {k:v for k,v in aportes.items()})
    print(f"[resumen] nuevos cargados ahora: {nuevos} · total en la polla: {total_con_dato}/72")
    if unmatched:
        print("OJO, equipos sin mapear (revisa ALIASES/EXTRA):")
        for src,h,a in unmatched[:20]: print(f"  - [{src}] {h} vs {a}")

if __name__ == "__main__":
    main()
