# How to export your accounts and deals

Goal: a deals file with won, lost and open deals from the last 12 to 24 months, each naming its account. Plus an accounts file with firmographics for every account you sell to or want to sell to.

## HubSpot

**Deals**

1. CRM > Deals. Switch to the table view.
2. Filter: Close date is in the last 24 months, or the deal is still open.
3. Edit columns. Include Deal Name, Deal Stage, Amount, Create Date, Close Date.
4. Export > CSV. Under the associations option, keep the associated record name. The file gets an Associated Company column. The skill reads it.

**Companies**

1. CRM > Companies. Switch to the table view. Include every company you sell to or want to, worked or not.
2. Edit columns. Include Company name, Industry, Number of Employees, Annual Revenue, Country/Region, Year Founded, and Parent Company if you track it.
3. Export > CSV.

Annual Revenue exports in dollars. The skill converts it.

## Salesforce

**Deals and accounts in one report**

1. Reports > New Report > Opportunities.
2. Filters: Close Date is last 24 months. Show All Opportunities, open and closed.
3. Columns: Opportunity Name, Account Name, Stage, Amount, Created Date, Close Date. Then the account fields: Industry, Employees, Annual Revenue, Billing Country. Add Parent Account when the report type lists it.
4. Run the report. Export > Details Only > CSV.

**Accounts not yet worked**

Accounts with no opportunity do not appear on an opportunity report. To score them, run a second report: Reports > New Report > Accounts, with Account Name, Industry, Employees, Annual Revenue, Billing Country, Parent Account, and no filter on opportunities. Upload both files. The accounts report is the master list, so it must hold every account, worked or not.

## Any other CRM

Pipedrive, Zoho, Close, a spreadsheet. Any CSV works if deals carry an account name, a stage and an amount, and accounts carry at least one firmographic column. Column names can vary.

## Want to add your own fit signals?

Any account column can join the model. Tech stack, funding stage, ownership type, number of locations. Export it with the accounts and tell Claude which columns to add.

## Before you upload

- Include lost deals. The models learn as much from losses as from wins.
- Leave renewals and upsells out. They are not a new decision to buy.
- Do not clean the file first. The data checks are part of the answer.
- Remove anything you are not allowed to share. Deal names are optional.
