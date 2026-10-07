"""
omr + recortes por sistema + borrador dsl
  python omrtool.py run  <pdf> <workdir> [lang]
  python omrtool.py crops <workdir>          -> workdir/crops/pN_sM.png (300dpi gris, por sistema)
  python omrtool.py draft <workdir>          -> workdir/draft.txt
"""
import sys, os, re, zipfile, subprocess, shutil
from pathlib import Path
from fractions import Fraction

AV = r"C:\Users\diego\Canciones_work\audiveris\Audiveris\Audiveris.exe"


def run(pdf, work, lang="spa+eng"):
    work = Path(work); work.mkdir(parents=True, exist_ok=True)
    dst = work / "in.pdf"
    shutil.copy(pdf, dst)
    for f in work.glob("in.*"):
        if f.suffix in (".omr", ".mxl"):
            f.unlink()
    cmd = [AV, "-batch", "-transcribe", "-export", "-output", str(work),
           "-constant", f"org.audiveris.omr.text.Language.defaultSpecification={lang}", "--", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = work / "audiveris.log"
    log.write_text(r.stdout + r.stderr, encoding="utf-8")
    ok = (work / "in.mxl").exists()
    print("OMR", "OK" if ok else "FALLO", work)
    return ok


def systems(work):
    """[(page, [ (staff_top, staff_bottom), ... ]), ...] en píxeles 300dpi"""
    work = Path(work)
    out = []
    with zipfile.ZipFile(work / "in.omr") as z:
        names = sorted(n for n in z.namelist() if re.match(r"sheet#\d+/sheet#\d+\.xml", n))
        for n in names:
            page = int(re.search(r"sheet#(\d+)/", n).group(1))
            x = z.read(n).decode("utf-8")
            systs = []
            for sm in re.finditer(r"<system [^>]*>(.*?)</system>", x, re.S):
                staves = []
                for st in re.finditer(r"<staff [^>]*>(.*?)</staff>", sm.group(1), re.S):
                    ys = [float(v) for v in re.findall(r'<point x="[\d.]+" y="([\d.]+)"/>', st.group(1))]
                    if ys:
                        staves.append((min(ys), max(ys)))
                if staves:
                    systs.append(staves)
            out.append((page, systs))
    return out


def crops(work, dpi=300):
    import pymupdf
    work = Path(work)
    cdir = work / "crops"; cdir.mkdir(exist_ok=True)
    for f in cdir.glob("*.png"): f.unlink()
    doc = pymupdf.open(work / "in.pdf")
    sy = systems(work)
    for page, systs in sy:
        pg = doc[page - 1]
        pix = pg.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
        from PIL import Image
        im = Image.frombytes("L", (pix.width, pix.height), pix.samples)
        W, H = im.size
        # escala si audiveris usó otra resolución
        full = pg.get_pixmap(dpi=dpi).height
        for i, staves in enumerate(systs):
            top = min(s[0] for s in staves); bot = max(s[1] for s in staves)
            y0 = max(0, int(top - 90)); y1 = min(H, int(bot + 110))
            box = im.crop((0, y0, W, y1))
            box.save(cdir / f"p{page}_s{i+1}.png")
    print("crops:", len(list(cdir.glob('*.png'))))


def q(x):
    return Fraction(x).limit_denominator(12)


def tok(ql, pname):
    """quarterLength -> token dsl"""
    ql = q(ql)
    table = {Fraction(4): "/1", Fraction(2): "/2", Fraction(1): "", Fraction(1, 2): "/8", Fraction(1, 4): "/16",
             Fraction(6): "/1.", Fraction(3): "/2.", Fraction(3, 2): ".", Fraction(3, 4): "/8.", Fraction(3, 8): "/16."}
    if ql in table:
        return pname + table[ql]
    if ql == Fraction(2, 3): return pname + "/8(3)"
    if ql == Fraction(1, 3): return pname + "/16(3)"
    return pname + f"/?{ql}"


def draft(work):
    from music21 import converter
    work = Path(work)
    s = converter.parse(work / "in.mxl")
    parts = list(s.parts)
    lines = []
    lines.append("# borrador OMR - verificar cada nota contra crops/")
    nparts = len(parts)
    lines.append(f"# partes OMR: {nparts}")
    # agrupar por compás
    measures = {}
    lyr = {}
    for pi, p in enumerate(parts):
        for m in p.getElementsByClass("Measure"):
            evs = []
            for n in m.recurse().notesAndRests:
                off = q(n.getOffsetInHierarchy(m))
                if n.isRest:
                    evs.append((off, None, q(n.quarterLength)))
                else:
                    for pt in (n.pitches if n.isChord else [n.pitch]):
                        evs.append((off, pt, q(n.quarterLength)))
                for l in n.lyrics:
                    if l.text:
                        lyr.setdefault(m.number, []).append((off, pi, l.text.replace("\n", " ")))
            measures.setdefault(m.number, {})[pi] = (evs, m)
    nums = sorted(measures)

    def line(evs, upper):
        onsets = sorted(set(e[0] for e in evs))
        out = []; t = Fraction(0); end = Fraction(0)
        for o in onsets:
            if o < end:
                continue
            here = [e for e in evs if e[0] == o and e[1] is not None]
            if not here:
                rests = [e for e in evs if e[0] == o]
                if rests:
                    out.append(tok(rests[0][2], "r")); end = o + rests[0][2]
                continue
            e = max(here, key=lambda e: e[1].ps) if upper else min(here, key=lambda e: e[1].ps)
            nm = e[1].name.replace("-", "b").lower() + str(e[1].octave)
            out.append(tok(e[2], nm)); end = o + e[2]
        return " ".join(out)

    per_sys = 4
    for i in range(0, len(nums), per_sys):
        chunk = nums[i:i + per_sys]
        lines.append(f"\n@{chunk[0]}")
        hdr = []
        for n in chunk:
            m0 = measures[n].get(0, (None, None))[1]
            if m0 is not None:
                ks = m0.keySignature; ts = m0.timeSignature
                if ks is not None: hdr.append(f"c{n} key:{ks.asKey().tonic.name}{'m' if ks.asKey().mode=='minor' else ''}")
                if ts is not None: hdr.append(f"c{n} time:{ts.ratioString}")
                if m0.leftBarline is not None: hdr.append(f"c{n} left:{m0.leftBarline.type}")
                if m0.rightBarline is not None: hdr.append(f"c{n} right:{m0.rightBarline.type}")
        if hdr: lines.append("# " + "  ".join(hdr))
        if nparts >= 4:
            mapping = {"T1": (0, True), "T2": (1, True), "B1": (2, True), "B2": (3, True)}
        else:
            mapping = {"T1": (0, True), "T2": (0, False), "B1": (1, True), "B2": (1, False)}
        for vn, (pi, upper) in mapping.items():
            segs = []
            for n in chunk:
                evs = measures[n].get(pi, ([], None))[0]
                segs.append(line(evs, upper))
            lines.append(f"{vn}: " + " | ".join(segs))
        ls = []
        for n in chunk:
            ws = sorted(lyr.get(n, []), key=lambda x: (x[1], x[0]))
            ls.append(" ".join(w for _, _, w in ws))
        lines.append("L: " + " | ".join(ls))
    (work / "draft.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("draft:", work / "draft.txt", len(nums), "compases")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run":
        run(sys.argv[2], sys.argv[3], *(sys.argv[4:5]))
    elif cmd == "crops":
        crops(sys.argv[2])
    elif cmd == "draft":
        draft(sys.argv[2])
    elif cmd == "all":
        if run(sys.argv[2], sys.argv[3], *(sys.argv[4:5])):
            crops(sys.argv[3]); draft(sys.argv[3])
