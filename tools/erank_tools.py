"""
erank_tools.py — Strands tools that read REAL data from the eRank export.
============================================================================
Replaces the mocked research tools with queries over the CSV you export from
eRank (Bulk Keywords).

Expected export columns:
    Keywords, Avg Searches, Avg Clicks, Avg CTR, Etsy Competition, Keyword Difficulty
Special values it handles: "< 20" (minimal demand) and "Unknown".

Key design: the logic lives in plain functions (_lookup, _opportunities,
_validate) and the tools are thin @tool wrappers. This keeps the logic testable
without a model, and lets the VALIDATOR get an OBJECTIVE verdict computed by code
(we do not depend on how the local model reasons).
"""

import csv
import os

from strands import tool

from tools.pod_tools import trademark_risk

# Path to the eRank export. By default it looks in the project root (the folder
# that contains 'tools/'). You can force another path with ERANK_CSV.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERANK_CSV = os.getenv("ERANK_CSV", os.path.join(_PROJECT_ROOT, "eRank_-_Bulk_Keywords.csv"))

# Validation thresholds (tune to your business criteria)
MIN_SEARCHES = 200          # minimum demand to be worth it
MAX_COMPETITION = 250_000   # ceiling of competing listings (avoid saturation)
MAX_DIFFICULTY = 100        # max difficulty (0-100)


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------
def _num(v):
    """'17,192' -> 17192 · '140%' -> 140 · '< 20' -> 0 · 'Unknown'/'' -> None"""
    v = (v or "").strip()
    if v in ("", "Unknown"):
        return None
    if v.startswith("<"):
        return 0          # "< 20": treated as ~null demand for thresholds
    return int(v.replace(",", "").replace("%", ""))


def _record(row):
    return {
        "keyword": row["Keywords"].strip(),
        "searches": _num(row["Avg Searches"]),
        "searches_raw": row["Avg Searches"].strip(),
        "clicks": _num(row["Avg Clicks"]),
        "ctr": row["Avg CTR"].strip(),
        "competition": _num(row["Etsy Competition"]),
        "difficulty": _num(row["Keyword Difficulty"]),
    }


def _load():
    with open(ERANK_CSV, encoding="utf-8-sig") as f:
        return [_record(r) for r in csv.DictReader(f)]


# --------------------------------------------------------------------------
# Logic (testable without a model)
# --------------------------------------------------------------------------
def _lookup(keyword):
    kw = keyword.lower()
    for r in _load():
        if kw in r["keyword"].lower():
            return r
    return None


def _score(r):
    """Opportunity = demand per unit of competition. Higher = better."""
    if not r["searches"] or not r["competition"]:
        return -1.0
    return r["searches"] / r["competition"]


def _opportunities(top=5):
    ranked = sorted(_load(), key=_score, reverse=True)
    return [r for r in ranked if _score(r) > 0][:top]


def _validate(keyword):
    r = _lookup(keyword)
    if r is None:
        return False, f"'{keyword}' is not in the eRank export."
    reasons = []
    if r["searches"] is None or r["searches"] < MIN_SEARCHES:
        reasons.append(f"low demand ({r['searches_raw']} < {MIN_SEARCHES})")
    if r["competition"] is None or r["competition"] > MAX_COMPETITION:
        comp_txt = "Unknown" if r["competition"] is None else f"{r['competition']:,}"
        reasons.append(f"high competition ({comp_txt} > {MAX_COMPETITION:,})")
    if r["difficulty"] is not None and r["difficulty"] > MAX_DIFFICULTY:
        reasons.append(f"difficulty {r['difficulty']} > {MAX_DIFFICULTY}")
    ok = len(reasons) == 0
    return ok, ("meets demand and competition thresholds" if ok
                else "; ".join(reasons))


def _verdict(keywords, design_phrases=None):
    """Compute APPROVED/REJECTED 100% deterministically (no LLM).

    APPROVED only if there is at least one keyword, ALL are FIT and no design
    phrase brushes against a trademark. Returns (approved: bool, report: str).
    The report ALWAYS ends with the exact line 'VERDICT: APPROVED' or
    'VERDICT: REJECTED'.
    """
    keywords = [k for k in (keywords or []) if k and k.strip()]
    design_phrases = [f for f in (design_phrases or []) if f and f.strip()]

    lines, all_fit = [], True
    if not keywords:
        all_fit = False
        lines.append("- (no keywords to validate)")
    for kw in keywords:
        ok, reason = _validate(kw)
        lines.append(f"- {kw}: {'FIT' if ok else 'UNFIT'} — {reason}")
        all_fit = all_fit and ok

    risk = False
    tm_lines = []
    for phrase in design_phrases:
        has_risk, msg = trademark_risk(phrase)
        tm_lines.append(f"- {phrase}: {msg}")
        risk = risk or has_risk

    approved = all_fit and not risk
    report = ["Keyword validation:", *lines]
    if tm_lines:
        report += ["Trademark risk:", *tm_lines]
    else:
        report.append("Trademark risk: (no explicit design phrases)")
    report.append(f"VERDICT: {'APPROVED' if approved else 'REJECTED'}")
    return approved, "\n".join(report)


# --------------------------------------------------------------------------
# Strands TOOLS
# --------------------------------------------------------------------------
@tool
def erank_keyword(keyword: str) -> str:
    """Return real stats for a keyword from the eRank export.

    Args:
        keyword: the keyword or phrase to look up
    """
    r = _lookup(keyword)
    if r is None:
        return f"'{keyword}' is not in the eRank export."
    return (f"'{r['keyword']}': searches={r['searches_raw']}, "
            f"competition={r['competition']:,} listings, "
            f"CTR={r['ctr']}, difficulty={r['difficulty']}/100.")


@tool
def erank_opportunities(top: int = 5) -> str:
    """List the best keywords by demand/competition ratio (from the eRank export).

    Args:
        top: how many opportunities to return (default 5)
    """
    best = _opportunities(top)
    if not best:
        return "No keywords with enough data in the export."
    lines = [f"- {r['keyword']}: {r['searches_raw']} searches / "
             f"{r['competition']:,} competition (diff {r['difficulty']})"
             for r in best]
    return "Best opportunities (demand vs competition):\n" + "\n".join(lines)


@tool
def erank_validate_keyword(keyword: str) -> str:
    """Validate a keyword against objective demand/competition thresholds (eRank data).
    Returns a clear ruling so the validator can decide without ambiguity.

    Args:
        keyword: the keyword or phrase to validate
    """
    ok, reason = _validate(keyword)
    status = "FIT" if ok else "UNFIT"
    return f"{status}: '{keyword}' — {reason}."


@tool
def emit_niche_verdict(keywords: list, design_phrases: list = None) -> str:
    """Emit the final niche VERDICT deterministically (computed by code, not the
    model). Validates each keyword against the eRank thresholds and each design
    phrase against the trademark blocklist. Returns a report that ends EXACTLY
    with 'VERDICT: APPROVED' or 'VERDICT: REJECTED'.

    Args:
        keywords: list of candidate keywords to validate (the 3 recommended ones)
        design_phrases: optional list of design phrases/concepts to trademark-check
    """
    _, report = _verdict(keywords, design_phrases)
    return report


# --------------------------------------------------------------------------
# Manual test: python -m tools.erank_tools
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("Single keyword:")
    print(" ", erank_keyword("horror movie shirt"))
    print("\nTop 5 opportunities:")
    print(erank_opportunities(5))
    print("\nValidations:")
    for kw in ["horror movie shirt", "halloween shirt", "creepy cute shirt"]:
        print(" ", erank_validate_keyword(kw))

    print("\nDeterministic niche verdict:")
    print(emit_niche_verdict(
        ["horror movie shirt", "halloween shirt", "creepy cute shirt"],
        ["creepy cute pumpkin", "disney halloween"],
    ))
