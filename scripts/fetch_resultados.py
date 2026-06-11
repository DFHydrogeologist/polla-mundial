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

def to_es(api_name):
    return LOOKUP.get(norm(api_name))

def http_get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())

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
    # El plan gratis a veces no expone la competencia WC, pero sí lista los partidos
    # en el endpoint general /matches. Pedimos todos los FINISHED y luego el filtrado
    # por nombres de equipo (mapeo del fixture) se queda solo con los del Mundial.
    url = "https://api.football-data.org/v4/matches?status=FINISHED"
    data = http_get(url, {"X-Auth-Token": tok})
    matches = data.get("matches", []) or []
    print(f"[diag] football-data.org · partidos FINISHED recibidos (todas las competencias): {len(matches)}")
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
    fetch = {"apifootball":fetch_apifootball, "footballdata":fetch_footballdata}.get(PROVIDER)
    if not fetch:
        print("POLLA_PROVIDER inválido:", PROVIDER); sys.exit(1)

    results = fetch()
    # índice por par (local_es, visitante_es) -> (gl, gv)
    by_pair = {}
    unmatched = []
    for h, a, gh, ga in results:
        eh, ea = to_es(h), to_es(a)
        if not eh or not ea:
            unmatched.append((h, a)); continue
        by_pair[(eh, ea)] = (gh, ga)
        by_pair[(ea, eh)] = (ga, gh)   # por si la API invierte local/visitante

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

    real = []
    nuevos = 0
    total_con_dato = 0
    for i, f in enumerate(FIXTURE):
        key = (f["local"], f["visitante"])
        if key in by_pair:                       # resultado fresco desde la API
            gl, gv = by_pair[key]
            if prev[i][0] is None and prev[i][1] is None:
                nuevos += 1
            real.append([gl, gv])
        else:                                    # no vino ahora: conservar lo guardado
            real.append(prev[i])
        if real[i][0] is not None and real[i][1] is not None:
            total_con_dato += 1

    payload = {
        "source": "API-Football" if PROVIDER=="apifootball" else "football-data.org",
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "real": real,
    }
    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=0)

    print(f"[{PROVIDER}] partidos del Mundial mapeados ahora: {len(by_pair)//2} · nuevos cargados: {nuevos} · total en la polla: {total_con_dato}/72")
    if unmatched:
        print("OJO, equipos sin mapear (revisa ALIASES):")
        for h,a in unmatched: print("  -", h, "vs", a)

if __name__ == "__main__":
    main()
