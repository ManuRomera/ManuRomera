"""Cabeceras de sección del perfil (1600×170) a partir de scripts/portada.json -> banners/seccion-<id>.webp"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = Path(__file__).resolve().parent.parent
FONTS = Path("/System/Library/Fonts/Supplemental")
BOLD, ITALIC = FONTS / "Georgia Bold.ttf", FONTS / "Georgia Italic.ttf"
W, H = 1600, 170
hexrgb = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
data = json.loads((ROOT / "scripts/portada.json").read_text(encoding="utf-8"))
mono0 = Image.open(ROOT / "brand/MR_09_Monograma_Marfil_Transparente.png").convert("RGBA")
for c in data["categorias"]:
    ac = hexrgb(c["accent"])
    bg = Image.new("RGB", (W, H), (13, 15, 20))
    glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).ellipse((-200, -260, 700, 330), fill=95)
    bg = Image.composite(Image.new("RGB", (W, H), ac), bg, glow.filter(ImageFilter.GaussianBlur(120)))
    mono = mono0.resize((round(H * .9 * mono0.width / mono0.height), round(H * .9)), Image.LANCZOS)
    mono.putalpha(mono.getchannel("A").point(lambda v: int(v * .09)))
    bg.paste(mono, (W - mono.width - 60, (H - mono.height) // 2), mono)
    d = ImageDraw.Draw(bg)
    d.rectangle((0, 0, W, 3), fill=ac); d.rectangle((0, H - 2, W, H), fill=tuple(int(v * .35) for v in ac))
    d.rectangle((64, 38, 70, 132), fill=ac)
    tf = ImageFont.truetype(str(BOLD), 62); d.text((96, 66), c["titulo"], font=tf, fill=(245, 239, 226), anchor="lm")
    sf = ImageFont.truetype(str(ITALIC), 28); d.text((98, 116), c["lema"], font=sf, fill=(205, 198, 182), anchor="lm")
    n = str(len(c["proyectos"]))
    nf = ImageFont.truetype(str(BOLD), 74); d.text((W - 110, 70), n, font=nf, fill=ac, anchor="rm")
    lf = ImageFont.truetype(str(ITALIC), 24); d.text((W - 110, 118), "proyecto" if n == "1" else "proyectos", font=lf, fill=(205, 198, 182), anchor="rm")
    bg.save(ROOT / "banners" / f"seccion-{c['id']}.webp", "WEBP", quality=92, method=6)
    print("✓", c["id"])
