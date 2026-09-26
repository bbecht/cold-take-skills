# Answer key: planted patterns

Written from the generator (`examples/customer-segmentation/generate_sample.py`), not from the skill's output. Every test file except test4 comes from that generator with a different seed. A working model must recover each pattern on every file.

## What the generator plants

Each account's chance of winning a deal is set on the log-odds scale:

| Attribute | Planted effect on log-odds |
|---|---|
| Base | -0.35 |
| Sector | Software +0.9, Healthcare +0.6, Financial services +0.2, Manufacturing 0, Professional services -0.1, Telecommunications -0.3, Education -0.6, Retail -0.9 |
| Employees | 0.9 - 1.1 x (log10(employees) - 2.8) squared. Peaks near 630 employees |
| Parent company | -0.6 when owned by a parent |
| Country | United States 0, Canada 0, United Kingdom -0.5, Germany, Australia, Brazil, Japan -0.7 |
| Year established | 0. Pure noise |
| Revenue | 0. Moves with employees (employees x 0.12 to 0.40, in $M) |
| Unexplained | Random, standard deviation 0.35, per account |

Five whales (the largest account in five different sectors) get 8 deals each at an 80% win rate, sold as company-wide rollouts at 1.8 to 2.6 times the Enterprise list price.

## What the tests check

| Check | Why it follows from the plant |
|---|---|
| Top two sectors by regression odds are Software and Healthcare | Largest positive sector effects |
| Bottom two are Retail and Education | Largest negative sector effects |
| Employees reads Curved | The effect is a hill. A straight line cannot fit it, a forest can |
| 200 to 999 employees wins more than 1 to 49 and more than 5,000+ | The hill peaks near 630 |
| Year founded reads No signal | Planted at zero |
| Parent-owned wins less than independent | Planted at -0.6 |
| Forest check score beats the regression's, and is 0.66 or higher | The curve costs the regression ranking skill |
| On test1, the top five revenue accounts sit below the probability line | The whales are large, so the models rate them poorly, yet they won often |
| On test1, 25% or more of won revenue is off-fit | The whales' rollout revenue |
