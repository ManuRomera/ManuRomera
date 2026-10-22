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
    """badges/resumen.svg: franja compacta con el total, las descargas por categoría y los 6 proyectos más descargados."""
    import datetime
    from html import escape
    data = json.loads((ROOT / "scripts" / "portada.json").read_text(encoding="utf-8"))
    nombres = data["nombres"]
    items, cats = [], []
    for c in data["categorias"]:
        tot = 0
        for repo, _ in c["proyectos"]:
            d = summary.get(repo, {})
            items.append((repo, d.get("descargas", 0), c["accent"], d.get("con_archivos", False)))
            tot += d.get("descargas", 0)
        cats.append((c["titulo"], c["accent"], tot))
    total = sum(c[2] for c in cats)
    ranking = sorted([i for i in items if i[1] > 0], key=lambda i: -i[1])[:6]
    top = ranking[0][1] if ranking else 1
    W, M, H = 1200, 36, 252
    tw = (W - 2 * M - 3 * 12) / 4
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Resumen de descargas: {miles(total)}">',
         f'<rect width="{W}" height="{H}" rx="16" fill="#12141b"/><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="15" fill="none" stroke="#262935" stroke-width="2"/>',
         '<g font-family="Georgia,\'Times New Roman\',serif">',
         f'<text x="{M}" y="50" font-size="26" font-weight="700" fill="#ece6d6">Descargas</text>',
         f'<text x="{M + 160}" y="50" font-size="26" font-weight="700" fill="#d6af76">{miles(total)}</text>',
         f'<text x="{W - M}" y="48" font-size="15" font-style="italic" fill="#7d7f8c" text-anchor="end">releases de GitHub · {datetime.date.today().isoformat()}</text>']
    for i, (titulo, color, tot) in enumerate(cats):
        x = M + i * (tw + 12)
        o.append(f'<rect x="{x:.1f}" y="70" width="{tw:.1f}" height="54" rx="10" fill="#1a1d26"/><rect x="{x:.1f}" y="70" width="4" height="54" rx="2" fill="{color}"/>')
        o.append(f'<text x="{x + 18:.1f}" y="90" font-size="14" font-style="italic" fill="#a9a9b3">{escape(titulo)}</text>')
        o.append(f'<text x="{x + 18:.1f}" y="115" font-size="22" font-weight="700" fill="{color}">{miles(tot)}</text>')
    colw = (W - 2 * M - 40) / 2
    for k, (repo, d, color, _) in enumerate(ranking):
        cx = M + (k % 2) * (colw + 40); y = 148 + (k // 2) * 30
        lw = 190; bw = colw - lw - 56
        o.append(f'<text x="{cx:.1f}" y="{y + 16}" font-size="15" fill="#d9d4c5">{escape(nombres.get(repo, repo))}</text>')
        o.append(f'<rect x="{cx + lw:.1f}" y="{y + 5}" width="{bw:.1f}" height="9" rx="4.5" fill="#1a1d26"/><rect x="{cx + lw:.1f}" y="{y + 5}" width="{max(5, bw * d / top):.1f}" height="9" rx="4.5" fill="{color}"/>')
        o.append(f'<text x="{cx + colw:.1f}" y="{y + 16}" font-size="15" font-weight="700" fill="#ece6d6" text-anchor="end">{miles(d)}</text>')
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
