# Before you run Customer Segmentation

The models learn from what your CRM recorded. If the CRM never recorded who an account is or how its deals ended, no model can recover it. This page covers what has to be in place, and what happens when it is not.

## What do I need to run it at all?

- **A Claude account on any plan, Free included,** with code execution turned on. Skills do not run without it.
- **The skill uploaded.** In Claude: Customize > Skills > + > Create skill > Upload a skill.
- **Won AND lost deals** from the last 12 to 24 months, as a CSV. Open deals help too.
- **Firmographics for every account:** at least one of industry or sector, employee count, annual revenue, country, year founded, parent company. More attributes, sharper segments.
- **Enough history.** 100 closed deals across 30 accounts, with at least 20 won and 20 lost, is the floor. 300 or more closed deals is where segments get trustworthy.

No connectors or MCP servers are needed. The skill works from the files you upload, inside your own Claude session. Nothing is sent anywhere else.

## One file or two?

| Shape | What it holds | What you get |
|---|---|---|
| **Two files** | An accounts file with firmographics, plus a deals file with the account name on every deal | Everything, including scores for accounts nobody has worked yet |
| **One file** | A deal export with company firmographics on every row | Everything except untouched accounts, because they have no deals to appear on |

Two files is better. Put your full target account list in the accounts file, worked or not. The skill scores every account on it and ranks the untouched ones.

## Which columns does it read?

The skill finds these by name, in any order, any capitalization.

**Deals file**

| What | Names it recognizes |
|---|---|
| Account (required) | account, account name, company, company name, associated company |
| Stage (required) | deal_stage, deal stage, stage, stage name, status |
| Amount | close_value, amount, deal amount, value |
| Deal ID | opportunity_id, deal id, record id, id |
| Close date, create date | close date, create date, engage date |

**Accounts file** (or the same deal file, in one-file mode)

| What | Names it recognizes |
|---|---|
| Account (required) | account, account name, company name, name |
| Sector | sector, industry, vertical |
| Employees | employees, number of employees, employee count, headcount |
| Annual revenue | revenue, annual revenue. In dollars or in millions: the skill tells them apart |
| Country | office_location, country, country/region, billing country |
| Year founded | year_established, year founded, founded |
| Parent company | subsidiary_of, parent company, parent account. Blank means independent |

Stages containing "won" count as won. Stages containing "lost" count as lost. Everything else counts as open. Custom stage names work with `--won` and `--lost`, and the skill asks when it cannot tell.

Any other account column can join the model with `--features`: tech stack, funding stage, ownership type, whatever you believe drives fit.

## What makes the answer trustworthy?

| What has to be true | Why it matters | What you see if it is not |
|---|---|---|
| Lost deals are marked lost, not deleted | The models learn as much from losses as from wins | A stop, or a model that thinks everyone buys |
| Every deal is attached to an account | An orphan deal cannot teach the model anything | "Deals with no account name" in the data checks |
| Account names match across both files | The skill joins on the name | "Deals naming an account not in the accounts file" |
| Firmographics are filled in | A blank sector teaches nothing | "Blank attribute values" in the data checks |
| Firmographics are current | A company that grew from 50 to 500 employees is scored as the old one | Nothing. The skill cannot see stale data. Refresh it before you export |
| Amounts are on won deals | Deal size sets the value axis | "Won deals with no value" in the data checks |
| Renewals are left out of the export | A renewal is not a new decision to buy. The skill reads every deal as new business | Inflated win rates for your existing customers |

## Readiness checklist

- [ ] Code execution is on in Claude
- [ ] The skill is uploaded
- [ ] Deals export has won and lost deals, 12 to 24 months
- [ ] At least 100 closed deals across 30 accounts (300 or more is better)
- [ ] Every deal names its account
- [ ] Accounts carry sector, employees and country at minimum
- [ ] Account names match between the two files
- [ ] Your full target list is in the accounts file (to rank untouched accounts)

The first five are required. The rest decide how far you can trust the answer, and how much it can tell you.
