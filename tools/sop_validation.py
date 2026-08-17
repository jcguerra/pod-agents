"""
sop_validation.py — Keyword validation per SOP Investigación/Validación v1.1.
=============================================================================
The deterministic "brain" that classifies keywords from real eRank metrics,
following the measured rules of the SOP (not the LLM):

  - Ratio R = searches / competition: >=0.02 green, 0.01-0.02 yellow, <0.01 red
  - Core gate: KD <= 85 AND searches >= 100  (Pass-1 survival counts these)
  - Trap detector: near-null searches + crowded shelf -> discard always
  - Apparel test: "X" has volume but "X shirt" < 20 -> demand is not apparel
  - Keyword type by word count: 2 = head, 3 = mid, 4+ = long-tail

Pure functions here operate on plain metric values, so they are testable with
the SOP's measured examples (see __main__). Wiring to the DB/eRank import comes
in later steps.
"""

from strands import tool

# --- SOP thresholds (tunable) ---------------------------------------------
MIN_SEARCHES = 100          # a keyword must clear this to pass the core gate
MAX_KD = 85                 # Keyword Difficulty ceiling
R_GOOD = 0.02               # ratio R: green at/above
R_WEAK = 0.01               # ratio R: yellow down to here, red below
REPORT_FLOOR = 20           # eRank reporting floor: "< 20" ~ null demand
TRAP_MIN_COMPETITION = 10_000  # crowded shelf for the trap detector


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def word_count(keyword):
    return len((keyword or "").split())


def keyword_type(keyword):
    wc = word_count(keyword)
    if wc <= 2:
        return "head"
    if wc == 3:
        return "mid"
    return "long_tail"


def _below_floor(searches):
    """True when demand is null/unreported (Unknown or '< 20')."""
    return searches is None or searches < REPORT_FLOOR


def _searches_disp(searches):
    if searches is None:
        return "Unknown"
    if searches < REPORT_FLOOR:
        return f"< {REPORT_FLOOR}"
    return f"{searches:,}"


def ratio_r(searches, competition):
    """R = searches / competition. None if either is missing/zero."""
    if not searches or not competition:
        return None
    return searches / competition


def r_label(r):
    if r is None:
        return "n/a"
    if r >= R_GOOD:
        return "green"
    if r >= R_WEAK:
        return "yellow"
    return "red"


def is_trap(searches, competition):
    """High competition + null searches: sellers piled where buyers don't
    search. The most dangerous signal because it looks like a live niche."""
    return _below_floor(searches) and (competition or 0) >= TRAP_MIN_COMPETITION


# --------------------------------------------------------------------------
# Per-keyword classification
# --------------------------------------------------------------------------
def classify(keyword, searches, competition, kd):
    """Classify one keyword from its eRank metrics.

    Returns a dict with: keyword, type, searches, competition, kd, r, r_label,
    decision ('fit' | 'unfit' | 'trap'), reason.
    """
    r = ratio_r(searches, competition)
    rl = r_label(r)
    base = {
        "keyword": keyword, "type": keyword_type(keyword),
        "searches": searches, "competition": competition, "kd": kd,
        "r": None if r is None else round(r, 4), "r_label": rl,
    }

    if is_trap(searches, competition):
        return {**base, "decision": "trap",
                "reason": f"trap: {competition:,} listings with {_searches_disp(searches)} searches"}

    reasons = []
    if searches is None or searches < MIN_SEARCHES:
        reasons.append(f"searches {_searches_disp(searches)} < {MIN_SEARCHES}")
    if kd is None or kd > MAX_KD:
        reasons.append(f"KD {kd} > {MAX_KD}")
    if rl == "red":
        reasons.append(f"ratio R {base['r']} < {R_WEAK}")

    if reasons:
        return {**base, "decision": "unfit", "reason": "; ".join(reasons)}
    return {**base, "decision": "fit",
            "reason": f"passes SOP gate (KD<={MAX_KD}, searches>={MIN_SEARCHES}, R={rl})"}


# --------------------------------------------------------------------------
# Apparel test (pairwise: bare term vs '<term> shirt')
# --------------------------------------------------------------------------
def apparel_test(bare_searches, shirt_searches):
    """Volume on the bare term does not prove the buyer wants a shirt.

    Returns (result, reason): 'apparel' | 'not_apparel' | 'n/a'.
    """
    if bare_searches is None or bare_searches < MIN_SEARCHES:
        return "n/a", "bare term has no volume to begin with"
    if shirt_searches is not None and shirt_searches >= REPORT_FLOOR:
        return "apparel", "'X shirt' has volume -> apparel market"
    return "not_apparel", "'X' has volume but 'X shirt' < 20 -> demand is not apparel"


# --------------------------------------------------------------------------
# Niche-level survival (Pass 1 sweep)
# --------------------------------------------------------------------------
def niche_survives(classified):
    """Pass-1 rule: a niche survives with >=2 keywords that clear the core gate
    (KD <= 85 AND searches >= 100). Returns (bool, passing_keywords)."""
    passing = [c for c in classified
               if c.get("kd") is not None and c["kd"] <= MAX_KD
               and c.get("searches") is not None and c["searches"] >= MIN_SEARCHES]
    return len(passing) >= 2, passing


# --------------------------------------------------------------------------
# Strands TOOL (single-keyword; DB-wide analysis comes with the eRank importer)
# --------------------------------------------------------------------------
@tool
def classify_keyword_stats(keyword: str, searches: int = None,
                           competition: int = None, kd: int = None) -> str:
    """Classify a keyword from its eRank metrics per SOP v1.1 (deterministic).
    Returns fit / unfit / trap with the reason and the ratio R.

    Args:
        keyword: the keyword phrase
        searches: eRank Average Searches (None if Unknown, 0 for '< 20')
        competition: eRank Etsy Competition (listings)
        kd: eRank Keyword Difficulty (0-100)
    """
    c = classify(keyword, searches, competition, kd)
    return (f"{c['decision'].upper()}: '{keyword}' [{c['type']}] — {c['reason']} "
            f"(R={c['r']}/{c['r_label']}).")


# --------------------------------------------------------------------------
# Manual test against the SOP's measured examples: python -m tools.sop_validation
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # (keyword, searches, competition, kd, expected_decision)
    CASES = [
        ("golf birthday", 0, 53_142, None, "trap"),
        ("camping birthday", 0, 78_186, None, "trap"),
        ("gardener birthday gift", None, 106_718, None, "trap"),
        ("promoted to grandma", 486, 20_245, 81, "fit"),
        ("new grandma", 479, 109_207, 100, "unfit"),
        ("40th birthday gift", 1_864, 58_327, 75, "fit"),
        ("book lover gift", 17_557, 537_834, 74, "fit"),
        ("chapter 40 shirt", 0, 2_686, 100, "unfit"),
        ("milestone birthday", 0, 72_436, 100, "trap"),
        ("college mom", 0, 41_826, None, "trap"),
    ]
    print("SOP validation vs measured examples:")
    ok = True
    for kw, s, comp, kd, expected in CASES:
        c = classify(kw, s, comp, kd)
        mark = "✓" if c["decision"] == expected else "✗ MISMATCH"
        if c["decision"] != expected:
            ok = False
        print(f"  {mark}  {kw:<24} -> {c['decision']:<6} (exp {expected}) | {c['reason']}")

    print("\nApparel test:")
    for name, bare, shirt in [("senior 2027", 497, 145), ("90th birthday", 1_439, 0)]:
        res, why = apparel_test(bare, shirt)
        print(f"  {name:<16} bare={bare} shirt={shirt} -> {res} ({why})")

    print("\nNiche survival (Pass 1):")
    classified = [classify(kw, s, comp, kd) for kw, s, comp, kd, _ in CASES]
    survives, passing = niche_survives(classified)
    print(f"  survives={survives} with {len(passing)} passing keyword(s): "
          f"{[c['keyword'] for c in passing]}")

    print("\nALL MATCH" if ok else "\nSOME MISMATCHES — review thresholds")
