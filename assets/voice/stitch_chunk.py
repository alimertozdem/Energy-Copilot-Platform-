#!/usr/bin/env python3
"""xfade(video)+acrossfade(audio) a list of av/sNN.mp4 clips into one chunk.
Usage: python3 stitch_chunk.py <out.mp4> <T> s01 s02 ...
Run from video_v2 dir.
"""
import sys, subprocess

def dur(p):
    return float(subprocess.check_output(
        ['ffprobe','-v','error','-show_entries','format=duration',
         '-of','default=noprint_wrappers=1:nokey=1',p]))

out = sys.argv[1]; T = float(sys.argv[2]); ids = sys.argv[3:]
files = [f"av/{i}.mp4" for i in ids]
ds = [dur(f) for f in files]
ins = []
for f in files: ins += ["-i", f]

chains = []
# video xfade chain
prev = "[0:v]"; running = ds[0]
for i in range(1, len(files)):
    off = running - T
    lbl = f"[v{i}]"
    chains.append(f"{prev}[{i}:v]xfade=transition=fade:duration={T}:offset={off:.3f}{lbl}")
    prev = lbl; running = running + ds[i] - T
vout = prev
# audio acrossfade chain
preva = "[0:a]"
for i in range(1, len(files)):
    lbl = f"[a{i}]"
    chains.append(f"{preva}[{i}:a]acrossfade=d={T}:c1=tri:c2=tri{lbl}")
    preva = lbl
aout = preva

fc = ";".join(chains)
cmd = ["ffmpeg","-y","-loglevel","error",*ins,"-filter_complex",fc,
       "-map",vout,"-map",aout,
       "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",
       "-r","25","-c:a","aac","-b:a","160k","-movflags","+faststart",out]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("ERR"); print(r.stderr[-1800:]); sys.exit(1)
print("OK", out, "expected %.2fs"%(running))
