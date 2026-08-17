"""Phase A probe for the EverBee Research Open API.

Standalone diagnostic — NOT part of the pipeline. Run it once after creating your
app in the EverBee Dev Portal to answer three questions before we wire anything:

  1. Do the credentials work as-is, or does the API require an approved app?
     (200 = works now, 401 = needs approval / bad creds.)
  2. What are the real scales of `vol`, `competition`, `score`?
  3. Does the EXACT keyword we ask for come back in `results`, or only related
     suggestions? (Decides how everbee_tools.py must match the keyword.)

Usage (from the pod-agents/ folder):
    ./venv/bin/python -m tools.everbee_probe
    ./venv/bin/python -m tools.everbee_probe "halloween nurse mom"

Reads EVERBEE_CLIENT_ID / EVERBEE_CLIENT_SECRET from .env (never hard-code them).
"""

import json
import sys
import urllib.parse
import urllib.request
import urllib.error

from dotenv import dotenv_values

BASE_URL = "https://research-open-api.everbee.com"
CONFIG = dotenv_values(".env")


def fetch_keyword(keyword: str) -> None:
    client_id = CONFIG.get("EVERBEE_CLIENT_ID")
    client_secret = CONFIG.get("EVERBEE_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit(
            "Missing EVERBEE_CLIENT_ID / EVERBEE_CLIENT_SECRET in .env.\n"
            "Add them (from the EverBee Dev Portal app) and re-run."
        )

    url = f"{BASE_URL}/api/v1/keywords/{urllib.parse.quote(keyword)}?per_page=20"
    req = urllib.request.Request(
        url,
        headers={"client_id": client_id, "client_secret": client_secret},
    )

    print(f"GET {url}\n")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            headers = dict(resp.headers)
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} {e.reason}")
        print("Body:", e.read().decode("utf-8", "replace")[:500])
        if e.code == 401:
            print("\n-> 401 = credentials rejected or app not yet approved.")
        return

    # Rate-limit headers tell us the real quota and prove auth is active.
    print(f"HTTP {status}")
    for h in sorted(headers):
        if h.lower().startswith(("x-limit", "x-remaining", "retry-after")):
            print(f"  {h}: {headers[h]}")

    results = body.get("results", [])
    print(f"\nreturned {len(results)} keyword rows "
          f"(total_count={body.get('total_count')})\n")

    exact = None
    for row in results[:20]:
        kw = row.get("keyword", "")
        vol = row.get("vol")
        comp = row.get("competition")
        score = row.get("score")
        # R = vol / competition is the SOP ratio; competition may be 0/None.
        ratio = round(vol / comp, 2) if vol and comp else None
        print(f"  {kw!r:40} vol={vol:<8} comp={comp:<6} score={score:<10} R={ratio}")
        if kw.strip().lower() == keyword.strip().lower():
            exact = row

    print()
    if exact:
        print(f"EXACT MATCH found for {keyword!r} -> per-keyword lookup is reliable.")
    else:
        print(f"NO exact match for {keyword!r} in results -> we get related "
              f"suggestions only; everbee_tools.py must handle exact matching.")


if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "halloween nurse mom"
    fetch_keyword(kw)
