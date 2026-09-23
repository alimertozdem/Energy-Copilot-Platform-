#!/usr/bin/env python3
"""Composite each screenshot into a browser window on a branded background (2x, 3840x2160).
Usage: python3 generate_composites.py all   (or: s06 s09 ...)
Run from video_v2 dir. Outputs comp/<scene>.png and comp/bg.png
"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 3840, 2160
POPB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
DJV  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
EMER = (52, 211, 153)

SCENES = {
 "s02": ("s02_landing.jpg",     "energy-copilot-platform.vercel.app"),
 "s03": ("s03_connections.jpg", "energy-copilot-platform.vercel.app/connections"),
 "s04": ("s04_modbus.jpg",      "energy-copilot-platform.vercel.app/connections"),
 "s05": ("s05_buildings.jpg",   "energy-copilot-platform.vercel.app/buildings"),
 "s06": ("s06_portfolio.jpg",   "energy-copilot-platform.vercel.app/portfolio"),
 "s07": ("s07_building.jpg",    "energy-copilot-platform.vercel.app/buildings/B001"),
 "s08": ("s08_reports.jpg",     "energy-copilot-platform.vercel.app/buildings/B001/reports"),
 "s09": ("s09_pbi.jpg",         "energy-copilot-platform.vercel.app/demo"),
 "s10": ("s10_actions.jpg",     "energy-copilot-platform.vercel.app/actions"),
 "s11": ("s11_alerts.jpg",      "energy-copilot-platform.vercel.app/alerts"),
 "s12": ("s12_solar.jpg",       "energy-copilot-platform.vercel.app/solar"),
 "s13": ("s13_compliance.jpg",  "energy-copilot-platform.vercel.app/compliance"),
}

def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = yy / H
    base = np.empty((H, W, 3), np.float32)
    top = np.array([12, 24, 36]); bot = np.array([6, 12, 19])
    for c in range(3):
        base[:, :, c] = top[c] * (1 - t) + bot[c] * t
    # emerald glow near top-center
    cx, cy, sig = W * 0.5, H * 0.16, W * 0.34
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sig ** 2)))
    glow = np.array([14, 54, 44])
    for c in range(3):
        base[:, :, c] += glow[c] * g
    # vignette
    dx = (xx - W / 2) / (W / 2); dy = (yy - H / 2) / (H / 2)
    d = np.sqrt(dx * dx + dy * dy)
    vig = 1 - 0.33 * np.clip(d, 0, 1.4) ** 2
    base *= vig[:, :, None]
    # faint dot grid
    base[::72, ::72, :] += 7
    arr = np.clip(base, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")

def rounded_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0]-1, size[1]-1], radius=r, fill=255)
    return m

def wordmark(draw, x, y, size):
    fb = ImageFont.truetype(POPB, size)
    we = draw.textlength("Energy", font=fb)
    draw.text((x, y), "Energy", font=fb, fill=(255,255,255,235))
    draw.text((x+we, y), "Lens", font=fb, fill=(*EMER,235))
    return we + draw.textlength("Lens", font=fb)

def make_window(shot_path, url):
    content_w = 3060
    im = Image.open(shot_path).convert("RGB")
    sc = content_w / im.width
    content_h = int(round(im.height * sc))
    shot = im.resize((content_w, content_h), Image.LANCZOS)
    bar_h = 84
    win = Image.new("RGBA", (content_w, content_h + bar_h), (18, 26, 37, 255))
    d = ImageDraw.Draw(win)
    d.rectangle([0, 0, content_w, bar_h], fill=(19, 27, 38, 255))
    # traffic dots
    cyd = bar_h // 2
    for i, col in enumerate([(255,95,87),(254,188,46),(40,200,64)]):
        cx = 44 + i*46
        d.ellipse([cx-13, cyd-13, cx+13, cyd+13], fill=col)
    # url pill
    pw, ph = int(content_w*0.5), int(bar_h*0.56)
    px = (content_w - pw)//2; py = (bar_h - ph)//2
    d.rounded_rectangle([px, py, px+pw, py+ph], radius=ph//2, fill=(9, 16, 25, 255))
    f = ImageFont.truetype(DJV, 30)
    # small lock
    lx = px+34; ly = cyd
    d.rounded_rectangle([lx, ly-3, lx+16, ly+11], radius=3, fill=(120,140,160))
    d.arc([lx+2, ly-12, lx+14, ly+2], 180, 360, fill=(120,140,160), width=3)
    tw = d.textlength(url, font=f)
    d.text((px+pw/2 - tw/2 + 16, cyd - 20), url, font=f, fill=(150, 172, 192))
    # screenshot
    win.paste(shot, (0, bar_h))
    # round corners
    win.putalpha(rounded_mask(win.size, 34))
    return win

def composite(scene, bg):
    shot, url = SCENES[scene]
    win = make_window(f"src/{shot}", url)
    canvas = bg.copy()
    x0 = (W - win.width)//2
    y0 = 286
    # shadow
    sh = Image.new("RGBA", (W, H), (0,0,0,0))
    shm = Image.new("L", win.size, 0)
    ImageDraw.Draw(shm).rounded_rectangle([0,0,win.width-1,win.height-1], radius=34, fill=150)
    sh.paste((0,0,0,255), (x0, y0+34), shm)
    sh = sh.filter(ImageFilter.GaussianBlur(46))
    canvas = Image.alpha_composite(canvas, sh)
    canvas.alpha_composite(win, (x0, y0))
    # watermark
    d = ImageDraw.Draw(canvas)
    wmw = wordmark(d, 0, 0, 44)  # measure not needed; draw directly:
    # redraw at position
    canvas2 = canvas
    dd = ImageDraw.Draw(canvas2)
    fb = ImageFont.truetype(POPB, 46)
    total = dd.textlength("EnergyLens", font=fb)
    wx = W - total - 70; wy = H - 96
    we = dd.textlength("Energy", font=fb)
    dd.text((wx, wy), "Energy", font=fb, fill=(255,255,255,200))
    dd.text((wx+we, wy), "Lens", font=fb, fill=(*EMER,220))
    canvas2.convert("RGB").save(f"comp/{scene}.png")
    print("comp", scene)

if __name__ == "__main__":
    import os
    os.makedirs("comp", exist_ok=True)
    bg = make_bg()
    bg.convert("RGB").save("comp/bg.png")
    args = sys.argv[1:]
    ids = list(SCENES.keys()) if (not args or args==["all"]) else args
    for s in ids:
        composite(s, bg)
