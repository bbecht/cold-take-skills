"""Regression tests for revenue-by-channel.

Run from the repo root:  python tests/revenue-by-channel/test_analyze.py

Each test file's expected output was checked by hand against an answer key built
independently of the skill (see answer_keys/). These tests stop the numbers drifting.
"""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "skills", "revenue-by-channel", "scripts"))
import analyze  # noqa: E402

KEYS = ("new_business", "renewals_excluded", "by_source", "channel_detail", "data_quality",
        "no_source_share_of_revenue", "vague_source_share_of_revenue", "months_covered")

class TestAnalyze(unittest.TestCase):
    pass

def make(name):
    def test(self):
        got = analyze.analyze(os.path.join(HERE, "data", name + ".csv"))
        with open(os.path.join(HERE, "expected", name + ".json")) as fh:
            want = json.load(fh)
        got = json.loads(json.dumps({k: got[k] for k in KEYS}, default=str))
        for k in KEYS:
            self.assertEqual(got[k], want[k], f"{name}: {k} changed")
    return test

for f in sorted(os.listdir(os.path.join(HERE, "data"))):
    n = f[:-4]
    setattr(TestAnalyze, "test_" + n, make(n))

class TestRules(unittest.TestCase):
    def test_no_guessing_paid_search_from_search_terms(self):
        # A blank campaign with "brand strategy consultant" as the search term must stay Unclassified
        self.assertEqual(analyze.classify("Paid Search", "", "Paid Search"), analyze.UNCLASSIFIED)
    def test_nonbrand_beats_brand(self):
        self.assertEqual(analyze.classify("Paid Search", "google-search-nonbrand-x-202601", ""), "Non-brand")
    def test_event_from_source_label(self):
        self.assertEqual(analyze.classify("Events", "", "Trade Show"), "Trade show")

if __name__ == "__main__":
    unittest.main(verbosity=2)
