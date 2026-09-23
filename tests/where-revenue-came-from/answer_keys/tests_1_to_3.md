# Where Revenue Came From: test answer key

Rules used for every number below. The skill must match them.
- Only Closed Won and Closed Lost count. Open stages are excluded.
- Existing business / upgrades are excluded from source analysis and reported separately. Blank deal type is treated as new business and flagged.
- Win rate = won deals / closed deals, by count. Sources under 10 deals show counts, not a rate.
- Median days to close uses won deals only, create date to close date.
- Blank source stays blank and is reported as (No source). Never reassigned.

## Test 1: HubSpot, clean

New business deals analyzed: 210. Won: 58. Revenue won: $1,319,500. Overall win rate: 28%.
Renewal / existing business excluded from source analysis: 24 deals, $221,750 won.

| Source | Deals | Won | Win rate | Revenue won | Share | Median days (won) | Avg won deal |
|---|---|---|---|---|---|---|---|
| Referrals | 34 | 17 | 50% | $498,000 | 37.7% | 49 | $29,294 |
| Organic Search | 45 | 13 | 29% | $234,250 | 17.8% | 76 | $18,019 |
| Offline Sources | 11 | 6 | 55% | $185,000 | 14.0% | 40 | $30,833 |
| Direct Traffic | 19 | 5 | 26% | $103,250 | 7.8% | 58 | $20,650 |
| Email Marketing | 21 | 5 | 24% | $98,500 | 7.5% | 73 | $19,700 |
| Paid Search | 27 | 5 | 19% | $80,750 | 6.1% | 92 | $16,150 |
| Other Campaigns | 6 | 3 | n<10, show count | $66,250 | 5.0% | 84 | $22,083 |
| Paid Social | 47 | 4 | 9% | $53,500 | 4.1% | 115.5 | $13,375 |

Story the skill should find: Referrals leads revenue at the best win rate. Paid Social is the busiest source and closes the least. Other Campaigns is too small for a rate.

## Test 2: Salesforce, clean

New business deals analyzed: 169. Won: 49. Revenue won: $1,249,250. Overall win rate: 29%.
Renewal / existing business excluded from source analysis: 11 deals, $57,000 won.

| Source | Deals | Won | Win rate | Revenue won | Share | Median days (won) | Avg won deal |
|---|---|---|---|---|---|---|---|
| Partner Referral | 34 | 16 | 47% | $450,750 | 36.1% | 48 | $28,172 |
| Trade Show | 17 | 6 | 35% | $336,750 | 27.0% | 136.5 | $56,125 |
| Web | 47 | 11 | 23% | $178,000 | 14.2% | 76 | $16,182 |
| Employee Referral | 12 | 7 | 58% | $154,750 | 12.4% | 46 | $22,107 |
| Phone Inquiry | 7 | 4 | n<10, show count | $78,500 | 6.3% | 27.5 | $19,625 |
| Advertisement | 40 | 4 | 10% | $43,250 | 3.5% | 143 | $10,812 |
| Purchased List | 12 | 1 | 8% | $7,250 | 0.6% | 102 | $7,250 |

Note: since v1.1 the skill reports Trade Show as Events, with Trade show in the channel detail. Numbers are unchanged.

Story the skill should find: Trade Show has the largest deals and the slowest cycle. Advertisement and Purchased List burn volume. Phone Inquiry is too small for a rate.

## Test 3: HubSpot, messy

Planted problems. RevOps readout must catch every one.

| Problem | Count |
|---|---|
| Rows in file | 182 |
| Exact duplicate rows | 6 |
| Same deal under a second Record ID | 4 |
| Open deals (not closed) | 12 |
| Blank deal type | 8 |
| Source label variants (non-standard spelling) | 14 |
| Blank source | 42 |
| Amount stored as text with $ or commas | 15 |
| Blank amount | 6 |
| Zero amount | 4 |
| Dates in a second format (M/D/YY) | 40 |
| Closed deal with no close date | 4 |
| Close date before create date | 5 |

After cleaning: duplicates removed, open deals removed, labels normalized, blank source kept as (No source), blank and zero amounts count as $0 revenue and are flagged, bad dates excluded from cycle time only.

## Test 3 results after cleaning

New business deals analyzed: 136. Won: 37. Revenue won: $827,500. Overall win rate: 27%.
Renewal / existing business excluded from source analysis: 24 deals, $193,750 won.

| Source | Deals | Won | Win rate | Revenue won | Share | Median days (won) | Avg won deal |
|---|---|---|---|---|---|---|---|
| (No source) | 36 | 11 | 31% | $302,500 | 36.6% | 60 | $27,500 |
| Referrals | 24 | 10 | 42% | $231,250 | 27.9% | 45 | $23,125 |
| Offline Sources | 23 | 7 | 30% | $125,250 | 15.1% | 73 | $17,893 |
| Organic Search | 21 | 6 | 29% | $104,750 | 12.7% | 67.5 | $17,458 |
| Paid Social | 23 | 2 | 9% | $40,500 | 4.9% | 88 | $20,250 |
| Direct Traffic | 9 | 1 | n<10, show count | $23,250 | 2.8% | 45 | $23,250 |

Story the skill should find: the headline is data quality. The biggest revenue line is (No source), 37% of revenue on 26% of deals. Offline Sources is large enough to hide real channels too. Referrals still leads. Paid Social still closes the least. Any confident budget call from this file must carry that warning.
