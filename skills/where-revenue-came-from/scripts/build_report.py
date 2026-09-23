#!/usr/bin/env python3
"""Build the interactive report from analyze.py output.

Usage: python build_report.py result.json --role ceo|cro|revops|marketing --out report.html
"""
import json, sys, os

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    data = json.load(open(sys.argv[1]))
    if data.get("stop"):
        sys.exit("Analysis stopped: " + data["stop"])
    role = sys.argv[sys.argv.index("--role") + 1] if "--role" in sys.argv else "ceo"
    if role not in ("ceo", "cro", "revops", "marketing"):
        role = "ceo"
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "revenue_report.html"
    tpl = open(os.path.join(os.path.dirname(__file__), "..", "assets", "report_template.html")).read()
    blob = json.dumps(data, default=str).replace("</", "<\\/")
    html = tpl.replace("/*__DATA__*/null", blob).replace('/*__ROLE__*/"ceo"', json.dumps(role))
    open(out, "w").write(html)
    print("Report written to " + out)

if __name__ == "__main__":
    main()
