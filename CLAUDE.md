# CLAUDE.md — Contexto del proyecto pod-agents

Este archivo lo lee Claude Code automáticamente al iniciar. Resume qué es el
proyecto, cómo está armado y qué decisiones se tomaron, para continuar sin
re-explicar nada.

## Qué es

Sistema multiagente para una tienda Print-on-Demand (POD) en Etsy, construido
con **Strands Agents SDK**. Flujo partido en 2 etapas por el gate humano de eRank:
- **Etapa 1 (discovery):** direction → research → entrega el bloque de 20 keywords.
- **[humano: eRank Bulk Tool → CSV → `import_erank`]**
- **Etapa 2 (production):** design → production → marketing → operations (corre solo si el nicho sobrevive la validación SOP).

## Idioma (convención)

- **Conversación con el usuario: español.**
- **Todo el código en inglés:** identificadores, nombres de archivo, columnas/enums de DB,
  comentarios y los system prompts de los agentes + el texto de la compuerta
  (`VERDICT: APPROVED/REJECTED`). No mezclar idiomas en identificadores.

## Stack y entorno

- **Orquestación:** Strands (patrón Graph, `strands.multiagent.GraphBuilder`). Versión probada: `strands-agents 1.51`.
- **Python:** 3.12 en `venv/` (NO usar 3.14: sin wheels para las deps). Deps en `requirements.txt`.
- **Modelo local:** Ollama con `qwen3.5:9b` (máquina: MacBook Pro M2 Pro, 16GB).
  **`think=False`** obligatorio en `config.py` (ver Ajustes): sin eso qwen3 vuelca todo a un
  campo `thinking` y agota `max_tokens` → `MaxTokensReachedException` que mata el grafo.
- **Modelo hosted (opcional):** para el nodo de validación (más confiable).
- **Datos reales:** export CSV de eRank (Bulk Keywords).
- **Persistencia:** Postgres 16 en Docker (`docker-compose.yml`) — estado/memoria del negocio.
  - `keywords` (Base de Keywords) YA cableada vía `tools/db_tools.py`: el researcher persiste
    keywords y el validator escribe `decision`/`validation_reason`.
  - `niche_items` (taxonomía de cross-niching, 453 ítems del "Cross-Niching Guide Book 2.0")
    con `popularity` para rankear. Tools en `tools/niche_tools.py`: `suggest_niches` (cruza
    holiday × {career|hobby|family_relation|pet}, profundidad 2/3/4 componentes, ranking por
    popularidad), `suggest_niches_bulk` (grupos de 20 separados por comas para el Bulk Keyword
    Tool de eRank), `planning_dates`, `list_niche_items`. CABLEADAS: el director usa
    `planning_dates`+`suggest_niches` para elegir el nicho estacional; el researcher usa
    `suggest_niches_bulk`. El `niche` ahora sale de la taxonomía (ej. "Halloween Nurse Mom").

## Regla de negocio: lead time estacional (config.PLANNING)

El trabajo estacional va adelantado: **sugerir/investigar nichos 90 días antes** de la holiday,
**publicar 60 días antes** (el algoritmo de Etsy tarda ~30 días en reconocer y rankear el listing).
Por eso `suggest_niches` ancla por defecto en el mes que cae ~90 días adelante de hoy (no el mes
actual). El Bulk Keyword Tool de eRank procesa **20 keywords por request**, con un límite de
**100 requests/día = 2000 keywords/día** → salida en grupos de 20 por comas.
- **MCP de dev:** `strands-docs` (`uvx strands-agents-mcp-server`, scope user) para consultar la
  doc oficial de Strands desde Claude Code. Es solo herramienta de desarrollo, no runtime.

## Contexto de negocio (manual operativo)

El know-how real de la tienda está en `POD_Factory_OS_Manual_Operativo_v1.0.pdf` (carpeta padre
`Joy Design/`): pipeline maestro de 13 pasos, 5 áreas funcionales, SOPs por fase, matriz de
automatización y las 7 "Bases" (Google Sheets → migrar a Postgres). Claves al leerlo:
- Escalar por **variación** (un diseño base → decenas de listings), no crear desde cero.
- Pensar en **lotes de producción** (fan-out), no producto por producto.
- El **activo** es el conocimiento acumulado (por eso importa la persistencia).
- Separar **Agente/IA** vs **Script/nativo** vs **Humano**: mucha "automatización" del manual
  es script o feature nativa (Canva Bulk Create, fórmulas de Sheets), NO agentes.

## Estructura

```
pod-agents/
├── main.py            # entrada: python main.py (correr desde ESTA carpeta)
├── config.py          # STORE_CONFIG, modelos LOCAL/HOSTED, brand_context()
├── pipeline.py        # arma el grafo: nodos, edges, compuertas
├── tracing.py         # Tracer: trazas por nodo y por tool (hooks de Strands)
├── eRank_-_Bulk_Keywords.csv
├── requirements.txt   # deps (Python 3.12)
├── docker-compose.yml # Postgres 16 local (estado persistente)
├── .env               # credenciales locales de dev (NO commitear si se inicia git)
├── db/
│   ├── init/          # SQL que corre al inicializar el volumen de Postgres
│   │   ├── 001_keywords.sql   # tabla `keywords` (columnas en inglés)
│   │   └── 002_niches.sql     # tabla `niche_items` (taxonomía de cross-niching)
│   └── seed_niches.py # carga la taxonomía (453 ítems) — `python -m db.seed_niches`
├── tools/
│   ├── erank_tools.py # tools REALES sobre el CSV + veredicto determinístico (_verdict)
│   ├── pod_tools.py   # tools mock: trademark, design, production, publishing
│   ├── db_tools.py    # persistencia Postgres: record_researched_keywords, validate_and_record_niche, list_keywords
│   ├── niche_tools.py # sugerencia de DISEÑO/tags: suggest_niches (cross-niching + popularidad), suggest_niches_bulk
│   ├── sop_validation.py # validación SOP v1.1 (ratio R, KD<=85, searches>=100, trampa, apparel, survival)
│   ├── import_erank.py   # importa el export de eRank a la DB + analyze() SOP (gate humano)
│   └── keyword_gen.py    # genera el bloque de 20 por ejes (5 head/12 mid/3 long-tail) + pre-filtros
└── agents/            # un archivo por agente, cada uno con build(tracer)
    ├── director.py  researcher.py  validator.py  designer.py
    └── producer.py  marketer.py  operations.py
```

Cada agente expone `build(tracer) -> Agent` con un prompt estructurado en inglés
(ROLE, OBJECTIVE, INPUTS, PROCESS, RULES, OUTPUT FORMAT).

## Decisiones clave (no revertir sin motivo)

1. **Graph, no Swarm:** el flujo es una cadena determinística con una compuerta
   de validación; el patrón Graph es el correcto.
2. **Híbrido local/hosted:** nodos de volumen en local (costo $0); validación es
   el candidato a hosted por ser decisión de riesgo legal (marcas). Config en `config.py`.
3. **La tool decide, no el LLM:** en validación, `validate_and_record_niche` (en
   `db_tools.py`, envuelve `_verdict` de `erank_tools.py`) calcula el veredicto
   APPROVED/REJECTED por código (valida cada keyword contra MIN_SEARCHES/MAX_COMPETITION
   y cada frase contra la blocklist) Y persiste cada `decision` en la Base. Devuelve un
   reporte que termina en la línea exacta `VERDICT: ...`. El validador la copia verbatim;
   la compuerta (`pipeline.py`) lee `verdict: approved`/`verdict: rejected`. Robusto en local.
4. **Trazas por hooks:** `tracing.py` engancha eventos de nodo (en el grafo) y de
   tool (en cada agente).
5. **Lógica pura + wrapper `@tool`:** en `erank_tools.py`/`pod_tools.py` la lógica vive en
   funciones normales (testeables sin modelo) y la tool es un envoltorio fino. No romper esto.
6. **Correr tools sueltas como módulo:** `python -m tools.erank_tools` (NO `python tools/...`,
   rompe los imports del paquete).

## Ajustes ya aplicados (historial)

- **`additional_args={"think": False}`** en el modelo local: fix del bloqueante
  `MaxTokensReachedException`. Bajó cada nodo de ~100s a ~6-27s. NO revertir.
- `max_tokens=8192` (subido de 4096): headroom porque un nodo que divaga puede volver a
  agotar el límite. Además se reforzó el prompt del researcher para NO divagar en prosa.
- Validación = **veredicto determinístico** (`validate_and_record_niche` → `_verdict`); el
  prompt del validator solo copia la última línea `VERDICT: ...`.
- Bug arreglado en `_validate`: crash al formatear `competition = None` ("Unknown") con `:,`.
- `venv/` recreado en Python 3.12 (antes 3.14 sin wheels). Deps + `psycopg[binary]`, `python-dotenv`.
- `main.py` imprime salida legible por nodo (recorre `result.results`).
- **Migración completa a inglés** (código, nombres de archivo, columnas DB, prompts, gate).
- **Postgres cableado** (Base de Keywords) vía `db_tools.py`.

Verificado end-to-end (12/08/2026): el pipeline corre completo en inglés, la compuerta funciona,
el **bucle de reintento validation→research SÍ se dispara** (rechazó 1ª ronda, aprobó 2ª) y
escribe keywords + decisiones en Postgres. Termina en operations con el listing en DRAFT.

Pendientes de pulido detectados en esa corrida (no bloqueantes):
- El researcher a veces se saltea `record_researched_keywords` (modelo local); la Base igual se
  puebla por el fallback insert del validator. Reforzar prompt o mover la persistencia.
- Los `niche` salen verbosos/inconsistentes entre rondas → filas desprolijas por la clave
  `(keyword, niche)`. Conviene normalizar el niche a un slug corto que fluya entre nodos.

## Cómo correr

```
# 0) Postgres (persistencia). Ollama con qwen3.5:9b.
docker compose up -d
# 1) Etapa 1: elige ocasión + genera el bloque de 20 keywords (queda pending en DB)
./venv/bin/python main.py discover
# 2) [HUMANO] correr el bloque en eRank Bulk Tool → exportar CSV → importar:
./venv/bin/python -m tools.import_erank <csv> "<niche>"
# 3) Etapa 2: valida (SOP) y si el nicho sobrevive, produce hasta DRAFT
./venv/bin/python main.py produce "<niche>"
```

### Mini-UI (Streamlit)
Panel liviano sobre el MISMO backend + Postgres (mismas 2 etapas y el gate humano):
```
docker compose up -d           # Postgres arriba
./venv/bin/streamlit run streamlit_app.py
```

Reglas para 16GB: un solo modelo local, `keep_alive="30m"`, ejecución secuencial.

## Pendientes / próximos pasos

- [x] ~~Cablear Postgres (Base de Keywords)~~ → hecho en `db_tools.py` (researcher + validator).
- [x] ~~Taxonomía de nichos + sugerencia (Fase 1)~~ → `niche_items` + `suggest_niches` (popularidad,
      profundidad 2/3/4, lead time 90d, grupos de 20 para eRank), **cableada a director/researcher**.
- [ ] **Reencuadre por SOP v1.1** ([[project-sop-keywords-validation]]): el cross-niche NO es la
      keyword (es diseño/tags). Motor de keywords = ejes (cohorte/edad/fórmula/rol/hobby/ocupación),
      bloque 5/12/3. Plan revisado de Fase 1:
      - [x] Validación SOP determinística (`tools/sop_validation.py`) — testeada vs 10 ejemplos medidos, ALL MATCH.
      - [x] Schema extendido: `keywords` con `axis`, columnas generadas `ratio_r` y `keyword_type`, enum decision con `trap`.
      - [x] Importador `tools/import_erank.py` (`python -m tools.import_erank <csv> [niche]`) → carga métricas + corre `analyze()` SOP.
      - [x] Generador de bloque de 20 por ejes (`tools/keyword_gen.py`): `build_keyword_block` (templates
            por ocasión) + `compose_keyword_block` (para candidatos del LLM), 5/12/3 + pre-filtros. Probado.
      - [x] **Pipeline partido en 2 etapas** (`pipeline.py`: `build_discovery_graph` + `build_production_graph`),
            `main.py discover` / `main.py produce "<niche>"`, con el gate humano de eRank en el medio. Probado E2E.
      - [ ] Pulir: el generador con ocasiones multi-palabra (ej. "dia de los muertos") queda corto de head/mid
            (los templates se van a long-tail) → dio 18/20. Ajustar para ocasiones largas.
- [ ] Pulir el cableado de keywords: que el researcher siempre persista.
- [~] (Fase 3) UI con Streamlit sobre el mismo backend + Postgres. **Esqueleto hecho**
      (`streamlit_app.py`): navegación por sidebar que refleja el pipeline de 2 etapas —
      Base de Keywords (visor de la tabla), Etapa 1 Discovery (`generate_and_stage_block`),
      Gate humano (upload CSV → `import_csv`+`analyze`), Etapa 2 (`analyze_niche_report` +
      botón para correr `build_production_graph`). Sin lógica nueva: solo envuelve el backend.
      Correr: `./venv/bin/streamlit run streamlit_app.py`. Pendiente: pulir tabla/estilos,
      quizá partir en `pages/` multipágina, y mostrar métricas/decisiones más ricas.
- [ ] Agregar las demás Bases del manual (`db/init/002_*.sql`: ideas, products, listings, sales, learnings).
- [ ] Trío determinístico que faltaba (paso 2 del plan): `calculate_margin` (producer),
      `validate_seo` (marketer), y `check_trademark` ya está en designer.
- [ ] Separar la mitad event-driven (venta/fulfillment/postventa/análisis, pasos 8-13) del grafo
      generativo (pasos 1-7): esos van como agentes disparados por evento / tareas agendadas.
- [ ] Fan-out por "lotes de producción" (procesar listas, no un producto por corrida).
- [ ] Integraciones reales (hoy mockeadas): Printify (producción/fulfillment), Etsy API
      (publicación/stats/mensajes), trademark real, generador de imágenes (diseño), Pinterest.
- [ ] Gate humano explícito antes de publicar y antes de pagar órdenes (hoy queda en DRAFT).
- [x] ~~Confirmar veredicto consistente en local~~ → resuelto con el veredicto determinístico.
