"""
qa de una carpeta base: python qa.py <carpeta_base> [compases_esperados]
"""
import sys, subprocess, json
from pathlib import Path
import xml.etree.ElementTree as ET
import mido

REQ = ["Partitura_Grupal.pdf", "Edicion/partitura.musicxml", "Edicion/partitura.mscz",
       "MIDIS/Tenor1.mid", "MIDIS/Tenor2.mid", "MIDIS/Baritono.mid", "MIDIS/Bajo.mid",
       "MP3/Tenor1.mp3", "MP3/Tenor2.mp3", "MP3/Baritono.mp3", "MP3/Bajo.mp3"]


def qa(base, expected=None):
    base = Path(base); errs = []
    for r in REQ:
        if not (base / r).exists() or (base / r).stat().st_size == 0:
            errs.append(f"falta {r}")
    extra = [p for p in base.rglob("*") if p.is_file() and str(p.relative_to(base)).replace("\\", "/") not in REQ]
    if extra: errs.append(f"ficheros extra: {[str(p.relative_to(base)) for p in extra]}")
    info = {}
    try:
        root = ET.parse(base / "Edicion/partitura.musicxml").getroot()
        parts = root.findall("part")
        info["partes"] = len(parts)
        info["compases"] = len(parts[0].findall("measure")) if parts else 0
        names = [sp.findtext("part-name") for sp in root.find("part-list").findall("score-part")]
        info["nombres"] = names
        progs = {mi.findtext("midi-program") for mi in root.iter("midi-instrument")}
        info["programas"] = sorted(progs)
        if names != ["Tenor 1", "Tenor 2", "Baritono", "Bajo"]: errs.append(f"nombres de parte {names}")
        if progs - {"1"}: errs.append(f"midi-program != 1: {progs}")
        if expected and info["compases"] != expected: errs.append(f"compases {info['compases']} != {expected}")
        lyr = sum(1 for _ in root.iter("lyric"))
        info["silabas"] = lyr
        if lyr == 0: errs.append("sin letra")
    except Exception as e:
        errs.append(f"xml inválido: {e}")
    durs = []
    for v in ["Tenor1", "Tenor2", "Baritono", "Bajo"]:
        try:
            m = mido.MidiFile(base / f"MIDIS/{v}.mid")
            notes = sum(1 for t in m.tracks for x in t if x.type == "note_on" and x.velocity > 0)
            progs = {x.program for t in m.tracks for x in t if x.type == "program_change"}
            chans = {x.channel for t in m.tracks for x in t if x.type == "note_on"}
            if len(m.tracks) != 1: errs.append(f"{v}.mid tracks={len(m.tracks)}")
            if progs - {0}: errs.append(f"{v}.mid programa {progs}")
            if len(chans) > 1: errs.append(f"{v}.mid canales {chans}")
            if notes == 0: errs.append(f"{v}.mid sin notas")
            info[f"notas_{v}"] = notes
        except Exception as e:
            errs.append(f"{v}.mid: {e}")
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(base / f"MP3/{v}.mp3")], capture_output=True, text=True)
            d = float(r.stdout.strip()); durs.append(d)
            if d <= 0: errs.append(f"{v}.mp3 duración 0")
        except Exception as e:
            errs.append(f"{v}.mp3: {e}")
    if durs and max(durs) - min(durs) > 0.5: errs.append(f"duraciones mp3 distintas {durs}")
    info["mp3_seg"] = round(durs[0], 1) if durs else None
    return errs, info


if __name__ == "__main__":
    errs, info = qa(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
    print(json.dumps(info, ensure_ascii=False))
    print("QA_PASS" if not errs else "QA_FAIL " + "; ".join(errs))
