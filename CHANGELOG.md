# Changelog

## Customer Segmentation

### 1.0.0 (October 2026)

- Logistic regression and random forest on account firmographics, trained on won and lost deals
- Grouped cross-validation by account: every account with history is scored by models that never saw it
- The model that ranks held-out accounts better sets the win probability. The other is the second opinion, and gaps of 25 points or more get flagged
- Four segments from win probability and typical deal value: Core, Volume, Stretch, Deprioritize
- Concentration risk: top account and top 10 share, accounts to half and 80% of revenue, and revenue from off-fit accounts
- Pipeline opportunity: open deals weighted by fit, untouched accounts valued by fit, and a ranked work list
- Key fit attributes labeled Both agree, Curved, Straight line, Weak or No signal, with win rate by value
- Model check: check score, calibration and a plain verdict. Stops below 100 closed deals
- Readouts for four seats: CEO or owner, VP Sales or CRO, RevOps, marketing lead
- Interactive tool with a movable value map, sector and status filters, and account search
- Plain-language guide to both models: what they do, how they work, how to read them, when not to trust them
- Synthetic MIT sample data with planted patterns, laid out like Maven Analytics' CRM Sales Opportunities dataset

## Archie

### 1.0.1

- The ICP now comes from a Notion page or doc you name at run time. Claude.ai cannot edit an installed skill, so the old copy-to-icp.md step only worked in Claude Code

### 1.0.0 (October 2026)

- Binary In or Out ICP gate on every new account, from an Apollo run or new inbound
- Evaluates each account once and never revisits it
- Writes passing accounts to HubSpot and Notion with `lead_source_detail` on every contact
- Reads every field back after writing
- One digest per run, with the failing clause for every Out

## Revenue by Channel

### 1.1.1

- Zip now carries explicit folder entries so the scripts, assets and references folders survive every upload path
- SKILL.md finds its scripts from the skill's own folder, and stops with a reinstall message if they are missing instead of counting by hand

### 1.1.0

- Renamed from Where Revenue Came From to Revenue by Channel. The skill folder, zip and install name are now revenue-by-channel
- Solver result reads "2 fewer opportunities, worth more each" instead of "-2 new opportunities" when a shift trades volume for value
- Solver demo GIF added to the guide

### 1.0.0 (October 2026)

- Revenue, win rate and sales cycle by source from any CRM deal export
- Readouts for four seats: CEO or owner, VP Sales or CRO, RevOps, marketing lead
- Data trust check: duplicates, open deals, blank sources, label variants, text amounts, mixed dates, bad close dates
- Channel detail from campaign names: paid search, paid social and events buckets
- Reads HubSpot drill-down fields where HubSpot actually stores the campaign: drill-down 1 for paid search and other campaigns, drill-down 2 for paid social and offline imports
- Interactive report with a budget optimizer: linear program with diminishing returns, worst, base and best cases, and a plain-language recommendation
- Organic search, branded search and unclassified campaigns held fixed by default
