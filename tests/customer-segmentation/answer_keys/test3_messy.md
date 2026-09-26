# Answer key: test3 messy file

Every problem planted by `make_test_data.py`, counted by hand from the code that plants it. The skill must report each one exactly.

| # | Planted problem | Planted count | Expected in `data_quality` |
|---|---|---|---|
| 1 | Accounts with a blank sector | 6 | `blank_attributes.Sector = 6` |
| 1 | Accounts with a blank employee count | 4 | `blank_attributes.Employees = 4` |
| 2 | One account in a country no other account shares (Iceland) | 1 | `grouped_as_other.Country` includes Iceland |
| 3 | Stages written Closed Won and Closed Lost | all closed deals | `stage_mapping` reads them as won and lost |
| 4 | Won deals with text amounts ($45,000 or 45k style) | 8 | `text_values_parsed = 8` |
| 5 | Won deals with no amount | 3 | `won_without_value = 3` |
| 6 | Exact duplicate deals | 5 | `duplicate_deals = 5` |
| 7 | Deals naming accounts missing from the accounts file | 4 deals, 2 names | `deals_unmatched_account = 4`, names Nowhere Analytics and Phantom Freight |
| 8 | Deals with no account name | 2 | `deals_without_account = 2` |

The six blank sectors also group as Other in the model, since six accounts carry fewer than 15 closed deals between them. The test checks the counts above. The closed deal, won deal and won revenue totals are recomputed independently in `test_segment.py` with the csv module alone.
