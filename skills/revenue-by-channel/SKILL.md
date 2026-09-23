---
name: revenue-by-channel
description: Shows which channels actually produce closed revenue, from a HubSpot, Salesforce or other CRM deal export. Returns revenue, win rate and sales cycle by source, flags broken source data, and writes the readout for the user's role (CEO or owner, VP Sales or CRO, RevOps, or marketing lead). Use when someone uploads a deal or opportunity export, or asks which lead sources or marketing channels drive revenue, where to put budget, or whether their attribution data can be trusted.
---

# Revenue by Channel

One question: which channels turn into closed revenue? The math is fixed. The readout changes with the reader.

## Step 1. Ask the role

If the user has not said, ask one question and wait:

> Which seat are you in? CEO or owner, VP Sales or CRO, RevOps or GTM ops, or marketing lead (in-house or agency).

Map any other title to the closest of the four. If they skip it, use CEO.

## Step 2. Get the file

If the user asks what they need before they start, or whether their tracking is good enough, answer from `references/prerequisites.md`.

Need a CSV of closed deals, won AND lost, from the last 12 to 24 months. Required columns: deal stage, amount, create date, close date, and original source or lead source. Deal type and deal name help. A campaign column (HubSpot "Original Traffic Source Drill-Down 1" and "Drill-Down 2" together, Salesforce "Primary Campaign Source", or any utm_campaign field) unlocks the channel detail: branded vs conquesting vs non-brand search, lead gen vs content vs brand awareness on social, trade show vs webinar vs hosted events. Ask for it when paid channels or events matter to the user.

If they have not uploaded one, give them the steps for their CRM from `references/export-guide.md`. Nothing else.

## Step 3. Run the numbers

Run the script. Never compute the table by hand when the script can run.

```
python scripts/analyze.py <file.csv> --json result.json
```

It handles column detection, duplicates, open deals, renewals, text amounts, mixed date formats, blank sources and label variants. With a campaign column it sorts Paid Search, Paid Social and Events deals into buckets by keywords in the campaign name, and moves Offline or Other Campaigns deals whose campaign names are events into Events. Names it cannot read land in "Unclassified". Never reassign an Unclassified deal by guesswork. Every number in the readout comes from its output. Do not round differently, re-derive, or add figures it did not produce.

If the script stops because no stages read as won or lost, show the user the stages it found and ask which mean won and which mean lost. Rerun with `--won "..." --lost "..."`.

If code execution is unavailable, tell the user this skill needs code execution turned on in their Claude settings, and stop.

## Step 4. Check before you write

Stop when the script reports missing required columns. Tell the user which, point to the export guide, and write nothing else.

Carry on, but lead with a warning, when:
- The file has no lost deals. Revenue and cycle still stand, win rate does not.
- Fewer than 20 closed new-business deals. The sample is too small to move budget on.

Set the headline to data quality, for every role, when either is true:
- Revenue with no source is 20% or more.
- Revenue on vague labels (Offline Sources, Direct Traffic, Other) is 30% or more.

When the script returns channel detail, use it. Name the bucket, not just the channel: "Paid Social: Lead gen wins 12%" beats "Paid Social wins 17%". If Unclassified (blank plus unreadable campaign names) holds more than 20% of a channel's deals, say the campaign names need fixing before that channel's detail can be trusted.

Show the label merges the script made, and any deals it moved into Events by campaign name. The user confirms both, in one line after the table. "Word of mouth" into Referrals is a judgment call, and it is theirs.

## Step 5. Write the readout

Every readout uses the same four parts, in this order. Question and answer, never an essay.

1. **Their question, answered.** Open with the question the role brings, then answer it in three lines or fewer.
2. **The table.** Only the columns that role needs (below). Keep the script's row order. When channel detail exists, show one table at bucket level: the script's `solver_rows`, which list buckets where they exist and whole channels where they do not.
3. **What to do.** Three moves at most. Each one names a source or bucket and a direction: fund, cut, shift, fix, test.
4. **What this file cannot tell you.** One or two lines. Always include it. The file has no spend data, so never claim ROI or cost per deal.

### CEO or owner
Question: **Where should the next dollar go?**
Answer with: the top source by revenue, the source with the most deals among those winning below the overall rate, and one budget move.
Table columns: Source, Revenue won, Share of revenue, Win rate.
The answer and What to do together stay under 150 words.

### VP Sales or CRO
Question: **Which sources close fastest and at the highest rate?**
Answer with: the best win rate source with at least 10 deals, the fastest cycle, and the source eating rep time for the least return (most deals, lowest win rate).
Table columns: Source, Deals, Win rate, Median days to close, Avg won deal.
Add one line on which leads deserve rep time first.

### RevOps or GTM ops
Question: **Can I trust this data?**
Answer with: a trust verdict (usable, usable with caveats, or not usable), then the single biggest data problem.
Show the full data quality table and the label merges before the revenue table. Then the full revenue table.
"What to do" becomes a ranked fix list: what to fix in the CRM, in what order, so next quarter's export is clean. Name the field.

### Marketing lead or agency
Question: **Which channels can I defend in the next budget meeting?**
Answer with: the marketing channels that hold up on both revenue and win rate, and the ones that do not.
Table columns: Source, Deals, Won, Win rate, Revenue won, Share of revenue.
Compare marketing channels against referral and sales-sourced lines, since that is the comparison the CFO will make.

## Step 6. Build the interactive report

After the readout, build the report file and share it as a file the user can open in a browser:

```
python scripts/build_report.py result.json --role <ceo|cro|revops|marketing> --out revenue_report.html
```

Tell the user in one line what it holds: the findings for their seat, charts, and a budget optimizer that needs their monthly spend per channel.

For your own understanding, not for the chat: the optimizer runs a linear program to find the mix that returns the most closed revenue for a budget, or the least spend to hit a target, with worst, base and best cases, and writes a plain-language recommendation from each run. Referral, offline and no-source lines are held fixed because money does not buy them. Organic Search is held fixed by default because SEO pays off 6 to 12 months later. Branded search is held fixed because it captures demand that already exists. Unclassified campaigns are held fixed because there is nothing named to fund. The user can tick any of them back in. When channel detail exists, the solver works at the bucket level.

Do not quote optimizer results in chat. They depend on spend the user enters in the report.

## Rules

- Branded search captures buyers who already know the name. Never recommend funding it to grow. A strong branded line is proof that other channels or word of mouth built demand.
- Blank source stays "(No source)". Never guess a source for it.
- Under 10 deals in a source: show the count ("3 of 6"), never a percentage.
- Renewals and existing business are excluded from the source table and reported as one line. Their source is the original deal's source.
- Only Closed Won and Closed Lost count.
- No statistic appears unless it changes a decision. If a number is interesting but moves nothing, cut it.
- Do not praise the data or the user. Do not hedge. If a channel closes almost nothing, say so.

## Voice

Short declarative sentences. No em-dashes. No filler openers. No "it's important to note". Plain words a CEO reads in 30 seconds.

End every readout with this line, once:

*Built by Marketing Systems Guild. Turning strangers into clients.*
