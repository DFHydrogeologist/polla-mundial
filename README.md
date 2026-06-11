# Polla Mundial 2026

Página estática (GitHub Pages) que muestra el ranking de la polla. Las predicciones de los
10 jugadores van empaquetadas dentro de `index.html`. Los **resultados reales los rellena
solo la API** mediante un GitHub Action; nadie los edita a mano.

## Cómo funciona

```
API de fútbol  ──>  GitHub Action (cada 30 min)  ──>  resultados.json  ──>  index.html (solo lectura)
```

- `index.html` — la página. Lee `resultados.json` del mismo origen (sin CORS, sin exponer la key).
- `resultados.json` — 72 marcadores de la fase de grupos. Lo escribe **únicamente** el Action.
- `scripts/fetch_resultados.py` — llama a la API, traduce nombres y arma `resultados.json`.
- `.github/workflows/actualizar-resultados.yml` — corre el script cada 30 min.

## Puesta en marcha (una sola vez)

1. **Sube estos archivos** a un repositorio de GitHub (raíz del repo).
2. **Settings → Pages**: Source = Deploy from a branch, rama `main`, carpeta `/ (root)`.
   Tu polla queda en `https://TU_USUARIO.github.io/TU_REPO/`.
3. Elige proveedor de datos y carga la credencial en **Settings → Secrets and variables → Actions**:

   **Opción A — API-Football** (api-sports.io):
   - Secret `APIFOOTBALL_KEY` = tu key.
   - (Variable opcional `POLLA_PROVIDER` = `apifootball`, es el valor por defecto.)
   - Nota: el plan gratis tiene tope de ligas; verifica que `league=1&season=2026` te devuelva datos.

   **Opción B — football-data.org** (suele incluir el Mundial en el plan gratis):
   - Secret `FOOTBALLDATA_TOKEN` = tu token.
   - Variable `POLLA_PROVIDER` = `footballdata`.

4. **Actions → Actualizar resultados → Run workflow** para la primera corrida (o espera al cron).

## Probar el script localmente

```bash
export POLLA_PROVIDER=apifootball
export APIFOOTBALL_KEY=xxxxxxxx
python scripts/fetch_resultados.py
```
Imprime cuántos partidos finalizados mapeó (`X/72`) y avisa si algún equipo no calzó
(para ajustar el diccionario `ALIASES` del script).

## Puntaje
- 2 pts: acertar el resultado (gana/empata/pierde)
- 4 pts: además acertar el margen (diferencia de goles)
- 6 pts: marcador exacto

Solo se cuentan partidos **finalizados**. La fase de llave se suma cuando se conozcan los cruces.
