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

import os, sys, json, csv, io, re, unicodedata, datetime, urllib.request, urllib.parse

# ─────────────────────────── CONFIG (ajusta esto) ───────────────────────────

SHEET_ID = os.environ.get("POLLA_SHEET_ID", "1y6omPkb9NWIfSITMSJKmzXF4AIAo5oevW6t9DfDn_bc")
LLAVES_TAB = "Llaves"
PERSONAS = os.environ.get("POLLA_PERSONAS", "Demian,Jano,Nacho,Pelao,Raul,Jlo,Paula,Six,Chapa,Bob,Claudia,Chorero").split(",")

DEADLINES = {
    "rondade32":   datetime.datetime(2026, 7, 1, 20, 10, tzinfo=datetime.timezone.utc),
    "rondade32e":  datetime.datetime(2026, 6, 28, 19, 58, tzinfo=datetime.timezone.utc),
    "octavos":     datetime.datetime(2026, 7,  4, 16,  0, tzinfo=datetime.timezone.utc),  # respaldo si algún cruce quedó como "Octavos" a secas
    "octavosdia1": datetime.datetime(2026, 7,  4, 17,  31, tzinfo=datetime.timezone.utc),  # 4 jul 11:00 Chile
    "octavosdia2": datetime.datetime(2026, 7,  5, 18,  0, tzinfo=datetime.timezone.utc),  # 5 jul 14:00 Chile
    "octavosdia3": datetime.datetime(2026, 7,  6, 17,  0, tzinfo=datetime.timezone.utc),  # 6 jul 13:00 Chile
    "octavosdia4": datetime.datetime(2026, 7,  7, 14,  0, tzinfo=datetime.timezone.utc),  # 7 jul 10:00 Chile
    "cuartos":     datetime.datetime(2026, 7,  11, 19,  0, tzinfo=datetime.timezone.utc),
    "semifinal":   datetime.datetime(2026, 7, 18, 19,  30, tzinfo=datetime.timezone.utc),
    "3erpuesto":   datetime.datetime(2026, 7, 18, 18,  0, tzinfo=datetime.timezone.utc),
    "final":       datetime.datetime(2026, 7, 19, 18,  0, tzinfo=datetime.timezone.utc),
}

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pronosticos_llaves.json")

# ─────────────────────────── helpers ───────────────────────────

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return "".join(c for c in s.lower() if c.isalnum())

def to_int(x):
    if x is None:
        return None
    x = str(x).strip()
    if x == "":
        return None
    try:
        return int(float(x))
    except ValueError:
        return None

def clean(x):
    return str(x).strip() if x is not None else ""

COLMAP = {
    "ronda": "ronda", "cruce": "cruce",
    "local": "local", "gl": "gl", "gv": "gv",
    "visitante": "visita", "visita": "visita",
    "pasa": "pasa", "quienavanza": "pasa", "avanza": "pasa",
}

def parse_csv_text(text):
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
    url = (f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq"
           f"?tqx=out:csv&headers=1&sheet={urllib.parse.quote(tab)}")
    req = urllib.request.Request(url, headers={"User-Agent": "polla-bot"})
    with urllib.request.urlopen(req, timeout=40) as r:
        text = r.read().decode("utf-8")
    return parse_csv_text(text)

def avance_real(local, visita, gl, gv, pasa_celda):
    if gl is None or gv is None:
        return clean(pasa_celda) or None
    if gl > gv:
        return local
    if gv > gl:
        return visita
    return clean(pasa_celda) or None

def avance_pred(local, visita, gl, gv, pasa_celda):
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

# ───────────── ESPN: resultados reales de llaves ─────────────

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
    return _LOOKUP.get(norm(api_name))

def goles90_linescores(comp):
    """
    Intenta obtener goles de los 90' usando linescores (períodos 1 y 2).
    Devuelve el total o None si no hay linescores disponibles.
    """
    ls = comp.get("linescores")
    if not isinstance(ls, list) or not ls:
        return None
    tiene_period = any(isinstance(p, dict) and p.get("period") is not None for p in ls)
    s = 0
    if tiene_period:
        for p in ls:
            if isinstance(p, dict) and p.get("period") is not None and p.get("period") <= 2:
                try:
                    s += int(float(p.get("value") or 0))
                except (TypeError, ValueError):
                    pass
    else:
        for p in ls[:2]:
            try:
                s += int(float((p or {}).get("value") if isinstance(p, dict) else 0))
            except (TypeError, ValueError):
                pass
    return s

def _es_alargue(ev):
    """True si el gol/evento ocurrió en tiempo extra (alargue), False si es reglamentario.

    Validado contra la estructura real de ESPN de este Mundial. clock.displayValue trae
    el minuto: '67\\'', '45\\'+2\\'', '90\\'+5\\'', '105\\'', '105\\'+2\\'', '120\\'+3\\''.
      - Minuto base = número antes del '+'.
      - Reglamentario (cuenta): base <= 90. Incluye el descuento '45\\'+x' y '90\\'+x'
        (ej. un gol al 95' llega como '90\\'+5\\'' → base 90 → cuenta).
      - Alargue (no cuenta): base > 90. Incluye '105\\'', '105\\'+x', '119\\'', '120\\'+x'.
    Sin displayValue, cae a clock.value en segundos (poco fiable: ESPN deja el value
    pegado en 5400 durante el descuento, por eso el displayValue manda si existe)."""
    clk = ev.get("clock") or {}
    disp = clk.get("displayValue")
    if disp:
        m = re.match(r"\s*(\d+)", str(disp))
        if m:
            return int(m.group(1)) > 90     # la base decide; '90'+x' = 90 (cuenta), '105'+x' = 105 (alargue)
    val = clk.get("value")
    if val is not None:
        try:
            return float(val) > 5400.0
        except (TypeError, ValueError):
            pass
    return False   # ante la duda, cuenta (no descartamos un gol reglamentario)

def goles90_desde_details(comp_dict, home_id, away_id):
    """Cuenta los goles de los 90' reglamentarios leyendo los eventos (details) del partido.

    - Excluye alargue (minuto > 90 sin '+') y penales (shootout).
    - Incluye descuento reglamentario ('90\\'+x').
    - ownGoal: ESPN ya asigna el team beneficiado en el evento."""
    details = comp_dict.get("details") or []
    gl, gv = 0, 0
    for ev in details:
        if not ev.get("scoringPlay"):
            continue
        if ev.get("shootout"):
            continue
        if _es_alargue(ev):
            continue
        team_id = str((ev.get("team") or {}).get("id") or "")
        val = ev.get("scoreValue") or 1
        if team_id == str(home_id):
            gl += val
        elif team_id == str(away_id):
            gv += val
    return gl, gv

def fetch_espn_llaves():
    """
    Baja de ESPN los partidos TERMINADOS y devuelve
    [(localES, visitaES, gl90, gv90, ganadorES)].

    Prioridad para goles de 90':
      1. linescores (períodos 1+2) si ESPN los manda
      2. details filtrando clock.value <= 5400  ← fix para alargue
    """
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
        if st.get("completed") is not True:
            continue

        hC = aC = None
        for c in comp.get("competitors", []):
            if c.get("homeAway") == "home":
                hC = c
            elif c.get("homeAway") == "away":
                aC = c
        if not hC or not aC:
            continue

        hn = (hC.get("team") or {}).get("displayName") or (hC.get("team") or {}).get("name")
        an = (aC.get("team") or {}).get("displayName") or (aC.get("team") or {}).get("name")
        he, ae = to_es(hn), to_es(an)
        if not he or not ae:
            continue

        home_id = str((hC.get("team") or {}).get("id") or hC.get("id") or "")
        away_id = str((aC.get("team") or {}).get("id") or aC.get("id") or "")

        # 90' desde los details (eventos con minuto). Este feed de ESPN no trae linescores,
        # así que los details son la fuente confiable; separan alargue por el minuto real.
        gl90, gv90 = goles90_desde_details(comp, home_id, away_id)
        # respaldo por si un partido no trajera details
        if (gl90 == 0 and gv90 == 0):
            l1, l2 = goles90_linescores(hC), goles90_linescores(aC)
            if l1 is not None and l2 is not None:
                gl90, gv90 = l1, l2
                print(f"[diag] {hn} vs {an}: sin details → linescores ({gl90}-{gv90})")
            else:
                print(f"[diag] {hn} vs {an}: 90' = {gl90}-{gv90} (details)")
        else:
            print(f"[diag] {hn} vs {an}: 90' = {gl90}-{gv90} (details)")

        winner = he if hC.get("winner") is True else (ae if aC.get("winner") is True else None)

        # marcador FINAL (incluye alargue) desde el score del competidor
        def _score_int(c):
            try:
                return int(float(c.get("score")))
            except (TypeError, ValueError):
                return None
        glF, gvF = _score_int(hC), _score_int(aC)
        # ¿hubo alargue? si el final difiere de los 90', o si hay algún gol con minuto > 90
        went_et = False
        if glF is not None and gvF is not None:
            if glF != gl90 or gvF != gv90:
                went_et = True
        for ev in (comp.get("details") or []):
            if ev.get("scoringPlay") and not ev.get("shootout") and _es_alargue(ev):
                went_et = True
                break
        out.append((he, ae, gl90, gv90, winner, glF, gvF, went_et))

    print(f"[diag] ESPN llaves: {len(out)} partidos terminados mapeados")
    return out

def fetch_deadlines_por_fecha(margen_horas=1):
    """Consulta ESPN las fechas reales de TODOS los cruces (jugados o no) y devuelve
    un dict {(localES, visitaES): deadline_utc}, donde el deadline es `margen_horas`
    antes del PRIMER partido del día en que se juega ese cruce.

    Así, todos los partidos de un mismo día comparten el mismo deadline (el más temprano
    de ese día menos el margen). Devuelve {} si ESPN falla (el caller usa DEADLINES fijos)."""
    hoy = datetime.datetime.now(datetime.timezone.utc).date()
    d1 = (hoy - datetime.timedelta(days=2)).strftime("%Y%m%d")
    d2 = (hoy + datetime.timedelta(days=20)).strftime("%Y%m%d")   # ventana amplia hacia adelante
    url = (f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/"
           f"scoreboard?dates={d1}-{d2}&limit=300")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "polla-bot"})
        with urllib.request.urlopen(req, timeout=40) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print(f"[diag] fechas ESPN fallaron: {e}  -> uso DEADLINES fijos")
        return {}

    # 1) juntar (fecha_partido, localES, visitaES) de cada evento con fecha
    partidos = []
    primero_del_dia = {}   # date -> datetime más temprano de ese día
    for ev in data.get("events", []) or []:
        fecha_raw = ev.get("date")
        if not fecha_raw:
            continue
        try:
            dt = datetime.datetime.fromisoformat(fecha_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        comp = (ev.get("competitions") or [{}])[0]
        hC = aC = None
        for c in comp.get("competitors", []):
            if c.get("homeAway") == "home":
                hC = c
            elif c.get("homeAway") == "away":
                aC = c
        if not hC or not aC:
            continue
        hn = (hC.get("team") or {}).get("displayName") or (hC.get("team") or {}).get("name")
        an = (aC.get("team") or {}).get("displayName") or (aC.get("team") or {}).get("name")
        he, ae = to_es(hn), to_es(an)
        if not he or not ae:
            continue
        dia = dt.date()
        partidos.append((dia, he, ae))
        if dia not in primero_del_dia or dt < primero_del_dia[dia]:
            primero_del_dia[dia] = dt

    # 2) deadline por partido = primer partido de su día - margen
    deadlines = {}
    for dia, he, ae in partidos:
        dl = primero_del_dia[dia] - datetime.timedelta(hours=margen_horas)
        deadlines[(norm(he), norm(ae))] = dl
        deadlines[(norm(ae), norm(he))] = dl   # por si el orden local/visita difiere
    if deadlines:
        dias = sorted({d.isoformat() for d, _, _ in partidos})
        print(f"[diag] deadlines por fecha: {len(partidos)} partidos en {len(dias)} días ({', '.join(dias)})")
    return deadlines

# ─────────────────────────── core ───────────────────────────

def build_llaves(rows):
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

    # 1) Llaves
    try:
        llaves_rows = fetch_csv(LLAVES_TAB)
    except Exception as e:
        print(f"[error] no pude leer la pestaña '{LLAVES_TAB}': {e}")
        sys.exit(1)
    print(f"[diag] Llaves: {len(llaves_rows)} filas leídas")
    if len(llaves_rows) != 32:
        print(f"[diag] OJO: esperaba 32 partidos en Llaves, llegaron {len(llaves_rows)}.")

    llaves = build_llaves(llaves_rows)
    keys = [(norm(m["ronda"]), norm(m["cruce"])) for m in llaves]

    # 1b) Resultados reales desde ESPN
    espn = fetch_espn_llaves()
    espn_pair = {}
    for he, ae, gl, gv, w, glF, gvF, et in espn:
        espn_pair[(norm(he), norm(ae))] = (gl, gv, w, glF, gvF, et)
        espn_pair[(norm(ae), norm(he))] = (gv, gl, w, (gvF if gvF is not None else None), (glF if glF is not None else None), et)
    n_espn = 0
    for m in llaves:
        if not m["local"] or not m["visita"]:
            continue
        hit = espn_pair.get((norm(m["local"]), norm(m["visita"])))
        if hit:
            m["realGL"], m["realGV"] = hit[0], hit[1]
            m["realPasa"] = hit[2] or m.get("realPasa")
            m["realFinalGL"], m["realFinalGV"] = hit[3], hit[4]
            m["realWentET"] = bool(hit[5])
            n_espn += 1
    print(f"[diag] resultados de llaves aplicados desde ESPN: {n_espn}")

    # 2) JSON previo
    prev = {}
    prev_pron = {}
    prev_real = {}
    try:
        with open(OUT, encoding="utf-8") as fp:
            prev = json.load(fp)
        for i, m in enumerate(prev.get("llaves", [])):
            k = (norm(m.get("ronda", "")), norm(m.get("cruce", "")))
            prev_real[k] = {"realGL": m.get("realGL"), "realGV": m.get("realGV"),
                            "realPasa": m.get("realPasa"),
                            "realFinalGL": m.get("realFinalGL"), "realFinalGV": m.get("realFinalGV"),
                            "realWentET": m.get("realWentET")}
        for per, lst in prev.get("pronosticos", {}).items():
            for i, ap in enumerate(lst):
                if i < len(keys):
                    prev_pron[(per,) + keys[i]] = ap
    except Exception:
        pass

    # 2b) Merge: conserva resultados previos si la celda quedó vacía
    for i, m in enumerate(llaves):
        if m["realGL"] is None and m["realGV"] is None:
            pr = prev_real.get(keys[i])
            if pr and pr.get("realGL") is not None:
                m["realGL"], m["realGV"], m["realPasa"] = pr["realGL"], pr["realGV"], pr.get("realPasa")
                m["realFinalGL"] = pr.get("realFinalGL")
                m["realFinalGV"] = pr.get("realFinalGV")
                m["realWentET"] = pr.get("realWentET")

    # 3) Pronósticos por persona, con congelado por ronda / por fecha real del partido
    # deadline efectivo de un cruce:
    #   1) si la ronda tiene un DEADLINES manual explícito → ese manda (control total)
    #   2) si no, se usa la fecha real de ESPN (automático)
    # Así, poner "Octavos_dia1..4" con su hora en DEADLINES tiene prioridad y no lo pisa ESPN.
    dl_por_fecha = fetch_deadlines_por_fecha(margen_horas=1)
    def deadline_de(m):
        manual = DEADLINES.get(norm(m["ronda"]))
        if manual is not None:
            return manual
        k = (norm(m.get("local") or ""), norm(m.get("visita") or ""))
        if k in dl_por_fecha:
            return dl_por_fecha[k]
        return None

    estado_ronda = {}
    for m in llaves:
        rn = norm(m["ronda"])
        dl = deadline_de(m)
        # el estado por ronda es informativo; si algún cruce de la ronda está cerrado lo marca
        est = "cerrada" if (dl and ahora >= dl) else "abierta"
        # si ya había una marca 'cerrada' para la ronda, la conservamos (mezcla de días)
        if estado_ronda.get(rn) != "cerrada":
            estado_ronda[rn] = est
    print("[diag] estado rondas:", estado_ronda)

    pronosticos = {}
    sin_deadline = set()
    for persona in [p.strip() for p in PERSONAS if p.strip()]:
        try:
            prows = fetch_csv(persona)
        except Exception as e:
            print(f"[diag] pestaña '{persona}' falló: {e}  -> conservo lo previo si existe")
            prows = []

        sheet_ap = {}
        for r in prows:
            k = (norm(r["ronda"]), norm(r["cruce"]))
            sheet_ap[k] = [r["gl"], r["gv"],
                           avance_pred(r["local"], r["visita"], r["gl"], r["gv"], r["pasa"])]

        lista = []
        leidos = 0
        for i, m in enumerate(llaves):
            rn = norm(m["ronda"]); k = keys[i]
            dl = deadline_de(m)
            cerrada = bool(dl and ahora >= dl)
            if dl is None:
                sin_deadline.add(m["ronda"])

            if not cerrada:
                ap = sheet_ap.get(k, [None, None, None])
                if ap[0] is not None or ap[1] is not None:
                    leidos += 1
            else:
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

    # 4) Escribir JSON
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
