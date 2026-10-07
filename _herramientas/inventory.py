# inventario: pdf -> carpeta base (nombres según tabla del superprompt)
from pathlib import Path
REPO = Path(r"C:\Users\diego\Canciones")
FOLDERS = ["Español", "Inglés", "Navidad", "Rumano"]
OVERRIDES = {
    "andaba yo sin paz": "Andaba yo sin paz",
    "He touched me(español)": "He touched me (español)",
    "It came upon the midnight clear (español": "It came upon the midnight clear (español)",
    "Sa nu te temi( letra Español)": "Sa nu te temi (letra Español)",
    "Here Comes the Light_TTBB": "Here Comes the Light TTBB",
    "it came upon the midnight partitura": "It came upon the midnight partitura",
    "VINE IAR (comp.)": "VINE IAR (comp)",
    "un glas": "Un glas",
    "Pe crucea  din dealul iubirii": "Pe crucea din dealul iubirii",
}
def clean(stem):
    if stem in OVERRIDES: return OVERRIDES[stem]
    name = stem.rstrip("_ ")
    for ch in '+:*?"<>|': name = name.replace(ch, "_")
    return name.rstrip("_ ")
def songs():
    out = []
    for f in FOLDERS:
        for pdf in sorted((REPO / f).glob("*.pdf")):
            out.append((pdf, pdf.parent / clean(pdf.stem)))
    return out
if __name__ == "__main__":
    s = songs(); print(len(s))
    for pdf, base in s: print(f"{pdf.parent.name}/{base.name}")
