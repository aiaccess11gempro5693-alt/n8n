"""Ужать паузы в озвучке и отрезать «жертвенный» хвост.

python3 tools/trim_voice.py SRC DST --cut SECONDS [--keep 0.5] [--minpause 0.7] [--tempo 1.0]
Паузы длиннее minpause сокращаются до keep (середина паузы сохраняется), звук после cut отрезается
с коротким затуханием, в конце добавляется 0.8 с тишины.
"""
import argparse
import re
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("dst")
ap.add_argument("--cut", type=float, required=True)
ap.add_argument("--keep", type=float, default=0.5)
ap.add_argument("--minpause", type=float, default=0.7)
ap.add_argument("--tempo", type=float, default=1.0)
a = ap.parse_args()
out = subprocess.run(["ffmpeg", "-i", a.src, "-af", f"silencedetect=n=-35dB:d={a.minpause}", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
segs, cur = [], 0.0
for s, e in zip(st, en):
    if s >= a.cut:
        break
    segs.append((cur, s + a.keep / 2))
    cur = e - a.keep / 2
segs.append((cur, a.cut))
f = ";".join(f"[0:a]atrim={x:.3f}:{y:.3f},asetpts=PTS-STARTPTS[s{i}]" for i, (x, y) in enumerate(segs))
tail = f",atempo={a.tempo}" if a.tempo != 1.0 else ""
f += ";" + "".join(f"[s{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1{tail},areverse,afade=t=in:d=0.25,areverse,apad=pad_dur=0.8,asetpts=N/SR/TB[o]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-filter_complex", f, "-map", "[o]", "-b:a", "192k", a.dst],
               check=True)
print(a.dst, subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                       a.dst]).decode().strip())
