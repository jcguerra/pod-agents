# POD Pipeline for Etsy — multi-agent system (Strands + Ollama)

Multi-agent system that walks, end to end, the workflow of a Print-on-Demand
store on Etsy:

```
direction → research → validation → design → production → marketing → operations
                              │
                              └─ gate: if REJECTED, goes back to research
```

Each stage is a [Strands](https://strandsagents.com) agent with a narrow role.
Orchestration is a deterministic **Graph** with a validation gate. The validation
decision is computed by **code** (not by the LLM), reading real data from an eRank
export.

---

## Structure

```
pod-agents/
├── main.py                 # entry point: python main.py
├── config.py               # brand, models (LOCAL/HOSTED), brand context
├── pipeline.py             # builds the graph: nodes, edges and gates
├── tracing.py              # per-node and per-tool traces (Strands hooks)
├── requirements.txt        # dependencies
├── docker-compose.yml      # local Postgres 16 (persistent state)
├── .env                    # local dev credentials
├── db/init/001_keywords.sql    # initial schema (Keywords Base)
├── eRank_-_Bulk_Keywords.csv   # your eRank export (drop yours here)
├── tools/
│   ├── erank_tools.py      # REAL tools over the CSV + deterministic verdict
│   ├── pod_tools.py        # brand/design/production/publishing tools (mock)
│   └── db_tools.py         # Postgres persistence (Keywords Base)
└── agents/
    ├── director.py  researcher.py  validator.py  designer.py
    └── producer.py  marketer.py  operations.py
```

Every agent exposes `build(tracer) -> Agent`. The graph is assembled in
`pipeline.py` by importing those functions.

---

## Prerequisites

1. **Python 3.11 or 3.12** (recommended). Very new versions such as 3.14 may not
   have wheels for the dependencies yet.
2. **Ollama** running with the local model:
   ```bash
   ollama serve            # in another terminal (on Mac, the app already does it)
   ollama list             # confirm qwen3.5:9b shows up
   ```
   If you don't have it: `ollama pull qwen3.5:9b`
3. Your **eRank export** (Bulk Keywords) saved as
   `eRank_-_Bulk_Keywords.csv` at the project root.
4. **Docker** (for the persistent-state Postgres). Optional today: the pipeline
   runs without the database; it becomes a requirement once persistence is wired in.

---

## Installation (step by step)

From the project folder (`pod-agents/`):

```bash
# 1. Create the virtual environment with Python 3.12
python3.12 -m venv venv

# 2. Install dependencies
./venv/bin/pip install -r requirements.txt

# 3. (Optional) Pin exact versions for reproducibility
./venv/bin/pip freeze > requirements.lock.txt
```

> You can also activate the venv with `source venv/bin/activate` and then use
> `pip`/`python` without the `./venv/bin/` prefix.

---

## Running

```bash
./venv/bin/python main.py
```

You'll see in the console:

- The **per-node and per-tool traces** in real time (symbols `▶`/`✔`/`↳`).
- The **total time** of the pipeline.
- The **result of each executed node**, with separators.

---

## Database (Postgres with Docker)

The project uses Postgres for the business's **persistent state** (the "Bases" from
the operations manual: Keywords, and later Ideas, Products, Sales, etc.). Today only
the `keywords` table is created. The pipeline does **not** use it yet; that's the
next step.

```bash
# Start the database (creates the db/init schema the first time)
docker compose up -d

# Stop it (data persists in the pod_pgdata volume)
docker compose down

# Full reset (DELETES the data and re-runs db/init)
docker compose down -v
```

- **Connection:** `postgresql://pod:pod_local_dev@localhost:5432/pod_agents` (see `.env`).
- **SQL console:** `docker exec -it pod_agents_db psql -U pod -d pod_agents`
- **Credentials:** they live in `.env` (local dev). If you initialize git, add `.env` to `.gitignore`.
- **Schema:** the `.sql` files in `db/init/` run only when initializing an empty volume. To
  add new tables create `db/init/002_*.sql` and run `docker compose down -v && up -d`
  (⚠️ deletes data), or apply the SQL by hand through `psql`.

---

## User guide

### Changing the business objective

The objective that kicks off the pipeline is in `main.py`, variable `objetivo`.
Edit that natural-language sentence. Example:

```python
objetivo = (
    "Lanzar una línea de tazas para amantes del café, nicho con demanda "
    "y baja saturación, alineado a nuestra marca."
)
```

Direction interprets it and defines a concrete niche; the rest of the flow follows.

### How the validation gate works

- The **research** node recommends 3 keywords using real eRank data and stores them
  in the Base with `record_researched_keywords`.
- The **validation** node calls the `validate_and_record_niche` tool, which computes by
  code (not by the LLM) whether the niche is `APPROVED` or `REJECTED`:
  - every keyword must meet the demand/competition thresholds, **and**
  - no design phrase may brush against a trademark in the blocklist.
  It also persists each `decision` (fit/unfit) in the `keywords` table.
- If `APPROVED` → it moves on to **design**.
- If `REJECTED` → it goes back to **research** to retry.

The validator's output always ends with the exact line
`VERDICT: APPROVED` or `VERDICT: REJECTED`, which is what the gate reads.

### Tuning the validation thresholds

In `tools/erank_tools.py`:

| Constant          | What it controls                              | Default   |
|-------------------|-----------------------------------------------|-----------|
| `MIN_SEARCHES`    | minimum demand for it to be worth it          | `200`     |
| `MAX_COMPETITION` | ceiling of competing listings (saturation)    | `250_000` |
| `MAX_DIFFICULTY`  | maximum difficulty (0–100)                    | `100`     |

Raising `MIN_SEARCHES` or lowering `MAX_COMPETITION` = stricter criteria.

### Tuning the brand and the business rules

In `config.py`, `STORE_CONFIG`: store name, brand voice, POD provider, target
margin, price ceiling and `blocklist_marcas` (trademarks banned from designs).
Those values are injected into every agent's prompt via `brand_context()`.

### Using a hosted model for validation (recommended in production)

The validation node is the most sensitive one (legal trademark risk). To run it with
a more reliable hosted model, in `config.py`:

1. Uncomment the two `AnthropicModel` lines.
2. Comment out `HOSTED = LOCAL`.
3. Export your API key: `export ANTHROPIC_API_KEY=...`

Only the validation node will use the hosted model; the rest stays local ($0).

### Testing the tools without starting the pipeline

The eRank tools run in isolation (useful to check the CSV and the thresholds
without spending on the model). Run it **as a module from the root**
(not as `python tools/erank_tools.py`, which breaks the package imports):

```bash
./venv/bin/python -m tools.erank_tools
```

It prints: stats for a keyword, top opportunities, individual validations and
an example of a deterministic verdict.

### Publishing and the human gate

**Operations** leaves the listing in **DRAFT** and never publishes for real:
actual publishing requires human approval. The real integrations
(Printify/Printful, Etsy API, trademark screening, image generator) are
mocked today in `tools/pod_tools.py`, marked with `>>> INTEGRACIÓN REAL`.

---

## Common problems

| Symptom                                        | Likely cause / fix                                                     |
|------------------------------------------------|------------------------------------------------------------------------|
| `ModuleNotFoundError: No module named 'strands'` | The venv is empty or you're not using it. Reinstall with `requirements.txt`. |
| Dependency install fails                       | Python too new (e.g. 3.14). Use 3.11/3.12.                             |
| The pipeline hangs after validation            | The model didn't emit the `VERDICT: ...` line. Try hosted validation.  |
| `Connection refused` to `localhost:11434`      | Ollama isn't running. Run `ollama serve`.                              |
| The niche finds no keywords                    | The CSV isn't at the root or has another name. Check `ERANK_CSV`.      |

> The CSV path can be forced with the `ERANK_CSV` environment variable.
