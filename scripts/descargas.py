#!/usr/bin/env python3
"""Insignias de descargas (SVG propias) para todos los repositorios públicos de ManuRomera.

Por qué: la insignia en vivo de shields.io depende de su cuota de peticiones a la API de GitHub y devuelve «invalid»
de forma intermitente. Aquí el cálculo lo hace GitHub Actions una vez al día y las SVG viven en este repo.

Uso en el README de cualquier repo:
  <img alt="Downloads" src="https://raw.githubusercontent.com/ManuRomera/ManuRomera/main/badges/descargas/<repo>.svg">

Escribe badges/descargas/<repo>.svg y badges/descargas.json. Solo cuenta archivos adjuntos a las releases: un repo cuyo
manifiesto apunta al «archive» del código (no adjunta zip) muestra «n/d», porque GitHub no cuenta esas descargas.
Solo biblioteca estándar. Variable de entorno: GITHUB_TOKEN.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

OWNER = "ManuRomera"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "badges" / "descargas"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def api(path):
    """Todas las páginas de un listado de la API de GitHub."""
    items, url = [], f"https://api.github.com{path}{'&' if '?' in path else '?'}per_page=100"
    while url:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "descargas-badges",
                                                   **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
        with urllib.request.urlopen(req, timeout=30) as r:
            items += json.load(r)
            link = r.headers.get("Link", "")
        url = next((p.split(";")[0].strip(" <>") for p in link.split(",") if 'rel="next"' in p), None)
    return items


def fmt(n):
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def badge(value, label="DOWNLOADS"):
    """Insignia con el aspecto «for-the-badge» de shields (etiqueta gris, valor naranja)."""
    lw = round(len(label) * 7.2 + 24)
    vw = round(len(value) * 8.4 + 26)
    w = lw + vw
    fill = "#ff7a1f" if value != "n/d" else "#7d8793"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="28" role="img" aria-label="{label}: {value}">'
            f'<title>{label}: {value}</title>'
            f'<g shape-rendering="crispEdges"><rect width="{lw}" height="28" fill="#555"/><rect x="{lw}" width="{vw}" height="28" fill="{fill}"/></g>'
            f'<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="10" text-rendering="geometricPrecision">'
            f'<text x="{lw / 2:.1f}" y="17.5" textLength="{round(len(label) * 7.2)}" letter-spacing="1">{label}</text>'
            f'<text x="{lw + vw / 2:.1f}" y="17.5" textLength="{round(len(value) * 8.4)}" font-weight="bold" letter-spacing="1">{value}</text>'
            f'</g></svg>\n')


def badge_flat(value, label="downloads"):
    """Variante plana de 20 px (para READMEs con insignias pequeñas), como el estilo «flat» de shields."""
    lw = round(len(label) * 6.1 + 12)
    vw = round(len(value) * 6.8 + 12)
    w = lw + vw
    fill = "#fe7d37" if value != "n/d" else "#9f9f9f"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{label}: {value}">'
            f'<title>{label}: {value}</title>'
            f'<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>'
            f'<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="#555"/><rect x="{lw}" width="{vw}" height="20" fill="{fill}"/></g>'
            f'<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11" text-rendering="geometricPrecision">'
            f'<text x="{lw / 2:.1f}" y="14" textLength="{round(len(label) * 6.1)}">{label}</text>'
            f'<text x="{lw + vw / 2:.1f}" y="14" textLength="{round(len(value) * 6.8)}">{value}</text>'
            f'</g></svg>\n')


def miles(n):
    return f"{n:,}".replace(",", ".")


def resumen(summary):
    """badges/resumen.svg: panel con el total, las descargas por categoría y el ranking de proyectos (colores de scripts/portada.json)."""
    import datetime
    from html import escape
    data = json.loads((ROOT / "scripts" / "portada.json").read_text(encoding="utf-8"))
    nombres = data["nombres"]
    items = []  # (repo, descargas, color, categoria)
    cats = []
    for c in data["categorias"]:
        tot = 0
        for repo, _ in c["proyectos"]:
            d = summary.get(repo, {})
            items.append((repo, d.get("descargas", 0), c["accent"], c["titulo"], d.get("con_archivos", False)))
            tot += d.get("descargas", 0)
        cats.append((c["titulo"], c["accent"], tot, len(c["proyectos"])))
    total = sum(c[2] for c in cats)
    ranking = sorted([i for i in items if i[1] > 0], key=lambda i: -i[1])[:14]
    sin = [nombres.get(i[0], i[0]) for i in items if not i[4]]
    W, M = 1200, 48
    tile_w = (W - 2 * M - 3 * 16) / 4
    y0 = 300
    row = 36
    H = y0 + len(ranking) * row + (74 if sin else 40)
    top = ranking[0][1] if ranking else 1
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Resumen de descargas: {miles(total)}">',
         '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#171923"/><stop offset="1" stop-color="#0d0f14"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="22" fill="url(#bg)"/><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="21" fill="none" stroke="#2c2f3b" stroke-width="2"/>',
         '<g font-family="Georgia,\'Times New Roman\',serif">',
         f'<text x="{M}" y="82" font-size="46" font-weight="700" fill="#f5efe2">Descargas</text>',
         f'<text x="{M}" y="118" font-size="20" font-style="italic" fill="#a9a9b3">Archivos de las releases · actualizado {datetime.date.today().isoformat()}</text>',
         f'<text x="{W - M}" y="96" font-size="76" font-weight="700" fill="#d6af76" text-anchor="end">{miles(total)}</text>',
         f'<text x="{W - M}" y="128" font-size="20" font-style="italic" fill="#a9a9b3" text-anchor="end">descargas de estos proyectos</text>']
    for i, (titulo, color, tot, n) in enumerate(cats):
        x = M + i * (tile_w + 16)
        o.append(f'<rect x="{x:.1f}" y="164" width="{tile_w:.1f}" height="106" rx="14" fill="#1d2029"/><rect x="{x:.1f}" y="164" width="{tile_w:.1f}" height="5" rx="2.5" fill="{color}"/>')
        o.append(f'<text x="{x + 18:.1f}" y="200" font-size="17" font-style="italic" fill="#c9c4b6">{escape(titulo)}</text>')
        o.append(f'<text x="{x + 18:.1f}" y="248" font-size="40" font-weight="700" fill="{color}">{miles(tot)}</text>')
        o.append(f'<text x="{x + tile_w - 16:.1f}" y="248" font-size="16" font-style="italic" fill="#8e8e99" text-anchor="end">{n} proyectos</text>')
    bx, bw = 330, W - M - 330 - 90
    for k, (repo, d, color, _, _) in enumerate(ranking):
        y = y0 + k * row
        w = max(6, bw * d / top)
        o.append(f'<text x="{bx - 14}" y="{y + 22}" font-size="18" fill="#e9e5d8" text-anchor="end">{escape(nombres.get(repo, repo))}</text>')
        o.append(f'<rect x="{bx}" y="{y + 6}" width="{bw}" height="20" rx="10" fill="#1d2029"/><rect x="{bx}" y="{y + 6}" width="{w:.1f}" height="20" rx="10" fill="{color}"/>')
        o.append(f'<text x="{bx + w + 12:.1f}" y="{y + 23}" font-size="18" font-weight="700" fill="#f5efe2">{miles(d)}</text>')
    if sin:
        o.append(f'<text x="{M}" y="{H - 28}" font-size="14" font-style="italic" fill="#8e8e99">Sin zip adjunto a la release (GitHub no cuenta esas descargas): {escape(", ".join(sin))}.</text>')
    o.append('</g></svg>\n')
    (ROOT / "badges" / "resumen.svg").write_text("\n".join(o), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT.parent / "descargas-flat").mkdir(parents=True, exist_ok=True)
    repos = [r["name"] for r in api(f"/users/{OWNER}/repos?type=owner") if not r["private"]]
    summary, failures = {}, 0
    for name in sorted(repos, key=str.lower):
        try:
            assets = [a for rel in api(f"/repos/{OWNER}/{name}/releases") for a in rel["assets"]]
        except Exception as e:  # noqa: BLE001 - se conserva la insignia anterior
            print(f"AVISO {name}: {e}", file=sys.stderr)
            failures += 1
            continue
        total = sum(a["download_count"] for a in assets)
        summary[name] = {"descargas": total, "con_archivos": bool(assets)}
        value = fmt(total) if assets else "n/d"
        (OUT / f"{name}.svg").write_text(badge(value), encoding="utf-8")
        (OUT.parent / "descargas-flat" / f"{name}.svg").write_text(badge_flat(value), encoding="utf-8")
    summary["_total"] = sum(v["descargas"] for v in summary.values())
    (ROOT / "badges" / "descargas.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    resumen(summary)
    print(f"{len(summary) - 1} repos, {summary['_total']} descargas en total, {failures} avisos")
    return 0 if repos else 1


if __name__ == "__main__":
    sys.exit(main())
