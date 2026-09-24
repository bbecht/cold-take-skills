# Changelog

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
