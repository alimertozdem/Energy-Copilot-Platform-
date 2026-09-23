#!/usr/bin/env python3
"""Render one cinematic scene: motion + optional cursor/click + caption. Silent.
Usage: python3 render_scene.py <scene_id> <duration_seconds>
Run from the video_v2 working dir (expects base/, caps/, cursor.png, ring.png).
"""
import sys, subprocess, os

FPS = 25
BW, BH = 3136, 1376  # screenshot base size

# cursor tuple = (sx, sy, tx, ty, glide_time)
SCENES = {
 "s01": dict(base="s01_intro.png",       motion="card",          size=(2400,1350), cursor=None, cap=None),
 "s02": dict(base="s02_landing.png",     motion="zoom", focus=(0.50,0.44), zmax=1.10, cursor=None, cap="cap_s02.png"),
 "s03": dict(base="s03_connections.png", motion="pan_lr", xr=(60,1120), cursor=(1480,880,720,360,1.2), cap="cap_s03.png"),
 "s04": dict(base="s04_modbus.png",      motion="zoom", focus=(0.63,0.62), zmax=1.16, cursor=(1460,900,1245,505,1.2), cap="cap_s04.png"),
 "s05": dict(base="s05_buildings.png",   motion="pan_lr", xr=(60,1120), cursor=(1500,880,1020,290,1.2), cap="cap_s05.png"),
 "s06": dict(base="s06_portfolio.png",   motion="pan_lr", xr=(1120,60), cursor=None, cap="cap_s06.png"),
 "s07": dict(base="s07_building.png",    motion="zoom", focus=(0.74,0.52), zmax=1.15, cursor=(360,900,1150,430,1.2), cap="cap_s07.png"),
 "s08": dict(base="s08_reports.png",     motion="pan_lr", xr=(60,900), cursor=(760,560,150,300,1.1), cap="cap_s08.png"),
 "s09": dict(base="s09_pbi.png",         motion="zoom", focus=(0.50,0.46), zmax=1.13, cursor=None, cap="cap_s09.png"),
 "s10": dict(base="s10_actions.png",     motion="zoom", focus=(0.60,0.64), zmax=1.16, cursor=(1460,900,1180,470,1.2), cap="cap_s10.png"),
 "s11": dict(base="s11_alerts.png",      motion="pan_down", xc=608, yr=(30,290), cursor=None, cap="cap_s11.png"),
 "s12": dict(base="s12_solar.png",       motion="pan_lr", xr=(60,1120), cursor=None, cap="cap_s12.png"),
 "s13": dict(base="s13_compliance.png",  motion="pan_lr", xr=(60,1120), cursor=(1500,880,760,530,1.2), cap="cap_s13.png"),
 "s14": dict(base="s14_outro.png",       motion="card",  size=(2400,1350), cursor=None, cap=None),
}

def motion(cfg, D):
    m = cfg["motion"]; nf = int(round(D*FPS))
    if m == "card":
        bw,bh = cfg.get("size",(2400,1350))
        return (f"[0:v]scale={bw}:{bh},zoompan=z='min(1.0+0.06*on/({D}*{FPS}),1.06)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nf}:s=1920x1080:fps={FPS}[m]")
    if m == "zoom":
        fx,fy = cfg["focus"]; zmax = cfg.get("zmax",1.13)
        return (f"[0:v]zoompan=z='min(1.0+{zmax-1.0:.3f}*on/({D}*{FPS}),{zmax})':"
                f"x='iw*{fx}-(iw/zoom/2)':y='ih*{fy}-(ih/zoom/2)':d={nf}:s=1920x1080:fps={FPS}[m]")
    if m == "pan_lr":
        x0,x1 = cfg.get("xr",(60,1120)); yc = cfg.get("yc",148)
        return f"[0:v]crop=1920:1080:x='{x0}+({x1-x0})*(t/{D})':y={yc},fps={FPS}[m]"
    if m == "pan_down":
        xc = cfg.get("xc",608); y0,y1 = cfg.get("yr",(30,290))
        return f"[0:v]crop=1920:1080:x={xc}:y='{y0}+({y1-y0})*(t/{D})',fps={FPS}[m]"
    raise SystemExit("bad motion "+m)

def build(sid, D):
    cfg = SCENES[sid]
    ins = ["-loop","1","-t",f"{D}","-i",f"base/{cfg['base']}"]
    idx = {}; n = 1
    if cfg["cursor"]:
        ins += ["-loop","1","-t",f"{D}","-i","cursor.png"]; idx["cur"]=n; n+=1
        ins += ["-loop","1","-t",f"{D}","-i","ring.png"];   idx["ring"]=n; n+=1
    if cfg["cap"]:
        ins += ["-loop","1","-t",f"{D}","-i",f"caps/{cfg['cap']}"]; idx["cap"]=n; n+=1

    chains = [motion(cfg, D)]
    cur_lbl = "[m]"
    if cfg["cursor"]:
        sx,sy,tx,ty,gt = cfg["cursor"]
        ox0, oy0 = sx-6, sy-4; ox1, oy1 = tx-6, ty-4
        chains.append(
            f"{cur_lbl}[{idx['cur']}:v]overlay="
            f"x='{ox0}+({ox1-ox0})*min(t/{gt},1)':y='{oy0}+({oy1-oy0})*min(t/{gt},1)'[c1]")
        rx, ry = tx-110, ty-110
        chains.append(
            f"[c1][{idx['ring']}:v]overlay=x={rx}:y={ry}:enable='between(t,{gt},{gt+0.5})'[c2]")
        cur_lbl = "[c2]"
    if cfg["cap"]:
        chains.append(
            f"[{idx['cap']}:v]format=rgba,fade=t=in:st=0.4:d=0.45:alpha=1,"
            f"fade=t=out:st={D-0.6:.2f}:d=0.5:alpha=1[capf]")
        chains.append(f"{cur_lbl}[capf]overlay=0:0[vout]")
        cur_lbl = "[vout]"
    fc = ";".join(chains)
    out = f"scenes/{sid}.mp4"
    cmd = ["ffmpeg","-y","-loglevel","error",*ins,
           "-filter_complex",fc,"-map",cur_lbl,
           "-c:v","libx264","-preset","veryfast","-crf","20",
           "-pix_fmt","yuv420p","-r",str(FPS),"-t",f"{D}","-movflags","+faststart",out]
    return cmd, out

if __name__ == "__main__":
    sid = sys.argv[1]; D = float(sys.argv[2])
    os.makedirs("scenes", exist_ok=True)
    cmd, out = build(sid, D)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ERR", sid); print(r.stderr[-1500:]); sys.exit(1)
    print("OK", out)
