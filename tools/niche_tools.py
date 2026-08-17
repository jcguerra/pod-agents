"""
niche_tools.py — Niche suggestion via cross-niching over the taxonomy.
=====================================================================
Reads the `niche_items` table (seeded from the Cross-Niching Guide) and crosses
a seasonal anchor (holidays of a month) with one or more other categories —
career, hobby, family_relation, pet — to propose a curated, popularity-ranked
shortlist of candidate niches instead of the full 40,000+ combinations.

Two levers:
  - depth: how many categories are combined = 1 (holiday) + len(cross_categories).
    ["career"] -> "Christmas Teacher" · ["career","family_relation"] ->
    "Christmas Teacher Mom" · ["career","pet","family_relation"] -> 4 components.
  - popularity: each item carries a commercial weight; combos are ranked by the
    sum of their components' weights so money combos float to the top.

Downstream, the researcher validates the shortlist against real eRank data; here
we only generate seasonally-relevant, popularity-ranked candidates.
"""

from datetime import date, timedelta
from itertools import product

import psycopg
from psycopg.rows import dict_row
from strands import tool

import config

CROSS_CATEGORIES = ("career", "hobby", "family_relation", "pet")
_ANCHOR_CAP = 12   # top holidays considered
_CROSS_CAP = 10    # top items per cross category considered (bounds the product)

# eRank Bulk Keyword Tool: processes 20 keywords at a time, ~100/day cap.
BATCH_SIZE = 20
ERANK_DAILY_LIMIT = 100


def _batches(items, size=BATCH_SIZE):
    return [items[i:i + size] for i in range(0, len(items), size)]


def _connect():
    return psycopg.connect(config.DATABASE_URL, row_factory=dict_row, connect_timeout=5)


def _parse_today(today=None):
    if today is None:
        return date.today()
    if isinstance(today, date):
        return today
    return date.fromisoformat(str(today))


def _lead_month(lead_days=None, today=None):
    """Month (1-12) that falls `lead_days` ahead of today — the seasonal anchor
    for suggestions (default lead from config.PLANNING)."""
    if lead_days is None:
        lead_days = config.PLANNING["suggest_lead_days"]
    return (_parse_today(today) + timedelta(days=lead_days)).month


def _items(category, month=None, cap=None):
    """Fetch active items for a category, most popular first. Holidays can be
    filtered by month."""
    query = ("SELECT name, subcategory, month, seasonality, popularity FROM niche_items "
             "WHERE category = %s::niche_category AND active = true")
    params = [category]
    if month is not None:
        query += " AND month = %s"
        params.append(month)
    query += " ORDER BY popularity DESC, name"
    if cap:
        query += " LIMIT %s"
        params.append(cap)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def _suggest(cross_categories=("career",), month=None, lead_days=None, today=None, limit=10):
    """Cross the seasonal holiday anchor with the given categories into ranked
    niche candidates.

    The holiday anchor is the month that falls `lead_days` (default 90) ahead of
    today, so we plan seasons with the required lead time. Pass an explicit
    `month` to override.

    Returns a list of dicts: {niche, components, score, month, seasonality},
    sorted by combined popularity (desc).
    """
    cross_categories = list(cross_categories) or ["career"]
    for c in cross_categories:
        if c not in CROSS_CATEGORIES:
            raise ValueError(f"cross_categories must be within {CROSS_CATEGORIES}; got '{c}'")

    target_month = month if month is not None else _lead_month(lead_days, today)
    anchor = _items("holiday", month=target_month, cap=_ANCHOR_CAP)
    cross_lists = [_items(c, cap=_CROSS_CAP) for c in cross_categories]
    if not anchor or any(not lst for lst in cross_lists):
        return []

    ideas = []
    for combo in product(anchor, *cross_lists):
        parts = list(combo)
        ideas.append({
            "niche": " ".join(p["name"] for p in parts),
            "components": [p["name"] for p in parts],
            "score": sum(p["popularity"] for p in parts),
            "month": parts[0]["month"],
            "seasonality": parts[0]["seasonality"],
        })
    # Rank by combined popularity, then alphabetically for stable output.
    ideas.sort(key=lambda x: (-x["score"], x["niche"]))
    return ideas[:limit]


# --------------------------------------------------------------------------
# Strands TOOLS
# --------------------------------------------------------------------------
@tool
def suggest_niches(cross_categories: list = None, month: int = None, limit: int = 10) -> str:
    """Suggest candidate niches by cross-niching seasonal holidays with one or
    more other categories, ranked by commercial popularity. Use this to pick
    grounded, seasonally-relevant niches instead of inventing them.

    Seasonal timing: by default the holiday anchor is the month ~90 days ahead of
    today (the required planning lead time), so you research a season with enough
    runway to design and publish ~60 days before the holiday.

    Args:
        cross_categories: list of categories to cross with the holiday anchor,
            each one of 'career', 'hobby', 'family_relation', 'pet'. The number
            of components = 1 + len(this list): ['career'] -> 2 (e.g. "Christmas
            Teacher"), ['career','family_relation'] -> 3 ("Christmas Teacher Mom").
            Defaults to ['career'].
        month: 1-12 to force a specific month's holidays; omit to use the
            90-day-ahead planning window.
        limit: how many niche ideas to return (default 10).
    """
    try:
        ideas = _suggest(cross_categories or ["career"], month=month, limit=limit)
    except ValueError as e:
        return str(e)
    except Exception as e:  # noqa: BLE001 — degrade if DB is down
        return f"Could not read the niche taxonomy ({type(e).__name__})."
    if not ideas:
        return "No niche ideas for those filters."
    target = month if month is not None else _lead_month()
    cats = " × ".join(["holiday"] + (cross_categories or ["career"]))
    window = f"month {target}" + ("" if month is not None else " (~90d ahead)")
    header = f"Niche ideas ({cats}, {window}), ranked:"
    lines = [f"- {x['niche']}  (score {x['score']}, {x['seasonality'] or 'any'})"
             for x in ideas]
    return header + "\n" + "\n".join(lines)


@tool
def suggest_niches_bulk(cross_categories: list = None, month: int = None,
                        total: int = 20) -> str:
    """Suggest niches formatted for eRank's Bulk Keyword Tool: comma-separated
    groups of 20 (eRank processes 20 keywords at a time, ~100/day). Paste each
    group into eRank to validate demand/competition in bulk.

    Args:
        cross_categories: categories to cross with the holiday anchor (see
            suggest_niches). Defaults to ['career'].
        month: 1-12 to force a month; omit to use the 90-day-ahead planning window.
        total: how many niches total (capped at 100 = eRank's daily limit).
            Returned in groups of 20.
    """
    total = min(max(int(total), 1), ERANK_DAILY_LIMIT)
    try:
        ideas = _suggest(cross_categories or ["career"], month=month, limit=total)
    except ValueError as e:
        return str(e)
    except Exception as e:  # noqa: BLE001 — degrade if DB is down
        return f"Could not read the niche taxonomy ({type(e).__name__})."
    if not ideas:
        return "No niche ideas for those filters."
    niches = [x["niche"] for x in ideas]
    groups = _batches(niches, BATCH_SIZE)
    blocks = [f"Group {i} ({len(g)} keywords):\n{', '.join(g)}"
              for i, g in enumerate(groups, 1)]
    return "\n\n".join(blocks)


@tool
def planning_dates(today: str = None) -> str:
    """Report the seasonal planning timeline from a reference date: when to
    research niches and when to publish so Etsy's algorithm ranks the listing in
    time for the holiday.

    Args:
        today: reference date 'YYYY-MM-DD' (defaults to the current date)
    """
    p = config.PLANNING
    base = _parse_today(today)
    suggest_on = base + timedelta(days=p["suggest_lead_days"])
    return (
        f"Planning from {base.isoformat()}: "
        f"research/suggest niches for holidays ~{p['suggest_lead_days']}d out "
        f"(around {suggest_on.strftime('%B %Y')}); "
        f"publish {p['publish_lead_days']}d before each holiday; "
        f"Etsy needs ~{p['algo_pickup_days']}d to recognize and rank the listing."
    )


@tool
def list_niche_items(category: str, limit: int = 50) -> str:
    """List items from the niche taxonomy for one category (most popular first).

    Args:
        category: 'holiday', 'career', 'family_relation', 'pet' or 'hobby'
        limit: max items to return (default 50)
    """
    valid = ("holiday", "career", "family_relation", "pet", "hobby")
    if category not in valid:
        return f"category must be one of {valid}"
    try:
        rows = _items(category, cap=limit)
    except Exception as e:  # noqa: BLE001
        return f"Could not read the niche taxonomy ({type(e).__name__})."
    if not rows:
        return f"No items in category '{category}'."
    names = ", ".join(r["name"] for r in rows)
    return f"{category} ({len(rows)}): {names}"


# --------------------------------------------------------------------------
# Manual test: python -m tools.niche_tools
# --------------------------------------------------------------------------
if __name__ == "__main__":
    REF = "2026-08-12"   # reference "today" for a deterministic demo
    print(planning_dates(REF))
    print()
    print(f"90-day-ahead anchor month from {REF}: {_lead_month(today=REF)}")
    print()
    print("=== eRank bulk (groups of 20), holiday × career, 90d ahead ===")
    ideas = _suggest(["career"], lead_days=90, today=REF, limit=20)
    groups = _batches([x["niche"] for x in ideas])
    for i, g in enumerate(groups, 1):
        print(f"Group {i} ({len(g)}):\n{', '.join(g)}")
    print()
    print("=== 3 components (holiday × career × family), 90d ahead ===")
    ideas3 = _suggest(["career", "family_relation"], lead_days=90, today=REF, limit=20)
    print(", ".join(x["niche"] for x in ideas3))
