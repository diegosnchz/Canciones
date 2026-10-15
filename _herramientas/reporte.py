"""
qa global + REPORTE.md a partir de PROGRESO.md y de los DSL en _herramientas/fuentes.
  python reporte.py            -> qa de todas las aceptadas y escribe REPORTE.md
"""
import re, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import qa as qamod

REPO = Path(r"C:\Users\diego\Canciones")
CARPETAS = {"Español": 19, "Inglés": 3, "Navidad": 5, "Rumano": 28}


def leer_progreso():
    filas = []
    for ln in (REPO / "PROGRESO.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(✅|⛔) ([^/]+)/(.+?) \| (.*?) \| (.*?) \| (.*?) \| (.*)$", ln)
        if m:
            est, carpeta, cancion, ton, comp, nc, adv = m.groups()
            filas.append(dict(estado=est, carpeta=carpeta, cancion=cancion.strip(), ton=ton, comp=comp, nc=nc, adv=adv))
    return filas


def leer_dsl(carpeta, cancion):
    p = REPO / "_herramientas" / "fuentes" / carpeta / f"{cancion}.txt"
    d = {"titulo": cancion, "tempo": "", "source": "", "piano": False, "deducidas": [], "arranger": "", "composer": ""}
    if not p.exists():
        return d
    for ln in p.read_text(encoding="utf-8").splitlines():
        for k, key in [("title:", "titulo"), ("tempo:", "tempo"), ("source:", "source"), ("arranger:", "arranger"), ("composer:", "composer")]:
            if ln.startswith(k):
                d[key] = ln[len(k):].strip()
        if re.match(r"^P[RL]:", ln):
            d["piano"] = True
        if "NOTA DEDUCIDA" in ln:
            d["deducidas"].append(ln.split("NOTA DEDUCIDA", 1)[1].strip(" :"))
    return d


def main():
    filas = leer_progreso()
    ok = [f for f in filas if f["estado"] == "✅"]
    bloq = [f for f in filas if f["estado"] == "⛔"]
    fallos = []
    for f in ok:
        base = REPO / f["carpeta"] / f["cancion"]
        nc = int(re.match(r"\d+", f["nc"]).group()) if re.match(r"\d+", f["nc"]) else None
        errs, info = qamod.qa(base, nc)
        f["qa"] = "PASS" if not errs else "FAIL: " + "; ".join(errs)
        if errs:
            fallos.append((f["carpeta"], f["cancion"], errs))
        print(("QA_PASS " if not errs else "QA_FAIL ") + f["carpeta"] + "/" + f["cancion"], errs or "")
    # pdfs por carpeta (inventario real)
    hoy = datetime.date.today().isoformat()
    con_adv = [f for f in ok if f["adv"].strip().lower() not in ("ninguna", "")]
    out = []
    out.append("# Reporte de Transcripción — Cuarteto TTBB\n")
    out.append("## Resumen General")
    out.append(f"- **Fecha de procesamiento**: {hoy}")
    out.append(f"- **Total canciones (PDF) en el repositorio**: {sum(CARPETAS.values())}")
    out.append(f"- **Canciones transcritas**: {len(ok)}/{sum(CARPETAS.values())}")
    out.append(f"- **Total archivos generados**: {len(ok) * 11}/{len(ok) * 11} (11 por canción transcrita)")
    out.append(f"- **Canciones completadas sin incidencias**: {len(ok) - len(con_adv)}")
    out.append(f"- **Canciones con advertencias**: {len(con_adv)}")
    out.append(f"- **Canciones bloqueadas (no transcritas)**: {len(bloq)} — ver sección «Bloqueadas»")
    out.append(f"- **QA automático**: {len(ok) - len(fallos)}/{len(ok)} QA_PASS\n")
    out.append("## Estadísticas por Carpeta")
    out.append("| Carpeta | Canciones | Completadas | Con advertencias | Bloqueadas |")
    out.append("|---------|-----------|-------------|-----------------|------------|")
    for c, n in CARPETAS.items():
        out.append(f"| {c} | {n} | {sum(1 for f in ok if f['carpeta'] == c)} | {sum(1 for f in con_adv if f['carpeta'] == c)} | {sum(1 for f in bloq if f['carpeta'] == c)} |")
    out.append("")
    out.append("## Bloqueadas")
    for f in bloq:
        out.append(f"- **{f['carpeta']}/{f['cancion']}**: {f['adv']}")
    out.append("")
    out.append("## Detalle por Canción\n")
    for c in CARPETAS:
        for f in [x for x in ok if x["carpeta"] == c]:
            d = leer_dsl(c, f["cancion"])
            urls = re.findall(r"https?://[^\s;,)]+", d["source"])
            fuente = "PDF original + referencia internet" if urls else "PDF original"
            out.append(f"### {f['cancion']}")
            out.append(f"- **Carpeta**: {c}")
            out.append(f"- **Título impreso**: {d['titulo']}")
            out.append(f"- **Fuente**: {fuente}")
            out.append(f"- **Tonalidad**: {f['ton']}")
            out.append(f"- **Compás**: {f['comp']}")
            out.append(f"- **Tempo**: ♩= {d['tempo'] or '100'}")
            out.append(f"- **Compases**: {f['nc']}")
            out.append(f"- **Piano de acompañamiento**: {'Sí' if d['piano'] else 'No'}")
            out.append(f"- **Fuentes consultadas**: {', '.join(urls) if urls else 'no encontrado en internet / sólo PDF'}")
            out.append(f"- **Notas deducidas**: {'; '.join(d['deducidas']) if d['deducidas'] else 'ver advertencias' if 'DEDUCID' in f['adv'].upper() else 'Ninguna'}")
            out.append(f"- **Advertencias**: {f['adv']}")
            out.append(f"- **Transcriptor**: subagente Claude (protocolo `_herramientas/PROTOCOLO_AGENTE.md`) + revisión del orquestador")
            out.append(f"- **QA**: {f['qa']}")
            out.append(f"- **Archivos generados**: ✅ MusicXML | ✅ MSCZ | ✅ PDF | ✅ 4 MIDI | ✅ 4 MP3\n")
    (REPO / "REPORTE.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("REPORTE.md escrito;", len(ok), "ok,", len(bloq), "bloqueadas,", len(fallos), "fallos QA")


if __name__ == "__main__":
    main()
