# The Cold Take Skills

Free Claude skills for B2B revenue teams, one new skill each month. From [The Cold Take](https://www.marketingsystemsguild.com) by Marketing Systems Guild.

Each skill does one job with your own data and gives a straight answer. Nothing is sent to us. The analysis runs inside your Claude session.

## The skills

| Skill | The question it answers | Released |
|---|---|---|
| [Revenue by Channel](docs/revenue-by-channel.md) | Which channels actually turn into closed revenue, and where should the next dollar go? | October 2026 |

## How do I install a skill?

1. Download the skill's zip from the [latest release](../../releases/latest).
2. In Claude, go to **Customize > Skills**, click **+**, choose **Create skill**, then **Upload a skill**.
3. Turn on code execution in your Claude settings. Skills need it.

Skills work on every Claude plan, Free included. In Claude Code, unzip into `~/.claude/skills/` instead.

## What is in this repo?

```
skills/       the skills themselves, one folder each, exactly what gets zipped
docs/         a guide per skill, with screenshots
examples/     sample data to try each skill on, plus a sample output
tests/        test data, independent answer keys and regression tests
tools/        build_zips.py packages every skill into dist/
```

## For contributors

```
python tests/revenue-by-channel/test_analyze.py   # regression tests, standard library only
python tools/build_zips.py                        # builds dist/<skill>.zip and checks each SKILL.md
```

Found a bug or a CRM export the skill cannot read? Open an issue with the column headers (no customer data).

## License

MIT. Use it, change it, share it.

---
Built by Marketing Systems Guild. Turning strangers into clients.
