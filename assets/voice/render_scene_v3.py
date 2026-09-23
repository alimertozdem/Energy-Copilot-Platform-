#!/usr/bin/env python3
"""v3 scene render: browser-framed composite base + gentle zoom + optional cursor(mapped) + slide caption.
Usage: python3 render_scene_v3.py <scene_id> <duration>
"""
import sys, subprocess, os
FPS = 25
# window->final mapping (composite shown full at z=1 -> 1920x1080)
FX0, FY0, SX, SY = 195.0, 203.0, 0.97577, 0.97638
def tf(px, py): return (FX0 + px*SX, FY0 + py*SY)

# cursor cfg in ORIGINAL screenshot coords: (sx,sy,tx,ty,glide)
SCENES = {
 "s01": dict(base="base/s01_intro.png",  motion="card", cursor=None, cap=None, size=(2400,1350)),
 "s02": dict(base="comp/s02.png", motion="zoom", focus=(0.50,0.50), zmax=1.05, cursor=None, cap="cap_s02.png"),
 "s03": dict(base="comp/s03.png", motion="zoom", focus=(0.50,0.50), zmax=1.03, cursor=(1440,600,405,205,0.9), cap="cap_s03.png"),
 "s04": dict(base="comp/s04.png", motion="zoom", focus=(0.50,0.50), zmax=1.03, cursor=(1450,640,1015,397,0.9), cap="cap_s04.png"),
 "s05": dict(base="comp/s05.png", motion="zoom", focus=(0.50,0.50), zmax=1.03, cursor=(1480,620,1020,230,0.9), cap="cap_s05.png"),
 "s06": dict(base="comp/s06.png", motion="zoom", focus=(0.50,0.60), zmax=1.07, cursor=None, cap="cap_s06.png"),
 "s07": dict(base="comp/s07.png", motion="zoom", focus=(0.50,0.50), zmax=1.03, cursor=(360,640,1150,430,0.9), cap="cap_s07.png"),
 "s08": dict(base="comp/s08.png", motion="zoom", focus=(0.50,0.50), zmax=1.03, cursor=(820,560,120,300,0.9), cap="cap_s08.png"),
 "s09": dict(base="comp/s09.png", motion="zoom", focus=(0.50,0.50), zmax=1.05, cursor=None, cap="cap_s09.png"),
 "s10": dict(base="comp/s10.png", motion="zoom", focus=(0.50,0.55), zmax=1.06, cursor=(1450,640,1175,248,0.9), cap="cap_s10.png"),
 "s11": dict(base="comp/s11.png", motion="zoom", focus=(0.50,0.55), zmax=1.06, cursor=None, cap="cap_s11.png"),
 "s12": dict(base="comp/s12.png", motion="zoom", focus=(0.50,0.50), zmax=1.05, cursor=None, cap="cap_s12.png"),
 "s13": dict(base="comp/s13.png", motion="zoom", focus=(0.50,0.50), zmax=1.03, cursor=(1480,620,700,530,0.9), cap="cap_s13.png"),
 "s14": dict(base="base/s14_outro.png", motion="card", cursor=None, cap=None, size=(2400,1350)),
}

def motion(cfg, D):
    nf = int(round(D*FPS))
    if cfg["motion"] == "card":
        bw,bh = cfg.get("size",(2400,1350))
        return (f"[0:v]scale={bw}:{bh},zoompan=z='min(1.0+0.06*on/({D}*{FPS}),1.06)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nf}:s=1920x1080:fps={FPS}[m]")
    fx,fy = cfg["focus"]; zmax = cfg.get("zmax",1.05)
    return (f"[0:v]zoompan=z='min(1.0+{zmax-1.0:.3f}*on/({D}*{FPS}),{zmax})':"
            f"x='iw*{fx}-(iw/zoom/2)':y='ih*{fy}-(ih/zoom/2)':d={nf}:s=1920x1080:fps={FPS}[m]")

def build(sid, D):
    cfg = SCENES[sid]
    ins = ["-loop","1","-t",f"{D}","-i",cfg["base"]]
    idx = {}; n = 1
    if cfg["cursor"]:
        ins += ["-loop","1","-t",f"{D}","-i","cursor.png"]; idx["cur"]=n; n+=1
        ins += ["-loop","1","-t",f"{D}","-i","ring.png"];   idx["ring"]=n; n+=1
    if cfg["cap"]:
        ins += ["-loop","1","-t",f"{D}","-i",f"caps/{cfg['cap']}"]; idx["cap"]=n; n+=1
    chains = [motion(cfg, D)]; cur = "[m]"
    if cfg["cursor"]:
        sx,sy,tx,ty,gt = cfg["cursor"]
        (fsx,fsy),(ftx,fty) = tf(sx,sy), tf(tx,ty)
        ox0,oy0,ox1,oy1 = fsx-6, fsy-4, ftx-6, fty-4
        chains.append(f"{cur}[{idx['cur']}:v]overlay="
                      f"x='{ox0:.1f}+({ox1-ox0:.1f})*min(t/{gt},1)':"
                      f"y='{oy0:.1f}+({oy1-oy0:.1f})*min(t/{gt},1)'[c1]")
        chains.append(f"[c1][{idx['ring']}:v]overlay=x={ftx-110:.0f}:y={fty-110:.0f}:"
                      f"enable='between(t,{gt},{gt+0.5})'[c2]")
        cur = "[c2]"
    if cfg["cap"]:
        chains.append(f"[{idx['cap']}:v]format=rgba,fade=t=in:st=0.3:d=0.4:alpha=1,"
                      f"fade=t=out:st={D-0.5:.2f}:d=0.4:alpha=1[capf]")
        chains.append(f"{cur}[capf]overlay=x=0:y='26*(1-min(t/0.5,1))'[vout]")
        cur = "[vout]"
    fc = ";".join(chains)
    out = f"scenes_v3/{sid}.mp4"
    return (["ffmpeg","-y","-loglevel","error",*ins,"-filter_complex",fc,"-map",cur,
             "-c:v","libx264","-preset","ultrafast","-crf","18","-pix_fmt","yuv420p",
             "-r",str(FPS),"-t",f"{D}","-movflags","+faststart",out], out)

if __name__ == "__main__":
    sid=sys.argv[1]; D=float(sys.argv[2]); os.makedirs("scenes_v3",exist_ok=True)
    cmd,out=build(sid,D)
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode!=0:
        print("ERR",sid); print(r.stderr[-1600:]); sys.exit(1)
    print("OK",out)
