"""
db_tools.py — Persistence layer over Postgres (the "bases" from the manual).
============================================================================
First base implemented: `keywords` (see db/init/001_keywords.sql).

Design mirrors erank_tools/pod_tools: plain functions hold the logic (testable
and reusable) and the @tool wrappers are thin. Metrics are enriched from the
eRank export via erank_tools._lookup so agents only pass keyword + niche.

Resilience: every tool degrades gracefully if Postgres is down — the pipeline
must never die because the database is unavailable.
"""

import psycopg
from psycopg.rows import dict_row
from strands import tool

import config
from tools.erank_tools import _lookup, _num, _validate, _verdict
from tools.keyword_gen import (
    generate_candidates, compose_all, render_all, MILESTONE_AGES,
)


# --------------------------------------------------------------------------
# Connection + low-level helpers
# --------------------------------------------------------------------------
def _connect():
    return psycopg.connect(config.DATABASE_URL, row_factory=dict_row, connect_timeout=5)


def _enrich(keyword):
    """Pull eRank metrics for a keyword (or Nones if it is not in the export)."""
    r = _lookup(keyword)
    if r is None:
        return {"search_volume": None, "avg_clicks": None, "ctr": None,
                "competition": None, "difficulty": None}
    return {
        "search_volume": r["searches"],
        "avg_clicks": r["clicks"],
        "ctr": _num(r["ctr"]),
        "competition": r["competition"],
        "difficulty": r["difficulty"],
    }


def _upsert_keyword(cur, keyword, niche, seasonality=None, source="eRank"):
    """Insert/update a keyword row with fresh metrics. Never touches `decision`."""
    m = _enrich(keyword)
    cur.execute(
        "INSERT INTO keywords (keyword, niche, seasonality, search_volume, "
        "avg_clicks, ctr, competition, difficulty, source) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (keyword, niche) DO UPDATE SET "
        "seasonality = COALESCE(EXCLUDED.seasonality, keywords.seasonality), "
        "search_volume = EXCLUDED.search_volume, avg_clicks = EXCLUDED.avg_clicks, "
        "ctr = EXCLUDED.ctr, competition = EXCLUDED.competition, "
        "difficulty = EXCLUDED.difficulty, source = EXCLUDED.source",
        (keyword, niche, seasonality, m["search_volume"], m["avg_clicks"],
         m["ctr"], m["competition"], m["difficulty"], source),
    )


def _set_decision(cur, keyword, decision, reason, niche="general"):
    """Write a validation decision. Matches existing rows by keyword (any niche)
    so the researcher's saved rows get updated; inserts a minimal row otherwise."""
    cur.execute(
        "UPDATE keywords SET decision = %s::keyword_decision, validation_reason = %s "
        "WHERE lower(keyword) = lower(%s)",
        (decision, reason, keyword),
    )
    if cur.rowcount == 0:
        m = _enrich(keyword)
        cur.execute(
            "INSERT INTO keywords (keyword, niche, search_volume, avg_clicks, ctr, "
            "competition, difficulty, decision, validation_reason) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s::keyword_decision, %s) "
            "ON CONFLICT (keyword, niche) DO UPDATE SET "
            "decision = EXCLUDED.decision, validation_reason = EXCLUDED.validation_reason",
            (keyword, niche, m["search_volume"], m["avg_clicks"], m["ctr"],
             m["competition"], m["difficulty"], decision, reason),
        )


# --------------------------------------------------------------------------
# Stage 1 (discovery): generate the eRank block and stage it as pending
# --------------------------------------------------------------------------
def _stage_keywords(cur, keywords, niche, seasonality=None):
    for kw in keywords:
        cur.execute(
            "INSERT INTO keywords (keyword, niche, seasonality, decision, source) "
            "VALUES (%s, %s, %s, 'pending', 'staged') "
            "ON CONFLICT (keyword, niche) DO UPDATE SET "
            "seasonality = COALESCE(EXCLUDED.seasonality, keywords.seasonality)",
            (kw, niche, seasonality),
        )


@tool
def generate_and_stage_keywords(occasion: str, niche: str, year: int = None,
                                seasonality: str = None) -> str:
    """Generate ALL keyword candidates for an occasion (by SOP axes, no 5/12/3
    cap), stage every one as 'pending' in the Keywords base for the niche, and
    return the full priority-ordered list plus the same keywords chunked into
    comma-separated groups of 20 to run in eRank's Bulk Keyword Tool.

    The occasion is the SEARCH term base (e.g. 'birthday', 'graduation',
    'christmas') — not the cross-niche, which is only for design/tags.

    Args:
        occasion: the searchable occasion/life-event
        niche: short niche slug to group these keywords under (e.g. 'milestone-birthday')
        year: cohort year for 'class of {year}' / 'senior {year}' (optional)
        seasonality: season tag, e.g. 'Q4' (optional)
    """
    occ = (occasion or "").strip().lower()
    if not occ:
        return "Provide an occasion (e.g. 'birthday')."
    if not (niche or "").strip():
        return "Provide a niche slug."
    ages = MILESTONE_AGES if occ == "birthday" else None
    candidates = generate_candidates(occ, year=year, ages=ages)
    rows = compose_all(candidates, occasion=occ)
    if not rows:
        return "Could not generate keyword candidates for that occasion."
    block = [k for _, _, k in rows]
    try:
        with _connect() as conn, conn.cursor() as cur:
            _stage_keywords(cur, block, niche.strip(), seasonality)
            conn.commit()
        staged = f"\n\nStaged {len(block)} keywords as pending for niche '{niche.strip()}'."
    except Exception as e:  # noqa: BLE001 — still return the block if DB is down
        staged = f"\n\n(warning: could not stage to DB — {type(e).__name__})"
    nxt = (f"\nNext: run EACH group in eRank's Bulk Keyword Tool, export the CSV(s), then:"
           f"\n  python -m tools.import_erank <csv> '{niche.strip()}'")
    return render_all(rows) + staged + nxt


# --------------------------------------------------------------------------
# Strands TOOLS
# --------------------------------------------------------------------------
@tool
def record_researched_keywords(keywords: list, niche: str, seasonality: str = None) -> str:
    """Save the researched keywords to the Keywords base, enriching each with real
    eRank metrics. Use this after choosing the final keywords for a niche.

    Args:
        keywords: list of keywords to persist
        niche: the niche these keywords belong to
        seasonality: optional season/occasion (e.g. 'Q4', 'Halloween')
    """
    clean = [k for k in (keywords or []) if k and k.strip()]
    if not clean:
        return "No keywords to record."
    try:
        with _connect() as conn, conn.cursor() as cur:
            for kw in clean:
                _upsert_keyword(cur, kw, niche, seasonality)
            conn.commit()
    except Exception as e:  # noqa: BLE001 — best-effort persistence
        return f"Could not save to the database ({type(e).__name__}). Keywords not persisted."
    return f"Recorded {len(clean)} keyword(s) in the base for niche '{niche}'."


@tool
def validate_and_record_niche(keywords: list, niche: str = "general",
                              design_phrases: list = None) -> str:
    """Emit the niche VERDICT deterministically AND record each keyword's decision
    in the Keywords base. Returns a report ending EXACTLY with 'VERDICT: APPROVED'
    or 'VERDICT: REJECTED'. The verdict is computed by code; never override it.

    Args:
        keywords: candidate keywords to validate
        niche: the niche these keywords belong to
        design_phrases: optional design phrases/concepts to trademark-check
    """
    _, report = _verdict(keywords, design_phrases)

    persisted = True
    try:
        with _connect() as conn, conn.cursor() as cur:
            for kw in [k for k in (keywords or []) if k and k.strip()]:
                ok, reason = _validate(kw)
                _set_decision(cur, kw, "fit" if ok else "unfit", reason, niche)
            conn.commit()
    except Exception:  # noqa: BLE001 — verdict still returned even if DB is down
        persisted = False

    if not persisted:
        lines = report.split("\n")
        lines.insert(-1, "(note: decisions were not persisted to the database)")
        report = "\n".join(lines)
    return report


@tool
def list_keywords(niche: str = None, only_fit: bool = False, limit: int = 50) -> str:
    """List keywords stored in the Keywords base, most searched first.

    Args:
        niche: optional niche filter
        only_fit: if true, only keywords marked fit/to_design
        limit: max rows to return (default 50)
    """
    query = ("SELECT keyword, niche, search_volume, competition, difficulty, decision "
             "FROM keywords")
    conds, params = [], []
    if niche:
        conds.append("niche = %s")
        params.append(niche)
    if only_fit:
        conds.append("decision IN ('fit', 'to_design')")
    if conds:
        query += " WHERE " + " AND ".join(conds)
    query += " ORDER BY search_volume DESC NULLS LAST LIMIT %s"
    params.append(limit)

    try:
        with _connect() as conn, conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    except Exception as e:  # noqa: BLE001
        return f"Could not read the database ({type(e).__name__})."

    if not rows:
        return "No keywords found for that filter."
    lines = [f"- {r['keyword']} [{r['niche']}]: vol={r['search_volume']}, "
             f"comp={r['competition']}, diff={r['difficulty']}, decision={r['decision']}"
             for r in rows]
    return "Keywords in base:\n" + "\n".join(lines)


# --------------------------------------------------------------------------
# Manual test: python -m tools.db_tools
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print(record_researched_keywords(
        ["horror movie shirt", "halloween shirt", "creepy cute shirt"],
        niche="halloween", seasonality="Q4",
    ))
    print(validate_and_record_niche(
        ["horror movie shirt", "halloween shirt", "creepy cute shirt"],
        niche="halloween",
        design_phrases=["creepy cute pumpkin", "disney halloween"],
    ))
    print(list_keywords(niche="halloween"))
