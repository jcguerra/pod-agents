"""
streamlit_app.py — Mini UI skeleton over the pod-agents backend + Postgres.
==========================================================================
A thin panel that mirrors the two-stage pipeline (split around the human eRank
gate). It reuses the real backend functions — it adds no business logic:

  - Keywords base : read the `keywords` table (filter by niche / decision).
  - Stage 1       : generate + stage the 20-keyword SOP block (deterministic).
  - Human gate    : upload an eRank Bulk export CSV, import it, run SOP analysis.
  - Stage 2       : SOP survival report for a niche; optionally run production.

Run (from the project root, with Postgres up and the venv active):
    ./venv/bin/streamlit run streamlit_app.py

Display strings are Spanish (the panel is for the non-technical partner);
identifiers, comments and DB columns stay in English per project convention.
"""

import re
import tempfile

import psycopg
import streamlit as st
from psycopg.rows import dict_row

import config
from agents import director
from tracing import Tracer
from main import _field, _first_option, _slug  # reuse the robust director parsing
from tools.db_tools import generate_and_stage_keywords
from tools.import_erank import analyze as sop_analyze
from tools.import_erank import import_csv
from tools.analysis_tools import analyze_niche_report


# --------------------------------------------------------------------------
# DB helpers (read-only views; actions go through the backend functions)
# --------------------------------------------------------------------------
def _db_ok() -> tuple[bool, str]:
    try:
        with psycopg.connect(config.DATABASE_URL, connect_timeout=3) as conn, conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM keywords")
            (n,) = cur.fetchone()
        return True, f"{n} keyword(s) en la base"
    except Exception as e:  # noqa: BLE001
        return False, type(e).__name__


@st.cache_data(ttl=15)
def _niches() -> list[str]:
    with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("SELECT DISTINCT niche FROM keywords WHERE niche IS NOT NULL ORDER BY niche")
        return [r["niche"] for r in cur.fetchall()]


@st.cache_data(ttl=15)
def _keywords(niche: str | None, decision: str | None) -> list[dict]:
    query = ("SELECT keyword, niche, keyword_type AS type, search_volume AS searches, "
             "competition AS comp, difficulty AS kd, ratio_r AS ratio, decision, seasonality "
             "FROM keywords")
    conds, params = [], []
    if niche:
        conds.append("niche = %s")
        params.append(niche)
    if decision:
        conds.append("decision = %s::keyword_decision")
        params.append(decision)
    if conds:
        query += " WHERE " + " AND ".join(conds)
    query += " ORDER BY search_volume DESC NULLS LAST LIMIT 500"
    with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


DECISIONS = ["pending", "fit", "unfit", "trap", "to_design", "discarded"]


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def page_keywords():
    st.header("📊 Base de Keywords")
    st.caption("Vista de solo lectura de la tabla `keywords`.")

    niches = ["(todos)"] + _niches()
    c1, c2, c3 = st.columns([2, 2, 1])
    niche = c1.selectbox("Nicho", niches)
    decision = c2.selectbox("Decisión", ["(todas)"] + DECISIONS)
    if c3.button("↻ Refrescar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    rows = _keywords(
        None if niche == "(todos)" else niche,
        None if decision == "(todas)" else decision,
    )
    if not rows:
        st.info("No hay keywords para ese filtro. Corré la Etapa 1 para stagear un bloque.")
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption(f"{len(rows)} fila(s).")


def _stage_block_ui(occasion: str, niche: str, year, seasonality):
    """Generate + stage the 20-keyword block and render the result. Shared by
    both discovery modes (manual and director-suggested)."""
    with st.spinner("Generando keywords…"):
        out = generate_and_stage_keywords(
            occasion.strip(), niche.strip(),
            year=int(year) or None,
            seasonality=(seasonality or "").strip() or None,
        )
    st.success("Keywords generadas y stageadas como `pending`.")
    st.code(out, language="text")
    st.cache_data.clear()


def _discovery_manual():
    """Mode A — the user decides the occasion and niche."""
    with st.form("discovery_manual"):
        occasion = st.text_input("Ocasión (término de búsqueda base)", placeholder="birthday, graduation, christmas…")
        niche = st.text_input("Nicho (slug corto)", placeholder="milestone-birthday")
        c1, c2 = st.columns(2)
        year = c1.number_input("Año de cohorte (opcional, solo graduaciones)",
                               min_value=0, max_value=2100, value=0, step=1)
        seasonality = c2.text_input("Seasonality (opcional)", placeholder="Q4")
        submitted = st.form_submit_button("Generar y stagear bloque")

    if submitted:
        if not occasion.strip() or not niche.strip():
            st.warning("Completá ocasión y nicho.")
            return
        _stage_block_ui(occasion, niche, year, seasonality)


def _discovery_director():
    """Mode B — the director agent (LLM) suggests the occasion and niche."""
    st.caption("El director (IA) elige la ocasión y el nicho por vos: mira el calendario "
               "(lead time ~90 días) y la taxonomía de nichos por popularidad. Usa el modelo "
               "local (Ollama) — puede tardar.")
    default_goal = (
        "Choose the single best seasonal opportunity for the store right now. "
        "Pick ONE searchable occasion and one design theme, with the right lead time."
    )
    goal = st.text_area("Objetivo de negocio para el director", value=default_goal, height=90)

    if st.button("🤖 Que el director sugiera"):
        with st.spinner("El director está pensando (modelo local, puede tardar)…"):
            text = str(director.build(Tracer())(goal))
        # Parse occasion/niche/year the same way main.py discover() does.
        occ = _field(text, "occasion") or ""
        occ = re.split(r"[.\n;]", occ)[0] if occ else ""
        occ = re.sub(r"[\"']", "", _first_option(occ)).strip().lower()
        occ = " ".join(occ.split()[:2])
        niche_raw = _field(text, "niche slug", "niche")
        niche = _slug(_first_option(niche_raw)) if niche_raw else (_slug(occ) if occ else "")
        ym = re.search(r"\b(20\d{2})\b", text)
        st.session_state["dir_suggestion"] = {
            "occasion": occ, "niche": niche,
            "theme": _field(text, "design theme") or "—",
            "year": int(ym.group(1)) if ym else 0, "raw": text,
        }

    sug = st.session_state.get("dir_suggestion")
    if not sug:
        return

    with st.expander("Ver respuesta completa del director"):
        st.code(sug["raw"], language="text")
    if not sug["occasion"]:
        st.error("No pude extraer una ocasión de la respuesta del director. "
                 "Revisá el detalle de arriba o probá de nuevo.")
        return

    st.markdown(f"**Tema de diseño sugerido:** {sug['theme']}  ·  _(va en diseño/tags, no en las keywords)_")
    st.info("Ajustá la sugerencia si querés y luego generá el bloque.")
    c1, c2, c3 = st.columns([2, 2, 1])
    occasion = c1.text_input("Ocasión", value=sug["occasion"])
    niche = c2.text_input("Nicho (slug)", value=sug["niche"])
    year = c3.number_input("Año", min_value=0, max_value=2100, value=sug["year"], step=1)

    if st.button("Generar y stagear bloque con esta sugerencia",
                 disabled=not (occasion.strip() and niche.strip())):
        _stage_block_ui(occasion, niche, year, "Q4")


def page_discovery():
    st.header("🧭 Etapa 1 · Discovery")
    st.caption("Genera el bloque de 20 keywords por ejes (5 head / 12 mid / 3 long-tail) "
               "y lo deja como `pending` en la base.")
    mode = st.radio("¿Quién elige el nicho?",
                    ["✍️ Yo elijo (manual)", "🤖 Que el director sugiera (IA)"],
                    horizontal=True)
    st.divider()
    if mode.startswith("🤖"):
        _discovery_director()
    else:
        _discovery_manual()


def page_import():
    st.header("📥 Gate humano · Importar CSV de eRank")
    st.caption("Subí el export del Bulk Keyword Tool de eRank. Se cargan las métricas reales "
               "y se corre la validación SOP v1.1 (fit / unfit / trap).")

    niche = st.text_input("Nicho al que pertenece el CSV", placeholder="milestone-birthday")
    upload = st.file_uploader("CSV export de eRank", type=["csv"])

    if st.button("Importar y analizar", disabled=not (upload and niche.strip())):
        with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as tmp:
            tmp.write(upload.getbuffer())
            path = tmp.name
        with st.spinner("Importando y clasificando…"):
            n = import_csv(path, niche.strip())
            counts, total = sop_analyze(niche.strip())
        st.success(f"Importadas {n} keyword(s); clasificadas {total} por SOP.")
        st.write({k: v for k, v in sorted(counts.items())})
        st.cache_data.clear()


def page_production():
    st.header("✅ Etapa 2 · Validación & Producción")
    st.caption("Reporte de supervivencia SOP del nicho (necesita ≥2 keywords fit). "
               "Si sobrevive, podés correr la producción (LLM — lento).")

    niches = _niches()
    if not niches:
        st.info("Todavía no hay nichos en la base.")
        return
    niche = st.selectbox("Nicho", niches)

    rep = analyze_niche_report(niche)
    st.code(rep["report"], language="text")

    if not rep["has_metrics"]:
        st.warning("Sin datos de eRank todavía. Importá el CSV en el gate humano.")
        return
    if not rep["survives"]:
        st.error("El nicho NO sobrevive la validación SOP. Generá una nueva ronda de keywords.")
        return

    st.success(f"Sobrevive con {len(rep['fit_keywords'])} keyword(s) fit.")
    if st.button("▶ Correr producción (design → production → marketing → operations)"):
        from pipeline import build_production_graph
        task = (f"Niche: {niche}. SOP-validated keywords: {', '.join(rep['fit_keywords'])}. "
                f"Create the design concept, the POD product, the listing copy, and leave "
                f"the listing as a DRAFT.")
        with st.spinner("Corriendo el grafo de producción (puede tardar varios minutos)…"):
            result = build_production_graph()(task)
        st.success("Producción terminada (listing en DRAFT).")
        for node_id, node in getattr(result, "results", {}).items():
            with st.expander(f"### {node_id}"):
                st.write(str(getattr(node, "result", node)).strip())


# --------------------------------------------------------------------------
# Shell
# --------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="pod-agents", page_icon="🧵", layout="wide")
    st.sidebar.title("🧵 pod-agents")
    st.sidebar.caption(f"Marca: {config.STORE_CONFIG['brand']}")

    ok, detail = _db_ok()
    (st.sidebar.success if ok else st.sidebar.error)(
        f"{'Postgres OK' if ok else 'Postgres caído'} · {detail}")

    pages = {
        "📊 Base de Keywords": page_keywords,
        "🧭 Etapa 1 · Discovery": page_discovery,
        "📥 Gate · Importar CSV": page_import,
        "✅ Etapa 2 · Producción": page_production,
    }
    choice = st.sidebar.radio("Navegación", list(pages.keys()))
    st.sidebar.divider()
    st.sidebar.caption("Flujo: Discovery → [eRank humano] → Import → Validación → Producción")

    if not ok:
        st.error("No hay conexión a Postgres. Levantá la base con `docker compose up -d`.")
    pages[choice]()


if __name__ == "__main__":
    main()
