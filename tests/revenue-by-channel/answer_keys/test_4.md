## Test 4: HubSpot with campaign names in the drill-down fields

Truth comes from the generator's labels, not from the skill's classifier.
Campaign names sit where HubSpot puts them: drill-down 1 for Paid Search and Other Campaigns, drill-down 2 for Paid Social and Offline imports. Paid Search drill-down 2 holds search terms, including decoys like brand strategy consultant, which must never set the bucket.
Planted: 10 paid deals with a blank campaign name, 6 with names nobody can classify (q3-push, test-campaign-2, spring-promo). All 16 must land in Unclassified.
Events arrive as Offline Sources and Other Campaigns in the CRM. 49 deals must be moved to Events by campaign name.

| Channel | Deals | Won | Win rate | Revenue won |
|---|---|---|---|---|
| Referrals | 30 | 15 | 50% | $407,000 |
| Paid Search: Branded | 27 | 14 | 52% | $333,500 |
| Events: Trade show | 18 | 6 | 33% | $272,000 |
| Organic Search | 35 | 10 | 29% | $170,000 |
| Events: Hosted event | 9 | 5 | 5 of 9 | $137,750 |
| Events: Webinar | 22 | 6 | 27% | $115,500 |
| Paid Search: Non-brand | 35 | 6 | 17% | $104,500 |
| Paid Social: Content promotion | 19 | 5 | 26% | $102,500 |
| Paid Search: Conquesting | 22 | 4 | 18% | $100,500 |
| Paid Social: Lead gen | 42 | 5 | 12% | $69,000 |
| Direct Traffic | 15 | 4 | 27% | $65,250 |
| Paid Search: Retargeting | 7 | 3 | 3 of 7 | $48,750 |
| Paid Search: Unclassified | 12 | 2 | 17% | $48,250 |
| Paid Social: Brand awareness | 12 | 2 | 17% | $42,250 |
| Paid Social: Retargeting | 10 | 3 | 30% | $27,750 |
| Paid Social: Unclassified | 4 | 0 | 0 of 4 | $0 |

Story the skill should find: Branded search has the best paid win rate but only captures demand that already exists, so it stays held fixed. Conquesting and paid social lead gen draw volume and close poorly. Content promotion outperforms lead gen on LinkedIn. Trade shows bring the biggest deals and the longest cycle.
