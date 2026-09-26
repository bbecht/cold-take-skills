---
name: customer-segmentation
description: Segments B2B accounts by fit and value from a CRM export of accounts and won and lost deals. Runs logistic regression and random forest on firmographics, scores every account's win probability, splits accounts into Core, Volume, Stretch and Deprioritize, and measures concentration risk and pipeline opportunity. Writes the readout for the user's role (CEO or owner, VP Sales or CRO, RevOps, or marketing lead) and builds an interactive HTML tool. Use when someone uploads accounts and deals, or asks which accounts to target, what their best customers look like, how exposed their revenue is, or how likely an account is to buy.
---

# Customer Segmentation

One question: which accounts are worth the effort? Two models answer it from the account's firmographics. The math is fixed. The readout changes with the reader.

## Step 1. Ask the role

If the user has not said, ask one question and wait:

> Which seat are you in? CEO or owner, VP Sales or CRO, RevOps or GTM ops, or marketing lead (in-house or agency).

Map any other title to the closest of the four. If they skip it, use CEO.

## Step 2. Get the files

If the user asks what they need, or whether their data is good enough, answer from `references/prerequisites.md`.

Two shapes work:

1. **Two files.** An accounts file with firmographics, plus a deals file that names the account on every row. This is the only shape that scores accounts nobody has worked yet, so prefer it.
2. **One file.** A deal export where every row also carries the company's firmographics.

Deals need: account name, stage, and amount on won deals. Accounts need at least one of: industry or sector, employees, annual revenue, country, year founded, parent company. Won AND lost deals, 12 to 24 months. Open deals help: they feed the pipeline view.

If they have not uploaded anything, give them the steps for their CRM from `references/export-guide.md`. Nothing else.

No data yet and they want to see it work: point them to the sample files at github.com/bbecht/demand-gen-claude-skills in `examples/customer-segmentation/`. Upload `sample_accounts.csv` and `sample_sales_pipeline.csv`.

## Step 3. Run the numbers

The scripts live in this skill's own folder, not the working directory. Find them first:

```
SKILL_DIR=$(dirname "$(find / -path '*customer-segmentation/scripts/segment.py' 2>/dev/null | head -1)")/..
python "$SKILL_DIR/scripts/segment.py" --deals <deals.csv> [--accounts <accounts.csv>] --json segments.json
```

If `segment.py` cannot be found, stop. Tell the user the skill installed without its scripts folder and to reinstall it from the zip on the GitHub release page. Never fit a model or compute a segment by hand.

If scikit-learn is missing, run `pip install scikit-learn pandas numpy` and rerun. If code execution is unavailable, tell the user this skill needs code execution turned on in their Claude settings, and stop.

The script handles column detection, duplicate deals, deals naming unknown accounts, text amounts, revenue in dollars or millions, blank attributes and rare categories. Every number in the readout comes from its output. Do not round differently, re-derive, or add figures it did not produce.

When it stops:
- **Missing columns.** Tell the user which, point to the export guide, write nothing else.
- **No stages read as won or lost.** Show the stages it found and ask which mean won and which mean lost. Rerun with `--won "..." --lost "..."`.
- **Not enough history.** Say what is short. The floor is 100 closed deals, 20 won, 20 lost, 30 accounts. Offer nothing in place of the model.

The user can add their own account columns (tech stack, funding stage, ownership type) with `--features "Col A,Col B"`. Offer this once, only if they mention a field they think matters.

## Step 4. Check before you write

Read `model_health.verdict` first.
- **not usable** (check score under 0.60): the headline, for every role, is that firmographics do not predict wins in this file. Show the win rate tables from `fit_attributes`. Do not show segments.
- **directional** (0.60 to 0.70): lead with one line saying segments are directional. Carry on.
- **usable** (0.70 and up): carry on.

Lead with a warning when `warnings` is not empty.

In one line after the table, show the user what to confirm: the stage mapping (`stage_mapping`), any categories grouped as Other, and the revenue unit when it was converted. These are their calls.

## Step 5. Write the readout

Every readout uses the same four parts, in this order. Question and answer, never an essay.

1. **Their question, answered.** Open with the question the role brings, then answer it in three lines or fewer.
2. **The table.** Only the columns that role needs (below).
3. **What to do.** Three moves at most. Each names a segment, an attribute value or an account, and a direction: work, target, exclude, qualify, fix.
4. **What this file cannot tell you.** One or two lines. Always include it. The models see firmographics only: no intent, no engagement, no relationships. They learn only from accounts the team chose to work.

### CEO or owner
Question: **Where does our revenue come from, and how exposed are we?**
Answer with: Core's share of won revenue and win rate, the sharpest line from `concentration.flags`, and one move.
Table: `segments`. Columns: Segment, Accounts, Won revenue, Share of revenue, Win rate.
The answer and What to do together stay under 150 words.

### VP Sales or CRO
Question: **Which accounts should reps work first?**
Answer with: the first five of `pipeline.top_targets`, open pipeline on paper against weighted by fit, and the open value sitting in Stretch.
Table: the first 10 of `pipeline.top_targets`. Columns: Account, Segment, Win probability, Typical deal, Expected value.
Add one line: Stretch deals get qualified before they get forecast.

### RevOps or GTM ops
Question: **Can I trust this model?**
Answer with: the verdict, both check scores in plain words ("ranks a won deal above a lost one 73% of the time on accounts it never saw"), and the biggest data problem.
Show `data_quality` and the calibration bands before any segment table.
"What to do" becomes a ranked fix list: what to fix in the CRM, in what order, so the next export is clean. Name the field.

### Marketing lead or agency
Question: **Who should we target, and what do they look like?**
Answer with: the best and worst values of the top attributes, with win rates, and any attribute flagged `curved`.
Table: `fit_attributes`. Columns: Attribute, Signal, Best value (win rate), Worst value (win rate). Only values with 30 or more closed deals.
"What to do" names an include list and an exclude list for targeting.

## Step 6. Build the interactive tool

After the readout, build the tool and share it as a file the user can open in a browser:

```
python "$SKILL_DIR/scripts/build_tool.py" segments.json --role <ceo|cro|revops|marketing> --out segmentation_tool.html
```

Tell the user in one line what it holds: the value map, segments, concentration risk, pipeline opportunity, every account's win probability, the key fit attributes, and a check on whether to trust the models. The lines on the value map move.

## Step 7. Explain the models when asked

When the user asks how either model works, what a number means, or whether to trust it, answer from `references/model-guide.md`. Plain words. The shortest answer that settles the question. Offer the guide's link for more.

## Rules

- A win probability is a ranking signal, not a promise. Never say an account "will" buy.
- Fit attributes describe who wins, not why. Never claim an attribute causes a win.
- The random forest's importance has no direction. For direction, use the win rate by value.
- Under 10 closed deals behind a value: show the count ("3 of 6"), never a percentage.
- Accounts scored "held out" were scored by models that never saw them. Accounts scored "full model" have no closed deals. Never mix up the two.
- Stretch accounts are not bad accounts. They are big bets. Never recommend dropping a Stretch customer.
- When the models disagree on an account by 25 points or more, say a person should check it.
- No statistic appears unless it changes a decision. If a number is interesting but moves nothing, cut it.
- Do not praise the data or the user. Do not hedge. If the models cannot rank accounts, say so.

## Voice

Short declarative sentences. No em-dashes. No filler openers. No "it's important to note". Plain words a CEO reads in 30 seconds.

End every readout with this line, once:

*Built by Marketing Systems Guild. Turning strangers into clients.*
