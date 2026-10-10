"""
Genera los banners del perfil con una única plantilla (1600×480): monograma MR, barra de color, título, lema y arte del proyecto.
Uso:  python3 scripts/make-banners.py [repo ...]     (sin argumentos: todos)
El arte se descarga de cada repo (raw.githubusercontent.com) y se guarda en scripts/.cache. Necesita Pillow y la tipografía Georgia.
"""
import json, sys, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "scripts" / ".cache"; CACHE.mkdir(exist_ok=True)
OUT = ROOT / "banners"; OUT.mkdir(exist_ok=True)
W, H = 1600, 480
FONTS = Path("/System/Library/Fonts/Supplemental")
BOLD, ITALIC = FONTS / "Georgia Bold.ttf", FONTS / "Georgia Italic.ttf"
MONOGRAM = ROOT / "brand" / "MR_09_Monograma_Marfil_Transparente.png"
BASE = (10, 12, 15)
IVORY = (245, 239, 226)

def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def fetch(repo, path):
    dest = CACHE / f"{repo}__{path.replace('/', '_')}"
    if not dest.exists():
        url = f"https://raw.githubusercontent.com/ManuRomera/{repo}/main/{urllib.parse.quote(path)}"
        urllib.request.urlretrieve(url, dest)
    return Image.open(dest).convert("RGB")

def cover(img, w, h, focus=(0.5, 0.5)):
    s = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    x = round((img.width - w) * focus[0]); y = round((img.height - h) * focus[1])
    return img.crop((x, y, x + w, y + h))

def hgradient(w, h, stops):
    """Máscara L horizontal: stops = [(x relativo 0..1, alfa 0..255)]."""
    line = Image.new("L", (w, 1))
    px = line.load()
    for x in range(w):
        t = x / (w - 1)
        for (x0, a0), (x1, a1) in zip(stops, stops[1:]):
            if x0 <= t <= x1:
                u = (t - x0) / (x1 - x0 or 1); u = u * u * (3 - 2 * u)
                px[x, 0] = round(a0 + (a1 - a0) * u); break
    return line.resize((w, h))

def abstract(accent):
    bg = Image.new("RGB", (W, H), BASE)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((W * 0.50, -H * 0.35, W * 1.05, H * 1.35), fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(210))
    bg = Image.composite(Image.new("RGB", (W, H), accent), bg, glow)
    mono = Image.open(MONOGRAM).convert("RGBA"); mono = mono.resize((int(H * 0.8 * mono.width / mono.height), int(H * 0.8)), Image.LANCZOS)
    mono.putalpha(mono.getchannel("A").point(lambda v: int(v * 0.10)))
    bg.paste(mono, (W - mono.width - 120, (H - mono.height) // 2), mono)
    return bg

def compose(p):
    accent = hexrgb(p["accent"])
    if "art" not in p:
        bg = abstract(accent)
    else:
        art = fetch(p["repo"], p["art"])
        if p.get("crop"):
            c = p["crop"]; art = art.crop((round(art.width * c[0]), round(art.height * c[1]), round(art.width * c[2]), round(art.height * c[3])))
        bg = Image.new("RGB", (W, H), BASE)
        if p.get("mode") == "right":
            rw = round(W * p.get("region", 0.54)); bg.paste(cover(art, rw, H, p.get("focus", (0.5, 0.5))), (W - rw, 0))
        else:
            bg = cover(art, W, H, p.get("focus", (0.5, 0.5)))
        shade = Image.new("RGB", (W, H), BASE)
        bg = Image.composite(shade, bg, hgradient(W, H, [(0, 250), (0.42, 240), (0.60, 178), (0.80, 48), (1, 14)]))
        vig = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg, Image.linear_gradient("L").resize((W, H)).point(lambda v: int(max(0, v - 150) * 0.9)))
        bg = vig
    bg_before = bg.copy()
    d = ImageDraw.Draw(bg)
    text_layer = Image.new("L", (W, H), 0)
    mono = Image.open(MONOGRAM).convert("RGBA"); mono = mono.resize((round(86 * mono.width / mono.height), 86), Image.LANCZOS)
    bg.paste(mono, (72, 50), mono)
    d.rectangle((72, 130, 79, 254), fill=accent)
    # título: ajustado al ancho disponible
    max_w, size = 1040, 118
    while size > 56:
        f = ImageFont.truetype(str(BOLD), size)
        if d.textlength(p["title"], font=f) <= max_w: break
        size -= 4
    f = ImageFont.truetype(str(BOLD), size)
    ImageDraw.Draw(text_layer).text((108, 192), p["title"], font=f, fill=255, anchor="lm")
    d.text((108, 192), p["title"], font=f, fill=IVORY, anchor="lm")
    # lema
    tf = ImageFont.truetype(str(ITALIC), 34)
    words, lines, cur = p["tagline"].split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=tf) <= 960: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    y = 290
    for line in lines[:2]:
        ImageDraw.Draw(text_layer).text((108, y), line, font=tf, fill=255, anchor="lm")
        y += 46
    # la sombra se pinta ANTES del texto: se rehace la composición con una capa borrosa debajo
    shadow = text_layer.filter(ImageFilter.GaussianBlur(14)).point(lambda v: min(255, int(v * 1.6)))
    base = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg_before, shadow.point(lambda v: int(v * 0.85)))
    d = ImageDraw.Draw(base)
    base.paste(mono, (72, 50), mono)
    d.rectangle((72, 130, 79, 254), fill=accent)
    d.text((108, 192), p["title"], font=f, fill=IVORY, anchor="lm")
    y = 290
    for line in lines[:2]:
        d.text((108, y), line, font=tf, fill=(226, 218, 200), anchor="lm"); y += 46
    return base

def main():
    projects = json.loads((ROOT / "scripts" / "projects.json").read_text(encoding="utf-8"))
    only = set(sys.argv[1:])
    for p in projects:
        if only and p["repo"] not in only: continue
        try:
            compose(p).save(OUT / f"{p['repo']}.webp", "WEBP", quality=90, method=6)
            print("✓", p["repo"])
        except Exception as e:
            print("✗", p["repo"], e)

if __name__ == "__main__":
    main()
