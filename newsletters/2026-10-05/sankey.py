#!/usr/bin/env python3
"""
Generador del gráfico de evolución de señales VTC.

Metodología de grosor (ajustada tras feedback del 2026-10-01):
- El grosor de cada banda ya NO es una categoría fija (Fuerte/Débil↑/Débil).
  Es proporcional al NÚMERO DE EVIDENCIAS (len(evidencia_ids)) que respalda
  la señal en cada edición, leído directamente de signal-registry.json.
- Para periodos anteriores a la existencia del registro estructurado
  (17-31 ago y 31 ago-7 sep 2026, que solo quedaron documentados como
  categoría dentro de historial_fuerza, sin registro propio) se usa un
  equivalente aproximado por categoría (CATEGORY_EQUIV) como única
  alternativa disponible. Todo periodo con registry.json propio usa el
  conteo real de evidencias.
- Las señales débiles ya no se agregan todas en una sola banda genérica:
  las dos con más evidencias en la última edición se dibujan como bandas
  propias; el resto se agrega en "Otras señales débiles".

Para la siguiente edición: añadir su signal-registry.json a REGISTRY_FILES
(con su periodo/etiqueta) y volver a ejecutar.
"""
import json
import os

WHITE = "#FFFFFF"
BLACK = "#111111"
GRAY = "#8A8A8A"
ACCENT = "#1F4E5F"
ACCENT_SOFT = "#5E8797"

CATEGORY_EQUIV = {"Fuerte": 10, "Débil↑": 4, "Débil": 1}

REPO = "/home/user/newletter-trabajo/newsletters"

# (etiqueta de columna, periodo-clave en historial_fuerza, ruta de registry.json o None)
PERIODS = [
    ("17–31 ago 2026", "2026-08-31", None),
    ("31 ago–7 sep 2026", "2026-09-07", None),
    ("8–22 sep 2026", "2026-09-22", f"{REPO}/2026-09-22/signal-registry.json"),
    ("23–28 sep 2026", "2026-09-28", f"{REPO}/2026-09-28/signal-registry.json"),
    ("29 sep–3 oct 2026 (hoy)", "2026-10-05", f"{REPO}/2026-10-05/signal-registry.json"),
]

registries = {}
for _, periodo, path in PERIODS:
    if path and os.path.exists(path):
        with open(path) as f:
            registries[periodo] = {s["id_senal"]: s for s in json.load(f)["senales"]}

LATEST_PERIODO = [p for _, p, path in PERIODS if path][-1]
latest_registry = registries[LATEST_PERIODO]


def value_for(signal_id, periodo, nombre_corto):
    """Grosor de la señal en un periodo: nº de evidencias si hay registry
    propio de ese periodo; si no, equivalente por categoría de historial_fuerza."""
    if periodo in registries:
        sig = registries[periodo].get(signal_id)
        return len(sig["evidencia_ids"]) if sig else None
    # fallback: categoría histórica, leída del registro más reciente que la conserve
    sig = latest_registry.get(signal_id)
    if not sig:
        return None
    for h in sig["historial_fuerza"]:
        if h["periodo"] == periodo:
            return CATEGORY_EQUIV.get(h["valor"])
    return None


macro_ids = [s["id_senal"] for s in latest_registry.values() if s["id_senal"].startswith("S-")]
macro_ids = sorted(macro_ids, key=lambda x: int(x.split("-")[1]))

debil_ids = [s["id_senal"] for s in latest_registry.values() if s["id_senal"].startswith("SD-")]
# las dos señales débiles más notorias de la última edición = más evidencias acumuladas
debil_ids_sorted = sorted(debil_ids, key=lambda sid: len(latest_registry[sid]["evidencia_ids"]), reverse=True)
TOP_DEBILES = debil_ids_sorted[:2]
OTHER_DEBILES = debil_ids_sorted[2:]

# nombres cortos "de gráfico" (más compactos que nombre_corto completo del registro)
DISPLAY_NAME = {
    "S-01": "Bifurcación laboral",
    "S-02": "Gobernanza rebasada",
    "S-03": "Robótica China",
    "S-04": "Respuesta institucional",
    "S-05": "Redefinición del trabajo",
    "S-06": "Riesgo macro IA",
    "S-07": "Robótica global",
    "S-08": "IA en contratación",
    "SD-06": "Robots-soldado (Pentágono)",
    "SD-09": "Ordenanza San Mateo",
    "SD-12": "Riesgo existencial IA (discurso)",
    "SD-13": "Pluriempleo / ejec. fraccionales",
}

PIVOT_FROM, PIVOT_TO = "S-03", "S-07"  # Robótica China -> Robótica global, pivote histórico en P3
PIVOT_WIDTH_UNITS = 3  # unidades (evidencias) que se "llevan" del pivote

signals = []
for sid in macro_ids:
    nombre = DISPLAY_NAME.get(sid, latest_registry[sid]["nombre_corto"])
    vals = [value_for(sid, periodo, nombre) for _, periodo, _ in PERIODS]
    signals.append((nombre, vals, "macro", sid))

for sid in TOP_DEBILES:
    nombre = DISPLAY_NAME.get(sid, latest_registry[sid]["nombre_corto"])
    vals = [value_for(sid, periodo, nombre) for _, periodo, _ in PERIODS]
    signals.append((nombre, vals, "debil_top", sid))

# agregado "otras señales débiles": suma de evidencias de las no destacadas, por periodo
otras_vals = []
for _, periodo, path in PERIODS:
    total = 0
    found_any = False
    for sid in OTHER_DEBILES:
        v = value_for(sid, periodo, None)
        if v is not None:
            total += v
            found_any = True
    otras_vals.append(total if found_any else None)
if any(v is not None for v in otras_vals):
    signals.append(("Otras señales débiles", otras_vals, "debil_other", None))

N_PERIODS = len(PERIODS)
periods_labels = [p[0] for p in PERIODS]

TOP = 70
BAND_GAP = 8
SCALE = 10  # px por evidencia (o por unidad-categoría equivalente)
X = [150, 370, 590, 810, 1030]
CANVAS_W = 1260


def color_for(grp):
    if grp == "macro":
        return ACCENT
    if grp == "debil_top":
        return ACCENT_SOFT
    return GRAY


def stack(period_idx):
    ys = {}
    y = TOP
    for name, vals, grp, sid in signals:
        v = vals[period_idx]
        h = max((v if v else 0) * SCALE, 3 if v else 0)
        ys[name] = (y, h)
        y += h + BAND_GAP
    return ys


stacks = [stack(i) for i in range(N_PERIODS)]
CHART_HEIGHT = max(y + h for st in stacks for (y, h) in st.values()) + 70


def bezier_ribbon(x0, y0, h0, x1, y1, h1, color, opacity=1.0):
    if h0 <= 0 and h1 <= 0:
        return ""
    mx = (x0 + x1) / 2
    top = f"M {x0},{y0} C {mx},{y0} {mx},{y1} {x1},{y1} " \
          f"L {x1},{y1+h1} C {mx},{y1+h1} {mx},{y0+h0} {x0},{y0+h0} Z"
    return f'<path d="{top}" fill="{color}" fill-opacity="{opacity}" stroke="none"/>'


svg_parts = [f'<svg viewBox="0 0 {CANVAS_W} {CHART_HEIGHT}" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica Now, Inter, Arial, sans-serif">']
svg_parts.append(f'<rect x="0" y="0" width="{CANVAS_W}" height="{CHART_HEIGHT}" fill="{WHITE}"/>')

for i, label in enumerate(periods_labels):
    svg_parts.append(f'<text x="{X[i]}" y="36" font-size="12.5" font-weight="700" fill="{BLACK}" text-anchor="middle">{label}</text>')
    svg_parts.append(f'<line x1="{X[i]}" y1="46" x2="{X[i]}" y2="{CHART_HEIGHT-20}" stroke="{GRAY}" stroke-opacity="0.25" stroke-width="1"/>')

for name, vals, grp, sid in signals:
    for seg in range(N_PERIODS - 1):
        i0, i1 = seg, seg + 1
        v0, v1 = vals[i0], vals[i1]
        if v0 is None and v1 is None:
            continue
        color = color_for(grp)
        if v0 is None and v1 is not None:
            y1, h1 = stacks[i1][name]
            x0 = X[i1] - 26
            y0 = y1 + h1 / 2
            svg_parts.append(bezier_ribbon(x0, y0, 0.001, X[i1], y1, h1, color, 0.9))
            continue
        if v1 is None:
            continue
        y0, h0 = stacks[i0][name]
        y1, h1 = stacks[i1][name]
        cont = min(v0, v1) * SCALE
        svg_parts.append(bezier_ribbon(X[i0], y0, cont, X[i1], y1, cont, color, 0.85))
        if v1 > v0:
            rf_h = (v1 - v0) * SCALE
            rx0 = X[i1] - 26
            ry0 = y1 + cont
            svg_parts.append(bezier_ribbon(rx0, ry0 + rf_h / 2, 0.001, X[i1], y1 + cont, rf_h, color, 0.55))

# pivote histórico Robótica China -> Robótica global (nace en P3)
if "S-03" in [s[3] for s in signals] and "S-07" in [s[3] for s in signals]:
    i_from, i_to = 1, 2  # P2 -> P3
    py0, ph0 = stacks[i_from][DISPLAY_NAME["S-03"]]
    py1, ph1 = stacks[i_to][DISPLAY_NAME["S-07"]]
    w = min(PIVOT_WIDTH_UNITS * SCALE, ph0, ph1)
    svg_parts.append(bezier_ribbon(X[i_from], py0 + ph0 - w, w, X[i_to], py1, w, ACCENT, 0.45))

for i in range(N_PERIODS):
    for name, vals, grp, sid in signals:
        v = vals[i]
        if v is None:
            continue
        y, h = stacks[i][name]
        color = color_for(grp)
        svg_parts.append(f'<rect x="{X[i]-3}" y="{y}" width="6" height="{h}" fill="{color}"/>')
        label = name if i != N_PERIODS - 1 else f"{name} ({v})"
        if i == 0:
            svg_parts.append(f'<text x="{X[i]-12}" y="{y + h/2 + 4}" font-size="11.5" fill="{BLACK}" text-anchor="end">{label}</text>')
        elif i == N_PERIODS - 1:
            svg_parts.append(f'<text x="{X[i]+12}" y="{y + h/2 + 4}" font-size="11.5" fill="{BLACK}" text-anchor="start">{label}</text>')
        elif vals[i - 1] is None:
            svg_parts.append(f'<text x="{X[i]-12}" y="{y + h/2 + 4}" font-size="11.5" fill="{BLACK}" text-anchor="end">{name}</text>')

svg_parts.append("</svg>")
svg = "\n".join(svg_parts)

OUT_SVG = f"{REPO}/2026-10-05/sankey.svg"
with open(OUT_SVG, "w") as f:
    f.write(svg)

print("OK ->", OUT_SVG, "| alto:", CHART_HEIGHT, "| señales débiles destacadas:", TOP_DEBILES, "| otras:", OTHER_DEBILES)
