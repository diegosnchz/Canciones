"""
dsl -> MusicXML (4 voces TTBB + piano opcional) usando music21.

formato del fichero .txt:
  cabecera  clave: valor   (title, composer, lyricist, arranger, key, time, tempo, pickup, source)
  bloques   @N   (N = número del primer compás del bloque; 0 = anacrusa)
            T1: notas | notas | ...
            T2: =T1  (copia) | TT: (ambos tenores) | BB: (ambos graves)
            B1: ...   B2: ...
            L: sílabas   L2: segunda estrofa   L.T1: sólo tenor 1
tokens de nota:  g3  c#4  bb3  r  (octava científica, altura REAL que suena)
  duración: /1 /2 /4(defecto) /8 /16 /32 ; punto: g3/2. ; ligadura: g3~ ; calderón: g3^
  staccato g3' ; acento g3> ; sin sílaba g3_ ; tresillo 3[ g3/8 a3/8 b3/8 ]
  dinámica \mf ; texto !rit. (guión bajo = espacio) ; ligadura de expresión ( ... )
barras: |  |:  :|  :|:  ||  |]   casillas: [1  [2  (se cierran en :| o |] o ] )
directivas de compás dentro de T1: key:E  time:3/4  tempo:80
"""
import re, sys
from fractions import Fraction
from music21 import (stream, note, chord, pitch, key, meter, clef, instrument, tempo,
                     bar, spanner, dynamics, expressions, duration, tie, metadata, layout)

VOICES = ["T1", "T2", "B1", "B2"]
PIANO = ["PR", "PL"]
NAMES = {"T1": "Tenor 1", "T2": "Tenor 2", "B1": "Baritono", "B2": "Bajo", "PR": "Piano", "PL": "Piano"}
NOTE_RE = re.compile(r"^(?P<p>[a-g](?:##|#|bb|b|n)?\d(?:\+[a-g](?:##|#|bb|b|n)?\d)*|r)(?:/(?P<d>\d+))?(?P<dots>\.*)(?P<mods>[~^'_>]*)$")
BARS = {"|", "|:", ":|", ":|:", "||", "|]"}


class Tok:
    def __init__(self, kind, val=None, **kw):
        self.kind, self.val = kind, val
        self.__dict__.update(kw)

    def __repr__(self):
        return f"{self.kind}:{self.val}"


def tokenize(line):
    out = []
    for t in line.split():
        if t in BARS:
            out.append(Tok("bar", t))
        elif re.match(r"^\[\d$", t):
            out.append(Tok("ending", int(t[1])))
        elif t == "]":
            out.append(Tok("endclose"))
        elif t in (r"\cresc", r"\dim", r"\!"):
            out.append(Tok("wedge", t[1:]))
        elif t.startswith("\\"):
            out.append(Tok("dyn", t[1:]))
        elif t.startswith("!"):
            out.append(Tok("text", t[1:].replace("_", " ")))
        elif t in ("(", ")"):
            out.append(Tok("slur", t))
        elif t == "3[":
            out.append(Tok("tup", 3))
        elif re.match(r"^(key|time|tempo):", t):
            k, v = t.split(":", 1)
            out.append(Tok(k, v))
        else:
            m = NOTE_RE.match(t)
            if not m:
                raise ValueError(f"token no reconocido: {t!r} en: {line}")
            d = int(m.group("d") or 4)
            ql = Fraction(4, d) * (Fraction(2) - Fraction(1, 2 ** len(m.group("dots"))))
            out.append(Tok("note", m.group("p"), ql=ql, dots=len(m.group("dots")), base=d, mods=m.group("mods")))
    return out


def split_measures(tokens):
    """devuelve lista de compases: cada uno {'left':bar,'right':bar,'toks':[...], 'ending':n}"""
    measures, cur, left = [], [], None
    for t in tokens:
        if t.kind == "bar":
            if cur or measures or t.val in ("|:",):
                if cur:
                    measures.append({"left": left, "right": t.val, "toks": cur})
                    cur = []
                    left = t.val
                else:
                    left = t.val
            else:
                left = t.val
        else:
            cur.append(t)
    if cur:
        measures.append({"left": left, "right": None, "toks": cur})
    return measures


def parse_file(path):
    hdr, blocks, cur = {}, [], None
    for raw in open(path, encoding="utf-8"):
        line = re.sub(r"(^|\s)#.*$", "", raw).rstrip()
        if not line.strip():
            continue
        if line.startswith("@"):
            cur = {"start": int(line[1:].split()[0]), "voices": {}, "lyrics": []}
            blocks.append(cur)
        elif cur is None:
            k, v = line.split(":", 1)
            hdr[k.strip()] = v.strip()
        else:
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if k.startswith("L"):
                m = re.match(r"^L(\d*)(?:\.(T1|T2|B1|B2|TT|BB))?$", k)
                cur["lyrics"].append((int(m.group(1) or 1), m.group(2) or "ALL", v))
            else:
                cur["voices"][k] = v
    return hdr, blocks


def expand_voices(block):
    v = block["voices"]
    out = {}
    for name in ACTIVE:
        src = v.get(name)
        if src is None:
            src = v.get("TT" if name.startswith("T") else "BB")
        if src is None and name in PIANO:
            src = "=T1"  # provisional: se sustituye por silencios abajo
            out[name] = None
            continue
        if src is None:
            raise ValueError(f"falta voz {name} en bloque @{block['start']}")
        out[name] = src
    for _ in range(3):
        for name in ACTIVE:
            if out[name] and out[name].startswith("="):
                out[name] = out[out[name][1:].strip()]
    for name in ACTIVE:
        if out[name] is None:  # piano ausente en este bloque: un silencio de compás entero por compás
            nmeas = out["T1"].count("|") + 1
            out[name] = " | ".join(["r/1"] * nmeas)
    return out


def lyric_tokens(text):
    toks = []
    for w in text.replace("|", " ").split():
        toks.append(w)
    return toks


def apply_lyrics(notes_list, toks, number):
    """asigna sílabas a notas (ignorando silencios, notas ligadas de continuación y notas con _)"""
    i = 0
    prev_cont = False
    for n in notes_list:
        if i >= len(toks):
            break
        if n.isRest or getattr(n, "_nolyric", False) or (n.tie is not None and n.tie.type in ("stop", "continue")):
            continue
        w = toks[i]
        i += 1
        if w == "_":
            continue
        cont = w.endswith("-")
        txt = w[:-1] if cont else w
        if prev_cont and cont:
            syl = "middle"
        elif prev_cont:
            syl = "end"
        elif cont:
            syl = "begin"
        else:
            syl = "single"
        txt = txt.replace("_", "‿")
        n.lyrics.append(note.Lyric(text=txt, number=number, syllabic=syl, applyRaw=True))
        prev_cont = cont
    return i, len(toks)


ACTIVE = list(VOICES)


def _qtype(ql):
    # music21 reciente devuelve (tipo, exacto)
    t = duration.quarterLengthToClosestType(ql)
    return t[0] if isinstance(t, tuple) else t


def build(hdr, blocks, warn=print):
    global ACTIVE
    ACTIVE = list(VOICES) + (PIANO if any("PR" in b["voices"] or "PL" in b["voices"] for b in blocks) else [])
    sc = stream.Score()
    sc.metadata = metadata.Metadata()
    sc.metadata.title = hdr.get("title", "")
    comp = hdr.get("composer", "")
    if hdr.get("arranger"):
        comp = (comp + " · " if comp else "") + hdr["arranger"]
    sc.metadata.composer = comp or " "
    if hdr.get("lyricist"):
        sc.metadata.lyricist = hdr["lyricist"]
    if hdr.get("arranger"):
        sc.metadata.addContributor(metadata.Contributor(role="arranger", name=hdr["arranger"]))

    parts = {}
    for i, vn in enumerate(ACTIVE):
        p = stream.Part(id=f"P{i+1}")
        p.partName = NAMES[vn]
        p.partAbbreviation = {"T1": "T1", "T2": "T2", "B1": "Bar.", "B2": "B.", "PR": "Pno.", "PL": ""}[vn]
        inst = instrument.Piano()
        inst.partName = NAMES[vn]
        inst.instrumentName = "Piano"
        inst.midiChannel = i
        p.insert(0, inst)
        parts[vn] = p

    cur_key = hdr.get("key", "C")
    cur_time = hdr.get("time", "4/4")
    tempo_bpm = int(hdr.get("tempo", 100))
    mnum = None
    endings = {vn: {} for vn in ACTIVE}   # vn -> {ending_no: [measures]}
    open_ending = {vn: None for vn in ACTIVE}
    slur_open = {vn: None for vn in ACTIVE}
    wedge_open = {vn: None for vn in ACTIVE}   # (tipo, nota inicial)
    pending_wedge = {vn: None for vn in ACTIVE}
    pending_tie = {vn: None for vn in ACTIVE}
    first = True
    total = 0

    for block in blocks:
        voices = expand_voices(block)
        parsed = {vn: split_measures(tokenize(voices[vn])) for vn in ACTIVE}
        nm = len(parsed["T1"])
        for vn in ACTIVE:
            if len(parsed[vn]) != nm:
                raise ValueError(f"bloque @{block['start']}: {vn} tiene {len(parsed[vn])} compases, T1 tiene {nm}")
        if mnum is not None and block["start"] != mnum:
            warn(f"AVISO: bloque @{block['start']} esperado @{mnum}")
        mnum = block["start"]
        block_notes = {vn: [] for vn in ACTIVE}

        for mi in range(nm):
            # directivas de T1 para todas las voces
            t1 = parsed["T1"][mi]
            new_key = new_time = new_tempo = None
            t1_endings = [t for t in t1["toks"] if t.kind in ("ending", "endclose")]
            for t in t1["toks"]:
                if t.kind == "key": new_key = t.val
                if t.kind == "time": new_time = t.val
                if t.kind == "tempo": new_tempo = int(t.val)
            if new_key: cur_key = new_key
            if new_time: cur_time = new_time
            ts = meter.TimeSignature(cur_time)
            for vn in ACTIVE:
                md = parsed[vn][mi]
                # barras y casillas: las de T1 mandan si la voz no las lleva
                if md["left"] is None or md["left"] == "|": md["left"] = t1["left"]
                if md["right"] is None or md["right"] == "|": md["right"] = t1["right"]
                if vn != "T1" and t1_endings and not any(t.kind in ("ending", "endclose") for t in md["toks"]):
                    md["toks"] = [t for t in t1_endings if t.kind == "ending"] + md["toks"] + [t for t in t1_endings if t.kind == "endclose"]
                m = stream.Measure(number=mnum)
                if first or new_key or new_time or new_tempo:
                    if first or new_key:
                        m.insert(0, key.Key(cur_key))
                    if first or new_time:
                        m.insert(0, meter.TimeSignature(cur_time))
                    if first:
                        m.insert(0, clef.Treble8vbClef() if vn.startswith("T") else (clef.TrebleClef() if vn == "PR" else clef.BassClef()))
                    if (first or new_tempo) and vn == "T1":
                        m.insert(0, tempo.MetronomeMark(number=new_tempo or tempo_bpm))
                # barras
                if md["left"] in ("|:", ":|:"):
                    m.leftBarline = bar.Repeat(direction="start")
                if md["right"] in (":|", ":|:"):
                    m.rightBarline = bar.Repeat(direction="end")
                elif md["right"] == "||":
                    m.rightBarline = bar.Barline("double")
                elif md["right"] == "|]":
                    m.rightBarline = bar.Barline("final")
                # casilla abierta de un compás anterior
                if open_ending[vn] is not None:
                    endings[vn].setdefault(open_ending[vn], []).append(m)
                # contenido
                off = Fraction(0)
                tup_left = 0
                pending_dyn, pending_text, pending_slur = [], [], False
                for t in md["toks"]:
                    if t.kind == "ending":
                        open_ending[vn] = t.val
                        if m not in endings[vn].setdefault(t.val, []):
                            endings[vn][t.val].append(m)
                    elif t.kind == "endclose":
                        open_ending[vn] = None
                    elif t.kind == "wedge":
                        if t.val == "!":
                            if wedge_open[vn] is not None and block_notes[vn]:
                                kind, n0 = wedge_open[vn]
                                w = dynamics.Crescendo(n0, block_notes[vn][-1]) if kind == "cresc" else dynamics.Diminuendo(n0, block_notes[vn][-1])
                                parts[vn].insert(0, w)
                            wedge_open[vn] = None
                        else:
                            pending_wedge[vn] = t.val
                    elif t.kind == "dyn":
                        pending_dyn.append(t.val)
                    elif t.kind == "text":
                        pending_text.append(t.val)
                    elif t.kind == "slur":
                        if t.val == "(":
                            pending_slur = True
                        else:
                            if slur_open[vn] is not None and block_notes[vn]:
                                sp = spanner.Slur(slur_open[vn], block_notes[vn][-1])
                                parts[vn].insert(0, sp)
                            slur_open[vn] = None
                    elif t.kind == "tup":
                        tup_left = 3
                    elif t.kind in ("key", "time", "tempo"):
                        pass
                    elif t.kind == "note":
                        if t.val == "r":
                            n = note.Rest()
                        else:
                            pns = [x[0].upper() + x[1:].replace("b", "-").replace("n", "") for x in t.val.split("+")]
                            n = note.Note(pns[0]) if len(pns) == 1 else chord.Chord(pns)
                        n.duration = duration.Duration(quarterLength=float(t.ql))
                        if tup_left:
                            tp = duration.Tuplet(3, 2, duration.Duration(type=_qtype(Fraction(4, t.base))))
                            tp.type = "start" if tup_left == 3 else ("stop" if tup_left == 1 else None)
                            n.duration = duration.Duration(type=_qtype(Fraction(4, t.base)), dots=t.dots)
                            n.duration.appendTuplet(tp)
                            tup_left -= 1
                        if "~" in t.mods:
                            n.tie = tie.Tie("start")
                            if pending_tie[vn]:
                                n.tie = tie.Tie("continue")
                            pending_tie[vn] = True
                        elif pending_tie[vn]:
                            n.tie = tie.Tie("stop")
                            pending_tie[vn] = False
                        if "^" in t.mods:
                            n.expressions.append(expressions.Fermata())
                        if "'" in t.mods:
                            from music21 import articulations
                            n.articulations.append(articulations.Staccato())
                        if ">" in t.mods:
                            from music21 import articulations
                            n.articulations.append(articulations.Accent())
                        if "_" in t.mods:
                            n._nolyric = True
                        for d in pending_dyn:
                            m.insert(float(off), dynamics.Dynamic(d))
                        for tx in pending_text:
                            te = expressions.TextExpression(tx)
                            te.placement = "above"
                            m.insert(float(off), te)
                        pending_dyn, pending_text = [], []
                        if pending_slur:
                            slur_open[vn] = n
                            pending_slur = False
                        if pending_wedge[vn]:
                            wedge_open[vn] = (pending_wedge[vn], n)
                            pending_wedge[vn] = None
                        m.insert(float(off), n)
                        block_notes[vn].append(n)
                        off += t.ql if not n.duration.tuplets else Fraction(n.duration.quarterLength).limit_denominator(12)
                # comprobación de duración
                bl = Fraction(ts.barDuration.quarterLength).limit_denominator(12)
                if off != bl:
                    if mnum == 0 or (mi == 0 and block is blocks[0] and off < bl):
                        m.paddingLeft = float(bl - off)
                    elif md["right"] in (":|", "|]") or off < bl:
                        m.paddingRight = float(bl - off)
                        if off > bl:
                            warn(f"ERROR c.{mnum} {vn}: suma {off} > {bl}")
                        else:
                            warn(f"AVISO c.{mnum} {vn}: suma {off} < {bl} (compás incompleto)")
                    else:
                        warn(f"ERROR c.{mnum} {vn}: suma {off} != {bl}")
                parts[vn].append(m)
                # cierre de casilla automático
                if open_ending[vn] is not None and md["right"] in (":|", "|]", "||"):
                    open_ending[vn] = None
            first = False
            mnum += 1
            total += 1

        # letras del bloque
        for number, target, text in block["lyrics"]:
            toks = lyric_tokens(text)
            targets = VOICES if target == "ALL" else (["T1", "T2"] if target == "TT" else ["B1", "B2"] if target == "BB" else [target])
            for vn in targets:
                used, n = apply_lyrics(block_notes[vn], list(toks), number)
                if used != n:
                    warn(f"AVISO letra @{block['start']} {vn}: {used}/{n} sílabas usadas")

    # casillas: agrupar compases consecutivos
    for vn in ACTIVE:
        for num, ms in endings[vn].items():
            ms = [x for x in ms if x is not None]
            if ms:
                rb = spanner.RepeatBracket(ms, number=num)
                parts[vn].insert(0, rb)
        parts[vn].makeAccidentals(inPlace=True, cautionaryNotImmediateRepeat=False)
        last = parts[vn].getElementsByClass(stream.Measure).last()
        if last is not None and last.rightBarline is None:
            last.rightBarline = bar.Barline("final")

    for vn in ACTIVE:
        sc.insert(0, parts[vn])
    sg = layout.StaffGroup([parts[v] for v in VOICES], name="", symbol="bracket")
    sc.insert(0, sg)
    if "PR" in ACTIVE:
        sc.insert(0, layout.StaffGroup([parts["PR"], parts["PL"]], name="Piano", symbol="brace", barTogether=True))
    return sc, total


def convert(txt_path, out_path):
    hdr, blocks = parse_file(txt_path)
    msgs = []
    sc, total = build(hdr, blocks, warn=lambda s: msgs.append(s))
    sc.write("musicxml", fp=out_path)
    return hdr, total, msgs


if __name__ == "__main__":
    hdr, total, msgs = convert(sys.argv[1], sys.argv[2])
    print(f"{hdr.get('title')}: {total} compases -> {sys.argv[2]}")
    for m in msgs:
        print(" ", m)
