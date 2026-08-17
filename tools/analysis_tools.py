"""
analysis_tools.py — Stage 2 analysis: validate a niche's keywords from the real
eRank data loaded into the DB, and decide if the niche survives.
=============================================================================
Runs after the human gate (eRank Bulk Tool -> CSV -> import_erank). Applies the
SOP validation to the imported metrics and reports fit/unfit/trap per keyword
plus a survival verdict (SOP Pass-1 rule: >= 2 keywords clear the core gate).
"""

import psycopg
from psycopg.rows import dict_row
from strands import tool

import config
from tools.import_erank import analyze as _classify_niche
from tools.sop_validation import MAX_KD, MIN_SEARCHES


def analyze_niche_report(niche: str) -> dict:
    """Classify a niche's imported keywords per SOP and assess survival.

    Returns {report, survives, has_metrics, fit_keywords, total}.
    """
    try:
        _classify_niche(niche)  # writes decision/validation_reason to the DB
        with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT keyword, search_volume, competition, difficulty, ratio_r, "
                "keyword_type, decision FROM keywords WHERE niche = %s "
                "ORDER BY decision, search_volume DESC NULLS LAST",
                (niche,),
            )
            rows = cur.fetchall()
    except Exception as e:  # noqa: BLE001
        return {"report": f"Could not analyze niche '{niche}' ({type(e).__name__}).",
                "survives": False, "has_metrics": False, "fit_keywords": [], "total": 0}

    if not rows:
        return {"report": f"No keywords for niche '{niche}'. Run stage 1 first.",
                "survives": False, "has_metrics": False, "fit_keywords": [], "total": 0}

    has_metrics = any(r["search_volume"] is not None or r["competition"] is not None
                      for r in rows)
    if not has_metrics:
        return {"report": (f"Niche '{niche}' has {len(rows)} staged keywords but no eRank "
                           f"data yet. Run the Bulk Tool and import the CSV first."),
                "survives": False, "has_metrics": False, "fit_keywords": [], "total": len(rows)}

    fit = [r["keyword"] for r in rows if r["decision"] == "fit"]
    survives = len(fit) >= 2

    lines = [f"SOP analysis for '{niche}' — {len(fit)} fit keyword(s) "
             f"(survival needs >=2 with KD<={MAX_KD}, searches>={MIN_SEARCHES}):"]
    for r in rows:
        lines.append(f"  [{r['decision']:<5}|{r['keyword_type']:<9}] {r['keyword']} — "
                     f"searches={r['search_volume']}, comp={r['competition']}, "
                     f"KD={r['difficulty']}, R={r['ratio_r']}")
    lines.append(f"VERDICT: {'SURVIVES' if survives else 'FAILED'}")
    return {"report": "\n".join(lines), "survives": survives,
            "has_metrics": True, "fit_keywords": fit, "total": len(rows)}


@tool
def analyze_niche(niche: str) -> str:
    """Validate a niche's keywords from the imported eRank data (SOP v1.1) and
    report fit/unfit/trap per keyword plus a survival VERDICT.

    Args:
        niche: the niche slug whose keywords were staged and imported
    """
    return analyze_niche_report(niche)["report"]


if __name__ == "__main__":
    import sys
    n = sys.argv[1] if len(sys.argv) > 1 else "imported"
    print(analyze_niche_report(n)["report"])
