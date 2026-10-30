"""Genera README.md y docs/index.html a partir de scripts/portada.json (categorías, descripciones y orden).
Uso: python3 scripts/make-portada.py   (los banners salen de make-banners.py y make-sections.py)"""
import json, re
from urllib.parse import quote
from html import escape
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "scripts/portada.json").read_text(encoding="utf-8"))
DL = json.loads((ROOT / "badges/descargas.json").read_text(encoding="utf-8"))
PAGES = set(D["pages"]); NOM = D["nombres"]
GH = "https://github.com/ManuRomera/"; IO = "https://manuromera.github.io/"; RAW = "https://raw.githubusercontent.com/ManuRomera/ManuRomera/main/"
md_i = lambda s: re.sub(r"\*(.+?)\*", r"<i>\1</i>", s)          # cursivas en HTML dentro de la tabla

def celda(repo, desc):
    n = NOM.get(repo, repo)
    web = f' · <a href="{IO}{repo}/">Página</a>' if repo in PAGES else ""
    return (f'<td width="50%" valign="top">\n<a href="{GH}{repo}"><img src="./banners/{repo}.webp" alt="{escape(n)}" width="100%"></a>\n<br>\n'
            f'<b>{escape(n)}</b><br>\n<sub>{md_i(escape(desc, quote=False))}</sub><br>\n<sub><a href="{GH}{repo}">Repositorio</a>{web}</sub><br>\n<img src="./badges/descargas-flat/{repo}.svg" alt="Descargas de {escape(n)}">\n</td>')

def tabla(proy):
    filas = []
    for i in range(0, len(proy), 2):
        par = [celda(*p) for p in proy[i:i + 2]]
        if len(par) == 1: par.append('<td width="50%"></td>')
        filas.append("  <tr>\n" + "\n".join(par) + "\n  </tr>")
    return "<table>\n" + "\n".join(filas) + "\n</table>"

nav = " ".join(f'<a href="#{c["id"]}"><img src="https://img.shields.io/badge/{quote(c["titulo"].replace(" ","_").replace("-","--"))}-{len(c["proyectos"])}-{c["accent"].lstrip("#")}?style=for-the-badge&labelColor=1a1f2b" alt="{c["titulo"]}"></a>' for c in D["categorias"])
total = sum(len(c["proyectos"]) for c in D["categorias"])

out = f'''<p align="center">
  <img src="./banner.png" alt="Manu Romera · Foundry VTT, sistemas, módulos y herramientas para jugar mejor" width="100%" />
</p>

<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="badges/mr-logo-marfil.svg">
    <img src="badges/mr-logo-negro.svg" alt="Manu Romera · Digital RPG Design" width="360">
  </picture>
</h1>

<p align="center">
  <strong>Diseño experiencias para Foundry VTT donde la tecnología intenta desaparecer detrás de la partida.</strong><br>
  Sistemas completos, aventuras, herramientas y traducciones para mesas virtuales.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Foundry_VTT-13_%7C_14-2B4B6F?style=for-the-badge&logo=foundryvirtualtabletop&logoColor=white" alt="Foundry VTT 13 y 14" />
  <img src="https://img.shields.io/badge/JavaScript-D8A657?style=for-the-badge&logo=javascript&logoColor=1A1F2B" alt="JavaScript" />
  <img src="https://img.shields.io/badge/ES_%7C_EN-i18n-1F6F78?style=for-the-badge" alt="Español e inglés" />
  <img src="https://img.shields.io/badge/{total}_proyectos-7B3F61?style=for-the-badge" alt="{total} proyectos" />
</p>

<p align="center">
  <a href="{IO}ManuRomera/"><b>🌐 Ver como web</b></a> &nbsp;·&nbsp; <a href="https://github.com/ManuRomera?tab=repositories"><b>📚 Todos los repositorios</b></a>
</p>

<p align="center">
{nav}
</p>

<p align="center"><a href="https://github.com/ManuRomera?tab=repositories"><img src="./badges/resumen.svg" alt="Resumen de descargas de todos los proyectos" width="100%"></a></p>

'''
for c in D["categorias"]:
    out += f'<a id="{c["id"]}"></a>\n<p align="center"><img src="./banners/seccion-{c["id"]}.webp" alt="{c["titulo"]}" width="100%"></p>\n\n{tabla(c["proyectos"])}\n\n'
out += '''---

<h2 align="center">🧭 Lo que intento repetir en todos mis proyectos</h2>

<table>
  <tr>
    <td width="33%" valign="top"><b>Una sola herramienta para Foundry 13/14</b><br><sub>Cuando es viable, sin duplicar versiones.</sub></td>
    <td width="33%" valign="top"><b>Ventanas con memoria</b><br><sub>Recuerdan dónde estaban y cuánto medían.</sub></td>
    <td width="33%" valign="top"><b>Información bajo demanda</b><br><sub>Hover o clic derecho; buen uso del espacio de pantalla.</sub></td>
  </tr>
  <tr>
    <td valign="top"><b>Accesibilidad</b><br><sub>Teclado, contraste y reducción de movimiento.</sub></td>
    <td valign="top"><b>Automatizar lo repetitivo</b><br><sub>Sin automatizar las decisiones narrativas.</sub></td>
    <td valign="top"><b>Identidad propia</b><br><sub>Una identidad visual distinta para cada juego.</sub></td>
  </tr>
</table>

<p align="center"><b><i>Menos software visible. Más partida.</i></b></p>

<p align="center"><sub>Gran parte de estos proyectos se desarrolla con apoyo de herramientas de IA para programación, diseño y revisión, siempre bajo mi dirección y revisión final.<br>
Banners y cabeceras generados con <code>scripts/make-banners.py</code>, <code>scripts/make-sections.py</code> y <code>scripts/portada.json</code>; esta página con <code>scripts/make-portada.py</code>.</sub></p>
'''
(ROOT / "README.md").write_text(out, encoding="utf-8")

# --- página web (GitHub Pages) -------------------------------------------------
def cuenta(repo):
    d = DL.get(repo, {})
    return f'<em class="dl">{d["descargas"]:,} descargas</em>'.replace(",", ".") if d.get("descargas") else ""

secs = ""
for c in D["categorias"]:
    cards = ""
    for repo, desc in c["proyectos"]:
        n = NOM.get(repo, repo); href = f"{IO}{repo}/" if repo in PAGES else f"{GH}{repo}"
        cards += (f'<a class="card" href="{href}" style="--a:{c["accent"]}"><img src="{RAW}banners/{repo}.webp" alt="" loading="lazy">'
                  f'<div><small>{c["tipo"]}</small><h3>{escape(n)}</h3><p>{md_i(escape(desc, quote=False))}</p><span>Explorar ↗</span></div>{cuenta(repo)}</a>')
    secs += (f'<section id="{c["id"]}" style="--a:{c["accent"]}"><div class="sh"><h2>{c["titulo"]}</h2><p>{c["lema"]}</p><b>{len(c["proyectos"])}</b></div>'
             f'<div class="grid">{cards}</div></section>')
chips = "".join(f'<a href="#{c["id"]}" style="--a:{c["accent"]}">{c["titulo"]} <b>{len(c["proyectos"])}</b></a>' for c in D["categorias"])
html = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#101118"><title>Proyectos de rol · Manu Romera</title><meta name="description" content="Sistemas, aventuras, herramientas y traducciones de Manu Romera para Foundry VTT.">
<style>
:root{{--bg:#101118;--ink:#f2efe7;--mut:#a9a9b3;--gold:#d6af76}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}a{{color:inherit}}
header,main,footer{{width:min(1220px,calc(100% - 32px));margin:auto}}
header{{padding:22px 0;border-bottom:1px solid #353640;display:flex;justify-content:space-between;gap:20px;align-items:center}}header a{{text-decoration:none}}header strong{{letter-spacing:.1em}}header nav{{display:flex;gap:20px;color:var(--mut)}}
.hero{{margin-top:26px;border-radius:18px;overflow:hidden;position:relative;min-height:340px;display:grid;align-items:end;background:linear-gradient(0deg,rgba(16,17,24,.95),rgba(16,17,24,.25) 70%),url({RAW}banner.png) center/cover}}
.hero div{{padding:40px}}.hero small{{color:var(--gold);text-transform:uppercase;letter-spacing:.2em;font-weight:800}}.hero h1{{font:700 clamp(2.4rem,7vw,5.2rem)/.95 Georgia,serif;margin:.25em 0;letter-spacing:-.03em}}.hero p{{max-width:44rem;color:#d4d4da;font-size:1.15rem;margin:0}}
.panel{{width:100%;margin-top:26px;border-radius:22px;display:block}}.dl{{position:absolute;top:10px;right:10px;background:rgba(10,11,16,.82);color:var(--a);border:1px solid var(--a);font:700 .75rem system-ui;font-style:normal;padding:3px 10px;border-radius:99px;backdrop-filter:blur(4px)}}.card{{position:relative}}.chips{{display:flex;flex-wrap:wrap;gap:10px;padding:26px 0 8px;position:sticky;top:0;background:linear-gradient(var(--bg) 75%,transparent);z-index:5}}
.chips a{{text-decoration:none;border:1px solid var(--a);color:var(--a);padding:9px 16px;border-radius:99px;font-weight:700;font-size:.9rem;transition:.2s}}.chips a b{{opacity:.7;margin-left:6px}}.chips a:hover,.chips a:focus-visible{{background:var(--a);color:#101118;outline:none}}
section{{padding-top:34px}}.sh{{display:grid;grid-template-columns:1fr auto;gap:2px 20px;align-items:end;border-left:5px solid var(--a);padding:2px 0 2px 18px;margin-bottom:20px}}.sh h2{{margin:0;font:700 2.1rem/1.1 Georgia,serif}}.sh p{{margin:0;color:var(--mut);font-style:italic;grid-column:1}}.sh b{{grid-row:1/3;grid-column:2;font:700 3rem/1 Georgia,serif;color:var(--a)}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
.card{{display:flex;flex-direction:column;background:linear-gradient(145deg,#22232c,#181920);border:1px solid #393a43;border-radius:14px;overflow:hidden;text-decoration:none;transition:transform .2s,border-color .2s}}.card:hover,.card:focus-visible{{transform:translateY(-4px);border-color:var(--a);outline:none}}
.card img{{width:100%;aspect-ratio:10/3;object-fit:cover;display:block}}.card div{{padding:16px 18px 18px;display:flex;flex-direction:column;flex:1}}.card small{{color:var(--a);text-transform:uppercase;letter-spacing:.17em;font-weight:800;font-size:.7rem}}.card h3{{margin:6px 0;font-size:1.25rem;line-height:1.15}}.card p{{margin:0;color:var(--mut);font-size:.92rem}}.card span{{margin-top:auto;padding-top:14px;color:var(--a);font-weight:700;font-size:.9rem}}
footer{{border-top:1px solid #353640;margin-top:60px;padding:26px 0 45px;color:var(--mut);font-size:.9rem}}
@media(max-width:960px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:600px){{.grid{{grid-template-columns:1fr}}.hero div{{padding:24px}}.sh h2{{font-size:1.6rem}}}}
@media(prefers-reduced-motion:reduce){{*{{transition:none!important;scroll-behavior:auto!important}}}}
</style></head><body>
<header><strong>MR · MANU ROMERA</strong><nav><a href="https://github.com/ManuRomera">GitHub</a></nav></header>
<main>
<div class="hero"><div><small>Sistemas · aventuras · herramientas · traducciones</small><h1>Proyectos de rol</h1><p>Las herramientas y mundos que voy creando para nuestras mesas de Foundry VTT. Entra en cada proyecto para conocerlo y llegar a su descarga e instalación.</p></div></div>
<img class="panel" src="{RAW}badges/resumen.svg" alt="Resumen de descargas" loading="lazy">
<nav class="chips" aria-label="Categorías">{chips}</nav>
{secs}
</main>
<footer>Manu Romera · Los créditos y condiciones de uso de cada obra figuran en su repositorio.</footer>
</body></html>'''
(ROOT / "docs/index.html").write_text(html, encoding="utf-8")
print("README y docs/index.html listos")
