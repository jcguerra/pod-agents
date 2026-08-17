# EverBee Dev — Call Script (Open API access)

**Goal of the call:** unblock Research Open API access for a **private/internal**
integration, and confirm a few data details before we build. Keep it tight —
lead with the one question that decides everything (Q1).

**My context (one line):** "I'm an EverBee subscriber building a private,
internal automation for my own Etsy print-on-demand shop. It's not a public app
for your store — it just reads keyword data from the Research API to speed up my
own keyword research."

---

## 30-second opener

> "Hi, thanks for the time. I created an app in the Dev Portal and generated my
> `client_id` / `client_secret`, but every request to the Research Open API
> returns **`401 — "App is not approved for Open API access"`**. My use case is
> private: an internal script for my own Etsy shop, not an app I plan to publish
> on your store. I want to understand the right way to get approved for this kind
> of private use."

---

## Q1 — THE decision question (ask first)

**"Is there an approval path for private/internal API use that does NOT require
publishing a public app — i.e. without a Production URL, demo video, and reviewer
login?"**

- If **YES** → ask: *what exactly do I submit, and how long does approval take?*
- If **NO / must go through review** → jump to Q2.

▸ Notes: _______________________________________________

---

## Q2 — If review is mandatory

**"The App Demo step requires a live Production URL, a demo video, and reviewer
login credentials. For a private backend tool that has no public UI, what do you
expect me to put there? Would a small hosted demo UI that calls the API be
enough to pass review?"**

- Goal: find out the *minimum real thing* they need to see. (We can stand up a
  small real Streamlit UI on top of pod-agents and demo it honestly.)

▸ Notes: _______________________________________________

---

## Q3 — Approval timeline

**"Roughly how long does approval take once I submit? Is there a way to expedite
for an existing paying subscriber?"**

▸ Notes: _______________________________________________

---

## Q4 — Plan-based data visibility (important for our logic)

The docs say listing fields are filtered by the user's subscription
("plan-based data visibility").

**"On my current plan, which fields does the Keywords endpoint return? Are any of
`vol`, `competition`, `score`, `new_volume`, `cpc` gated or limited? Same
question for the Listings endpoint (`est_mo_sales`, `est_mo_revenue`,
`visibility_score`, `conversion_rate`)."**

▸ My current plan is: ____________________
▸ Notes: _______________________________________________

---

## Q5 — Exact-keyword lookup

**"For `GET /api/v1/keywords/{keyword}`, does the exact keyword I request always
come back in `results`, or only related suggestions? I need reliable metrics for
a specific keyword, not just suggestions."**

▸ Notes: _______________________________________________

---

## Q6 — Keyword Difficulty

**"eRank gives a 0–100 Keyword Difficulty. Your keyword response has `vol`,
`competition`, `score`, `new_volume`, `cpc` but no difficulty field. Is there any
difficulty metric available, or is `score` the intended opportunity signal? What
exactly is `competition` — a count of competing listings?"**

▸ Notes: _______________________________________________

---

## Q7 — Rate limits (quick confirm)

**"Docs say 10 requests/second and 50,000/day per `client_id`. Is that right for
my plan, and does it change after approval?"**

▸ Notes: _______________________________________________

---

## Wrap-up asks

- "Can you send me the next steps in writing (email) so I have it on record?"
- "Who do I follow up with if I hit issues after approval?"

## My reference details (fill before the call)

- EverBee account email: **juancarlosguerra46@gmail.com**
- App name / App ID in the Dev Portal: ____________________
- Date I emailed dev@everbee.io: ____________________

---

### Decision after the call
- [ ] Private path exists → submit, wait for approval, then run `everbee_probe.py`
- [ ] Review mandatory → build the small Streamlit demo UI, then submit
- [ ] Other: ____________________
