# Before you run Archie

Archie writes to your CRM. Everything below has to exist before the first run, or the write fails.

## What do I need?

- **A Claude plan with connectors,** and the Apollo, HubSpot and Notion connectors turned on.
- **Your ICP** in a Notion page or doc you name when you run Archie, written using the sections in `icp.sample.md`. In Claude Code you can instead save it as `references/icp.md` inside the skill folder.
- **Four custom HubSpot properties.** Create them in Settings > Properties before the first run. HubSpot rejects the whole batch if one is missing.

| Object | Property | Type |
|---|---|---|
| Company | `archie_scored_at` | Date |
| Company | `archie_verdict` | Dropdown: In, Out |
| Company | `archie_score_version` | Single-line text |
| Contact | `lead_source_detail` | Dropdown, values from the table in SKILL.md |

- **A Notion Accounts database** with Account, Vertical, HubSpot Link, Scored On and Status columns. Optional. Skip it and Archie writes to HubSpot only.

## What makes it trustworthy?

- **One ICP source.** Two copies drift. Archie stops rather than guess which one is current.
- **A cutoff date.** Without one, Archie reaches back into accounts your team already worked.
- **Reading the website.** Industry codes misfile agencies and resellers. Archie checks what a company sells.
