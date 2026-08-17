"""Compare eRank vs EverBee keyword metrics — decision harness.

Goal: decide, on REAL keywords, whether we drop eRank, keep both, or go
EverBee-only. It reads the eRank Bulk exports we already have in ``csv/`` (columns:
Keywords, Avg Searches, Avg Clicks, Avg CTR, Etsy Competition, Keyword Difficulty)
and, per keyword, pairs them against EverBee's ``vol / competition / score``.

Two modes:
  --mock  (default)  Synthesize EverBee responses with the REAL response shape
                     (fields keyword/vol/competition/score/new_volume/cpc). The
                     NUMBERS ARE FAKE — this mode only proves the plumbing works
                     (CSV parse, exact-match, Spearman, table). It is NOT a verdict.
  --live             Call the real API (needs an APPROVED app + creds in .env).
                     Only this mode produces a real comparison.

Usage (from the pod-agents/ folder):
    ./venv/bin/python -m tools.everbee_compare
    ./venv/bin/python -m tools.everbee_compare --live

Four questions it answers (see the printed SUMMARY):
  1. Coverage  — of N eRank keywords, how many does EverBee return as an EXACT match?
  2. Volume    — Spearman rank-corr between eRank Avg Searches and EverBee vol.
  3. Competition — Spearman between eRank Etsy Competition and EverBee competition.
  4. KD proxy  — Spearman between eRank Keyword Difficulty and EverBee score / R.
                 (High KD = hard. If score/R rank-orders difficulty the same way,
                  we can drop the KD gate; if not, EverBee can't replace it.)
"""

import csv
import glob
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from dotenv import dotenv_values

BASE_URL = "https://research-open-api.everbee.com"
CSV_DIR = "csv"
CONFIG = dotenv_values(".env")


# --------------------------------------------------------------------------- #
# eRank CSV parsing
# --------------------------------------------------------------------------- #
def parse_num(raw):
    """eRank cells → float or None. Handles '1,403', '< 20', 'Unknown', '96%', ''."""
    if raw is None:
        return None
    s = raw.strip().replace(",", "").replace("%", "").replace("$", "")
    if s == "" or s.lower() == "unknown":
        return None
    if s.startswith("<"):
        # '< 20' — treat as its upper bound; low-volume proxy.
        s = s.lstrip("<").strip()
    try:
        return float(s)
    except ValueError:
        return None


def load_erank(csv_dir=CSV_DIR):
    """All eRank Bulk exports → {keyword: {searches, competition, kd}}. Dedups keywords."""
    rows = {}
    for path in sorted(glob.glob(os.path.join(csv_dir, "*.csv"))):
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                kw = (r.get("Keywords") or "").strip()
                if not kw:
                    continue
                rows.setdefault(kw, {
                    "searches": parse_num(r.get("Avg Searches")),
                    "competition": parse_num(r.get("Etsy Competition")),
                    "kd": parse_num(r.get("Keyword Difficulty")),
                })
    return rows


# --------------------------------------------------------------------------- #
# EverBee side — live and mock
# --------------------------------------------------------------------------- #
def everbee_live(keyword):
    """Real API. Returns the row whose `keyword` matches exactly, else None."""
    cid, secret = CONFIG.get("EVERBEE_CLIENT_ID"), CONFIG.get("EVERBEE_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit("Missing EVERBEE_CLIENT_ID / EVERBEE_CLIENT_SECRET in .env.")
    url = f"{BASE_URL}/api/v1/keywords/{urllib.parse.quote(keyword)}?per_page=20"
    req = urllib.request.Request(url, headers={"client_id": cid, "client_secret": secret})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        sys.exit(f"HTTP {e.code} on {keyword!r}: {detail}\n"
                 f"(401 'App is not approved' = still waiting on EverBee approval.)")
    target = keyword.strip().lower()
    for row in body.get("results", []):
        if (row.get("keyword") or "").strip().lower() == target:
            return row
    return None  # only related suggestions came back — no exact match


def _h(keyword, salt):
    """Deterministic pseudo-random in [0,1) from the keyword — reproducible mock."""
    d = hashlib.sha256((salt + keyword).encode()).digest()
    return int.from_bytes(d[:4], "big") / 0xFFFFFFFF


def everbee_mock(keyword, er):
    """SYNTHETIC EverBee row with the real field shape. Numbers are fake."""
    if _h(keyword, "miss") < 0.08:
        return None  # exercise the coverage metric (~8% simulated misses)
    base_vol = er["searches"] if er["searches"] else 20 + _h(keyword, "v") * 3000
    vol = int(base_vol * (0.9 + _h(keyword, "vj") * 0.5))
    base_comp = er["competition"] if er["competition"] else 500 + _h(keyword, "c") * 90000
    comp = int(base_comp * (0.8 + _h(keyword, "cj") * 0.4))
    score = round(vol / max(comp, 1) ** 0.5 * 11, 1)  # ~EverBee opportunity magnitude
    return {"keyword": keyword, "vol": vol, "competition": comp,
            "score": score, "new_volume": vol, "cpc": "0.00"}


# --------------------------------------------------------------------------- #
# Spearman rank correlation (no scipy)
# --------------------------------------------------------------------------- #
def _ranks(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1  # 1-based, tie-averaged
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(pairs):
    """pairs: iterable of (x, y). Drops None. Returns (rho or None, n_used)."""
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return None, n
    rx, ry = _ranks([p[0] for p in pairs]), _ranks([p[1] for p in pairs])
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    dx = sum((rx[i] - mx) ** 2 for i in range(n)) ** 0.5
    dy = sum((ry[i] - my) ** 2 for i in range(n)) ** 0.5
    if dx == 0 or dy == 0:
        return None, n
    return num / (dx * dy), n


def ratio(vol, comp):
    """SOP ratio R = vol / competition."""
    if not vol or not comp:
        return None
    return round(vol / comp, 3)


# --------------------------------------------------------------------------- #
def fmt(v, width, nd=0):
    if v is None:
        return "—".ljust(width)
    return (f"{v:,.{nd}f}" if isinstance(v, float) else f"{v:,}").ljust(width)


def main():
    live = "--live" in sys.argv
    mode = "LIVE (real API)" if live else "MOCK (synthetic EverBee numbers)"
    er = load_erank()
    if not er:
        sys.exit(f"No eRank CSVs found in {CSV_DIR}/.")

    print("=" * 96)
    print(f"eRank vs EverBee — keyword metric comparison   [{mode}]")
    if not live:
        print("!! MOCK MODE: EverBee numbers are FAKE. Stats below are a plumbing check, NOT a verdict.")
    print("=" * 96)
    hdr = (f"{'keyword':34} {'eR_vol':>8} {'EB_vol':>8} {'eR_comp':>9} {'EB_comp':>9} "
           f"{'eR_KD':>5} {'EB_score':>9} {'R_eR':>7} {'R_EB':>7}")
    print(hdr)
    print("-" * len(hdr))

    rows, covered = [], 0
    for kw, e in er.items():
        eb = everbee_live(kw) if live else everbee_mock(kw, e)
        if eb is None:
            print(f"{kw[:34]:34} {fmt(e['searches'],8)} {'MISS':>8}   (no exact match in EverBee)")
            rows.append((e, None))
            continue
        covered += 1
        r_er = ratio(e["searches"], e["competition"])
        r_eb = ratio(eb["vol"], eb["competition"])
        print(f"{kw[:34]:34} {fmt(e['searches'],8)} {fmt(eb['vol'],8)} "
              f"{fmt(e['competition'],9)} {fmt(eb['competition'],9)} "
              f"{fmt(e['kd'],5)} {fmt(eb['score'],9,1)} "
              f"{fmt(r_er,7,2)} {fmt(r_eb,7,2)}")
        rows.append((e, eb))

    n = len(rows)
    both = [(e, eb) for e, eb in rows if eb is not None]
    rho_vol, nv = spearman([(e["searches"], eb["vol"]) for e, eb in both])
    rho_comp, nc = spearman([(e["competition"], eb["competition"]) for e, eb in both])
    rho_kd_score, nk = spearman([(e["kd"], eb["score"]) for e, eb in both])
    rho_kd_r, nr = spearman([(e["kd"], ratio(eb["vol"], eb["competition"])) for e, eb in both])

    def line(label, rho, k):
        val = "n/a (need ≥3 pairs)" if rho is None else f"{rho:+.2f}   (n={k})"
        return f"  {label:38} {val}"

    print("\n" + "=" * 96)
    print("SUMMARY")
    print("=" * 96)
    print(f"  1. Coverage (exact match)              {covered}/{n} = {covered/n*100:.0f}%")
    print(line("2. Volume     Spearman(searches, vol)", rho_vol, nv))
    print(line("3. Competition Spearman(comp, comp)", rho_comp, nc))
    print(line("4a. KD proxy  Spearman(KD, score)", rho_kd_score, nk))
    print(line("4b. KD proxy  Spearman(KD, R=vol/comp)", rho_kd_r, nr))
    print("\n  Decision guide (pre-registered):")
    print("    EverBee-only  if coverage ≳90%  AND vol/comp ρ ≳0.7  AND a KD proxy ρ is strong.")
    print("    Keep both     if EverBee wins on automation but no KD proxy is reliable.")
    print("    Keep eRank    if coverage is poor or the numbers diverge.")
    if not live:
        print("\n  !! Reminder: MOCK numbers. Re-run with --live once the EverBee app is approved.")
    print("=" * 96)


if __name__ == "__main__":
    main()
