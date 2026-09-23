# How to export your deals

Goal: one CSV of closed deals, won and lost, from the last 12 to 24 months.

## HubSpot

1. CRM > Deals. Switch to the table view.
2. Filter: Deal stage is any of Closed Won, Closed Lost. Close date is in the last 24 months.
3. Edit columns. Make sure these are included: Deal Name, Deal Stage, Amount, Create Date, Close Date, Deal Type, Original Traffic Source (older portals call it Original Source Type). For channel detail, add Original Traffic Source Drill-Down 1 and Drill-Down 2. HubSpot keeps the utm_campaign name in drill-down 1 for paid search and other campaigns, and in drill-down 2 for paid social. The skill reads the right one for each.
4. Export > CSV. HubSpot emails a download link.

Custom pipelines with renamed won/lost stages: rename them to Closed Won and Closed Lost in the CSV, or tell Claude which stages mean won and lost.

## Salesforce

1. Reports > New Report > Opportunities.
2. Filters: Stage equals Closed Won, Closed Lost. Close Date is last 24 months. Show All Opportunities.
3. Columns: Opportunity Name, Stage, Amount, Created Date, Close Date, Type, Lead Source. For channel detail, add Primary Campaign Source.
4. Run the report. Export > Details Only > CSV.

## Any other CRM

Pipedrive, Zoho, Close, a spreadsheet. Any CSV works if it has these five columns: stage (won or lost), amount, created date, close date, source. Column names can vary.

## Campaign names that sort cleanly

The channel detail reads keywords in campaign names. Names like these sort without help:

- Search: `google-search-brand-...`, `google-search-conquest-...` or `-vs-competitor-`, `google-search-nonbrand-...`, `-rlsa-` or `-retargeting-`
- Social: `linkedin-leadgen-...`, `linkedin-content-...`, `linkedin-awareness-...`, `meta-retargeting-...`
- Events: `event-tradeshow-...`, `event-webinar-...`, `event-hosted-dinner-...`, `event-sponsorship-...`

Anything else lands in Unclassified. That is a finding, not a failure.

## Before you upload

- Include lost deals. Without them there is no win rate.
- Do not clean the file first. The messy parts are part of the answer.
- Remove anything you are not allowed to share. Deal names are optional.
