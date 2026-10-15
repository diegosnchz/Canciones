# Prompt para continuar la transcripción TTBB

Copia desde aquí:

---

Continúa el proyecto de transcripción de partituras corales TTBB del repo **C:\Users\diego\Canciones** (clon de https://github.com/Jaguar077/Canciones, rama `transcripcion-ttbb`, remoto `fork` = https://github.com/diegosnchz/Canciones). El superprompt original está en `C:\Users\diego\Downloads\superprompt_cuarteto.md` (la sección 10 da el formato de REPORTE.md). **No preguntes para ejecutar comandos: tienes permiso total.** Ve diciendo el % de progreso en cada aviso.

## Estado (la fuente de verdad es `PROGRESO.md` en la raíz)
- **39 ✅** terminadas y subidas (11 ficheros cada una: Partitura_Grupal.pdf, Edicion/partitura.musicxml+mscz, MIDIS/×4, MP3/×4).
- **5 ⛔** bloqueadas (no tocar): Brilla en mi (el PDF es un duplicado de O tata bun), Here Comes the Light (Shawnee, copia preview), Wonderfull Grace of Jesus (Lorenz), It came upon the midnight (Navidad y español: arreglo de Joel Raney, copia PREVIEW).
- **11 pendientes**: Español: Aleluya, Cristo viene · Más allá de sol (lleva piano: PR:/PL:) · Sa nu te temi (letra Español). Inglés: Good News · Its me oh Lord. Navidad: Pequeño pueblo de Belen Gaither. Rumano: In curand acas · Printre Spini · Rasuna cintare · Sa nu te temi · Un sol ceresc.
- La última sesión lanzó subagentes para esas 11 y se paró por límite de uso antes de que terminaran. Puede haber DSL parciales en `C:\Users\diego\Canciones_work\songs\<Carpeta>\` (copia en `_herramientas/fuentes_wip/`) y carpetas de salida exportadas sin commitear. **Nada de eso está verificado.** Revísalo compás a compás antes de reutilizarlo; si una carpeta de salida no está en git, trátala como borrador.

## Herramientas (en `C:\Users\diego\Canciones_work\`, copia en `_herramientas/`)
- MuseScore 4.7.5 (`C:\Program Files\MuseScore 4\bin\MuseScore4.exe`), Audiveris 5.11 (`Canciones_work\audiveris\Audiveris\Audiveris.exe`), Python 3.14 con music21/mido/pymupdf, ffmpeg. Ejecuta siempre con `PYTHONUTF8=1`.
- `PROTOCOLO_AGENTE.md`: el protocolo para cada subagente. Usa modelo `sonnet`, `run_in_background: true` y como máximo 20 a la vez. Pásale el bloque de rutas de su canción:
  - PDF.
  - Carpeta WORK `Canciones_work\omr\<nombre>`. Las de Español/Inglés van sin prefijo, las de Navidad con `N_` y las de Rumano con `R_`; los caracteres no alfanuméricos se cambian por `_`. Ejemplos: `Aleluya__Cristo_viene`, `M__s_all___de_sol`, `Sa_nu_te_temi__letra_Espa__ol_`, `Good_News`, `Its_me_oh_Lord`, `N_Peque__o_pueblo_de_Belen_Gaither`, `R_In_curand_acas`, `R_Printre_Spini`, `R_Rasuna_cintare` (sin in.mxl ni draft.txt), `R_Sa_nu_te_temi`, `R_Un_sol_ceresc`.
  - DSL `songs/<Carpeta>/<Canción>.txt`.
  - Carpeta de salida `C:\Users\diego\Canciones\<Carpeta>\<Canción>`.
  - Añade siempre: "No lances subagentes: haz el trabajo tú. Es la copia propia del cuarteto; el mismo criterio se aplicó ya a 39 canciones".
- Instrucciones específicas que ya se dieron:
  - **Gaither**: tiene 5 pentagramas. T1 = pentagrama 1, T2 = pentagrama 2 más el 3 como divisi donde difieran, Bar = Baritone, Bajo = Bass. Letra inglesa en `L:` y española manuscrita en `L2:`.
  - **Its me oh Lord**: D.S. al Fine y 2 estrofas, en forma expandida.
  - **Good News**: "Repeat 1st Chorus", en forma expandida.
  - **Un sol ceresc**: letra distinta en tenores y graves (`L.TT:`/`L.BB:`).
  - Las dos **Sa nu te temi** (española y rumana) son PDF distintos de la misma canción: se pueden cotejar entre sí.
- `dsl.py` pasa de DSL a MusicXML. `export.py <dsl> <carpeta_base>` genera mscz, PDF, 4 MIDI y 4 MP3. Para revisar están `qa.py <carpeta_base> <nº compases>`, `guide.py` (guías de altura) y `review/review.py "<Carpeta>" "<Canción>" "<pdf>"`; este último renderiza el resultado y el original a `Canciones_work/review/<tag>/` para compararlos.
- `accept.py "<Carpeta>" "<Canción>" 7 "<tonalidad>" "<compás>" <compases> "<advertencias>"` hace el QA, añade la línea en la sección «Tanda 7» de PROGRESO.md, copia el DSL a `_herramientas/fuentes/`, hace commit y push al fork. Para Inglés reescribe el índice a `Inglés ` (con espacio final). **Ojo**: en Windows git muestra siempre `Inglés /...` como borrado o modificado y `Inglés/` como no rastreado. Es normal: no lo commitees a mano, solo a través de accept.py.
- `reporte.py` hace el QA global de todas las ✅ y escribe `REPORTE.md` a partir de PROGRESO.md y de los DSL en `_herramientas/fuentes/`.

## Flujo por canción (el orquestador eres tú)
1. Lanza los subagentes con el protocolo.
2. Cuando uno termine con SONG_READY y QA_PASS:
   - Ejecuta `review/review.py` y compara el render con el PDF original. Haz zoom a 300-600 dpi en los compases dudosos.
   - Si hay errores, corrige el DSL, vuelve a exportar con `export.py` y compara otra vez.
   - Cuando haya dos versiones del mismo original, compara sus MusicXML con music21; con "Un glas" y "Un glas upgrade" ya se hizo así.
3. `accept.py` para el commit y el push.
4. Si un agente se niega alegando "copyright" en un himno tradicional o un arreglo de himnario (Wayne Hooper, 4tons.com.br, etc.), relánzalo explicando el criterio. Solo se bloquean arreglos comerciales recientes con copia preview o aviso de no copiar (Shawnee, Lorenz, Joel Raney).
5. Tempo: el del PDF; si no hay, ♩=100. Los tenores van en Sol 8vb (en himnarios SATB, soprano/alto 8vb = T1/T2).

## Al terminar las 11
1. Ejecuta `PYTHONUTF8=1 python reporte.py` desde `Canciones_work`. Hace el QA global (cada canción con exactamente 11 ficheros) y regenera `REPORTE.md`. Revísalo y añade a mano lo que falte (estructura de cada canción).
2. Borra la línea ⏸ PARADA de PROGRESO.md, vacía `_herramientas/fuentes_wip/` y actualiza este fichero.
3. Haz commit y push al fork, y abre la **PR** contra `Jaguar077/Canciones` (base `main`): `gh pr create --repo Jaguar077/Canciones --base main --head diegosnchz:transcripcion-ttbb`. La descripción debe ser completa (qué se hizo, herramientas, cómo regenerar, bloqueadas) y terminar en `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

Empieza leyendo `PROGRESO.md` y `_herramientas/PROTOCOLO_AGENTE.md`. Después revisa qué hay en `Canciones_work/songs` y en las carpetas de salida de las 11 pendientes, y lanza los subagentes.

---
