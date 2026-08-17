"""
import_erank.py — Load an eRank Bulk Keywords export into the DB, then run the
SOP validation over the real metrics.
=============================================================================
This is the human gate of the pipeline: you run the 20-keyword groups through
eRank's Bulk Keyword Tool, export the CSV, and load it here.

Usage (from the project root):
    ./venv/bin/python -m tools.import_erank <path-to-erank.csv> [niche]

Steps:
  1. import_csv() upserts the real metrics (searches, clicks, CTR, competition, KD)
     into `keywords` (ratio_r and keyword_type are auto-computed by the DB).
  2. analyze() classifies each row per SOP v1.1 (fit / unfit / trap) and writes
     `decision` + `validation_reason`.

Expected CSV columns (eRank Bulk Keywords export):
    Keywords, Avg Searches, Avg Clicks, Avg CTR, Etsy Competition, Keyword Difficulty
"""

import csv
import sys

import psycopg
from psycopg.rows import dict_row

import config
from tools.erank_tools import ERANK_CSV, _num
from tools.sop_validation import classify


def _read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            kw = (row.get("Keywords") or "").strip()
            if not kw:
                continue
            yield {
                "keyword": kw,
                "search_volume": _num(row.get("Avg Searches", "")),
                "avg_clicks": _num(row.get("Avg Clicks", "")),
                "ctr": _num(row.get("Avg CTR", "")),
                "competition": _num(row.get("Etsy Competition", "")),
                "kd": _num(row.get("Keyword Difficulty", "")),
            }


def import_csv(path, niche="imported"):
    """Upsert the export's real metrics into `keywords`. Returns the row count."""
    rows = list(_read_csv(path))
    with psycopg.connect(config.DATABASE_URL) as conn, conn.cursor() as cur:
        for r in rows:
            cur.execute(
                "INSERT INTO keywords (keyword, niche, search_volume, avg_clicks, "
                "ctr, competition, difficulty, source) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, 'eRank') "
                "ON CONFLICT (keyword, niche) DO UPDATE SET "
                "search_volume = EXCLUDED.search_volume, avg_clicks = EXCLUDED.avg_clicks, "
                "ctr = EXCLUDED.ctr, competition = EXCLUDED.competition, "
                "difficulty = EXCLUDED.difficulty, source = 'eRank'",
                (r["keyword"], niche, r["search_volume"], r["avg_clicks"],
                 r["ctr"], r["competition"], r["kd"]),
            )
        conn.commit()
    return len(rows)


def analyze(niche=None):
    """Classify keywords that have real metrics per SOP v1.1, writing `decision`
    and `validation_reason`. Returns (counts_by_decision, total)."""
    where = "WHERE (search_volume IS NOT NULL OR competition IS NOT NULL)"
    params = []
    if niche:
        where += " AND niche = %s"
        params.append(niche)
    counts = {}
    with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(f"SELECT id, keyword, search_volume, competition, difficulty "
                    f"FROM keywords {where}", params)
        rows = cur.fetchall()
        for r in rows:
            c = classify(r["keyword"], r["search_volume"], r["competition"], r["difficulty"])
            cur.execute(
                "UPDATE keywords SET decision = %s::keyword_decision, validation_reason = %s "
                "WHERE id = %s",
                (c["decision"], c["reason"], r["id"]),
            )
            counts[c["decision"]] = counts.get(c["decision"], 0) + 1
        conn.commit()
    return counts, len(rows)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else ERANK_CSV
    niche = sys.argv[2] if len(sys.argv) > 2 else "imported"

    n = import_csv(path, niche)
    print(f"Imported {n} keyword(s) from {path} into niche '{niche}'.")

    counts, total = analyze(niche)
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"Analyzed {total} keyword(s) per SOP v1.1: {summary or '(none)'}")
