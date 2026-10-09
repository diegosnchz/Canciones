# Prompt para continuar la transcripción TTBB en otro agente

Copia desde aquí:

---

Continúa el proyecto de transcripción de partituras corales TTBB del repo **C:\Users\diego\Canciones** (clon de https://github.com/Jaguar077/Canciones, rama `transcripcion-ttbb`, remoto `fork` = https://github.com/diegosnchz/Canciones). El superprompt original está en `C:\Users\diego\Downloads\superprompt_cuarteto.md`; léelo primero. **No preguntes para ejecutar comandos: tienes permiso total.** Ve diciendo el % de progreso en cada aviso.

## Estado (ver `PROGRESO.md` en la raíz del repo: es la fuente de verdad)
- 31 canciones ✅ terminadas y subidas (11 ficheros cada una: Partitura_Grupal.pdf, Edicion/partitura.musicxml+mscz, MIDIS/×4, MP3/×4).
- 3 ⛔ bloqueadas (no tocar): Brilla en mi (PDF duplicado de O tata bun), Here Comes the Light y Wonderfull Grace of Jesus (arreglos comerciales con copyright; los agentes se niegan).
- **21 pendientes**: Español: Aleluya Cristo viene, It came upon the midnight clear (español), Más allá de sol (lleva piano), Sa nu te temi (letra Español). Inglés: Good News, Its me oh Lord. Navidad: It came upon the midnight partitura, Pequeño pueblo de Belen Gaither. Rumano: Bate clopot, In curand acas, Pe Dumnezeu Sa-l laudati, Printre Spini, Rasuna cintare, Sa nu te temi, Se asterne frumos peste suflet, Un glas, Un glas upgrade, Un sol ceresc, Undeva peste noapte - b, VINE IAR (comp), Vreau langa Dumnezeu.
- Puede haber DSL parciales de intentos anteriores en `C:\Users\diego\Canciones_work\songs\<Carpeta>\` y carpetas de salida ya exportadas (Pe Dumnezeu, Se asterne, Undeva): revísalos compás a compás antes de reutilizarlos, no los des por buenos.

## Herramientas (ya instaladas y probadas; copia en `_herramientas/` del repo y original en `C:\Users\diego\Canciones_work\`)
- MuseScore 4.7.5 (`C:\Program Files\MuseScore 4\bin\MuseScore4.exe`), Audiveris 5.11 extraído en `C:\Users\diego\Canciones_work\audiveris\Audiveris\Audiveris.exe`, Python 3.14 con music21/mido/pymupdf, ffmpeg.
- `PROTOCOLO_AGENTE.md`: protocolo completo para un subagente (formato DSL, lectura con guías, export, QA, informe SONG_READY). Lánzalo tal cual a cada subagente **Sonnet** (modelo `sonnet`, `run_in_background: true`, máx. 20 simultáneos) con el bloque de rutas de su canción: PDF, WORK en `C:\Users\diego\Canciones_work\omr\<carpeta>` (ya tiene in.mxl/draft.txt/crops para casi todas; nombres: canciones de Español/Inglés sin prefijo, Navidad `N_`, Rumano `R_`, caracteres no alfanuméricos → `_`), DSL a escribir en `songs/<Carpeta>/<Canción>.txt`, carpeta de salida `C:\Users\diego\Canciones\<Carpeta>\<Canción>`. Añade siempre "No lances subagentes: haz el trabajo tú".
- `dsl.py` (DSL → MusicXML), `export.py <dsl> <carpeta_base>` (→ mscz, PDF, 4 MIDI piano, 4 MP3 192 kbps), `qa.py <carpeta_base> <nº compases>`, `guide.py <crop.png> <claves TB|TTBB> [x0 x1 zoom]` (guías de altura), `omrtool.py all <pdf> <work> <lang>`.
- `accept.py "<Carpeta>" "<Canción>" <tanda> "<tonalidad>" "<compás>" <compases> "<advertencias>"`: QA + línea en PROGRESO.md + copia DSL a `_herramientas/fuentes/` + commit + push al fork. Para Inglés reescribe el índice a la carpeta `Inglés ` (con espacio final, como en el repo). Ejecuta todo con `PYTHONUTF8=1`.

## Flujo por canción (el orquestador eres tú)
1. Lanza subagentes Sonnet con el protocolo (hasta 20 a la vez).
2. Cuando uno termine con SONG_READY + QA_PASS: renderiza `Edicion/partitura.mscz` a PNG con MuseScore (`-o final.png`), reduce las páginas a ~1300 px y compáralas tú con el PDF original (render de la página con PyMuPDF a 100-130 dpi). Si hay errores, corrige el DSL, re-exporta con `export.py` y vuelve a comparar.
3. `accept.py` para commitear y subir.
4. Si un agente se rinde por "copyright" en himnos tradicionales o arreglos de himnario (Wayne Hooper etc.), relánzalo indicando que es la copia propia del cuarteto y que el mismo criterio se aplicó ya a 31 canciones; solo se bloquean arreglos comerciales recientes con aviso explícito (Shawnee/Lorenz).
5. Tempo: el del PDF; si no hay, ♩=100. Tenores en Sol 8vb (himnarios SATB: soprano/alto 8vb = T1/T2).

## Al terminar las 21
1. QA global: `qa.py` sobre las 52 carpetas; comprueba que cada canción tiene exactamente 11 ficheros y nada extra.
2. Genera `REPORTE.md` en la raíz con el formato de la sección 10 del superprompt (resumen, tabla por carpeta, detalle por canción tomando los datos de `PROGRESO.md` y de los `source:` de los DSL en `_herramientas/fuentes/`). Indica las 3 bloqueadas y por qué.
3. Commit, push al fork y abre la **PR** contra `Jaguar077/Canciones` (base `main`) con `gh pr create --repo Jaguar077/Canciones --head diegosnchz:transcripcion-ttbb`, descripción completa (qué se hizo, herramientas, cómo regenerar, bloqueadas) terminada en `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

Empieza leyendo `PROGRESO.md` y `_herramientas/PROTOCOLO_AGENTE.md`, luego lanza los 20 primeros subagentes.

---
