"""Regression tests for customer-segmentation.

Run from the repo root:  python tests/customer-segmentation/test_segment.py
Needs numpy, pandas and scikit-learn.

Three layers:
  1. Counts, data checks and concentration are recomputed here with the csv module alone,
     independent of the skill, and must match exactly.
  2. The models must recover the patterns planted in the generator (answer_keys/planted_patterns.md).
  3. Snapshots in expected/ stop the numbers drifting. Model scores get a tolerance, because a random
     forest's exact scores shift between scikit-learn versions. Checked on scikit-learn 1.7.2, 1.8.0 and 1.9.1.
"""
import csv, json, os, re, subprocess, sys, tempfile, unittest
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPTS = os.path.join(ROOT, "skills", "customer-segmentation", "scripts")
sys.path.insert(0, SCRIPTS)
import segment  # noqa: E402

D = lambda f: os.path.join(HERE, "data", f)
CASES = {
    "test1_two_files": (D("test1_deals.csv"), D("test1_accounts.csv")),
    "test2_hubspot_single": (D("test2_hubspot_single.csv"), None),
    "test3_messy": (D("test3_messy_deals.csv"), D("test3_messy_accounts.csv")),
}
EXACT = ("counts", "data_quality", "stage_mapping", "value_rule")
CONC_EXACT = ("won_revenue", "customers", "top_1_share", "top_5_share", "top_10_share",
              "accounts_to_half", "accounts_to_80pct", "effective_customers")
AUC_TOL, SEG_TOL = 0.03, 0.05  # SEG_TOL: share of all accounts a segment may move
_cache = {}


def run(name):
    if name not in _cache:
        _cache[name] = json.loads(json.dumps(segment.analyze(*CASES[name]), default=str))
    return _cache[name]


def independent(deals_path, accounts_path, acct_col, stage_col, value_col, id_col, won="won", lost="lost"):
    """Plain csv recount: dedupe on id, drop blank and unknown accounts, parse text amounts."""
    def num(v):
        s = v.strip().lower().replace(",", "").replace("$", "")
        if not s: return 0.0
        return float(s[:-1]) * 1000 if s.endswith("k") else float(s)
    known = None
    if accounts_path:
        with open(accounts_path, newline="", encoding="utf-8") as fh:
            known = {r["account"].strip() for r in csv.DictReader(fh)}
    seen, closed, won_n, rev = set(), 0, 0, defaultdict(float)
    with open(deals_path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r[id_col] in seen: continue
            seen.add(r[id_col])
            a = r[acct_col].strip()
            if not a or (known is not None and a not in known): continue
            st = r[stage_col].strip().lower()
            if won in st:
                closed += 1; won_n += 1
                if num(r[value_col]) > 0: rev[a] += num(r[value_col])
            elif lost in st:
                closed += 1
    tot = sum(rev.values())
    shares = sorted((v / tot for v in rev.values()), reverse=True)
    cum, half = 0.0, None
    for i, s in enumerate(shares):
        cum += s
        if half is None and cum >= 0.5: half = i + 1
    return {"closed": closed, "won": won_n, "won_revenue": round(tot), "customers": len(rev),
            "top_10_share": round(sum(shares[:10]), 3), "accounts_to_half": half}


class TestIndependentCounts(unittest.TestCase):
    def check(self, name, *cols, **kw):
        got, key = run(name), independent(*CASES[name], *cols, **kw)
        self.assertEqual(got["counts"]["closed_deals"], key["closed"])
        self.assertEqual(got["counts"]["won"], key["won"])
        self.assertEqual(got["concentration"]["won_revenue"], key["won_revenue"])
        self.assertEqual(got["concentration"]["customers"], key["customers"])
        self.assertEqual(got["concentration"]["top_10_share"], key["top_10_share"])
        self.assertEqual(got["concentration"]["accounts_to_half"], key["accounts_to_half"])

    def test_two_files(self):
        self.check("test1_two_files", "account", "deal_stage", "close_value", "opportunity_id")

    def test_single_file(self):
        self.check("test2_hubspot_single", "Associated Company", "Deal Stage", "Amount", "Record ID")

    def test_messy(self):
        self.check("test3_messy", "account", "deal_stage", "close_value", "opportunity_id")


class TestMessyFile(unittest.TestCase):
    """Every problem planted by make_test_data.py, counted by hand. See answer_keys/test3_messy.md."""
    def test_planted_problems(self):
        dq = run("test3_messy")["data_quality"]
        self.assertEqual(dq["duplicate_deals"], 5)
        self.assertEqual(dq["deals_unmatched_account"], 4)
        self.assertEqual(dq["unmatched_examples"], ["Nowhere Analytics", "Phantom Freight"])
        self.assertEqual(dq["deals_without_account"], 2)
        self.assertEqual(dq["text_values_parsed"], 8)
        self.assertEqual(dq["won_without_value"], 3)
        self.assertEqual(dq["blank_attributes"], {"Sector": 6, "Employees": 4})
        self.assertIn("Iceland", dq["grouped_as_other"]["Country"])


class TestPlantedPatterns(unittest.TestCase):
    """The answer key: what the generator planted, and the models must find."""
    def attr(self, res, key):
        return next(f for f in res["fit_attributes"] if f["key"] == key)

    def test_patterns(self):
        for name in CASES:
            res = run(name)
            with self.subTest(name):
                sec = self.attr(res, "sector")
                odds = sorted((l for l in sec["levels"] if l["lr_odds"] is not None and l["deals"] >= 30),
                              key=lambda l: -l["lr_odds"])
                self.assertEqual({l["level"] for l in odds[:2]}, {"Software", "Healthcare"})
                self.assertEqual({l["level"] for l in odds[-2:]}, {"Retail", "Education"})
                emp = self.attr(res, "employees")
                self.assertEqual(emp["signal"], "curved", "size sweet spot must read as a curve")
                rates = {l["level"]: l["win_rate"] for l in emp["levels"]}
                self.assertGreater(rates["200 to 999"], rates["1 to 49"])
                self.assertGreater(rates["200 to 999"], rates["5,000+"])
                self.assertEqual(self.attr(res, "founded")["signal"], "none", "year founded is noise")
                par = {l["level"]: l["win_rate"] for l in self.attr(res, "parent")["levels"]}
                self.assertLess(par["Yes"], par["No"])
                mh = res["model_health"]
                self.assertGreater(mh["auc_forest"], mh["auc_logistic"], "forest must beat the straight line here")
                self.assertGreaterEqual(mh["auc_forest"], 0.66)

    def test_whales_do_not_fit(self):
        # The five planted whales won about 80% of their deals, but their firmographics say they should not.
        # A model that learned the pattern scores them well under what they actually did. The exact score sits
        # near the probability line and moves between scikit-learn versions, so the test checks the gap instead.
        res = run("test1_two_files")
        acc = {a["account"]: a for a in res["accounts"]}
        top = [acc[t["account"]] for t in res["concentration"]["top_accounts"][:5]]
        gaps = [a["won"] / (a["won"] + a["lost"]) - a["p"] for a in top]
        self.assertTrue(all(a["p"] < 0.5 for a in top), [a["p"] for a in top])
        self.assertGreaterEqual(sum(gaps) / len(gaps), 0.3, gaps)


class TestRules(unittest.TestCase):
    def test_no_leakage(self):
        res = run("test1_two_files")
        for a in res["accounts"]:
            if a["won"] + a["lost"]:
                self.assertEqual(a["scored_by"], "held out", a["account"])

    def test_segments_follow_lines(self):
        res = run("test1_two_files")
        pl, vl = res["segment_rule"]["probability_line"], res["segment_rule"]["value_line"]
        for a in res["accounts"]:
            want = ("Core" if a["value"] >= vl else "Volume") if a["p"] >= pl else ("Stretch" if a["value"] >= vl else "Deprioritize")
            self.assertEqual(a["segment"], want, a["account"])

    def test_shares_add_up(self):
        for name in CASES:
            self.assertAlmostEqual(sum(s["share_of_revenue"] for s in run(name)["segments"]), 1.0, delta=0.005)

    def test_revenue_in_dollars_is_banded_in_millions(self):
        self.assertEqual(run("test2_hubspot_single")["data_quality"]["revenue_unit"], "dollars, converted to millions")

    def test_stop_when_too_small(self):
        res = segment.analyze(D("test4_tiny_deals.csv"), D("test4_tiny_accounts.csv"))
        self.assertIn("Not enough history", res["stop"])

    def test_stop_when_no_won_or_lost(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
            p = os.path.join(t, "d.csv")
            with open(p, "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(["account", "deal_stage", "close_value", "sector"])
                for i in range(150): w.writerow([f"A{i}", "Stage 3" if i % 2 else "Stage 9", 100, "X"])
            res = segment.analyze(p)
            self.assertIn("No stages read as won or lost", res["stop"])
            self.assertEqual(res["stages_found"], ["Stage 3", "Stage 9"])

    def test_numbers_and_stages(self):
        self.assertEqual(segment.to_number("$45,000"), 45000)
        self.assertEqual(segment.to_number("45k"), 45000)
        self.assertEqual(segment.to_number("1.2M"), 1200000)
        self.assertEqual(segment.classify_stage("Closed Won"), "won")
        self.assertEqual(segment.classify_stage("Closed Lost"), "lost")
        self.assertEqual(segment.classify_stage("Contract Sent"), "open")

    def test_tool_builds(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as t:
            j, h = os.path.join(t, "s.json"), os.path.join(t, "s.html")
            with open(j, "w") as fh: json.dump(run("test1_two_files"), fh)
            subprocess.run([sys.executable, os.path.join(SCRIPTS, "build_tool.py"), j, "--role", "cro", "--out", h],
                           check=True, capture_output=True)
            with open(h, encoding="utf-8") as fh: html = fh.read()
            self.assertNotIn("/*__DATA__*/", html)
            self.assertIn('const START_ROLE = "cro"', html)
            self.assertEqual(len(re.findall(r"</script>", html)), 1)


class TestSnapshots(unittest.TestCase):
    pass


def make(name):
    def test(self):
        got = run(name)
        with open(os.path.join(HERE, "expected", name + ".json")) as fh:
            want = json.load(fh)
        for k in EXACT:
            self.assertEqual(got[k], want[k], f"{name}: {k} changed")
        for k in CONC_EXACT:
            self.assertEqual(got["concentration"][k], want["concentration"][k], f"{name}: concentration {k} changed")
        for k in ("auc_logistic", "auc_forest"):
            self.assertAlmostEqual(got["model_health"][k], want["model_health"][k], delta=AUC_TOL)
        for g, w in zip(got["segments"], want["segments"]):
            tol = max(12, round(SEG_TOL * got["counts"]["accounts"]))
            self.assertLessEqual(abs(g["accounts"] - w["accounts"]), tol, f"{name}: {g['segment']} moved")
    return test


for n in CASES:
    setattr(TestSnapshots, "test_" + n, make(n))


def snapshot():
    """Write expected/ from the current code. Only after checking the numbers by hand."""
    os.makedirs(os.path.join(HERE, "expected"), exist_ok=True)
    for n in CASES:
        r = run(n)
        keep = {k: r[k] for k in EXACT}
        keep["concentration"] = {k: r["concentration"][k] for k in CONC_EXACT}
        keep["model_health"] = {k: r["model_health"][k] for k in ("auc_logistic", "auc_forest", "primary", "verdict")}
        keep["segments"] = [{k: s[k] for k in ("segment", "accounts", "share_of_revenue")} for s in r["segments"]]
        with open(os.path.join(HERE, "expected", n + ".json"), "w") as fh:
            json.dump(keep, fh, indent=1)
    print("snapshots written")


if __name__ == "__main__":
    if "--snapshot" in sys.argv:
        snapshot()
    else:
        unittest.main(verbosity=2)
