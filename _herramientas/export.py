"""
exporta una canción: Edicion/partitura.musicxml -> mscz, Partitura_Grupal.pdf, MIDIS/*.mid, MP3/*.mp3
  python export.py <song.txt> <carpeta_base>
"""
import sys, subprocess, shutil, tempfile, copy
from pathlib import Path
from music21 import converter, stream, instrument, metadata, layout
import mido
import dsl

MS = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"
VOICES = [("Tenor1", 0), ("Tenor2", 1), ("Baritono", 2), ("Bajo", 3)]
VEL = {"pp": 40, "p": 55, "mp": 65, "mf": 80, "f": 100, "ff": 120}


def ms(*args):
    r = subprocess.run([MS, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("  musescore error:", r.returncode, (r.stderr or r.stdout)[-400:])
    return r.returncode == 0


def single_part_xml(full_xml, idx, out_xml, title):
    sc = converter.parse(full_xml)
    parts = list(sc.parts)
    part = parts[idx]
    if idx != 0:
        # copiar tempo y textos (rit., etc.) de la primera voz para que el audio sea igual en todas
        from music21 import tempo as m21tempo, expressions as m21expr
        src = {m.number: m for m in parts[0].getElementsByClass(stream.Measure)}
        for m in part.getElementsByClass(stream.Measure):
            sm = src.get(m.number)
            if sm is None: continue
            for el in list(sm.getElementsByClass(m21tempo.MetronomeMark)) + list(sm.getElementsByClass(m21expr.TextExpression)):
                m.insert(sm.elementOffset(el), copy.deepcopy(el))
    new = stream.Score()
    new.metadata = metadata.Metadata(); new.metadata.title = title
    new.insert(0, part)
    new.write("musicxml", fp=out_xml)


def fix_midi(path):
    """un solo track, canal 0, programa 0, velocidad según dinámica (musescore ya lo aplica); comprobar"""
    m = mido.MidiFile(path)
    notes = sum(1 for t in m.tracks for x in t if x.type == "note_on" and x.velocity > 0)
    progs = {x.program for t in m.tracks for x in t if x.type == "program_change"}
    if progs - {0}:
        for t in m.tracks:
            for x in t:
                if x.type == "program_change": x.program = 0
        m.save(path)
    return notes, len(m.tracks)


def export(txt, base):
    base = Path(base)
    ed, mid, mp3 = base / "Edicion", base / "MIDIS", base / "MP3"
    for d in (ed, mid, mp3): d.mkdir(parents=True, exist_ok=True)
    xml = ed / "partitura.musicxml"
    hdr, total, msgs = dsl.convert(txt, str(xml))
    for m in msgs: print("  ", m)
    print(f"  {hdr.get('title')}: {total} compases")
    ok = ms(str(xml), "-o", str(ed / "partitura.mscz"))
    ok &= ms(str(ed / "partitura.mscz"), "-o", str(base / "Partitura_Grupal.pdf"))
    tmp = Path(tempfile.mkdtemp())
    for name, pid in VOICES:
        px = tmp / f"{name}.musicxml"
        single_part_xml(str(xml), pid, str(px), f"{hdr.get('title','')} - {name}")
        ok &= ms(str(px), "-o", str(mid / f"{name}.mid"))
        ok &= ms(str(px), "-o", str(mp3 / f"{name}.mp3"), "-b", "192")
        n, tr = fix_midi(str(mid / f"{name}.mid"))
        print(f"  {name}: midi notas={n} tracks={tr}")
    shutil.rmtree(tmp, ignore_errors=True)
    return ok, hdr, total, msgs


if __name__ == "__main__":
    ok, hdr, total, msgs = export(sys.argv[1], sys.argv[2])
    print("OK" if ok else "FALLO")
