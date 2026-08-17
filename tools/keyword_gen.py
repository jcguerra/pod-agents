"""
keyword_gen.py — Build the eRank 20-keyword block by axes (SOP v1.1).
====================================================================
The SOP keyword engine is the AXES (cohort/age/formula/family_role/hobby/
occupational), NOT the cross-niche. A block is exactly 20 keywords composed as:
    5 head (2 words) + 12 mid (3 words) + 3 long-tail (4+ words)

Two entry points:
  - build_keyword_block(occasion, ...): template generator for event-type
    occasions (birthday, graduation, retirement, anniversary...).
  - compose_keyword_block(keywords): when the agent supplies its own candidates,
    this enforces the 5/12/3 composition and the pre-filters.

Pre-filters (SOP 1.4): apparel trademarks (hubby, wifey, realtor, mama bear) and
the store trademark blocklist. Copyright and the JOY tone filter need human
judgment — flagged, not auto-applied.
"""

from strands import tool

from config import STORE_CONFIG
from tools.sop_validation import keyword_type

# Apparel trademarks that lose the listing (SOP 1.4).
APPAREL_TRADEMARKS = ["hubby", "wifey", "realtor", "mama bear"]

# Axis priority (best measured performance first) — drives which candidates win
# the limited slots in a block.
AXIS_ORDER = ["cohort", "age", "formula", "family_role", "hobby", "occupational",
              "occasion", "other"]
_AXIS_RANK = {a: i for i, a in enumerate(AXIS_ORDER)}
_TYPE_RANK = {"head": 0, "mid": 1, "long_tail": 2}

# Defaults for the template generator.
MILESTONE_AGES = [30, 40, 50, 60, 70, 80, 90]
DEFAULT_ROLES = ["mom", "dad", "grandma", "grandpa"]
DEFAULT_HOBBIES = ["book", "coffee", "plant"]   # -> "book lover gift"

# Holidays whose name is ALREADY the searchable term, so a trailing "day" is
# redundant for keywords ("thanksgiving shirt", not "thanksgiving day shirt").
# For occasions where "day" is essential (mother's day, memorial day, labor day)
# the base word is not the holiday, so they are intentionally NOT listed.
# (Ideally sourced from the niche_items taxonomy; a small whitelist for now.)
_REDUNDANT_DAY = {"thanksgiving", "christmas", "halloween", "easter",
                  "new year's", "new years"}


def occasion_search_base(occasion):
    """Reduce an occasion to the term buyers actually type. Drops a redundant
    trailing 'day' for holidays whose name already is the search term
    ('thanksgiving day' -> 'thanksgiving'); leaves occasions where 'day' is
    essential ('mother's day', 'memorial day') untouched.

    This keeps 2-word occasions from pushing every occasion-embedding keyword to
    3 words (which would strand the 5 head slots on generic role fillers)."""
    occ = (occasion or "").strip().lower()
    if occ.endswith(" day") and occ[:-4].strip() in _REDUNDANT_DAY:
        return occ[:-4].strip()
    return occ


def _blocked(keyword):
    low = keyword.lower()
    for term in list(STORE_CONFIG["trademark_blocklist"]) + APPAREL_TRADEMARKS:
        if term in low:
            return True
    return False


# --------------------------------------------------------------------------
# Template generator (axis -> candidate keywords)
# --------------------------------------------------------------------------
def generate_candidates(occasion, year=None, ages=None, roles=None, hobbies=None):
    """Produce a pool of (axis, keyword) candidates for an event-type occasion.
    Templates only fire when their inputs are provided (ages/year/roles/hobbies)."""
    occ = occasion_search_base(occasion)
    roles = roles if roles is not None else DEFAULT_ROLES
    hobbies = hobbies if hobbies is not None else DEFAULT_HOBBIES
    c = []

    # occasion base + occasion x role/career (these embed the occasion, so they
    # are the real niche keywords — head slots for single-word occasions)
    c += [("occasion", f"{occ} gift"), ("occasion", f"{occ} shirt"),
          ("occasion", f"funny {occ} shirt"), ("occasion", f"cute {occ} shirt"),
          ("occasion", f"personalized {occ} shirt")]
    for r in roles:
        c += [("occasion", f"{occ} {r}"), ("occasion", f"{occ} {r} shirt")]
    for job in ("nurse", "teacher"):
        c += [("occasion", f"{occ} {job}"), ("occasion", f"{occ} {job} shirt")]

    # age
    for a in (ages or []):
        c += [("age", f"{a}th {occ}"), ("age", f"{a}th {occ} gift"),
              ("age", f"{a}th {occ} shirt")]
        if roles:
            c.append(("age", f"{a}th {occ} gift for {roles[0]}"))

    # cohort
    if year:
        c += [("cohort", f"senior {year}"), ("cohort", f"class of {year}"),
              ("cohort", f"graduate {year} gift"), ("cohort", f"class of {year} shirt")]

    # formula
    for r in roles:
        c += [("formula", f"promoted to {r}"), ("formula", f"new {r} gift")]

    # family_role (incl. occasion-independent head/mid so the block stays full
    # even for long, multi-word occasions like "dia de los muertos")
    for r in roles:
        c += [("family_role", f"{r} gift"), ("family_role", f"{r} shirt"),
              ("family_role", f"{r} {occ} shirt"), ("family_role", f"best {r} ever"),
              ("family_role", f"{r} life shirt")]

    # occupational (SOP: only teacher survives)
    c += [("occupational", f"teacher {occ} shirt"), ("occupational", f"{occ} teacher gift")]

    # hobby / identity
    for h in hobbies:
        c.append(("hobby", f"{h} lover gift"))

    # long-tail fillers (work for any occasion, not just age-based ones)
    for r in roles:
        c.append(("family_role", f"{occ} gift for {r}"))        # e.g. "graduation gift for mom"
    for h in hobbies:
        c.append(("hobby", f"{occ} gift for {h} lover"))        # e.g. "graduation gift for book lover"
    if year:
        c.append(("cohort", f"class of {year} gift shirt"))

    return c


# --------------------------------------------------------------------------
# Composition: enforce 5 head / 12 mid / 3 long-tail, apply pre-filters
# --------------------------------------------------------------------------
def compose_block(candidates, occasion=None, want=(5, 12, 3)):
    """Assemble a 5/12/3 block from (axis, keyword) candidates.

    Keywords that embed the occasion win their slots first (so holiday blocks are
    occasion-specific, not generic role fillers), then by axis priority.

    Returns (block, chosen_by_type, shortfall): block is the ordered list of up
    to 20 keywords; shortfall maps type -> missing count when a pool is short.
    """
    occ = occasion_search_base(occasion)
    pools = {"head": [], "mid": [], "long_tail": []}
    seen = set()
    for axis, kw in candidates:
        k = (kw or "").strip()
        low = k.lower()
        if not k or low in seen or _blocked(k):
            continue
        seen.add(low)
        embeds = 0 if (occ and occ in low) else 1   # occasion-embedding wins
        pools[keyword_type(k)].append((embeds, _AXIS_RANK.get(axis, 99), axis, k))

    for t in pools:
        pools[t].sort(key=lambda x: (x[0], x[1], x[3]))

    targets = {"head": want[0], "mid": want[1], "long_tail": want[2]}
    chosen = {t: pools[t][:n] for t, n in targets.items()}
    block = [k for t in ("head", "mid", "long_tail") for (_, _, _, k) in chosen[t]]
    shortfall = {t: targets[t] - len(chosen[t]) for t in targets
                 if len(chosen[t]) < targets[t]}
    return block, chosen, shortfall


def render_block(block, chosen, shortfall):
    lines = ["Keyword block (5 head / 12 mid / 3 long-tail):"]
    for t, label in (("head", "HEAD (2 words)"), ("mid", "MID (3 words)"),
                     ("long_tail", "LONG-TAIL (4+ words)")):
        for _, _, axis, k in chosen[t]:
            lines.append(f"  [{label.split()[0].lower():<9}|{axis:<12}] {k}")
    lines.append("")
    lines.append(f"eRank bulk ({len(block)} keywords, comma-separated):")
    lines.append(", ".join(block))
    if shortfall:
        miss = ", ".join(f"{v} {t}" for t, v in shortfall.items())
        lines.append(f"\n⚠ short by: {miss} — add candidates in those types.")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Full sweep: ALL candidates (no 5/12/3 cap), for exhaustive eRank research
# --------------------------------------------------------------------------
def compose_all(candidates, occasion=None):
    """Dedup + pre-filter EVERY candidate (no 5/12/3 cap) and return them ordered
    by priority so the first eRank groups carry the most promising keywords.

    Priority = occasion-embedding first (holiday-specific before generic), then
    axis rank, then head/mid/long-tail, then alphabetical. Returns an ordered
    list of (type, axis, keyword)."""
    occ = occasion_search_base(occasion)
    seen = set()
    scored = []
    for axis, kw in candidates:
        k = (kw or "").strip()
        low = k.lower()
        if not k or low in seen or _blocked(k):
            continue
        seen.add(low)
        embeds = 0 if (occ and occ in low) else 1
        t = keyword_type(k)
        scored.append((embeds, _TYPE_RANK[t], _AXIS_RANK.get(axis, 99), k, t, axis))
    # occasion-embedding first, then head/mid/long-tail, then axis, then alpha
    scored.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    return [(t, axis, k) for (_, _, _, k, t, axis) in scored]


def render_all(rows, batch_size=20):
    """Render the full candidate list (priority-ordered) followed by the same
    keywords chunked into comma-separated groups of `batch_size` for eRank."""
    lines = [f"All {len(rows)} keyword candidates (priority-ordered — best first):"]
    for i, (t, axis, k) in enumerate(rows, 1):
        lines.append(f"  {i:>2}. [{t:<9}|{axis:<12}] {k}")

    kws = [k for _, _, k in rows]
    n = (len(kws) + batch_size - 1) // batch_size
    lines.append(f"\neRank — {len(kws)} keywords in {n} group(s) of {batch_size} "
                 f"(run one group per day, in order; ~100/day limit):")
    for gi in range(n):
        g = kws[gi * batch_size:(gi + 1) * batch_size]
        lines.append(f"\nGroup {gi + 1} ({len(g)}):\n{', '.join(g)}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Strands TOOLS
# --------------------------------------------------------------------------
@tool
def build_keyword_block(occasion: str, year: int = None, ages: list = None) -> str:
    """Build the 20-keyword eRank block for an event-type occasion, by SOP axes
    (5 head / 12 mid / 3 long-tail), pre-filtered and comma-separated.

    Args:
        occasion: the base occasion/life-event, e.g. 'birthday', 'graduation',
            'retirement', 'anniversary'. This is the SEARCH term base — not the
            cross-niche (which is for design/tags).
        year: cohort year for 'class of {year}' / 'senior {year}' (optional).
        ages: milestone ages for age keywords, e.g. [40,50,60] (optional; if the
            occasion is 'birthday' and omitted, common milestones are used).
    """
    occ = (occasion or "").strip().lower()
    if not occ:
        return "Provide an occasion (e.g. 'birthday')."
    if ages is None and occ == "birthday":
        ages = MILESTONE_AGES
    candidates = generate_candidates(occ, year=year, ages=ages)
    block, chosen, shortfall = compose_block(candidates, occasion=occ)
    return render_block(block, chosen, shortfall)


@tool
def compose_keyword_block(keywords: list) -> str:
    """Enforce the SOP 5/12/3 composition and pre-filters on a list of candidate
    keywords you generated. Use after producing keyword ideas along the axes.

    Args:
        keywords: candidate keyword phrases (any number). They are classified by
            word count into head/mid/long-tail and filtered against trademarks.
    """
    candidates = [("other", k) for k in (keywords or [])]
    block, chosen, shortfall = compose_block(candidates)
    if not block:
        return "No valid keywords after filtering."
    return render_block(block, chosen, shortfall)


# --------------------------------------------------------------------------
# Manual test: python -m tools.keyword_gen
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print(build_keyword_block("birthday", year=2027, ages=[40, 50, 60, 70]))
    print("\n" + "=" * 60 + "\n")
    print(build_keyword_block("graduation", year=2027))
