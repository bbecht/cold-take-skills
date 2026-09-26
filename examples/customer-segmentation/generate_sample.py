#!/usr/bin/env python3
"""Generate the synthetic B2B sample data for Customer Segmentation.

Usage (repo root):  python examples/customer-segmentation/generate_sample.py

Every account, deal, rep and product here is invented. The file layout follows the
structure of Maven Analytics' CRM Sales Opportunities dataset (accounts, products,
sales teams, sales pipeline). No rows come from that dataset. MIT licensed with the repo.

The patterns below are planted on purpose, so the models have something real to find.
They are the answer key: a working model must recover them.

  Sector       Software and Healthcare win most. Retail and Education win least.
  Size         Mid-size accounts (roughly 200 to 2,000 employees) win most. Very small
               and very large accounts win least. A curve, not a straight line.
  Subsidiary   Accounts owned by a parent company win less. The parent decides.
  Country      United States and Canada win most. Accounts outside North America win less.
  Founded      No effect at all. A pure noise attribute.
  Revenue      No direct effect. It moves with employee count, so it borrows size's signal.
  Deal value   Bigger companies buy bigger products.
  Whales       Five very large accounts, won through company-wide rollouts, carry an
               outsized share of won revenue. They do not fit the pattern.

Standard library only. Same seed, same files.
"""
import csv, math, os, random
from datetime import date, timedelta

SECTORS = {  # sector: planted effect on the log-odds of winning
    "Software": 0.9, "Healthcare": 0.6, "Financial services": 0.2, "Manufacturing": 0.0,
    "Professional services": -0.1, "Telecommunications": -0.3, "Education": -0.6, "Retail": -0.9,
}
SECTOR_MIX = {"Software": 16, "Healthcare": 13, "Financial services": 14, "Manufacturing": 15,
              "Professional services": 14, "Telecommunications": 8, "Education": 8, "Retail": 12}
COUNTRIES = {"United States": (70, 0.0), "Canada": (8, 0.0), "United Kingdom": (8, -0.5),
             "Germany": (5, -0.7), "Australia": (4, -0.7), "Brazil": (3, -0.7), "Japan": (2, -0.7)}
PARENTS = ["Northgate Holdings", "Brightwater Group", "Keystone Partners", "Halvorsen Capital",
           "Meridian Collective", "Tallis Industries"]
PRODUCTS = [("Starter", "Core", 6000), ("Growth", "Core", 18000),
            ("Scale", "Advanced", 45000), ("Enterprise", "Advanced", 110000)]
TEAMS = [("Avery Lin", "Dana Whitcomb", "East"), ("Marcus Ohl", "Dana Whitcomb", "East"),
         ("Priya Sand", "Dana Whitcomb", "East"), ("Theo Brandt", "Rafael Ionescu", "Central"),
         ("Nina Castell", "Rafael Ionescu", "Central"), ("Owen Pratt", "Rafael Ionescu", "Central"),
         ("Lena Morrow", "Keiko Vance", "West"), ("Sam Okafor", "Keiko Vance", "West"),
         ("Iris Holm", "Keiko Vance", "West")]
FIRST = ["Harbor", "Summit", "Cedar", "Northwind", "Bluestone", "Ironvale", "Lumen", "Copperline",
         "Redfield", "Silverbrook", "Oakmont", "Clearpath", "Brightline", "Granite", "Kestrel",
         "Westmark", "Halcyon", "Pinecrest", "Riverton", "Stonebridge", "Aldercroft", "Beacon",
         "Driftwood", "Fairhaven", "Glenmore", "Highpoint", "Juniper", "Larkspur", "Marlowe",
         "Nettle", "Orchard", "Quarry", "Ravenna", "Saltmarsh", "Thornbury", "Upland", "Vantage",
         "Willowby", "Yardley", "Zephyr", "Ashgrove", "Brackett", "Calder", "Dunmore", "Everly"]
SUFFIX = {"Software": ["Software", "Systems", "Labs", "Cloud", "Data"],
          "Healthcare": ["Health", "Medical", "Clinics", "Care", "Diagnostics"],
          "Financial services": ["Financial", "Capital", "Lending", "Advisors", "Insurance"],
          "Manufacturing": ["Manufacturing", "Industries", "Fabrication", "Components", "Works"],
          "Professional services": ["Consulting", "Partners", "Group", "Associates", "Advisory"],
          "Telecommunications": ["Telecom", "Networks", "Communications", "Wireless", "Fiber"],
          "Education": ["Learning", "Academy", "Education", "Institute", "Schools"],
          "Retail": ["Retail", "Outfitters", "Goods", "Market", "Stores"]}


def pick(rng, weights):
    keys = list(weights)
    return rng.choices(keys, weights=[weights[k] if not isinstance(weights[k], tuple) else weights[k][0]
                                      for k in keys])[0]


def size_effect(employees):
    """Planted sweet spot: peaks near 630 employees, falls off both ways."""
    return 0.9 - 1.1 * (math.log10(employees) - 2.8) ** 2


def product_for(rng, employees):
    if employees < 100:  return rng.choices(PRODUCTS[:2], [0.7, 0.3])[0]
    if employees < 1000: return rng.choices(PRODUCTS[1:3], [0.55, 0.45])[0]
    if employees < 5000: return rng.choices(PRODUCTS[1:4], [0.3, 0.5, 0.2])[0]
    return rng.choices(PRODUCTS[2:4], [0.6, 0.4])[0]


def generate(seed=16, n_accounts=800, n_untouched=160, start=date(2024, 10, 1), end=date(2026, 8, 31)):
    rng = random.Random(seed)
    names, accounts = set(), []
    while len(accounts) < n_accounts:
        sector = pick(rng, SECTOR_MIX)
        name = f"{rng.choice(FIRST)} {rng.choice(SUFFIX[sector])}"
        if name in names: continue
        names.add(name)
        employees = int(round(10 ** rng.uniform(1.2, 4.6)))
        revenue = round(employees * rng.uniform(0.12, 0.40), 2)  # $ millions, moves with size
        country = pick(rng, COUNTRIES)
        parent = rng.choice(PARENTS) if rng.random() < 0.22 else ""
        accounts.append({"account": name, "sector": sector, "year_established": rng.randint(1965, 2020),
                         "revenue": revenue, "employees": employees, "office_location": country,
                         "subsidiary_of": parent})

    days = (end - start).days
    deals, n = [], 0
    rng.shuffle(accounts)
    active = accounts[: n_accounts - n_untouched]
    whales, seen = [], set()  # the largest account in five different sectors
    for a in sorted(active, key=lambda a: -a["employees"]):
        if a["sector"] not in seen and len(whales) < 5:
            whales.append(a); seen.add(a["sector"])
    for a in active:
        logit = (-0.35 + SECTORS[a["sector"]] + size_effect(a["employees"])
                 + (-0.6 if a["subsidiary_of"] else 0.0) + COUNTRIES[a["office_location"]][1]
                 + rng.gauss(0, 0.35))  # the part no attribute explains
        p = 1 / (1 + math.exp(-logit))
        k = 1 + min(8, int(rng.expovariate(1 / 2.2)))
        if a in whales:
            k, p = 8, 0.8  # strategic accounts: company-wide rollouts, worked hard, won often
        for _ in range(k):
            n += 1
            agent = rng.choice(TEAMS)[0]
            prod = PRODUCTS[3] if a in whales else product_for(rng, a["employees"])
            engage = start + timedelta(days=rng.randrange(days))
            cycle = int(rng.uniform(20, 70) + (40 if prod[0] in ("Scale", "Enterprise") else 0))
            close = engage + timedelta(days=cycle)
            row = {"opportunity_id": f"OPP{n:05d}", "sales_agent": agent, "product": prod[0],
                   "account": a["account"], "deal_stage": "", "engage_date": engage.isoformat(),
                   "close_date": "", "close_value": ""}
            if close > end:
                row["deal_stage"] = "Engaging" if rng.random() < 0.7 else "Prospecting"
                if row["deal_stage"] == "Prospecting": row["engage_date"] = ""
            elif rng.random() < p:
                row.update(deal_stage="Won", close_date=close.isoformat(),
                           close_value=int(round(prod[2] * (rng.uniform(1.8, 2.6) if a in whales else rng.uniform(0.85, 1.05)), -2)))
            else:
                row.update(deal_stage="Lost", close_date=close.isoformat(), close_value=0)
            deals.append(row)
    accounts.sort(key=lambda a: a["account"])
    deals.sort(key=lambda d: d["opportunity_id"])
    return accounts, deals


def write(path, rows, fields=None):
    fields = fields or list(rows[0])
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    accounts, deals = generate()
    write(os.path.join(here, "sample_accounts.csv"), accounts)
    write(os.path.join(here, "sample_sales_pipeline.csv"), deals)
    write(os.path.join(here, "sample_products.csv"),
          [{"product": p, "series": s, "sales_price": v} for p, s, v in PRODUCTS])
    write(os.path.join(here, "sample_sales_teams.csv"),
          [{"sales_agent": a, "manager": m, "regional_office": r} for a, m, r in TEAMS])
    won = sum(1 for d in deals if d["deal_stage"] == "Won")
    lost = sum(1 for d in deals if d["deal_stage"] == "Lost")
    print(f"{len(accounts)} accounts, {len(deals)} deals: {won} won, {lost} lost, "
          f"{len(deals) - won - lost} open")


if __name__ == "__main__":
    main()
