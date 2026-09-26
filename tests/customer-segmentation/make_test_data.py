#!/usr/bin/env python3
"""Rebuild the Customer Segmentation test files. Run from the repo root.

  python tests/customer-segmentation/make_test_data.py

test1: two files, Maven-style layout, a different seed from the sample.
test2: one HubSpot-style deal export, firmographics on every row, HubSpot stage names.
test3: two files with planted data problems. See answer_keys/test3_messy.md.
test4: too small to model. The script must stop.
"""
import csv, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "examples", "customer-segmentation"))
from generate_sample import generate, write  # noqa: E402

DATA = os.path.join(HERE, "data")


def test1():
    a, d = generate(seed=20)
    write(os.path.join(DATA, "test1_accounts.csv"), a)
    write(os.path.join(DATA, "test1_deals.csv"), d)


def test2():
    a, d = generate(seed=15)
    acc = {x["account"]: x for x in a}
    stage = {"Won": "Closed Won", "Lost": "Closed Lost", "Engaging": "Contract Sent", "Prospecting": "Appointment Scheduled"}
    rows = []
    for x in d:
        c = acc[x["account"]]
        rows.append({"Record ID": x["opportunity_id"].replace("OPP", "9100"), "Deal Name": f"{x['account']} - {x['product']}",
                     "Deal Stage": stage[x["deal_stage"]], "Amount": x["close_value"] if x["deal_stage"] == "Won" else "",
                     "Create Date": x["engage_date"], "Close Date": x["close_date"],
                     "Associated Company": x["account"], "Industry": c["sector"],
                     "Number of Employees": c["employees"], "Annual Revenue": int(c["revenue"] * 1e6),
                     "Country/Region": c["office_location"], "Year Founded": c["year_established"],
                     "Parent Company": c["subsidiary_of"]})
    write(os.path.join(DATA, "test2_hubspot_single.csv"), rows)


def test3():
    rng = random.Random(3)
    a, d = generate(seed=5)
    # 1. six accounts lose their sector, four lose their employee count
    for x in a[10:16]: x["sector"] = ""
    for x in a[20:24]: x["employees"] = ""
    # 2. one account in a country nobody else is in: grouped as Other
    a[30]["office_location"] = "Iceland"
    # 3. stage labels in CRM style
    for x in d:
        x["deal_stage"] = {"Won": "Closed Won", "Lost": "Closed Lost"}.get(x["deal_stage"], x["deal_stage"])
    won = [x for x in d if x["deal_stage"] == "Closed Won"]
    # 4. text amounts on eight won deals
    for i, x in enumerate(won[:8]):
        v = int(x["close_value"])
        x["close_value"] = f"${v:,}" if i % 2 == 0 else f"{v / 1000:g}k"
    # 5. three won deals with no value
    for x in won[8:11]: x["close_value"] = ""
    # 6. five exact duplicate deals
    dups = [dict(x) for x in rng.sample(d, 5)]
    # 7. four deals naming two accounts missing from the accounts file
    ghosts = []
    for i, name in enumerate(["Phantom Freight", "Phantom Freight", "Nowhere Analytics", "Nowhere Analytics"]):
        g = dict(d[i]); g["opportunity_id"] = f"OPP9{i:04d}"; g["account"] = name; ghosts.append(g)
    # 8. two deals with no account name
    blanks = []
    for i in range(2):
        g = dict(d[50 + i]); g["opportunity_id"] = f"OPP8{i:04d}"; g["account"] = ""; blanks.append(g)
    rows = d + dups + ghosts + blanks
    rng.shuffle(rows)
    write(os.path.join(DATA, "test3_messy_accounts.csv"), a)
    write(os.path.join(DATA, "test3_messy_deals.csv"), rows)


def test4():
    a, d = generate(seed=9, n_accounts=40, n_untouched=5)
    write(os.path.join(DATA, "test4_tiny_accounts.csv"), a)
    write(os.path.join(DATA, "test4_tiny_deals.csv"), d)


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    test1(); test2(); test3(); test4()
    print("test files written to", os.path.relpath(DATA, ROOT))
