#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lee el Google Sheets de la polla (fase de llaves) y arma pronosticos_llaves.json.

Estructura del Sheets:
  - Pestaña "Llaves": la fuente única. Columnas:
        Ronda | Cruce | Local | GL | GV | Visitante | Pasa
    Acá Diego mete a mano los RESULTADOS REALES (GL/GV/Pasa) a medida que se juegan,
    y los equipos Local/Visitante a medida que se definen los cruces.
  - Una pestaña por persona (nombre = nombre de la pestaña). Mismas columnas, pero
    Ronda/Cruce/Local/Visitante vienen por fórmula desde Llaves (=Llaves!A2, etc.)
    y la persona solo edita GL/GV/Pasa (su pronóstico).

Lógica de congelado (freeze) por RONDA:
  - Ronda ABIERTA (aún no llega su deadline): se lee del Sheets en cada corrida.
  - Ronda CERRADA (ya pasó el deadline): se conserva lo que quedó congelado en el
    JSON de la corrida anterior. Aunque alguien edite el Sheets después, no entra.

Solo usa la librería estándar. Corre local con:  python leer_apuestas.py
"""

import os, sys, json, csv, io, unicodedata, datetime, urllib.request, urllib.parse

# ─────────────────────────── CONFIG (ajusta esto) ───────────────────────────

# ID del Google Sheets (lo que va entre /d/ y /edit en la URL del Sheets)
SHEET_ID = os.environ.get("POLLA_SHEET_ID", "1y6omPkb9NWIfSITMSJKmzXF4AIAo5oevW6t9DfDn_bc")

# Nombre EXACTO de la pestaña fuente (la de los 32 cruces). Si no es "Llaves", cámbialo.
LLAVES_TAB = "Llaves"

# Nombres EXACTOS de las pestañas de cada persona (= nombre del participante).
# Si tienen tilde funciona igual (se url-encodea), pero sin tilde es más a prueba de tontos.
PERSONAS = os.environ.get("POLLA_PERSONAS", "Demian,Jano,Nacho,Pelao,Raul,Jlo,Paula,Six,Chapa,Bob,Claudia,Chorero").split(",")

# Deadlines por ronda (UTC). Pon ~30 min antes del primer partido de cada ronda.
# Mundial 2026: R32 arranca 28-jun, final 19-jul. Ajusta las horas a los kickoffs reales.
DEADLINES = {
    "rondade32":   datetime.datetime(2026, 6, 29, 15, 30, tzinfo=datetime.timezone.utc),  # mañana 11:30 Chile
    "rondade32e":  datetime.datetime(2026, 6, 28, 18,  30, tzinfo=datetime.timezone.utc),  # hoy 14:00 Chile, inicio del partido
    "octavos":     datetime.datetime(2026, 7,  4, 18, 0, tzinfo=datetime.timezone.utc),
    "cuartos":     datetime.datetime(2026, 7,  9, 18, 0, tzinfo=datetime.timezone.utc),
    "semifinal":   datetime.datetime(2026, 7, 14, 18, 0, tzinfo=datetime.timezone.utc),
    "3erpuesto":   datetime.datetime(2026, 7, 18, 18, 0, tzinfo=datetime.timezone.utc),
    "final":       datetime.datetime(2026, 7, 19, 18, 0, tzinfo=datetime.timezone.utc),
}

# Sube un nivel desde scripts/ y deja el JSON en la raíz del repo (donde lo lee index.html),
# misma convención que fetch_resultados.py.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pronosticos_llaves.json")

# ─────────────────────────── helpers ───────────────────────────

def norm(s):
    """minúsculas, sin tildes, sin espacios ni signos. Para comparar nombres de ronda/columnas."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return "".join(c for c in s.lower() if c.isalnum())

def to_int(x):
    """'2' -> 2 ; '' / None / basura -> None"""
    if x is None:
        return None
    x = str(x).strip()
    if x == "":
        return None
    try:
        return int(float(x))   # tolera "2" y "2.0"
    except ValueError:
        return None

def clean(x):
    return str(x).strip() if x is not None else ""

# columnas esperadas -> clave interna (se mapean por encabezado, así no importa el orden)
COLMAP = {
    "ronda": "ronda", "cruce": "cruce",
    "local": "local", "gl": "gl", "gv": "gv",
    "visitante": "visita", "visita": "visita",
    "pasa": "pasa", "quienavanza": "pasa", "avanza": "pasa",
}

def parse_csv_text(text):
    """CSV (texto) -> lista de dicts con claves internas (ronda, cruce, local, gl, gv, visita, pasa)."""
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []
    header = [norm(h) for h in rows[0]]
    idx = {}
    for j, h in enumerate(header):
        if h in COLMAP:
            idx[COLMAP[h]] = j
    out = []
    for r in rows[1:]:
        def get(key):
            j = idx.get(key)
            return r[j] if (j is not None and j < len(r)) else ""
        # fila vacía completa -> la saltamos
        if not any(clean(get(k)) for k in ("ronda", "cruce", "local", "gl", "gv", "visita", "pasa")):
            continue
        out.append({
            "ronda":  clean(get("ronda")),
            "cruce":  clean(get("cruce")),
            "local":  clean(get("local")),
            "gl":     to_int(get("gl")),
            "gv":     to_int(get("gv")),
            "visita": clean(get("visita")),
            "pasa":   clean(get("pasa")),
        })
    return out

def fetch_csv(tab):
    """Baja una pestaña del Sheets como CSV vía gviz. Devuelve lista de dicts."""
    url = (f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
           f"?tqx=out:csv&sheet={urllib.parse.quote(tab)}")
    req = urllib.request.Request(url, headers={"User-Agent": "polla-bot"})
    with urllib.request.urlopen(req, timeout=40) as r:
        text = r.read().decode("utf-8")
    return parse_csv_text(text)

def avance_real(local, visita, gl, gv, pasa_celda):
    """Avance REAL (objetivo): gana el del marcador; si hay empate a los 90, lo que
    pongas en la celda Pasa de Resultados (penales). No se sobreescribe un ganador claro."""
    if gl is None or gv is None:
        return clean(pasa_celda) or None
    if gl > gv:
        return local
    if gv > gl:
        return visita
    return clean(pasa_celda) or None     # empate -> manda la celda (penales)

def avance_pred(local, visita, gl, gv, pasa_celda):
    """Avance de un PRONÓSTICO: la columna Pasa manda SIEMPRE, aunque contradiga el marcador
    (algunos apuestan 'pierde pero igual avanza'). Si Pasa está vacía, respaldo: ganador del
    marcador, o None si la persona predijo empate sin indicar quién pasa."""
    p = clean(pasa_celda)
    if p:
        return p
    if gl is None or gv is None:
        return None
    if gl > gv:
        return local
    if gv > gl:
        return visita
    return None

# ───────────── ESPN: resultados reales de llaves (para PERSISTIRLOS) ─────────────
# Traducción nombre-ESPN (inglés/variantes) -> nombre canónico en español del Sheet.
ALIASES = {
  "México":["Mexico"], "Sudáfrica":["South Africa"], "Corea del Sur":["South Korea","Korea Republic","Korea, South"],
  "Chequia":["Czech Republic","Czechia"], "Canadá":["Canada"], "Suiza":["Switzerland"], "Qatar":["Qatar","Catar"],
  "Bosnia y Herzegovina":["Bosnia and Herzegovina","Bosnia & Herzegovina","Bosnia","Bosnia-Herzegovina"],
  "Brasil":["Brazil"], "Marruecos":["Morocco"], "Haití":["Haiti"], "Escocia":["Scotland"],
  "Estados Unidos":["USA","United States","United States of America"], "Paraguay":["Paraguay"], "Australia":["Australia"],
  "Turquía":["Turkey","Turkiye","Türkiye"], "Alemania":["Germany"], "Curazao":["Curacao","Curaçao"],
  "Costa de Marfil":["Ivory Coast","Cote d'Ivoire","Côte d'Ivoire","Cote dIvoire"], "Ecuador":["Ecuador"],
  "Países Bajos":["Netherlands","Holland"], "Japón":["Japan"], "Túnez":["Tunisia"], "Suecia":["Sweden"],
  "Bélgica":["Belgium"], "Egipto":["Egypt"], "Irán":["Iran","IR Iran"], "Nueva Zelanda":["New Zealand"],
  "España":["Spain"], "Cabo Verde":["Cape Verde","Cape Verde Islands"], "Arabia Saudita":["Saudi Arabia"],
  "Uruguay":["Uruguay"], "Francia":["France"], "Senegal":["Senegal"], "Noruega":["Norway"], "Iraq":["Iraq"],
  "Argentina":["Argentina"], "Argelia":["Algeria"], "Austria":["Austria"], "Jordania":["Jordan"], "Portugal":["Portugal"],
  "Colombia":["Colombia"], "Uzbekistán":["Uzbekistan"],
  "DR Congo":["DR Congo","Congo DR","Democratic Republic of Congo","RD Congo"],
  "Inglaterra":["England"], "Croacia":["Croatia"], "Ghana":["Ghana"], "Panamá":["Panama"],
}
_LOOKUP = {}
for es, al in ALIASES.items():
    for name in [es] + al:
        _LOOKUP[norm(name)] = es

def to_es(api_name):
    """Nombre de ESPN -> español canónico (o None si no calza)."""
    return _LOOKUP.get(norm(api_name))

def goles90_espn(comp):
    """Goles de un competidor ESPN SOLO en los 90' (linescores períodos 1 y 2).
    HIPÓTESIS a validar con un partido real con alargue. Si no hay linescores, devuelve None."""
    ls = comp.get("linescores")
    if not isinstance(ls, list) or not ls:
        return None
    tiene_period = any(isinstance(p, dict) and p.get("period") is not None for p in ls)
    s = 0
    if tiene_period:
        for p in ls:
            if isinstance(p, dict) and p.get("period") is not None and p.get("period") <= 2:
                try: s += int(float(p.get("value") or 0))
                except (TypeError, ValueError): pass
    else:
        for p in ls[:2]:
            try: s += int(float((p or {}).get("value") if isinstance(p, dict) else 0))
            except (TypeError, ValueError): pass
    return s

def fetch_espn_llaves():
    """Baja de ESPN los partidos TERMINADOS y devuelve [(localES, visitaES, gl90, gv90, ganadorES)].
    Persistimos estos resultados en el JSON para que no se pierdan al salir de la ventana en vivo."""
    hoy = datetime.datetime.now(datetime.timezone.utc).date()
    d1 = (hoy - datetime.timedelta(days=5)).strftime("%Y%m%d")
    d2 = (hoy + datetime.timedelta(days=1)).strftime("%Y%m%d")
    url = (f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/"
           f"scoreboard?dates={d1}-{d2}&limit=200")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "polla-bot"})
        with urllib.request.urlopen(req, timeout=40) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print(f"[diag] ESPN llaves falló: {e}")
        return []
    out = []
    for ev in data.get("events", []) or []:
        comp = (ev.get("competitions") or [{}])[0]
        st = ((ev.get("status") or {}).get("type") or {})
        if st.get("completed") is not True:   # solo terminados (los en vivo los pone el navegador)
            continue
        hC = aC = None
        for c in comp.get("competitors", []):
            if c.get("homeAway") == "home": hC = c
            elif c.get("homeAway") == "away": aC = c
        if not hC or not aC:
            continue
        hn = (hC.get("team") or {}).get("displayName") or (hC.get("team") or {}).get("name")
        an = (aC.get("team") or {}).get("displayName") or (aC.get("team") or {}).get("name")
        he, ae = to_es(hn), to_es(an)
        if not he or not ae:
            continue
        gl90 = goles90_espn(hC); gv90 = goles90_espn(aC)
        if gl90 is None:
            try: gl90 = int(hC.get("score"))
            except (TypeError, ValueError): gl90 = None
        if gv90 is None:
            try: gv90 = int(aC.get("score"))
            except (TypeError, ValueError): gv90 = None
        if gl90 is None or gv90 is None:
            continue
        winner = he if hC.get("winner") is True else (ae if aC.get("winner") is True else None)
        out.append((he, ae, gl90, gv90, winner))
    print(f"[diag] ESPN llaves: {len(out)} partidos terminados mapeados")
    return out

# ─────────────────────────── core ───────────────────────────

def build_llaves(rows):
    """Lista ordenada de los 32 partidos desde la pestaña Llaves (con el resultado REAL)."""
    llaves = []
    for r in rows:
        llaves.append({
            "ronda": r["ronda"],
            "cruce": r["cruce"],
            "local": r["local"],
            "visita": r["visita"],
            "realGL": r["gl"],
            "realGV": r["gv"],
            "realPasa": avance_real(r["local"], r["visita"], r["gl"], r["gv"], r["pasa"]),
        })
    return llaves

def main():
    ahora = datetime.datetime.now(datetime.timezone.utc)
    print(f"[diag] corriendo {ahora.isoformat()}  ·  sheet={SHEET_ID}")

    # 1) Llaves (fuente única + resultados reales)
    try:
        llaves_rows = fetch_csv(LLAVES_TAB)
    except Exception as e:
        print(f"[error] no pude leer la pestaña '{LLAVES_TAB}': {e}")
        sys.exit(1)
    print(f"[diag] Llaves: {len(llaves_rows)} filas leídas")
    if len(llaves_rows) != 32:
        print(f"[diag] OJO: esperaba 32 partidos en Llaves, llegaron {len(llaves_rows)}.")

    llaves = build_llaves(llaves_rows)
    # clave estable por partido: (ronda_norm, cruce_norm)
    keys = [(norm(m["ronda"]), norm(m["cruce"])) for m in llaves]

    # 1b) Resultados reales desde ESPN (se PERSISTEN en el JSON, igual que grupos).
    # Esto es lo que evita que un cruce jugado "desaparezca" al salir de la ventana en vivo.
    espn = fetch_espn_llaves()
    espn_pair = {}
    for he, ae, gl, gv, w in espn:
        espn_pair[(norm(he), norm(ae))] = (gl, gv, w)
        espn_pair[(norm(ae), norm(he))] = (gv, gl, w)   # por si ESPN invierte local/visita
    n_espn = 0
    for m in llaves:
        if not m["local"] or not m["visita"]:
            continue
        hit = espn_pair.get((norm(m["local"]), norm(m["visita"])))
        if hit:
            m["realGL"], m["realGV"] = hit[0], hit[1]
            m["realPasa"] = hit[2] or m.get("realPasa")
            n_espn += 1
    print(f"[diag] resultados de llaves aplicados desde ESPN: {n_espn}")

    # 2) JSON previo (para conservar rondas cerradas y resultados ya cargados)
    prev = {}
    prev_pron = {}        # (persona, ronda_n, cruce_n) -> [gl,gv,pasa]
    prev_real = {}        # (ronda_n, cruce_n) -> {realGL, realGV, realPasa}
    try:
        with open(OUT, encoding="utf-8") as fp:
            prev = json.load(fp)
        for i, m in enumerate(prev.get("llaves", [])):
            k = (norm(m.get("ronda", "")), norm(m.get("cruce", "")))
            prev_real[k] = {"realGL": m.get("realGL"), "realGV": m.get("realGV"),
                            "realPasa": m.get("realPasa")}
        for per, lst in prev.get("pronosticos", {}).items():
            for i, ap in enumerate(lst):
                if i < len(keys):
                    prev_pron[(per,) + keys[i]] = ap
    except Exception:
        pass

    # 2b) Merge de resultados reales: si una celda quedó vacía pero antes había dato, lo conservo
    for i, m in enumerate(llaves):
        if m["realGL"] is None and m["realGV"] is None:
            pr = prev_real.get(keys[i])
            if pr and pr.get("realGL") is not None:
                m["realGL"], m["realGV"], m["realPasa"] = pr["realGL"], pr["realGV"], pr.get("realPasa")

    # 3) Pronósticos por persona, con congelado por ronda
    estado_ronda = {}     # ronda_norm -> "abierta"/"cerrada"
    for m in llaves:
        rn = norm(m["ronda"])
        dl = DEADLINES.get(rn)
        estado_ronda[rn] = "cerrada" if (dl and ahora >= dl) else "abierta"
    print("[diag] estado rondas:", estado_ronda)

    pronosticos = {}
    sin_deadline = set()
    for persona in [p.strip() for p in PERSONAS if p.strip()]:
        try:
            prows = fetch_csv(persona)
        except Exception as e:
            print(f"[diag] pestaña '{persona}' falló: {e}  -> conservo lo previo si existe")
            prows = []

        # index del sheet de la persona por (ronda_n, cruce_n)
        sheet_ap = {}
        for r in prows:
            k = (norm(r["ronda"]), norm(r["cruce"]))
            sheet_ap[k] = [r["gl"], r["gv"],
                           avance_pred(r["local"], r["visita"], r["gl"], r["gv"], r["pasa"])]

        lista = []
        leidos = 0
        for i, m in enumerate(llaves):
            rn = norm(m["ronda"]); k = keys[i]
            dl = DEADLINES.get(rn)
            cerrada = bool(dl and ahora >= dl)
            if dl is None:
                sin_deadline.add(m["ronda"])

            if not cerrada:
                # ronda abierta -> lee del sheet (y esto se congela en la última corrida antes del deadline)
                ap = sheet_ap.get(k, [None, None, None])
                if ap[0] is not None or ap[1] is not None:
                    leidos += 1
            else:
                # ronda cerrada -> conserva lo congelado; si no hay previo, último recurso = sheet (con aviso)
                pp = prev_pron.get((persona,) + k)
                if pp is not None:
                    ap = pp
                else:
                    ap = sheet_ap.get(k, [None, None, None])
                    if ap[0] is not None:
                        print(f"[diag] !! {persona} {m['ronda']}/{m['cruce']}: ronda cerrada sin previo congelado, tomo del sheet")
            lista.append(ap)
        pronosticos[persona] = lista
        print(f"[diag] {persona}: {leidos} apuestas leídas en rondas abiertas")

    if sin_deadline:
        print(f"[diag] OJO: rondas sin deadline en DEADLINES (no se congelan): {sorted(sin_deadline)}")

    # 4) escribir
    payload = {
        "updatedAt": ahora.isoformat(),
        "deadlines": {k: v.isoformat() for k, v in DEADLINES.items()},
        "llaves": llaves,
        "pronosticos": pronosticos,
    }
    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=1)

    con_real = sum(1 for m in llaves if m["realGL"] is not None)
    print(f"[resumen] personas: {len(pronosticos)} · partidos con resultado real: {con_real}/32")
    print(f"[resumen] escrito en {OUT}")

if __name__ == "__main__":
    main()
