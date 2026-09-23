#!/usr/bin/env python3
"""Revenue by Channel: deal export analysis.

Usage: python analyze.py deals.csv [--json out.json] [--won "Stage A,Stage B"] [--lost "Stage C"]

Reads a HubSpot or Salesforce deal/opportunity export and reports revenue,
win rate and sales cycle by source, plus every data quality problem found.
Standard library only. Numbers are deterministic; the readout is written from them.
"""
import csv, json, re, sys, statistics
from collections import Counter, defaultdict
from datetime import datetime

# ---------- column detection ----------
COLS = {
    "id":      ["record id", "deal id", "opportunity id", "id"],
    "name":    ["deal name", "opportunity name", "name"],
    "stage":   ["deal stage", "stage", "stage name", "status"],
    "amount":  ["amount", "deal amount", "amount (company currency)", "total contract value", "acv"],
    "created": ["create date", "created date", "createdate", "date created"],
    "closed":  ["close date", "closed date", "closedate", "date closed"],
    "type":    ["deal type", "type", "opportunity type"],
    "source":  ["original source type", "original source", "original traffic source", "lead source",
                "source", "opportunity source", "deal source", "hs_analytics_source"],
    "owner":   ["deal owner", "opportunity owner", "owner"],
    "campaign":["campaign", "campaign name", "primary campaign source", "utm_campaign", "utm campaign",
                "original campaign"],
    # HubSpot drill-downs. Where the campaign name sits depends on the source type:
    # Paid Search and Other Campaigns keep utm_campaign in drill-down 1 (drill-down 2 is the search term),
    # Paid Social keeps it in drill-down 2, Offline Sources keeps the import or integration name in drill-down 2.
    "dd1":     ["original traffic source drill-down 1", "original source drill-down 1"],
    "dd2":     ["original traffic source drill-down 2", "original source drill-down 2"],
}
CAMPAIGN_ORDER = {
    "Paid Search": ["campaign", "dd1"],
    "Paid Social": ["campaign", "dd2"],
    "Other Campaigns": ["campaign", "dd1", "dd2"],
    "Offline Sources": ["campaign", "dd2", "dd1"],
}
DEFAULT_ORDER = ["campaign", "dd1", "dd2"]
REQUIRED = ["stage", "amount", "created", "closed", "source"]

def detect(headers):
    low = {h.strip().lower(): h for h in headers}
    found = {}
    for key, options in COLS.items():
        for o in options:
            if o in low:
                found[key] = low[o]; break
    return found

# ---------- value rules ----------
WON = {"closed won", "won", "closedwon"}
LOST = {"closed lost", "lost", "closedlost"}
EXISTING = {"existing business", "existing customer - upgrade", "existing customer - replacement",
            "existing customer - downgrade", "renewal", "upsell", "existing customer", "expansion"}

SOURCE_SYNONYMS = {
    "referral": "Referrals", "referrals": "Referrals", "word of mouth": "Referrals",
    "customer referral": "Referrals",
    "linkedin": "Paid Social", "linkedin ads": "Paid Social", "paid social": "Paid Social",
    "facebook ads": "Paid Social", "meta ads": "Paid Social",
    "seo": "Organic Search", "organic search": "Organic Search", "organic": "Organic Search",
    "google ads": "Paid Search", "ppc": "Paid Search", "paid search": "Paid Search",
    "email": "Email Marketing", "email marketing": "Email Marketing",
    "direct": "Direct Traffic", "direct traffic": "Direct Traffic",
    "offline": "Offline Sources", "offline sources": "Offline Sources",
    "organic social": "Organic Social", "social media": "Organic Social",
    "other campaigns": "Other Campaigns",
    "trade show": "Events", "tradeshow": "Events", "event": "Events", "events": "Events",
    "webinar": "Events", "conference": "Events", "seminar": "Events", "sponsorship": "Events",
}

# ---------- channel detail (campaign buckets) ----------
# First matching rule wins. Matched against the campaign name, then the raw source label.
SUB_RULES = {
    "Paid Search": [
        (r"non[-_ ]?brand|generic|\bnb\b|unbranded", "Non-brand"),
        (r"conquest|competitor|\bcomp\b|\bvs\b|versus|alternative", "Conquesting"),
        (r"retarget|remarket|rlsa", "Retargeting"),
        (r"brand", "Branded"),
    ],
    "Paid Social": [
        (r"retarget|remarket", "Retargeting"),
        (r"lead[-_ ]?gen|leadgen|\blgf\b|lead[-_ ]?form|\bform\b|conversion|demo", "Lead gen"),
        (r"content|thought|article|video|promo|guide|report|newsletter", "Content promotion"),
        (r"brand|awareness|reach|\baw\b", "Brand awareness"),
    ],
    "Events": [
        (r"webinar|virtual|online[-_ ]?event", "Webinar"),
        (r"sponsor", "Sponsorship"),
        (r"trade[-_ ]?show|expo|booth|conference|summit|convention", "Trade show"),
        (r"hosted|dinner|roundtable|meetup|workshop|seminar|breakfast|lunch", "Hosted event"),
    ],
}
EVENT_RX = re.compile(r"webinar|virtual[-_ ]?event|sponsor|trade[-_ ]?show|expo|booth|conference|summit|roundtable|dinner|meetup|workshop|seminar|\bevent", re.I)
UNCLASSIFIED = "Unclassified"

def classify(family, campaign, raw):
    # Source labels only describe Events well ("Trade Show", "Webinar"). Paid channels need a campaign name.
    for text in ((campaign, raw) if family == "Events" else (campaign,)):
        t = (text or "").lower()
        if not t:
            continue
        for rx, label in SUB_RULES.get(family, []):
            if re.search(rx, t):
                return label
    return UNCLASSIFIED
NO_SOURCE = "(No source)"
# Labels that usually mean "we don't know" rather than a real channel
VAGUE = {"offline sources", "other", "direct traffic", "unknown", "none", "n/a", "other campaigns"}

DATE_FORMATS = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y",
                "%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M %p", "%d-%b-%Y", "%b %d, %Y", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]

def parse_date(s):
    s = (s or "").strip()
    if not s:
        return None, None
    for i, f in enumerate(DATE_FORMATS):
        try:
            return datetime.strptime(s, f), f
        except ValueError:
            pass
    return None, "unparseable"

def parse_amount(s):
    s = (s or "").strip()
    if s == "":
        return None, "blank"
    txt = bool(re.search(r"[\$,€£]", s))
    try:
        return float(re.sub(r"[^\d.\-]", "", s)), ("text" if txt else "ok")
    except ValueError:
        return None, "unparseable"

def norm_source(raw):
    r = (raw or "").strip()
    if r == "":
        return NO_SOURCE, False
    key = r.lower()
    canon = SOURCE_SYNONYMS.get(key)
    if canon is None:
        # title-case fallback so "web" and "Web" merge
        canon = r if r != r.lower() else r.title()
    return canon, canon != r

# ---------- analysis ----------
def analyze(path, extra_won=(), extra_lost=()):
    WON.update(x.strip().lower() for x in extra_won if x.strip())
    LOST.update(x.strip().lower() for x in extra_lost if x.strip())
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)

    cols = detect(headers)
    missing = [k for k in REQUIRED if k not in cols]
    result = {"file": path, "columns_used": cols, "missing_required": missing, "rows_in_file": len(rows)}
    if missing:
        result["stop"] = ("Missing required columns: " + ", ".join(missing) +
                          ". Re-export with deal stage, amount, create date, close date and original/lead source.")
        return result

    q = Counter()          # data quality counts
    label_map = defaultdict(Counter)

    # exact duplicates
    seen, uniq = set(), []
    for r in rows:
        k = tuple((h, r.get(h, "")) for h in headers)
        if k in seen:
            q["Exact duplicate rows"] += 1; continue
        seen.add(k); uniq.append(r)
    # same deal, second record id
    seen2, uniq2 = set(), []
    for r in uniq:
        k = (r.get(cols.get("name", ""), ""), r[cols["amount"]], r[cols["created"]], r[cols["stage"]])
        if cols.get("name") and k in seen2:
            q["Same deal under a second record ID"] += 1; continue
        seen2.add(k); uniq2.append(r)

    has_campaign = any(cols.get(k) for k in ("campaign", "dd1", "dd2"))
    deals, renewals = [], []
    stages_seen = Counter()
    for r in uniq2:
        st = r[cols["stage"]].strip().lower()
        stages_seen[r[cols["stage"]].strip()] += 1
        if st in WON: won = True
        elif st in LOST: won = False
        else:
            q["Open or unrecognized stage (excluded)"] += 1; continue

        dtype = r.get(cols.get("type", ""), "").strip() if cols.get("type") else ""
        if cols.get("type") and dtype == "":
            q["Blank deal type (treated as new business)"] += 1

        src, changed = norm_source(r[cols["source"]])
        if src == NO_SOURCE: q["Blank source"] += 1
        elif changed: q["Source label variants merged"] += 1
        label_map[src][r[cols["source"]].strip() or "(blank)"] += 1

        amt, astat = parse_amount(r[cols["amount"]])
        if astat == "blank": q["Blank amount (counted as $0)"] += 1
        elif astat == "text": q["Amount stored as text with $ or commas"] += 1
        elif astat == "unparseable": q["Unreadable amount (counted as $0)"] += 1
        amt = amt or 0.0
        if amt == 0 and astat in ("ok", "text"): q["Zero amount"] += 1

        c, cf = parse_date(r[cols["created"]]); x, xf = parse_date(r[cols["closed"]])
        fmts = {f for f in (cf, xf) if f and f != "unparseable"}
        for f in fmts: q["_fmt_" + f] += 1
        if cf == "unparseable" or xf == "unparseable": q["Unreadable date"] += 1
        if x is None and xf is None: q["Closed deal with no close date"] += 1
        cycle = None
        if c and x:
            if x < c: q["Close date before create date"] += 1
            else: cycle = (x - c).days

        cands = [r.get(cols[k], "").strip() for k in CAMPAIGN_ORDER.get(src, DEFAULT_ORDER) if cols.get(k)]
        cands = [c for c in cands if c]
        if src in ("Other Campaigns", "Offline Sources"):
            ev = next((c for c in cands if EVENT_RX.search(c)), None)
            if ev:
                src = "Events"; cands = [ev] + [c for c in cands if c != ev]
                q["Reclassified to Events from campaign name"] += 1
        sub = None
        if src in SUB_RULES:
            sub = UNCLASSIFIED
            for c in cands or [""]:
                sub = classify(src, c, r[cols["source"]])
                if sub != UNCLASSIFIED: break
            if has_campaign and not cands and sub == UNCLASSIFIED: q["Paid or event deal with no campaign name"] += 1
            elif cands and sub == UNCLASSIFIED: q["Campaign name not classified"] += 1
        d = dict(source=src, won=won, amount=amt, cycle=cycle, close=x, sub=sub)
        if dtype.lower() in EXISTING: renewals.append(d)
        else: deals.append(d)

    fmts = sorted(k[5:] for k in q if k.startswith("_fmt_"))
    for k in [k for k in q if k.startswith("_fmt_")]: del q[k]
    if len(fmts) > 1: q["Mixed date formats in file"] = len(fmts)

    # by source
    by = defaultdict(list)
    for d in deals: by[d["source"]].append(d)
    total_rev = sum(d["amount"] for d in deals if d["won"])
    def row(s, ds, family=None):
        won = [d for d in ds if d["won"]]
        rev = sum(d["amount"] for d in won)
        cyc = [d["cycle"] for d in won if d["cycle"] is not None]
        n = len(ds)
        return {
            "source": s, "family": family or s, "deals": n, "won": len(won),
            "win_rate": round(len(won) / n * 100) if n >= 10 else None,
            "small_sample": n < 10,
            "revenue_won": round(rev, 2),
            "share_of_revenue": round(rev / total_rev * 100, 1) if total_rev else 0,
            "share_of_deals": round(n / len(deals) * 100, 1) if deals else 0,
            "median_days_to_close_won": statistics.median(cyc) if cyc else None,
            "avg_won_deal": round(rev / len(won)) if won else None,
            "vague_label": s.lower() in VAGUE,
        }
    table = [row(s, ds) for s, ds in by.items()]
    table.sort(key=lambda t: -t["revenue_won"])
    # channel detail: break a family out only when at least one deal was classified
    detail, solver_rows = [], []
    for t in table:
        ds = by[t["source"]]
        subs = defaultdict(list)
        for d in ds:
            if d["sub"]: subs[d["sub"]].append(d)
        if subs and any(k != UNCLASSIFIED for k in subs):
            rows = sorted((row(f"{t['source']}: {k}", v, t["source"]) for k, v in subs.items()),
                          key=lambda r: -r["revenue_won"])
            for r_ in rows: r_["sub"] = r_["source"].split(": ", 1)[1]
            detail += rows; solver_rows += rows
        else:
            solver_rows.append(t)
    if not deals and not renewals:
        result["stop"] = ("No stages recognized as won or lost. Stages found: " + ", ".join(stages_seen) +
                          ". Rerun with --won and --lost naming the stages.")
        result["stages_seen"] = dict(stages_seen)
        return result

    closes = [d["close"] for d in deals if d["close"]]
    months = max(1.0, round(((max(closes) - min(closes)).days / 30.44), 1)) if closes else 1.0
    won_all = [d for d in deals if d["won"]]
    avg_won_all = round(sum(d["amount"] for d in won_all) / len(won_all)) if won_all else 0
    no_src = next((t for t in table if t["source"] == NO_SOURCE), None)
    vague_rev = sum(t["revenue_won"] for t in table if t["vague_label"])
    result.update({
        "date_range": [min(closes).strftime("%Y-%m-%d"), max(closes).strftime("%Y-%m-%d")] if closes else None,
        "new_business": {
            "deals": len(deals), "won": sum(d["won"] for d in deals),
            "lost": sum(not d["won"] for d in deals),
            "revenue_won": round(total_rev, 2),
            "win_rate": round(sum(d["won"] for d in deals) / len(deals) * 100) if deals else None,
        },
        "months_covered": months,
        "avg_won_deal_all": avg_won_all,
        "renewals_excluded": {"deals": len(renewals),
                              "revenue_won": round(sum(d["amount"] for d in renewals if d["won"]), 2)},
        "has_lost_deals": any(not d["won"] for d in deals),
        "by_source": table,
        "channel_detail": detail,
        "solver_rows": solver_rows,
        "campaign_column": ", ".join(cols[k] for k in ("campaign", "dd1", "dd2") if cols.get(k)) or None,
        "no_source_share_of_revenue": no_src["share_of_revenue"] if no_src else 0,
        "vague_source_share_of_revenue": round(vague_rev / total_rev * 100, 1) if total_rev else 0,
        "data_quality": dict(q),
        "label_merges": {k: dict(v) for k, v in label_map.items() if len(v) > 1 or list(v)[0] != k},
        "stages_seen": dict(stages_seen),
    })
    return result

def to_markdown(r):
    if r.get("stop"):
        return "STOP: " + r["stop"]
    nb = r["new_business"]
    out = [f"File: {r['file']}  |  Closed deals {r['date_range'][0]} to {r['date_range'][1]}" if r["date_range"] else f"File: {r['file']}",
           f"New business: {nb['deals']} closed deals, {nb['won']} won, ${nb['revenue_won']:,.0f} revenue, {nb['win_rate']}% win rate.",
           f"Renewals / existing business excluded: {r['renewals_excluded']['deals']} deals, ${r['renewals_excluded']['revenue_won']:,.0f} won.",
           f"Revenue with no source: {r['no_source_share_of_revenue']}%. Revenue on vague labels (Offline, Direct, Other): {r['vague_source_share_of_revenue']}%.",
           "", "| Source | Deals | Won | Win rate | Revenue won | Share of revenue | Median days (won) | Avg won deal |",
           "|---|---|---|---|---|---|---|---|"]
    for t in r["by_source"]:
        wr = f"{t['win_rate']}%" if t["win_rate"] is not None else f"{t['won']} of {t['deals']} (too few for a rate)"
        md = "" if t["median_days_to_close_won"] is None else f"{t['median_days_to_close_won']:g}"
        avg = "" if t["avg_won_deal"] is None else f"${t['avg_won_deal']:,.0f}"
        out.append(f"| {t['source']} | {t['deals']} | {t['won']} | {wr} | ${t['revenue_won']:,.0f} | {t['share_of_revenue']}% | {md} | {avg} |")
    if r.get("channel_detail"):
        out += ["", f"Channel detail (campaign column: {r.get('campaign_column') or 'none, from source labels'})", "",
                "| Channel | Deals | Won | Win rate | Revenue won | Share of revenue | Median days (won) | Avg won deal |",
                "|---|---|---|---|---|---|---|---|"]
        for t in r["channel_detail"]:
            wr = f"{t['win_rate']}%" if t["win_rate"] is not None else f"{t['won']} of {t['deals']} (too few for a rate)"
            md = "" if t["median_days_to_close_won"] is None else f"{t['median_days_to_close_won']:g}"
            avg = "" if t["avg_won_deal"] is None else f"${t['avg_won_deal']:,.0f}"
            out.append(f"| {t['source']} | {t['deals']} | {t['won']} | {wr} | ${t['revenue_won']:,.0f} | {t['share_of_revenue']}% | {md} | {avg} |")
    if not r["has_lost_deals"]:
        out.append("\nNo lost deals in the file. Win rates are not real. Re-export with Closed Lost included.")
    if r["data_quality"]:
        out += ["", "| Data quality problem | Count |", "|---|---|"]
        for k, v in sorted(r["data_quality"].items(), key=lambda kv: -kv[1]):
            out.append(f"| {k} | {v} |")
    if r["label_merges"]:
        out += ["", "Source labels merged (check these):"]
        for k, v in r["label_merges"].items():
            out.append(f"- {k} <- " + ", ".join(f'"{a}" x{b}' for a, b in v.items()))
    return "\n".join(out)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    def opt(name):
        return sys.argv[sys.argv.index(name) + 1].split(",") if name in sys.argv else []
    res = analyze(sys.argv[1], opt("--won"), opt("--lost"))
    if "--json" in sys.argv:
        p = sys.argv[sys.argv.index("--json") + 1]
        with open(p, "w") as f: json.dump(res, f, indent=2, default=str)
    print(to_markdown(res))
