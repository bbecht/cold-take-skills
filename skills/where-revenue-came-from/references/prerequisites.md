# Before you run Where Revenue Came From

The skill reads what your CRM recorded. If the CRM never recorded where a deal came from, no analysis can recover it. This page covers what has to be in place, and what happens when it is not.

## What do I need to run it at all?

- **A Claude account on any plan, Free included,** with code execution turned on. Skills do not run without it.
- **The skill uploaded.** In Claude: Customize > Skills > + > Create skill > Upload a skill.
- **A deal export from your CRM,** as a CSV. Won and lost deals, closed in the last 12 to 24 months.
- **Five columns in that export:** deal stage, amount, create date, close date, and a source field (HubSpot "Original Traffic Source", Salesforce "Lead Source").
- **Enough deals.** 20 closed new-business deals is the floor. 50 or more is where the answer gets useful. A channel needs 10 deals before it gets a win rate.

No connectors or MCP servers are needed. The skill works from the file you upload, inside your own Claude session. Nothing is sent anywhere else.

## What makes the answer trustworthy?

Every one of these shows up in the report's data trust check when it is missing.

| What has to be true | Why it matters | What you see if it is not |
|---|---|---|
| Your CRM's tracking code is on every page of your site | Without it, the CRM cannot see where a visitor came from | Deals land in Direct Traffic or (No source) |
| Every form on the site feeds the CRM | Leads from an unconnected form arrive with no history | Blank sources |
| Every deal has a contact attached (HubSpot) | HubSpot sets a deal's source from its earliest associated contact, or the company if there is no contact | Deal shows (No source) even when the lead came in tracked |
| Lead Source carries over on conversion (Salesforce) | The opportunity takes its source from the lead at conversion | Lead Source blank on opportunities |
| Offline leads are labeled when entered | Imports and manual entry otherwise read as "Offline" | A large Offline Sources line hiding real channels |
| Deal type is set: new vs existing | Renewals carry the original deal's source and inflate old channels | A "blank deal type" warning |
| Lost deals are marked Closed Lost, not deleted | Win rate needs the losses | No win rate at all |

## What do I need for the channel detail?

The channel detail splits paid search, paid social and events into buckets: branded vs conquesting search, lead gen vs content campaigns, trade shows vs webinars. That needs campaign names, and campaign names need UTM tags.

- **UTM tags on every paid link.** At minimum `utm_source`, `utm_medium` and `utm_campaign`. An untagged ad click looks like organic or direct traffic.
- **One naming pattern, used every time.** Put the campaign's objective in the name as a plain word. Pattern that works: `platform-objective-theme-audience-YYYYMM`, for example `linkedin-leadgen-diagnostic-cmo-202606`.
- **Objective words the skill reads:**
  - Search: `brand`, `nonbrand` or `generic`, `conquest` or `vs`, `rlsa` or `retargeting`
  - Social: `leadgen`, `content`, `awareness`, `retargeting`
  - Events: `tradeshow`, `webinar`, `hosted`, `sponsorship`
- **The CRM keeps the campaign name.** With the tracking code installed, HubSpot stores the utm_campaign value in Original Traffic Source Drill-Down 1 for paid search and other campaigns, and in Drill-Down 2 for paid social. Export both. Salesforce needs Campaigns with the opportunity's Primary Campaign Source set, or hidden form fields that write UTM values to the lead.
- **Events go in with a campaign name.** When you import a trade show or webinar list, give the import a campaign name like `event-tradeshow-industryexpo-202609`. The skill then moves those deals out of Offline Sources and into Events.

Campaign names the skill cannot read land in Unclassified. That tells you which campaigns need renaming.

## What do I need for the budget optimizer?

- **Monthly spend per channel,** from each ad platform or your books. With channel detail, spend per bucket: what you spend on branded search, on conquesting, on LinkedIn lead gen, and so on.
- **Your gross margin,** to judge the result. The optimizer reports closed revenue, not profit. A move that adds $1 of revenue for every $1 of spend loses money.

You type spend into the report. It never leaves your browser.

## What is deliberately held out of the optimizer?

- **Referrals, offline, direct and unsourced revenue.** Money does not buy it.
- **Organic search.** SEO pays off 6 to 12 months later. A same-month model would overstate it.
- **Branded search.** It captures people already looking for you. More budget buys the same buyers at a higher price.
- **Unclassified campaigns.** There is nothing named to fund.

You can switch any of them back in.

## Readiness checklist

- [ ] Code execution is on in Claude
- [ ] The skill is uploaded
- [ ] Export has won and lost deals, 12 to 24 months
- [ ] At least 20 closed new-business deals
- [ ] Source field filled on most deals
- [ ] Deal type set on every deal
- [ ] Tracking code on every page, every form connected
- [ ] UTM tags on every paid link, one naming pattern (for channel detail)
- [ ] Campaign column in the export (for channel detail)
- [ ] Monthly spend per channel on hand (for the optimizer)

The first four are required. The rest decide how far you can trust the answer, and how deep it goes.
