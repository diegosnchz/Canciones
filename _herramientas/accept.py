"""
acepta una canción terminada: copia el DSL al repo, QA, línea en PROGRESO.md, commit y push.
  python accept.py <Carpeta> <Canción> <tanda> "<tonalidad>" "<compás>" <compases> "<advertencias>"
"""
import sys, subprocess, shutil, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import qa as qamod

REPO = Path(r"C:\Users\diego\Canciones")
WORK = Path(r"C:\Users\diego\Canciones_work")


def run(*cmd, check=True):
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        print("ERROR", cmd, r.stdout[-500:], r.stderr[-500:])
        sys.exit(1)
    return r.stdout


def accept(folder, song, tanda, key, time, measures, warn):
    base = REPO / folder / song
    errs, info = qamod.qa(base, int(measures))
    print(info)
    if errs:
        print("QA_FAIL", errs); sys.exit(2)
    src = WORK / "songs" / folder / f"{song}.txt"
    dst = REPO / "_herramientas" / "fuentes" / folder / f"{song}.txt"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    for t in ["dsl.py", "omrtool.py", "export.py", "qa.py", "guide.py", "inventory.py", "accept.py", "PROTOCOLO_AGENTE.md"]:
        shutil.copy(WORK / t, REPO / "_herramientas" / t)
    prog = REPO / "PROGRESO.md"
    s = prog.read_text(encoding="utf-8")
    line = f"✅ {folder}/{song} | {key} | {time} | {measures} | {warn}\n"
    if f"✅ {folder}/{song} |" not in s:
        hdr = f"## Tanda {tanda}"
        i = s.index(hdr); j = s.index("\n", i) + 1
        # insertar al final de la sección
        k = s.find("\n## ", j)
        k = len(s) if k == -1 else k + 1
        s = s[:k].rstrip("\n") + "\n" + line + ("\n" if k < len(s) else "") + s[k:]
        prog.write_text(s, encoding="utf-8")
    run("git", "add", "PROGRESO.md", "_herramientas", f"{folder}/{song}")
    run("git", "commit", "-q", "-m", f"Tanda {tanda}: {song}\n\nTranscripción TTBB: MusicXML, MSCZ, PDF, 4 MIDI, 4 MP3.\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>")
    out = run("git", "push", "-q", "fork", "transcripcion-ttbb", check=False)
    print(run("git", "log", "--oneline", "-1"))
    print("ACEPTADA", folder, song)


if __name__ == "__main__":
    accept(*sys.argv[1:8])
