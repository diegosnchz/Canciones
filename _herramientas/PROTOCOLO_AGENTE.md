# Protocolo de transcripción de una canción (cuarteto TTBB)

Eres un transcriptor musical. Tu trabajo: convertir UN PDF de partitura coral en `partitura.musicxml` (4 voces: Tenor 1, Tenor 2, Barítono, Bajo, + piano sólo si la partitura original lo lleva) y generar todos los ficheros de salida con las herramientas ya hechas. **Precisión absoluta: ni una nota inventada, ni una omitida, letra exactamente como está impresa.** No hagas commits de git. No toques otras canciones.

## Rutas
- Herramientas: `C:\Users\diego\Canciones_work\` (`omrtool.py`, `guide.py`, `dsl.py`, `export.py`, `qa.py`).
- Carpeta de trabajo de tu canción: `C:\Users\diego\Canciones_work\omr\<WORK>\` con `in.pdf`, `in.mxl` (lectura OMR de Audiveris), `draft.txt` (borrador en formato DSL), `crops\pN_sM.png` (recortes de cada sistema a 300 dpi).
- Fichero DSL que debes escribir: `C:\Users\diego\Canciones_work\songs\<Carpeta>\<Canción>.txt`.
- Carpeta de salida (ya existe o la crea `export.py`): `C:\Users\diego\Canciones\<Carpeta>\<Canción>\`.
- Ejecuta python siempre con `PYTHONUTF8=1` (bash: `PYTHONUTF8=1 python ...`). Ignora los `warnings` de music21/requests.
- Si falta `in.mxl`/`draft.txt`/`crops`: `PYTHONUTF8=1 python omrtool.py all "<pdf>" "omr/<WORK>" spa+eng` (usa `ron+eng` para rumano, `eng` para inglés).

## Paso 1 — Búsqueda en internet (obligatoria, breve)
Busca (WebSearch) la canción: compositor/arreglista/año, letra completa, tempo habitual (grabaciones). Úsalo para validar la lectura (letra dudosa, tonalidad, tempo si el PDF no lo indica). Anota en el campo `source:` del DSL qué encontraste (URLs) o "no encontrado". No copies de internet nada que contradiga el PDF: el PDF manda.

## Paso 2 — Leer la partitura sistema a sistema
1. Mira primero las páginas enteras (`crops/` o renderiza el PDF) para entender: nº de pentagramas por sistema (2 = TT arriba en clave de Sol 8vb + BB abajo en Fa; 4 = una voz por pentagrama; +2 de piano), tonalidad, compás, anacrusa, repeticiones (|: :|), casillas 1ª/2ª, D.S./D.C./Coda, cambios de tonalidad/compás, dinámicas, calderones, rit., estrofas múltiples.
2. Genera recortes ampliados con guías de altura y léelos TODOS:
   `python guide.py crops/p1_s1.png TB 0 900 2.2` / `820 1700` / `1620 2484` (tres tercios de cada sistema). El 2º argumento son las claves de los pentagramas de arriba abajo: `T` = Sol 8vb (tenores, alturas REALES, una octava bajo lo escrito), `B` = Fa. Con 4 pentagramas: `TTBB`. Si hay piano: añade `TB` al final (la mano derecha del piano es clave de Sol normal: sus etiquetas salen una octava BAJAS; súmale una octava).
   Las guías: líneas rojas = líneas del pentagrama, azules discontinuas = espacios, verdes = líneas adicionales; etiqueta = altura real que suena. Si el detector no acierta (AVISO "N pentagramas detectados"), lee el recorte sin guías contando líneas.
3. En cada columna de acorde: nota superior del pentagrama de arriba = T1, inferior = T2; superior del de abajo = Barítono, inferior = Bajo. Una sola cabeza = unísono (las dos voces llevan la misma nota). Plicas arriba = voz superior, plicas abajo = inferior cuando los ritmos difieren.
4. Comprueba que cada compás suma el valor del compás. Comprueba las alteraciones (armadura + accidentales del compás; los becuadros se escriben `n`: `dn4`).
5. El borrador `draft.txt` (OMR) sirve de ayuda: suele acertar alturas pero falla ritmos, voces, octavas (clave 8vb) y letra. **Verifica todo contra la imagen.**
6. Letra: transcribe exactamente lo impreso (tildes, mayúsculas, puntuación, paréntesis). Cuando una voz tiene distinto texto o distinto nº de notas, usa líneas `L.T1:`, `L.T2:`, `L.B1:`, `L.B2:` (`L.TT:`/`L.BB:` para pares). Estrofas: `L:` (1ª), `L2:`, `L3:` ...
7. Si una nota es ilegible: deduce por contexto armónico, pon `# NOTA DEDUCIDA: c.X voz Y` como comentario en el DSL y anótalo en el informe.

## Paso 3 — Formato DSL (fichero .txt)
```
title: Título tal como aparece
composer: ...            # vacío si no consta
lyricist: ...
arranger: ...
key: G                   # tonalidad inicial (G, D, Bb, Em, F#m ...)
time: 4/4
tempo: 100               # el del PDF; si no hay, el de la grabación/himnario; si nada, 100
source: ...              # fuentes consultadas / observaciones

@1                       # nº del primer compás del bloque (0 = anacrusa)
T1: g3 g3/8 g3/8 b3 b3 | e4/2. e4 | d4 b3 c4 b3 | d4/2. a3
T2: =T1                  # copia de otra voz (unísono completo)
B1: g3 g3/8 g3/8 g3 g3 | g3/2. g3 | g3 e3 e3/8 f#3/8_ g3 | f#3/2. d3
B2: ...
L: A Cris- to co- ro- | nad di- | vi- no Sal- va- | dor, Sen-
```
- Bloque = un sistema o cualquier grupo de compases; todas las voces del bloque deben tener el mismo nº de compases (separados por `|`). `TT:` = las dos voces de tenor iguales; `BB:` = las dos graves.
- Nota: `letra[#|b|n]octava` con altura REAL (C4 = Do central; los tenores suenan ~g3-g4, graves ~e2-e3-c4). Duración: `/1` redonda, `/2` blanca, sin sufijo = negra, `/8`, `/16`; puntillo `.` (`g3/2.`, `g3.` = negra con puntillo). Silencio `r`, `r/2`, `r/1`. Acorde (piano): `c4+e4+g4/2`.
- Modificadores pegados a la nota: `~` ligadura de prolongación (tie) a la siguiente nota; `_` la nota NO recibe sílaba (melisma); `^` calderón; `'` staccato; `>` acento. Ej.: `d4/8_`, `g#4/1~`, `c#4^`.
- Tresillo: `3[ g3/8 a3/8 b3/8 ]`. Ligadura de expresión (slur): `( g3 a3 b3 )`.
- Dinámicas: `\p \mp \mf \f \ff \pp` antes de la nota. Texto: `!rit.`, `!a_tempo`, `!dolce` (guion bajo = espacio). Ponlos en T1 (se copian al audio de todas las voces).
- Barras (sólo hace falta ponerlas en T1; se propagan): `|:` inicio repetición, `:|` fin, `||` doble, `|]` final (se añade sola al último compás). Casillas: `[1` al principio del compás donde empieza la 1ª casilla (dura hasta `:|`), `[2` para la 2ª; `]` cierra la casilla explícitamente si dura menos (p.ej. `[2 d4 d4 d4 d4 ]`).
- Cambios a mitad: `key:E`, `time:3/4`, `tempo:80` como tokens dentro del compás de T1 donde ocurren.
- Letra: sílabas separadas por espacio; `-` al final = continúa en la siguiente nota (`Cris- to`); `|` opcional para alinear por compases; `_` dentro de una palabra = elisión impresa (`do_en`); las sílabas se asignan en orden a cada nota que no sea silencio, ni ligada (tie) ni marcada `_`. Si sobran o faltan sílabas, `dsl.py` avisa: corrígelo.
- D.S./D.C./Coda: si aparecen, escribe la forma expandida (repite los compases) y anótalo en `source:`. Anacrusa: bloque `@0` con el compás incompleto.
- Piano (sólo si lo hay en el original): líneas `PR:` (mano derecha, clave de Sol normal, octava real) y `PL:` (mano izquierda).

## Paso 4 — Exportar y verificar
```
cd C:\Users\diego\Canciones_work
PYTHONUTF8=1 python export.py "songs/<Carpeta>/<Canción>.txt" "C:/Users/diego/Canciones/<Carpeta>/<Canción>"
PYTHONUTF8=1 python qa.py "C:/Users/diego/Canciones/<Carpeta>/<Canción>" <nº compases>
```
- Resuelve TODOS los `ERROR`/`AVISO` de `export.py` (sumas de compás, sílabas).
- Renderiza el resultado y compáralo con el original sistema a sistema:
  `"/c/Program Files/MuseScore 4/bin/MuseScore4.exe" "<carpeta>/Edicion/partitura.mscz" -o omr/<WORK>/final.png` (crea `final-1.png`, ...; redúcelos con PIL a ~1500 px de ancho antes de mirarlos). Corrige el DSL y vuelve a exportar hasta que coincida nota a nota.
- `qa.py` debe decir `QA_PASS`.

## Paso 5 — Informe final (tu último mensaje)
```
SONG_READY | carpeta: "<Carpeta>/<Canción>" | tonalidad: ... | compás: ... | tempo: ... | compases: N | estructura: ... | piano: Sí/No | fuentes: [...] | notas_deducidas: ... | advertencias: ... | QA: PASS/FAIL
```
Añade una lista breve de cualquier duda real (p.ej. accidentales ambiguos, letra manuscrita ilegible). No describas el proceso; sólo resultados.
