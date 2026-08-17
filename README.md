# Pipeline POD para Etsy — sistema multiagente (Strands + Ollama)

Sistema multiagente que recorre, de punta a punta, el flujo de una tienda
Print-on-Demand en Etsy:

```
direction → research → validation → design → production → marketing → operations
                              │
                              └─ compuerta: si RECHAZA, vuelve a investigación
```

Cada etapa es un agente de [Strands](https://strandsagents.com) con un rol
acotado. La orquestación es un **Graph** determinístico con una compuerta de
validación. La decisión de validación la calcula **código** (no el LLM), leyendo
datos reales de un export de eRank.

---

## Estructura

```
pod-agents/
├── main.py                 # punto de entrada: python main.py
├── config.py               # marca, modelos (LOCAL/HOSTED), contexto de marca
├── pipeline.py             # arma el grafo: nodos, edges y compuertas
├── tracing.py              # trazas por nodo y por tool (hooks de Strands)
├── requirements.txt        # dependencias
├── docker-compose.yml      # Postgres 16 local (estado persistente)
├── .env                    # credenciales locales de dev
├── db/init/001_keywords.sql    # esquema inicial (Base de Keywords)
├── eRank_-_Bulk_Keywords.csv   # tu export de eRank (poné el tuyo acá)
├── tools/
│   ├── erank_tools.py      # tools REALES sobre el CSV + veredicto determinístico
│   ├── pod_tools.py        # tools de marca/diseño/producción/publicación (mock)
│   └── db_tools.py         # persistencia Postgres (Base de Keywords)
└── agents/
    ├── director.py  researcher.py  validator.py  designer.py
    └── producer.py  marketer.py  operations.py
```

Cada agente expone `build(tracer) -> Agent`. El grafo se arma en `pipeline.py`
importando esas funciones.

---

## Requisitos previos

1. **Python 3.11 o 3.12** (recomendado). Versiones muy nuevas como 3.14 pueden
   no tener wheels de las dependencias todavía.
2. **Ollama** corriendo con el modelo local:
   ```bash
   ollama serve            # en otra terminal (en Mac, la app ya lo hace)
   ollama list             # confirmá que aparece qwen3.5:9b
   ```
   Si no lo tenés: `ollama pull qwen3.5:9b`
3. Tu **export de eRank** (Bulk Keywords) guardado como
   `eRank_-_Bulk_Keywords.csv` en la raíz del proyecto.
4. **Docker** (para el Postgres de estado persistente). Opcional hoy: el pipeline
   corre sin la base; se vuelve requisito cuando se cablee la persistencia.

---

## Instalación (paso a paso)

Desde la carpeta del proyecto (`pod-agents/`):

```bash
# 1. Crear el entorno virtual con Python 3.12
python3.12 -m venv venv

# 2. Instalar dependencias
./venv/bin/pip install -r requirements.txt

# 3. (Opcional) Fijar versiones exactas para reproducibilidad
./venv/bin/pip freeze > requirements.lock.txt
```

> También podés activar el venv con `source venv/bin/activate` y luego usar
> `pip`/`python` sin el prefijo `./venv/bin/`.

---

## Ejecutar

```bash
./venv/bin/python main.py
```

Verás en consola:

- Las **trazas por nodo y por tool** en tiempo real (símbolos `▶`/`✔`/`↳`).
- El **tiempo total** del pipeline.
- El **resultado de cada nodo** ejecutado, con separadores.

---

## Base de datos (Postgres con Docker)

El proyecto usa Postgres para el **estado persistente** del negocio (las "Bases" del
manual operativo: Keywords, y a futuro Ideas, Productos, Ventas, etc.). Hoy solo está
creada la tabla `keywords`. El pipeline todavía **no** la usa; es el próximo paso.

```bash
# Levantar la base (crea el esquema de db/init la primera vez)
docker compose up -d

# Parar (los datos persisten en el volumen pod_pgdata)
docker compose down

# Reset total (BORRA los datos y vuelve a correr db/init)
docker compose down -v
```

- **Conexión:** `postgresql://pod:pod_local_dev@localhost:5432/pod_agents` (ver `.env`).
- **Consola SQL:** `docker exec -it pod_agents_db psql -U pod -d pod_agents`
- **Credenciales:** están en `.env` (dev local). Si inicializás git, agregá `.env` al `.gitignore`.
- **Esquema:** los `.sql` de `db/init/` corren solo al inicializar el volumen vacío. Para
  agregar tablas nuevas creá `db/init/002_*.sql` y hacé `docker compose down -v && up -d`
  (⚠️ borra datos), o aplicá el SQL a mano por `psql`.

---

## Guía de usuario

### Cambiar el objetivo de negocio

El objetivo que arranca el pipeline está en `main.py`, variable `objetivo`.
Editá esa frase en lenguaje natural. Ejemplo:

```python
objetivo = (
    "Lanzar una línea de tazas para amantes del café, nicho con demanda "
    "y baja saturación, alineado a nuestra marca."
)
```

Dirección lo interpreta y define un nicho concreto; el resto del flujo sigue.

### Cómo funciona la compuerta de validación

- El nodo **research** recomienda 3 keywords con datos reales de eRank y las guarda
  en la Base con `record_researched_keywords`.
- El nodo **validation** llama a la tool `validate_and_record_niche`, que calcula por
  código (no por el LLM) si el nicho es `APPROVED` o `REJECTED`:
  - cada keyword debe cumplir umbrales de demanda/competencia, **y**
  - ninguna frase de diseño puede rozar una marca de la blocklist.
  Además persiste cada `decision` (fit/unfit) en la tabla `keywords`.
- Si `APPROVED` → sigue a **design**.
- Si `REJECTED` → vuelve a **research** para reintentar.

La salida del validador termina siempre con la línea exacta
`VERDICT: APPROVED` o `VERDICT: REJECTED`, que es lo que lee la compuerta.

### Ajustar los umbrales de validación

En `tools/erank_tools.py`:

| Constante         | Qué controla                                  | Default   |
|-------------------|-----------------------------------------------|-----------|
| `MIN_SEARCHES`    | demanda mínima para que valga la pena         | `200`     |
| `MAX_COMPETITION` | techo de listings compitiendo (saturación)    | `250_000` |
| `MAX_DIFFICULTY`  | dificultad máxima (0–100)                      | `100`     |

Subir `MIN_SEARCHES` o bajar `MAX_COMPETITION` = criterio más exigente.

### Ajustar la marca y las reglas de negocio

En `config.py`, `STORE_CONFIG`: nombre de la tienda, voz de marca, proveedor POD,
margen objetivo, precio techo y `blocklist_marcas` (marcas prohibidas en diseños).
Esos valores se inyectan en el prompt de todos los agentes vía `brand_context()`.

### Usar un modelo hosted para validación (recomendado en producción)

El nodo de validación es el más sensible (riesgo legal de marcas). Para usarlo con
un modelo hosted más confiable, en `config.py`:

1. Descomentá las dos líneas de `AnthropicModel`.
2. Comentá `HOSTED = LOCAL`.
3. Exportá tu API key: `export ANTHROPIC_API_KEY=...`

Solo el nodo de validación usará el modelo hosted; el resto sigue en local ($0).

### Probar las tools sin levantar el pipeline

Las tools de eRank corren de forma aislada (útil para verificar el CSV y los
umbrales sin gastar en el modelo). Se ejecuta **como módulo desde la raíz**
(no como `python tools/erank_tools.py`, que rompe los imports del paquete):

```bash
./venv/bin/python -m tools.erank_tools
```

Imprime: stats de una keyword, top de oportunidades, validaciones individuales y
un ejemplo de veredicto determinístico.

### Publicación y gate humano

**Operaciones** deja el listing en **DRAFT** y nunca publica de forma definitiva:
la publicación real requiere aprobación humana. Las integraciones reales
(Printify/Printful, Etsy API, trademark screening, generador de imágenes) hoy
están mockeadas en `tools/pod_tools.py`, marcadas con `>>> INTEGRACIÓN REAL`.

---

## Problemas comunes

| Síntoma                                        | Causa probable / solución                                              |
|------------------------------------------------|------------------------------------------------------------------------|
| `ModuleNotFoundError: No module named 'strands'` | El venv está vacío o no lo estás usando. Reinstalá con `requirements.txt`. |
| Falla al instalar dependencias                 | Python demasiado nuevo (p. ej. 3.14). Usá 3.11/3.12.                    |
| El pipeline se cuelga tras validación          | El modelo no emitió la línea `VERDICT: ...`. Probá validación hosted. |
| `Connection refused` a `localhost:11434`       | Ollama no está corriendo. Ejecutá `ollama serve`.                      |
| El nicho no encuentra keywords                 | El CSV no está en la raíz o tiene otro nombre. Revisá `ERANK_CSV`.     |

> La ruta del CSV se puede forzar con la variable de entorno `ERANK_CSV`.
