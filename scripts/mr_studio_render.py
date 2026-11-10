#!/usr/bin/env python3
"""Render watermarked 20s silent preview videos from repo-owned screenshots."""
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.request import Request, urlopen
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path("studio/output")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(size, bold=False):
    try:
        return ImageFont.truetype(BOLD if bold else FONT, size)
    except OSError:
        return ImageFont.load_default()

def wrap(draw, text, f, width):
    words=str(text).split()
    lines=[]
    current=""
    for word in words:
        proposal=(current+" "+word).strip()
        if current and draw.textbbox((0,0),proposal,font=f)[2]>width:
            lines.append(current)
            current=word
        else:
            current=proposal
    if current:
        lines.append(current)
    return lines

def multiline(draw,text,x,y,f,width,fill,max_lines=5,line_gap=12):
    for line in wrap(draw,text,f,width)[:max_lines]:
        draw.text((x,y),line,font=f,fill=fill)
        y += int(getattr(f,"size",34)*1.35)+line_gap
    return y

def get_image(repo,path):
    if not path.startswith("docs/img/") or ".." in path:
        raise ValueError("Ruta visual fuera de lista blanca")
    url=f"https://raw.githubusercontent.com/ManuRomera/{repo}/main/{path}"
    with urlopen(Request(url,headers={"User-Agent":"MR-Studio-Pilot/0.1"}),timeout=25) as r:
        raw=r.read(12_000_001)
    if len(raw)>12_000_000:
        raise ValueError("Recurso demasiado grande")
    from io import BytesIO
    im=Image.open(BytesIO(raw))
    im.seek(0)
    return im.convert("RGB")

def gradient(size):
    w,h=size
    im=Image.new("RGB",size)
    top=(16,24,34)
    bottom=(51,20,32)
    px=im.load()
    for y in range(h):
        ratio=y/max(h-1,1)
        col=tuple(round(a*(1-ratio)+b*ratio) for a,b in zip(top,bottom))
        for x in range(w):
            px[x,y]=col
    return im

def slide(size,p,c,shot,scene_index):
    w,h=size
    im=gradient(size)
    dr=ImageDraw.Draw(im)
    pad=int(w*0.066)
    top=int(h*0.052)
    fs=lambda n:round(n*min(w/1080,h/1920 if h>w else h/1080))
    # Explicitly label unfinished previews, including any cropped extracts.
    dr.rounded_rectangle((pad,top,pad+fs(500),top+fs(62)),radius=fs(12),fill=(118,39,60))
    dr.text((pad+fs(20),top+fs(11)),"BORRADOR · NO PUBLICAR",font=font(fs(28),True),fill=(255,238,238))
    y=top+fs(115)
    dr.text((pad,y),"MR / MANU ROMERA",font=font(fs(31),True),fill=(219,185,135))
    y+=fs(70)
    name=p["name"]
    y=multiline(dr,name,pad,y,font(fs(66),True),w-pad*2,(250,245,237),max_lines=2,line_gap=fs(7))
    y+=fs(22)
    if scene_index==0:
        body=c["copy"]["hook"]
    elif scene_index==1:
        body=p["description"]
    elif scene_index==2:
        body=c["highlights"][0]
    else:
        body="Novedades y descarga en GitHub"
    y=multiline(dr,body,pad,y,font(fs(38)),w-pad*2,(239,226,209),max_lines=4,line_gap=fs(5))
    if shot is not None:
        box=(pad,int(h*0.47),w-pad,int(h*0.82))
        dr.rounded_rectangle((box[0]-fs(10),box[1]-fs(10),box[2]+fs(10),box[3]+fs(10)),
            radius=fs(20), fill=(228,205,169))
        fit=ImageOps.contain(shot,(box[2]-box[0],box[3]-box[1]),method=Image.Resampling.LANCZOS)
        im.paste(fit,(int((w-fit.width)/2),int((box[1]+box[3]-fit.height)/2)))
    else:
        line_y=int(h*0.67)
        dr.line((pad,line_y,w-pad,line_y),fill=(181,123,95),width=max(fs(3),2))
        if scene_index==3:
            multiline(dr,p["landing"],pad,line_y+fs(40),font(fs(28)),w-pad*2,(219,185,135),max_lines=3)
    footer=f"{c['release']['tag']}  ·  PREVISUALIZACIÓN SIN AUDIO  ·  REVISAR DERECHOS"
    multiline(dr,footer,pad,int(h*0.92),font(fs(23)),w-pad*2,(211,197,184),max_lines=2)
    return im

def encode(slides,folder,dest):
    manifest=folder/(dest.stem+".txt")
    lengths=[4,6,6,4]
    # The concat demuxer accepts image files and durations for still-image videos.
    entries=[]
    for path,secs in zip(slides,lengths):
        entries.append("file '"+str(path.resolve()).replace("'","'\\''")+"'")
        entries.append("duration "+str(secs))
    entries.append("file '"+str(slides[-1].resolve()).replace("'","'\\''")+"'")
    manifest.write_text("\n".join(entries)+"\n",encoding="utf8")
    cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        "-safe","0","-f","concat","-i",str(manifest),
        "-vf","fps=24,format=yuv420p","-c:v","libx264","-preset","veryfast",
        "-crf","24","-movflags","+faststart","-an",str(dest)]
    subprocess.run(cmd,check=True,timeout=180)
    print("Vídeo borrador:",dest)

def process(path):
    c=json.loads(path.read_text(encoding="utf8"))
    prod=c["product"]
    frames=[]
    for rel in prod.get("media",[])[:2]:
        try:
            frames.append(get_image(prod["repo"],rel))
        except Exception as exc:
            print("No se pudo descargar captura",rel,str(exc),file=sys.stderr)
    if not frames:
        print("SKIP video: no hay capturas verificables. Sólo copys.",path)
        return
    for size,label in [((1080,1920),"vertical"),((1920,1080),"horizontal")]:
        folder=path.parent/("slides-"+label)
        folder.mkdir(exist_ok=True,parents=True)
        shots=[None,frames[0],frames[-1],None]
        files=[]
        for i,shot in enumerate(shots):
            target=folder/f"{i:02d}.png"
            slide(size,prod,c,shot,i).save(target,optimize=True)
            files.append(target)
        encode(files,folder,path.parent/("preview-"+label+".mp4"))

def main():
    if not ROOT.exists():
        return
    for item in ROOT.glob("*/**/campaign.json"):
        try:
            process(item)
        except (OSError,ValueError,subprocess.SubprocessError) as exc:
            print("Fallo de render:",item,exc,file=sys.stderr)

if __name__=="__main__":
    main()
