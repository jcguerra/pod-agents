"""
main.py — Two-stage entry point (split around the human eRank gate).
====================================================================
Stage 1:  python main.py discover
    The DIRECTOR (LLM) picks the seasonal occasion + niche; then the block of 20
    keywords is generated and staged deterministically (by SOP axes).

Then (human): run the block in eRank's Bulk Keyword Tool, export the CSV, and:
    python -m tools.import_erank <csv> "<niche>"

Stage 2:  python main.py produce "<niche>"
    Validates the imported keywords (SOP) and, if the niche survives, runs
    design -> production -> marketing -> operations, leaving a DRAFT listing.

Requirements: Ollama with qwen3.5:9b, Postgres up (docker compose up -d).
"""

import re
import sys
import time

from tracing import Tracer
from agents import director
from pipeline import build_production_graph
from tools.db_tools import generate_and_stage_keywords
from tools.analysis_tools import analyze_niche_report


# --------------------------------------------------------------------------
# Parsing the director's decision (robust to markdown/parentheticals)
# --------------------------------------------------------------------------
def _clean(val):
    val = re.sub(r"\(.*?\)", "", val)          # parentheticals
    return val.strip().strip(".").strip()


def _field(text, *labels):
    # Normalize markdown so leading **/`` and inline emphasis don't block matching.
    norm = re.sub(r"[*`_#>]", "", text)
    for label in labels:
        m = re.search(rf"(?im)^\s*[-]?\s*{label}\s*[:：]\s*(.+)$", norm)
        if m:
            return _clean(m.group(1))
    return None


def _first_option(val):
    """Pick the first choice when the director offers alternatives ('A / B', 'A or B')."""
    val = re.split(r"\s*/\s*|\bor\b|,", val, maxsplit=1)[0]
    return val.strip()


def _slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", _clean(s).lower()).strip("-")
    return s or "niche"


def _print_results(result):
    print("\nResult by node:")
    results = getattr(result, "results", None)
    if results:
        for node_id, node in results.items():
            text = str(getattr(node, "result", node)).strip()
            print(f"\n{'─' * 60}\n### {node_id} ###\n{text}")
    else:
        print(result)


# --------------------------------------------------------------------------
# Stage 1 — discovery (director decides, block generated deterministically)
# --------------------------------------------------------------------------
def discover():
    print("=" * 60)
    print("STAGE 1 — Discovery (the director picks the occasion)")
    print("=" * 60)

    goal = (
        "Choose the single best seasonal opportunity for the store right now. "
        "Pick ONE searchable occasion and one design theme, with the right lead time."
    )
    t0 = time.perf_counter()
    text = str(director.build(Tracer())(goal))
    print(f"\n{'─' * 60}\nDirector decision:\n{text}")
    print(f"{'─' * 60}\n(director took {time.perf_counter() - t0:.1f}s)")

    occasion = _field(text, "occasion")
    if not occasion:
        print("\n⚠ Could not parse an occasion from the director's output above.")
        return
    # Hard-sanitize to a short, searchable occasion: first sentence, first
    # alternative, drop quotes, cap at 2 words (the SOP occasion is a search term).
    occasion = re.split(r"[.\n;]", occasion)[0]
    occasion = re.sub(r"[\"']", "", _first_option(occasion)).strip().lower()
    occasion = " ".join(occasion.split()[:2])
    if not occasion:
        print("\n⚠ Could not parse a clean occasion.")
        return
    niche_raw = _field(text, "niche slug", "niche")
    niche = _slug(_first_option(niche_raw)) if niche_raw else _slug(occasion)
    ym = re.search(r"\b(20\d{2})\b", text)
    year = int(ym.group(1)) if ym else None

    print("\n" + "=" * 60)
    print(f"Occasion: '{occasion}'  |  Niche: '{niche}'" + (f"  |  Year: {year}" if year else ""))
    print("=" * 60)
    print(generate_and_stage_keywords(occasion, niche, year=year, seasonality="Q4"))

    print("\n" + "=" * 60)
    print("NEXT (human gate):")
    print("  1. Run EACH group of 20 above in eRank's Bulk Keyword Tool, export the CSV(s).")
    print(f'  2. python -m tools.import_erank <csv> "{niche}"   (repeat per CSV)')
    print(f'  3. python main.py produce "{niche}"')


# --------------------------------------------------------------------------
# Stage 2 — production (only if the niche survives SOP validation)
# --------------------------------------------------------------------------
def produce(niche):
    print("=" * 60)
    print(f"STAGE 2 — Production for niche: {niche}")
    print("=" * 60)
    rep = analyze_niche_report(niche)
    print(rep["report"])
    if not rep["has_metrics"]:
        print("\n→ No eRank data yet. Import the CSV first (see stage 1 instructions).")
        return
    if not rep["survives"]:
        print("\n→ Niche did NOT survive SOP validation. Generate a new keyword round.")
        return

    task = (f"Niche: {niche}. SOP-validated keywords: {', '.join(rep['fit_keywords'])}. "
            f"Create the design concept, the POD product, the listing copy, and leave "
            f"the listing as a DRAFT.")
    print("\n→ Niche survived. Running production...\n")
    t0 = time.perf_counter()
    result = build_production_graph()(task)
    print("=" * 60)
    print(f"TOTAL: {time.perf_counter() - t0:.2f}s")
    _print_results(result)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "discover"
    if cmd == "discover":
        discover()
    elif cmd == "produce":
        if len(sys.argv) < 3:
            print('Usage: python main.py produce "<niche>"')
            return
        produce(sys.argv[2])
    else:
        print('Usage: python main.py [discover | produce "<niche>"]')


if __name__ == "__main__":
    main()
