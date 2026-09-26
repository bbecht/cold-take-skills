# The models, in plain language

This guide explains the two models behind Customer Segmentation: what each one does, how it works, how to read what it tells you, and when not to trust it. No math background needed. The examples use the sample data that ships with the skill.

## What question do the models answer?

**What does an account that buys look like?**

You have deals you won and deals you lost. Each deal belongs to an account, and each account has attributes: sector, employee count, revenue, country, year founded, whether a parent company owns it. The models study the won and lost deals and learn which attributes go with winning. Then they score every account, including accounts nobody has worked yet, with a win probability.

That probability, crossed with how big a deal the account signs, puts every account into one of four segments.

| Segment | Win probability | Typical deal | What to do |
|---|---|---|---|
| Core | At or above your win rate | At or above your median won deal | Work these first |
| Volume | At or above your win rate | Below your median won deal | Work them efficiently |
| Stretch | Below your win rate | At or above your median won deal | Pursue on purpose, never by default |
| Deprioritize | Below your win rate | Below your median won deal | Stop spending here |

## Why two models?

They fail in different ways. Logistic regression is easy to read and misses curves. Random forest catches curves and is hard to read. Run both and each covers the other's blind spot.

The skill does not average them. It tests both on accounts they never saw and lets the one that ranks better set the probability. The other becomes the second opinion. When they disagree, that disagreement is information.

---

## Logistic regression

### What does it do?

It gives every attribute a weight, adds the weights up, and turns the total into a probability between 0% and 100%.

### How does it work?

Think of a points card. Every account starts with the same base score. Being in Software adds points. Being in Retail takes points away. Being owned by a parent company takes points away. The model reads your won and lost deals and picks the points for each attribute that best separate winners from losers.

The total can be any number, positive or negative. A final step squeezes it into a probability: a very negative total lands near 0%, zero lands at 50%, a very positive total lands near 100%.

Two details matter:

- **Numbers get one weight each.** Employee count gets a single weight, so the model can only say "more employees is better" or "more employees is worse". It works on the logarithm of employees and revenue, so going from 50 to 500 counts the same as going from 500 to 5,000.
- **Weights are kept modest.** The model is penalized for extreme weights. A sector with only a handful of deals cannot earn a huge weight from one lucky win.

### How do I read its output?

The tool shows each weight as an **odds multiplier**.

- **Above 1.00x** raises the odds of winning. In the sample, Software reads 1.94x: Software accounts carry almost twice the odds of the average account.
- **Below 1.00x** lowers the odds. Retail reads 0.59x.
- **Near 1.00x** means no straight-line effect.

For number attributes, the multiplier is per standard step: the typical spread of that attribute. In the sample, one step up in employees multiplies the odds by 1.17x. Close to flat. Hold that thought.

Odds are not probability. Odds of 1 to 1 is a 50% chance. Doubling the odds to 2 to 1 takes you to 67%, not 100%. The multiplier tells you direction and strength. The probability column tells you where an account lands.

### When should I not trust it?

- **When the effect is a curve.** This is its biggest blind spot. In the sample, mid-size companies win most: 56% at 200 to 999 employees, 20% under 50 and 22% over 5,000. The regression can only draw a straight line through that hill, so it calls employee count nearly irrelevant (1.17x). The random forest sees the hill. The tool flags this as **Curved**.
- **When attributes move together.** Employees and revenue rise together. The regression has to split the credit between them, and the split can look odd: one gets a strong weight, the other a weak or even reversed one. Read correlated attributes as a pair.
- **When an attribute only matters in combination.** "Healthcare wins, but only mid-size Healthcare" is invisible to a points card. The forest can see it.
- **When a value has few deals.** The weight for a country with 35 deals rests on 35 outcomes. The skill groups any value with fewer than 15 closed deals into Other for exactly this reason.

---

## Random forest

### What does it do?

It grows hundreds of decision trees and lets them vote. The probability is the share of trees that vote "win".

### How does it work?

A decision tree is a flowchart of yes or no questions. "Over 200 employees?" Yes. "Software or Healthcare?" Yes. "Owned by a parent?" No. At the end of the path sits a group of past deals, and the tree's answer is the win rate in that group.

One tree overreacts to its data. So the forest grows 300 of them, each with two twists:

- **Each tree sees a different sample of deals,** drawn at random with repeats.
- **Each question considers only a random few attributes.** This stops every tree from asking the same question first.

Every tree ends up a little different. Their average is steadier than any single tree. The skill also requires at least 15 deals at the end of every path, so no tree memorizes one account.

Because a tree can ask "over 200?" and then "under 2,000?", the forest draws hills and valleys naturally. That is why it found the employee sweet spot the regression missed.

### How do I read its output?

- **The probability** is the share of trees voting "win". In the sample, the forest gives Vantage Labs 77%.
- **Importance** is how much the forest's ranking skill drops when one attribute is scrambled. Scramble employee count and the check score drops about 7 points. Scramble year founded and it drops nothing. Bigger drop, bigger driver.

Importance has **no direction**. It tells you employee count matters, not which counts win. For direction, open the attribute in the tool and read the win rate by value.

### When should I not trust it?

- **Its percentages bunch toward the middle.** Trees average, so the forest rarely says 5% or 95% even when it should. In the sample, accounts it scores 60% to 80% actually won 78% of the time. Trust its ranking more than its exact percent.
- **It can find patterns in noise.** Give a forest enough attributes and it will find some that look useful by luck, especially numbers with many distinct values like year founded. The skill scores importance only on accounts the forest never saw, and labels anything under 1.5 points **No signal**. In one test file, year founded scored 1.0 point from pure chance. It correctly lands as No signal.
- **It cannot see past its data.** If your largest won account has 20,000 employees, the forest treats a 200,000-employee company exactly like a 20,000-employee one. It never guesses beyond what it saw.
- **You cannot read it line by line.** There is no points card. When you need to explain a score to a skeptical sales leader, the regression is the one you can walk through.

---

## Checking the models

### How does the skill test them?

**Grouped cross-validation.** The accounts are split into five groups. The models train on four groups and score the fifth, five times over, so every account with history gets scored by models that never saw any of its deals.

Grouping by account matters. One account can have many deals. If some of its deals trained the model and others tested it, the model would recognize the account and look smarter than it is. Grouping stops that leak.

### What is the check score?

It answers one question: pick one won deal and one lost deal at random. How often does the model give the won deal the higher score?

| Check score | Meaning | What the skill does |
|---|---|---|
| 0.50 | A coin flip | |
| Under 0.60 | Barely better than a coin | Says firmographics do not predict wins. No segments |
| 0.60 to 0.70 | Directional | Segments shown, labeled directional |
| 0.70 and up | Usable | Segments shown |
| Over 0.90 | Suspicious for firmographics alone | Check the export for a column that leaks the outcome |

Statisticians call this the AUC. In the sample, the forest scores 0.73 and the regression 0.61. The forest sets the probability.

### What is calibration?

The check score tests ranking. Calibration tests the percentages. Take every deal the model scored 40% to 60%: did about half of them win? The tool shows predicted against actual for each band. Close together means you can use the percentages at face value. Far apart means use the ranking, not the number.

### Why do the models disagree on some accounts?

Most often, the account sits on a curve. Ironvale Labs in the sample is a Software company with 16 employees. The regression gives it 63%: Software is strong, and a straight line barely penalizes small size. The forest gives it 27%: it knows companies that small rarely buy. Any gap of 25 points or more gets a Check tag. A person should look at those accounts.

---

## Reading the tool

### The value map

Every dot is an account. Right means more likely to win. Up means bigger deals. The dashed lines are your overall win rate and your median won deal. Drag them to test a stricter or looser cut. Every table below updates.

Shapes and colors both carry the segment: blue for likely to win, amber for hard to win, solid for big deals, hollow for small ones.

Typical deal value comes from what accounts of the same size band paid. That is one rule for every account, including accounts with no deals yet.

### Concentration risk

The curve shows how fast won revenue piles up as you add customers, largest first. A curve that shoots up on the left means a few accounts carry the business. The tool flags:

- One account at 10% or more of won revenue
- The top 10 accounts at 30% or more
- One sector at 40% or more
- 25% or more of won revenue from accounts the models rate below the line

The last one is the quiet risk. In the sample, the five largest customers are all Stretch accounts. They were won through company-wide rollouts, and the model says accounts like them lose three deals in four. Nearly half the revenue rests on wins the business should not expect to repeat.

### Pipeline opportunity

Two pools. **Open deals**, weighted by each account's win probability. **Untouched accounts**, valued at win probability times typical deal. The work list ranks untouched accounts best segment first, then by expected value.

### Key fit attributes

Each attribute gets a label:

| Label | Meaning |
|---|---|
| Both agree | Both models rank it a driver. Trust it most |
| Curved | The forest sees it, the regression misses it. The middle beats the ends, or it matters only in combination |
| Straight line | Both see it, the regression more. A steady more-is-better or more-is-worse effect |
| Weak | Real but small. A tiebreaker, never a filter |
| No signal | Scrambling it barely moves either model. Stop targeting on it |

---

## When not to trust any of it

- **Too few deals.** Under 300 closed deals, treat everything as directional. Under 100, the skill will not run.
- **You only worked some accounts.** The models learn from accounts your team chose to pursue. If you never sold to hospitals, the models know nothing about hospitals, and a hospital's score is a guess wearing a number. This is the most common way segmentation goes wrong.
- **The market moved.** A new product, a price change, a new competitor or a downturn changes who buys. Deals from before the change teach the wrong lesson. Retrain after any big change.
- **It becomes a loop.** Work only Core accounts and next year's data holds only Core accounts. The model gets more certain and less right. Keep a small share of effort on Stretch to keep learning.
- **Firmographics are not the whole story.** Intent, timing, a champion, a burning problem: none of it is in the file. The models tell you where to look, not who is ready to buy today.
- **Correlation, not cause.** Software accounts win more. That does not make Software the reason they buy. Something about Software companies fits your offer. Find out what.
- **The data is dirty.** Blank industries, stale employee counts and deals logged under the wrong account all blur the pattern. The data checks panel shows what the script found.

## Glossary

| Term | Plain meaning |
|---|---|
| Win probability | The model's estimate of the chance a deal with this account closes won |
| Win rate | The share of closed deals that were won. Open deals do not count |
| Odds multiplier | How much an attribute raises or lowers the odds of winning. 1.00x is no effect |
| Importance | How much a model's ranking skill drops when an attribute is scrambled |
| Check score (AUC) | How often a model ranks a won deal above a lost one. 0.50 is a coin flip |
| Calibration | Whether a 40% score really wins about 40% of the time |
| Held out | Scored by models that never saw that account |
| Grouped cross-validation | Training on some accounts and testing on the rest, five times, so every account gets an honest score |
| Expected value | Win probability times typical deal |
