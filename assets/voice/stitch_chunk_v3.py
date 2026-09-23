#!/usr/bin/env python3
"""xfade(varied)+acrossfade a list of av_v3 clips. Usage: stitch_chunk_v3.py out.mp4 T off s01 s02 ..."""
import sys, subprocess
def dur(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',p]))
out=sys.argv[1]; T=float(sys.argv[2]); off=int(sys.argv[3]); ids=sys.argv[4:]
files=[f"av_v3/{i}.mp4" for i in ids]; ds=[dur(f) for f in files]
CYC=["fade","smoothleft","fade","smoothup","fade","smoothright"]
ins=[]
for f in files: ins+=["-i",f]
ch=[]; prev="[0:v]"; run=ds[0]
for i in range(1,len(files)):
    tr=CYC[(off+i-1)%len(CYC)]
    o=run-T; lbl=f"[v{i}]"
    ch.append(f"{prev}[{i}:v]xfade=transition={tr}:duration={T}:offset={o:.3f}{lbl}")
    prev=lbl; run=run+ds[i]-T
va=prev; pa="[0:a]"
for i in range(1,len(files)):
    lbl=f"[a{i}]"; ch.append(f"{pa}[{i}:a]acrossfade=d={T}:c1=tri:c2=tri{lbl}"); pa=lbl
fc=";".join(ch)
cmd=["ffmpeg","-y","-loglevel","error",*ins,"-filter_complex",fc,"-map",va,"-map",pa,
     "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-r","25",
     "-c:a","aac","-b:a","160k","-movflags","+faststart",out]
r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode!=0: print("ERR");print(r.stderr[-1600:]);sys.exit(1)
print("OK",out,"%.2fs"%run)
