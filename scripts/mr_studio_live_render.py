#!/usr/bin/env python3
"""Turn a REAL Foundry capture into watermarked portrait/landscape drafts.

Never generates fabricated UI. This is only for external self-published marketing
after manual approval, not the official Foundry package listing.
"""
import argparse
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont
from mr_studio_render import slide, font

VIDEO_LIMIT = 24

def ffprobe(source):
    raw=subprocess.check_output([
        "ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height,duration:format=duration",
        "-of","json",str(source)
    ],timeout=30)
    data=json.loads(raw)
    streams=data.get("streams",[])
    if not streams:
        raise RuntimeError("La captura no contiene vídeo.")
    dur=streams[0].get("duration") or data.get("format",{}).get("duration") or "0"
    seconds=float(dur)
    if seconds<2 or seconds>900:
        raise RuntimeError("Duración de captura no válida (mín. 2 s, máx. 15 min).")
    return seconds

def overlay(size,dest,tag):
    w,h=size
    image=Image.new("RGBA",size,(0,0,0,0))
    d=ImageDraw.Draw(image)
    margin=round(w*.04)
    banner_h=max(60,round(h*.065))
    d.rounded_rectangle((margin,margin,w-margin,margin+banner_h),radius=16,fill=(103,32,48,235))
    f=font(max(20,round(min(w,h)*.026)),True)
    d.text((margin+20,margin+banner_h*.23),"BORRADOR · NO PUBLICAR",font=f,fill=(255,243,234,255))
    footer=f"MR · {tag} · CAPTURA REAL DE FOUNDRY · REVISAR DERECHOS"
    d.rounded_rectangle((margin,h-banner_h-margin,w-margin,h-margin),radius=14,fill=(19,28,39,232))
    d.text((margin+20,h-banner_h-margin+banner_h*.23),footer[:90],font=font(max(16,round(min(w,h)*.018))),fill=(253,245,236,255))
    image.save(dest)

def render(capture,campaign,target,seconds):
    c=json.loads(campaign.read_text(encoding="utf-8"))
    p=c["product"]
    target.mkdir(parents=True,exist_ok=True)
    for size,aspect in [((1080,1920),"vertical"),((1920,1080),"horizontal")]:
        w,h=size
        intro=target/f"live-title-{aspect}.png"
        ending=target/f"live-outro-{aspect}.png"
        watermark=target/f"live-watermark-{aspect}.png"
        slide(size,p,c,None,0).save(intro)
        slide(size,p,c,None,3).save(ending)
        overlay(size,watermark,c["release"]["tag"])
        limit=min(VIDEO_LIMIT,seconds)
        layout=(
            f"[0:v]fps=24,scale={w}:{h},setsar=1,format=yuv420p[t];"
            f"[1:v]fps=24,scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x14202c,"
            "setsar=1[screen];"
            "[screen][3:v]overlay=0:0:shortest=1,format=yuv420p[clip];"
            f"[2:v]fps=24,scale={w}:{h},setsar=1,format=yuv420p[end];"
            "[t][clip][end]concat=n=3:v=1:a=0[v]"
        )
        dest=target/f"live-preview-{aspect}.mp4"
        subprocess.run([
            "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
            "-loop","1","-framerate","24","-t","2.5","-i",str(intro),
            "-t",str(limit),"-i",str(capture),
            "-loop","1","-framerate","24","-t","2.5","-i",str(ending),
            "-loop","1","-framerate","24","-t",str(limit),"-i",str(watermark),
            "-filter_complex",layout,"-map","[v]","-an",
            "-c:v","libx264","-preset","veryfast","-crf","26",
            "-pix_fmt","yuv420p","-movflags","+faststart",str(dest)
        ],check=True,timeout=300)
        if not dest.exists() or dest.stat().st_size<5000:
            raise RuntimeError(f"No se ha producido un vídeo válido: {dest}")
        print("Preview real creada:",dest,"bytes",dest.stat().st_size)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--capture",type=Path,required=True)
    parser.add_argument("--campaign",type=Path,required=True)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    if not args.capture.is_file() or not args.campaign.is_file():
        parser.error("Se necesitan una captura real y una campaña local.")
    data=json.loads(args.campaign.read_text(encoding="utf8"))
    if data.get("publication_enabled") is not False:
        parser.error("La campaña debe estar bloqueada para publicar.")
    duration=ffprobe(args.capture)
    render(args.capture,args.campaign,args.out or args.campaign.parent,duration)

if __name__=="__main__":
    main()
