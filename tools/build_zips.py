"""Build one uploadable zip per skill into dist/.

Usage (repo root):  python tools/build_zips.py

Claude expects the zip to contain a single folder named after the skill, with SKILL.md at its top.
"""
import os, re, sys, zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILLS, DIST = os.path.join(ROOT, "skills"), os.path.join(ROOT, "dist")
SKIP = {"__pycache__", ".DS_Store"}

def check(folder, name):
    md = open(os.path.join(folder, "SKILL.md"), encoding="utf-8").read()
    m = re.search(r"^---\s*\nname:\s*(.+?)\s*\ndescription:\s*(.+?)\s*\n---", md, re.S)
    if not m: sys.exit(f"{name}: SKILL.md frontmatter needs name and description")
    if m.group(1) != name: sys.exit(f"{name}: frontmatter name '{m.group(1)}' must match the folder name")
    if len(m.group(2)) > 1024: sys.exit(f"{name}: description over 1024 characters")
    for root, _, files in os.walk(folder):
        for f in files:
            if f.endswith((".md", ".html", ".py")) and chr(0x2014) in open(os.path.join(root, f), encoding="utf-8").read():
                sys.exit(f"{name}: em-dash found in {f}")

def build(name):
    folder = os.path.join(SKILLS, name); check(folder, name)
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, name + ".zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(folder):
            dirs[:] = sorted(d for d in dirs if d not in SKIP)
            # explicit folder entries, so every unzip tool recreates the subfolders
            rel = os.path.relpath(root, folder).replace(os.sep, "/")
            z.writestr(name + "/" if rel == "." else f"{name}/{rel}/", "")
            for f in files:
                if f in SKIP or f.endswith(".pyc"): continue
                p = os.path.join(root, f)
                z.write(p, os.path.join(name, os.path.relpath(p, folder)))
    print("built", os.path.relpath(out, ROOT))

if __name__ == "__main__":
    for n in sorted(os.listdir(SKILLS)):
        if os.path.isfile(os.path.join(SKILLS, n, "SKILL.md")): build(n)
