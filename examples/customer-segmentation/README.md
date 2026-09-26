# Customer Segmentation sample

Synthetic B2B data to try the skill on, and the tool it produces.

| File | What it is |
|---|---|
| `sample_accounts.csv` | 800 accounts with firmographics: sector, year established, revenue ($M), employees, office location, parent company |
| `sample_sales_pipeline.csv` | 1,790 deals: 607 won, 1,010 lost, 173 open. 160 accounts have no deals yet |
| `sample_products.csv` | 4 products and list prices |
| `sample_sales_teams.csv` | 9 reps, 3 managers, 3 regions |
| `sample_tool.html` | The interactive tool built from these files, CEO view. Download it and open it in a browser |
| `generate_sample.py` | The generator. Same seed, same files |

## Where does it come from?

Every account, deal, rep and product is invented. The layout follows the structure of Maven Analytics' CRM Sales Opportunities dataset: accounts, products, sales teams and a sales pipeline. No rows come from that dataset. Published under MIT with the rest of the repo.

## What patterns are planted?

The models have to find these. They are the answer key.

| Attribute | Planted effect |
|---|---|
| Sector | Software and Healthcare win most. Retail and Education win least |
| Employees | A sweet spot. Mid-size accounts win most. Very small and very large win least |
| Parent company | Owned by a parent: wins less. The parent decides |
| Country | United States and Canada win most. Outside North America wins less |
| Year established | No effect. Pure noise |
| Revenue | No direct effect. It moves with employees and borrows their signal |
| Deal size | Bigger companies buy bigger products |
| Five whales | Very large accounts won through company-wide rollouts. They hold an outsized share of revenue and do not fit the pattern |

Each account also gets a random push the attributes cannot explain, like any real account. That keeps the models honest: no model scores perfectly on this data, and none should.

## How do I try it?

Upload `sample_accounts.csv` and `sample_sales_pipeline.csv` to Claude with the skill installed and say: "Segment these accounts. I'm the CEO."

To rebuild the files: `python examples/customer-segmentation/generate_sample.py`
