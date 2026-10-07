"""
anota un recorte de sistema con guías de altura por línea/espacio.
  python guide.py <crop.png> <claves por pentagrama ej. TB o TTBB> [x0 x1 zoom]
salida: <crop>_g.png (y opcionalmente recorte horizontal ampliado)
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# alturas sonoras: índice 0 = línea inferior; pasos de línea/espacio hacia arriba
SCALE = {
    "T": ["A2", "B2", "C3", "D3", "E3", "F3", "G3", "A3", "B3", "C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"],  # E3 es línea 1 (idx 4)
    "B": ["C2", "D2", "E2", "F2", "G2", "A2", "B2", "C3", "D3", "E3", "F3", "G3", "A3", "B3", "C4", "D4", "E4"],  # G2 es línea 1 (idx 4)
}


def staff_lines(im):
    a = np.asarray(im.convert("L")) < 128
    frac = a.mean(axis=1)
    rows = np.where(frac > 0.45)[0]
    groups, cur = [], []
    for r in rows:
        if cur and r - cur[-1] > 1:
            groups.append(cur); cur = []
        cur.append(r)
    if cur: groups.append(cur)
    centers = [sum(g) / len(g) for g in groups]
    # agrupar en pentagramas de 5 con separación regular
    staves, i = [], 0
    while i + 4 < len(centers):
        c = centers[i:i + 5]
        gaps = np.diff(c)
        if gaps.max() - gaps.min() < 4:
            staves.append(c); i += 5
        else:
            i += 1
    return staves


def annotate(path, clefs, x0=None, x1=None, zoom=2.0):
    im = Image.open(path).convert("RGB")
    staves = staff_lines(im)
    if len(staves) != len(clefs):
        print(f"AVISO: {len(staves)} pentagramas detectados, claves={clefs}")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font = ImageFont.load_default()
    W = im.width
    for st, cl in zip(staves, clefs):
        sp = (st[4] - st[0]) / 4
        names = SCALE[cl]
        for k in range(-4, 13):          # k=0 línea inferior; positivo hacia arriba en semi-pasos
            y = st[4] - k * sp / 2
            name = names[4 + k] if 0 <= 4 + k < len(names) else "?"
            if k % 2 == 0:
                col = (220, 0, 0) if 0 <= k <= 8 else (0, 150, 0)
                d.line([(0, y), (W, y)], fill=col, width=1)
            else:
                for x in range(0, W, 12):
                    d.line([(x, y), (x + 5, y)], fill=(0, 90, 220), width=1)
            for x in range(2, W, 500):
                d.text((x, y - 7), name, fill=(120, 0, 120), font=font)
    out = path.replace(".png", "_g.png")
    if x0 is not None:
        im = im.crop((x0, 0, x1, im.height))
        im = im.resize((int(im.width * zoom), int(im.height * zoom)), Image.LANCZOS)
        out = path.replace(".png", f"_g_{x0}.png")
    im.save(out)
    print(out, "staves:", len(staves))


if __name__ == "__main__":
    p, clefs = sys.argv[1], sys.argv[2]
    if len(sys.argv) > 3:
        annotate(p, clefs, int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]) if len(sys.argv) > 5 else 2.0)
    else:
        annotate(p, clefs)
