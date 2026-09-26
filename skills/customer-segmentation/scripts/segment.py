#!/usr/bin/env python3
"""Customer Segmentation: fit models, value map, concentration and pipeline.

Usage:
  python segment.py --deals deals.csv [--accounts accounts.csv] [--json result.json]
                    [--won "Stage A,Stage B"] [--lost "Stage C"] [--features "col1,col2"]

Two input shapes:
  1. Two files. An accounts file with firmographics, plus a deals file that names the account
     on every row (the Maven CRM Sales Opportunities layout, or any CRM export like it).
  2. One file. A deal export where every row also carries the company's firmographics.

Logistic regression and random forest each predict the chance an account wins, from its
firmographics alone. The model that ranks held-out accounts better sets the probability. The
other is the second opinion. Every account lands in one of four segments: win probability
crossed with expected deal value. Needs numpy, pandas and scikit-learn. Deterministic: same file,
same numbers.
"""
import argparse, json, math, re, sys, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

VERSION = "1.0.0"
SEED = 42
FOLDS = 5
MIN = {"closed": 100, "won": 20, "lost": 20, "accounts": 30}     # below this: stop
WARN = {"closed": 300, "accounts": 80}                             # below this: warn
RARE = 15                                                          # closed deals a category needs
DISAGREE = 0.25                                                    # model gap that gets flagged

# ---------- column detection ----------
DEAL_COLS = {
    "id":      ["opportunity_id", "opportunity id", "deal id", "record id", "id"],
    "account": ["account", "account name", "account_name", "company", "company name",
                "associated company", "associated company name", "organization"],
    "stage":   ["deal_stage", "deal stage", "stage", "stage name", "status"],
    "value":   ["close_value", "close value", "amount", "deal amount", "amount (company currency)",
                "value", "deal value", "acv"],
    "closed":  ["close_date", "close date", "closed date", "closedate"],
    "created": ["engage_date", "engage date", "create date", "created date", "createdate"],
    "product": ["product", "product name"],
}
ACCOUNT_COLS = {
    "account":   DEAL_COLS["account"] + ["name", "record name"],  # a company export's own name column
    "sector":    ["sector", "industry", "company industry", "vertical"],
    "employees": ["employees", "number of employees", "employee count", "employee_count",
                  "headcount", "company size"],
    "revenue":   ["revenue", "annual revenue", "annual_revenue", "company revenue"],
    "country":   ["office_location", "country", "country/region", "billing country", "hq country",
                  "location", "company country"],
    "founded":   ["year_established", "year established", "year founded", "founded",
                  "founded year", "year_founded"],
    "parent":    ["subsidiary_of", "parent company", "parent account", "parent", "parent_company"],
}
FEATURES = {  # key: (label, kind)
    "sector":    ("Sector", "cat"),
    "employees": ("Employees", "log"),
    "revenue":   ("Company revenue", "log"),
    "country":   ("Country", "cat"),
    "founded":   ("Year founded", "num"),
    "parent":    ("Owned by a parent company", "bin"),
}
BANDS = {
    "employees": ([50, 200, 1000, 5000], ["1 to 49", "50 to 199", "200 to 999", "1,000 to 4,999", "5,000+"]),
    "revenue":   ([10, 50, 250, 1000], ["Under $10M", "$10M to $49M", "$50M to $249M", "$250M to $999M", "$1B+"]),
    "founded":   ([1980, 2000, 2010], ["Before 1980", "1980 to 1999", "2000 to 2009", "2010 or later"]),
}
SEGMENTS = ["Core", "Volume", "Stretch", "Deprioritize"]
SEGMENT_MEANING = {
    "Core": "Likely to win, big deals. Work these first.",
    "Volume": "Likely to win, smaller deals. Work them efficiently.",
    "Stretch": "Hard to win, big deals. Pursue on purpose, never by default.",
    "Deprioritize": "Hard to win, small deals. Stop spending here.",
}


def detect(headers, spec):
    low = {h.strip().lower(): h for h in headers}
    found = {}
    for key, options in spec.items():
        for o in options:
            if o in low:
                found[key] = low[o]; break
    if "account" in spec and "account" not in found:
        # HubSpot variants such as "Associated Company (Primary)"; never an ID column
        for h_low, h in low.items():
            if h_low.startswith("associated company") and "id" not in h_low.split():
                found["account"] = h; break
    return found


def to_number(v):
    """'$45,000' -> 45000, '45k' -> 45000, '1.2M' -> 1200000, blank -> nan."""
    if v is None or (isinstance(v, float) and math.isnan(v)): return float("nan")
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip().lower().replace(",", "").replace("$", "").replace("usd", "").strip()
    if not s: return float("nan")
    mult = 1.0
    if s.endswith("k"): mult, s = 1e3, s[:-1]
    elif s.endswith("m"): mult, s = 1e6, s[:-1]
    elif s.endswith("b"): mult, s = 1e9, s[:-1]
    try: return float(s) * mult
    except ValueError: return float("nan")


def clean_text(v):
    if v is None or (isinstance(v, float) and math.isnan(v)): return ""
    return re.sub(r"\s+", " ", str(v)).strip()


def classify_stage(stage, won=None, lost=None):
    s = clean_text(stage).lower()
    if won is not None:
        return "won" if s in won else "lost" if s in lost else "open"
    if s in ("won", "closed won", "closedwon") or re.search(r"\bwon\b", s): return "won"
    if s in ("lost", "closed lost", "closedlost") or re.search(r"\blost\b", s): return "lost"
    return "open"


def band(key, x):
    cuts, labels = BANDS[key]
    if x is None or (isinstance(x, float) and math.isnan(x)): return "(Unknown)"
    for c, lab in zip(cuts, labels):
        if x < c: return lab
    return labels[-1]


def r(x, n=3):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), n)


def money(x):
    return 0 if x is None or (isinstance(x, float) and math.isnan(x)) else int(round(float(x)))


# ---------- load ----------
def load(deals_path, accounts_path=None, won=None, lost=None, extra=None):
    dq = {"duplicate_deals": 0, "deals_without_account": 0, "deals_unmatched_account": 0,
          "unmatched_examples": [], "won_without_value": 0, "text_values_parsed": 0,
          "blank_attributes": {}, "conflicting_attributes": 0, "grouped_as_other": {}}
    deals = pd.read_csv(deals_path, dtype=str, keep_default_na=False)
    dc = detect(deals.columns, DEAL_COLS)
    missing = [k for k in ("account", "stage") if k not in dc]
    if missing:
        return None, None, {"stop": "Deals file is missing required columns: " + ", ".join(missing),
                            "columns_found": list(deals.columns)}

    # duplicates
    if "id" in dc:
        dup = deals.duplicated(subset=[dc["id"]], keep="first")
    else:
        dup = deals.duplicated(keep="first")
    dq["duplicate_deals"] = int(dup.sum())
    deals = deals[~dup].copy()

    d = pd.DataFrame({"account": deals[dc["account"]].map(clean_text),
                      "stage_raw": deals[dc["stage"]].map(clean_text)})
    d["id"] = deals[dc["id"]].map(clean_text) if "id" in dc else [f"row{i + 2}" for i in range(len(deals))]
    raw_val = deals[dc["value"]] if "value" in dc else pd.Series([""] * len(deals), index=deals.index)
    d["text_value"] = [bool(clean_text(v)) and not re.fullmatch(r"-?\d+(\.\d+)?", clean_text(v)) for v in raw_val]
    d["value"] = raw_val.map(to_number).values
    d["closed"] = deals[dc["closed"]].map(clean_text).values if "closed" in dc else ""
    won_set = {s.strip().lower() for s in won.split(",")} if won else None
    lost_set = {s.strip().lower() for s in lost.split(",")} if lost else set()
    d["status"] = d["stage_raw"].map(lambda s: classify_stage(s, won_set, lost_set))
    dq["deals_without_account"] = int((d["account"] == "").sum())
    d = d[d["account"] != ""].copy()

    # accounts
    if accounts_path:
        acc = pd.read_csv(accounts_path, dtype=str, keep_default_na=False)
        ac = detect(acc.columns, ACCOUNT_COLS)
        if "account" not in ac:
            return None, None, {"stop": "Accounts file has no account name column.",
                                "columns_found": list(acc.columns)}
        src = acc
    else:
        ac = detect(deals.columns, ACCOUNT_COLS)
        src = deals
    for col in (extra or []):
        if col not in src.columns:
            return None, None, {"stop": f"Feature column '{col}' not found.", "columns_found": list(src.columns)}
    a = pd.DataFrame({"account": src[ac["account"]].map(clean_text)})
    feats = [k for k in FEATURES if k in ac]
    for k in feats:
        a[k] = src[ac[k]].map(clean_text).values
    extra_kinds = {}
    for col in (extra or []):
        vals = src[col].map(clean_text)
        nums = vals.map(to_number)
        filled = vals[vals != ""]
        kind = "num" if len(filled) and nums[vals != ""].notna().mean() >= 0.9 else "cat"
        key = "x_" + re.sub(r"\W+", "_", col.lower()).strip("_")
        a[key] = vals.values
        extra_kinds[key] = (col, kind)
        feats.append(key)

    a = a[a["account"] != ""]
    if not accounts_path:
        # one row per account: first non-blank value; count conflicts
        rows = []
        for name, g in a.groupby("account", sort=True):
            row = {"account": name}
            for k in feats:
                vals = [v for v in g[k] if v != ""]
                row[k] = vals[0] if vals else ""
                if len(set(vals)) > 1: dq["conflicting_attributes"] += 1
            rows.append(row)
        a = pd.DataFrame(rows, columns=["account"] + feats)
    else:
        a = a.drop_duplicates(subset=["account"], keep="first")

    known = set(a["account"])
    unmatched = d[~d["account"].isin(known)]
    dq["deals_unmatched_account"] = int(len(unmatched))
    dq["unmatched_examples"] = sorted(unmatched["account"].unique())[:5]
    d = d[d["account"].isin(known)].copy()
    dq["won_without_value"] = int(((d["status"] == "won") & ~(d["value"] > 0)).sum())
    dq["text_values_parsed"] = int(d["text_value"].sum())

    # revenue in dollars (HubSpot, Salesforce) or in millions (Maven): bands are in millions
    if "revenue" in feats:
        rv = a["revenue"].map(to_number)
        if rv.notna().any() and rv.median() > 100000:
            a["revenue"] = [f"{x / 1e6:.4f}" if x == x else "" for x in rv]
            dq["revenue_unit"] = "dollars, converted to millions"
        else:
            dq["revenue_unit"] = "millions"

    spec = dict(FEATURES); spec.update(extra_kinds)
    return d, a, {"dq": dq, "features": feats, "spec": spec, "deal_columns": dc, "account_columns": ac,
                  "stages": {s: st for s, st in d.groupby("stage_raw")["status"].first().items()}}


# ---------- features ----------
def build_matrix(a, feats, spec, closed_counts, dq):
    """Model-ready frame, one row per account. Returns (frame, cat_cols, num_cols, labels)."""
    X = pd.DataFrame(index=a["account"].values)
    cat_cols, num_cols, labels = [], [], {}
    for k in feats:
        label, kind = spec[k]
        vals = a[k].values
        blanks = int(sum(1 for v in vals if v == ""))
        if blanks and kind != "bin": dq["blank_attributes"][label] = blanks  # blank parent means none
        if kind in ("log", "num"):
            x = np.array([to_number(v) for v in vals], dtype=float)
            if kind == "log":
                x = np.where(x > 0, x, np.nan)
                x = np.log10(x)
            med = np.nanmedian(x) if np.isfinite(x).any() else 0.0
            X[k] = np.where(np.isnan(x), med, x)
            num_cols.append(k)
        elif kind == "bin":
            X[k] = ["Yes" if v else "No" for v in vals]
            cat_cols.append(k)
        else:
            col = [v if v else "(Unknown)" for v in vals]
            # categories with too few closed deals get grouped, so the models do not memorize them
            counts = {}
            for acct, v in zip(a["account"].values, col):
                counts[v] = counts.get(v, 0) + closed_counts.get(acct, 0)
            small = sorted(c for c, n in counts.items() if n < RARE)
            if small:
                dq["grouped_as_other"][label] = small
                col = ["Other" if v in small else v for v in col]
            X[k] = col
            cat_cols.append(k)
        labels[k] = label
    return X, cat_cols, num_cols, labels


def pipelines(cat_cols, num_cols):
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    try:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # scikit-learn before 1.2
        ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)
    pre_lr = ColumnTransformer([("num", StandardScaler(), num_cols), ("cat", ohe, cat_cols)])
    pre_rf = ColumnTransformer([("num", "passthrough", num_cols), ("cat", ohe, cat_cols)])
    lr = Pipeline([("pre", pre_lr), ("model", LogisticRegression(C=1.0, max_iter=5000))])
    rf = Pipeline([("pre", pre_rf), ("model", RandomForestClassifier(
        n_estimators=300, min_samples_leaf=15, max_features="sqrt", random_state=SEED, n_jobs=1))])
    return lr, rf


def auc(y, p):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p)) if len(set(y)) == 2 else float("nan")


# ---------- analysis ----------
def analyze(deals_path, accounts_path=None, won=None, lost=None, extra=None):
    from sklearn.base import clone
    from sklearn.inspection import permutation_importance
    from sklearn.model_selection import GroupKFold

    d, a, meta = load(deals_path, accounts_path, won, lost, extra)
    if d is None:
        return meta
    dq, feats, spec = meta["dq"], meta["features"], meta["spec"]
    out = {"version": VERSION, "input": {"deals_file": deals_path, "accounts_file": accounts_path,
                                         "deal_columns": meta["deal_columns"],
                                         "account_columns": meta["account_columns"]},
           "stage_mapping": meta["stages"], "warnings": []}
    if not feats:
        out["stop"] = ("No firmographic columns found. Need at least one of: sector or industry, employees, "
                       "revenue, country, year founded, parent company.")
        return out

    closed = d[d["status"].isin(["won", "lost"])].copy()
    n_won, n_lost = int((closed["status"] == "won").sum()), int((closed["status"] == "lost").sum())
    closed_counts = closed.groupby("account").size().to_dict()
    n_acc_closed = len(closed_counts)
    out["counts"] = {"accounts": int(len(a)), "deals": int(len(d)), "closed_deals": int(len(closed)),
                     "won": n_won, "lost": n_lost, "open_deals": int((d["status"] == "open").sum()),
                     "accounts_with_closed_deals": n_acc_closed,
                     "customers": int(closed[closed["status"] == "won"]["account"].nunique()),
                     "untouched_accounts": int(len(set(a["account"]) - set(d["account"])))}
    if n_won == 0 or n_lost == 0:
        out["stop"] = "No stages read as won or lost. Rerun with --won and --lost."
        out["stages_found"] = sorted(d["stage_raw"].unique().tolist())
        return out
    short = [f"{k} ({v} needed)" for k, v, have in
             (("closed deals", MIN["closed"], len(closed)), ("won deals", MIN["won"], n_won),
              ("lost deals", MIN["lost"], n_lost), ("accounts with closed deals", MIN["accounts"], n_acc_closed))
             if have < v]
    if short:
        out["stop"] = "Not enough history to train a model. Short on: " + ", ".join(short) + "."
        out["data_quality"] = dq
        return out
    if len(closed) < WARN["closed"] or n_acc_closed < WARN["accounts"]:
        out["warnings"].append(f"Small sample: {len(closed)} closed deals across {n_acc_closed} accounts. "
                               "Treat segments as directional.")

    X_acc, cat_cols, num_cols, labels = build_matrix(a, feats, spec, closed_counts, dq)
    base = n_won / len(closed)

    # training rows: one per closed deal, carrying its account's attributes
    Xc = X_acc.loc[closed["account"].values].reset_index(drop=True)
    y = (closed["status"].values == "won").astype(int)
    groups = closed["account"].values
    lr, rf = pipelines(cat_cols, num_cols)

    # grouped cross-validation: an account's deals never sit in both training and test
    k = min(FOLDS, n_acc_closed)
    oof_lr, oof_rf = np.zeros(len(y)), np.zeros(len(y))
    imp_lr = {f: [] for f in X_acc.columns}
    imp_rf = {f: [] for f in X_acc.columns}
    for tr, te in GroupKFold(n_splits=k).split(Xc, y, groups):
        if len(set(y[tr])) < 2: continue
        m_lr, m_rf = clone(lr).fit(Xc.iloc[tr], y[tr]), clone(rf).fit(Xc.iloc[tr], y[tr])
        oof_lr[te] = m_lr.predict_proba(Xc.iloc[te])[:, 1]
        oof_rf[te] = m_rf.predict_proba(Xc.iloc[te])[:, 1]
        if len(set(y[te])) == 2:
            for model, store in ((m_lr, imp_lr), (m_rf, imp_rf)):
                pi = permutation_importance(model, Xc.iloc[te], y[te], scoring="roc_auc",
                                            n_repeats=5, random_state=SEED, n_jobs=1)
                for f, v in zip(Xc.columns, pi.importances_mean):
                    store[f].append(float(v))
    auc_lr, auc_rf = auc(y, oof_lr), auc(y, oof_rf)
    # the model that ranked held-out accounts better sets the probability; the other is the second opinion
    primary = "forest" if auc_rf > auc_lr else "logistic"
    oof = oof_rf if primary == "forest" else oof_lr
    auc_pr = max(auc_lr, auc_rf)

    # full fit, for accounts with no closed deals
    f_lr, f_rf = clone(lr).fit(Xc, y), clone(rf).fit(Xc, y)
    p_lr_all = f_lr.predict_proba(X_acc)[:, 1]
    p_rf_all = f_rf.predict_proba(X_acc)[:, 1]
    oof_acc = pd.DataFrame({"account": groups, "lr": oof_lr, "rf": oof_rf}).groupby("account").mean()

    # ---- model health ----
    verdict = ("usable" if auc_pr >= 0.70 else "directional" if auc_pr >= 0.60 else "not usable")
    bands = [0, 0.2, 0.4, 0.6, 0.8, 1.0001]
    calib = []
    for lo, hi in zip(bands[:-1], bands[1:]):
        m = (oof >= lo) & (oof < hi)
        if m.sum():
            calib.append({"band": f"{int(lo * 100)}% to {min(100, int(round(hi * 100)))}%", "deals": int(m.sum()),
                          "predicted": r(oof[m].mean()), "actual": r(y[m].mean())})
    out["model_health"] = {
        "auc_logistic": r(auc_lr), "auc_forest": r(auc_rf), "primary": primary, "auc_primary": r(auc_pr),
        "verdict": verdict,
        "folds": k, "method": "Grouped cross-validation by account. Every score for an account with "
                              "history comes from models that never saw that account.",
        "calibration": calib, "base_win_rate": r(base)}
    if verdict == "not usable":
        out["warnings"].append("The models rank accounts barely better than a coin flip (AUC "
                               f"{auc_pr:.2f}). Use the win rate tables, not the segments.")

    # ---- fit attributes ----
    lr_model = f_lr.named_steps["model"]
    names = f_lr.named_steps["pre"].get_feature_names_out()
    coef = dict(zip(names, lr_model.coef_[0]))
    fit = []
    cw = closed.assign(win=y)
    for f in X_acc.columns:
        label, kind = spec[f]
        li = float(np.mean(imp_lr[f])) if imp_lr[f] else 0.0
        ri = float(np.mean(imp_rf[f])) if imp_rf[f] else 0.0
        if kind in ("log", "num"):
            raw = a.set_index("account")[f].map(to_number)
            lv = raw.map(lambda x: band(f, x) if f in BANDS else x)
            if f not in BANDS:  # user-added numeric: quartile bands
                q = pd.qcut(raw.rank(method="first"), 4, labels=["Lowest quarter", "Second quarter",
                                                                 "Third quarter", "Highest quarter"])
                lv = q.astype(str)
            order = BANDS[f][1] + ["(Unknown)"] if f in BANDS else ["Lowest quarter", "Second quarter",
                                                                  "Third quarter", "Highest quarter"]
            odds_sd = math.exp(coef.get(f"num__{f}", 0.0))
        else:
            lv = X_acc[f]
            order = None
            odds_sd = None
        level = cw["account"].map(lv)
        levels = []
        for name, g in cw.groupby(level):
            lr_odds = math.exp(coef[f"cat__{f}_{name}"]) if kind in ("cat", "bin") and f"cat__{f}_{name}" in coef else None
            levels.append({"level": str(name), "deals": int(len(g)), "won": int(g["win"].sum()),
                           "win_rate": r(g["win"].mean()), "lift": r(g["win"].mean() / base, 2),
                           "lr_odds": r(lr_odds, 2)})
        if order:
            levels.sort(key=lambda x: order.index(x["level"]) if x["level"] in order else 99)
        else:
            levels.sort(key=lambda x: -x["win_rate"])
        fit.append({"key": f, "label": label, "kind": kind, "importance_logistic": r(max(li, 0.0), 4),
                    "importance_forest": r(max(ri, 0.0), 4), "logistic_odds_per_sd": r(odds_sd, 2),
                    "levels": levels})
    tot_l = sum(x["importance_logistic"] for x in fit) or 1
    tot_r = sum(x["importance_forest"] for x in fit) or 1
    for x in fit:
        x["share_logistic"] = r(x["importance_logistic"] / tot_l)
        x["share_forest"] = r(x["importance_forest"] / tot_r)
        il, ir = x["importance_logistic"], x["importance_forest"]
        # thresholds in check-score points: 0.015 is 1.5 points. Below that, sampling noise can produce it
        if max(il, ir) < 0.015:
            x["signal"] = "none"
        elif ir >= 0.02 and ir > 2 * il:
            x["signal"] = "curved"  # the forest sees it, the straight line misses it
        elif il >= 0.02 and il > 2 * ir:
            x["signal"] = "linear"
        elif max(il, ir) < 0.02:
            x["signal"] = "weak"
        else:
            x["signal"] = "agree"
    fit.sort(key=lambda x: -(x["importance_logistic"] + x["importance_forest"]))
    out["fit_attributes"] = fit

    # ---- value ----
    won_deals = closed[(closed["status"] == "won") & (closed["value"] > 0)]
    if not len(won_deals):
        out["stop"] = "Won deals carry no deal value. The value map needs amounts on won deals."
        return out
    median_won = float(won_deals["value"].median())
    vkey = "employees" if "employees" in feats else "revenue" if "revenue" in feats else None
    acct_band = {}
    band_value, band_n = {}, {}
    if vkey:
        raw = a.set_index("account")[vkey].map(to_number)
        acct_band = raw.map(lambda x: band(vkey, x)).to_dict()
        for b, g in won_deals.groupby(won_deals["account"].map(acct_band)):
            band_n[b] = int(len(g))
            if len(g) >= 5 and b != "(Unknown)":
                band_value[b] = float(g["value"].median())
    else:
        out["warnings"].append("No employee or revenue column. Every account gets the same deal value, "
                               "so the value map splits on probability only.")
    out["value_rule"] = {
        "basis": FEATURES[vkey][0] if vkey else None, "median_won_deal": money(median_won),
        "by_band": [{"band": b, "won_deals": band_n.get(b, 0),
                     "value": money(band_value.get(b, median_won)),
                     "fallback": b not in band_value}
                    for b in (BANDS[vkey][1] if vkey else [])]}

    # ---- accounts ----
    stats = d.groupby(["account", "status"]).size().unstack(fill_value=0)
    won_rev = won_deals.groupby("account")["value"].sum()
    open_d = d[d["status"] == "open"]
    # lines are compared at the precision the tool shows, so the tool and this script always agree
    p_line = round(base, 3)
    v_line = money(median_won)
    rows = []
    for i, name in enumerate(X_acc.index):
        if name in oof_acc.index:
            plr, prf, basis = oof_acc.at[name, "lr"], oof_acc.at[name, "rf"], "held out"
        else:
            plr, prf, basis = p_lr_all[i], p_rf_all[i], "full model"
        p = prf if primary == "forest" else plr
        val = band_value.get(acct_band.get(name), median_won) if vkey else median_won
        st = stats.loc[name] if name in stats.index else {}
        nw, nl, no = int(st.get("won", 0)), int(st.get("lost", 0)), int(st.get("open", 0))
        ov = open_d[open_d["account"] == name]["value"]
        open_val = float(sum(v if v > 0 else val for v in ov)) if no else 0.0
        hi_p, hi_v = round(float(p), 3) >= p_line, money(val) >= v_line
        seg = ("Core" if hi_v else "Volume") if hi_p else ("Stretch" if hi_v else "Deprioritize")
        status = ("customer" if nw else "worked, not won" if nl else "in pipeline" if no else "untouched")
        row = {"account": name, "segment": seg, "status": status, "p": r(p), "p_logistic": r(plr),
               "p_forest": r(prf), "scored_by": basis, "value": money(val), "expected": money(p * val),
               "won": nw, "lost": nl, "open": no, "won_revenue": money(won_rev.get(name, 0.0)),
               "open_value": money(open_val), "weighted_open": money(open_val * p),
               "disagree": bool(abs(plr - prf) >= DISAGREE)}
        for f in feats:
            row[f] = a.loc[a["account"] == name, f].values[0]
        rows.append(row)
    rows.sort(key=lambda x: (-x["expected"], x["account"]))
    out["accounts"] = rows
    out["segment_rule"] = {"probability_line": r(p_line), "value_line": money(v_line),
                           "probability_basis": "Overall win rate on closed deals",
                           "value_basis": "Median won deal"}

    # ---- segments ----
    total_rev = float(won_deals["value"].sum())
    seg_out = []
    for s in SEGMENTS:
        rs = [x for x in rows if x["segment"] == s]
        names_s = {x["account"] for x in rs}
        cs = closed[closed["account"].isin(names_s)]
        ws = won_deals[won_deals["account"].isin(names_s)]
        unt = [x for x in rs if x["status"] == "untouched"]
        seg_out.append({
            "segment": s, "meaning": SEGMENT_MEANING[s], "accounts": len(rs),
            "customers": sum(1 for x in rs if x["status"] == "customer"),
            "closed_deals": int(len(cs)), "win_rate": r((cs["status"] == "won").mean()) if len(cs) else None,
            "won_revenue": money(ws["value"].sum()), "share_of_revenue": r(ws["value"].sum() / total_rev),
            "avg_won_deal": money(ws["value"].mean()) if len(ws) else 0,
            "open_deals": sum(x["open"] for x in rs), "open_value": money(sum(x["open_value"] for x in rs)),
            "weighted_open": money(sum(x["weighted_open"] for x in rs)),
            "untouched": len(unt), "untouched_expected": money(sum(x["expected"] for x in unt)),
            "disagree": sum(1 for x in rs if x["disagree"])})
    out["segments"] = seg_out

    # ---- concentration ----
    rev = won_deals.groupby("account")["value"].sum().sort_values(ascending=False)
    shares = rev / total_rev
    cum = shares.cumsum().values
    n_c = len(rev)
    top10pct = max(1, int(math.ceil(n_c * 0.10)))
    sector_share = {}
    if "sector" in feats:
        sec = won_deals["account"].map(a.set_index("account")["sector"]).replace("", "(Unknown)")
        sector_share = (won_deals.groupby(sec.values)["value"].sum() / total_rev).sort_values(ascending=False)
    seg_of = {x["account"]: x["segment"] for x in rows}
    off_fit = sum(v for k2, v in rev.items() if seg_of.get(k2) in ("Stretch", "Deprioritize")) / total_rev
    conc = {
        "won_revenue": money(total_rev), "customers": n_c,
        "top_1_share": r(shares.iloc[0]), "top_5_share": r(shares.iloc[:5].sum()),
        "top_10_share": r(shares.iloc[:10].sum()), "top_10pct_accounts": top10pct,
        "top_10pct_share": r(shares.iloc[:top10pct].sum()),
        "accounts_to_half": int(np.searchsorted(cum, 0.5) + 1),
        "accounts_to_80pct": int(np.searchsorted(cum, 0.8) + 1),
        "effective_customers": r(1 / float((shares ** 2).sum()), 1),
        "off_fit_share": r(off_fit),
        "top_accounts": [{"account": k2, "won_revenue": money(v), "share": r(v / total_rev),
                          "segment": seg_of.get(k2)} for k2, v in rev.iloc[:10].items()],
        "curve": [r(x) for x in cum],
        "by_sector": [{"sector": s2, "share": r(v)} for s2, v in (sector_share.items() if len(sector_share) else [])],
    }
    flags = []
    if conc["top_1_share"] >= 0.10:
        flags.append(f"One account holds {conc['top_1_share']:.0%} of won revenue.")
    if conc["top_10_share"] >= 0.30:
        flags.append(f"The top 10 accounts hold {conc['top_10_share']:.0%} of won revenue.")
    if len(sector_share) and sector_share.iloc[0] >= 0.40:
        flags.append(f"{sector_share.index[0]} holds {sector_share.iloc[0]:.0%} of won revenue.")
    if off_fit >= 0.25:
        flags.append(f"{off_fit:.0%} of won revenue comes from accounts the models rate below the line. "
                     "Revenue rests on accounts that do not fit.")
    conc["flags"] = flags
    out["concentration"] = conc

    # ---- pipeline opportunity ----
    # work order: best segment first, then expected value
    targets = sorted((x for x in rows if x["status"] in ("untouched", "in pipeline")),
                     key=lambda x: (SEGMENTS.index(x["segment"]), -x["expected"], x["account"]))
    out["pipeline"] = {
        "open_deals": int(sum(x["open"] for x in rows)),
        "open_value": money(sum(x["open_value"] for x in rows)),
        "weighted_open": money(sum(x["weighted_open"] for x in rows)),
        "untouched_accounts": sum(1 for x in rows if x["status"] == "untouched"),
        "untouched_expected": money(sum(x["expected"] for x in rows if x["status"] == "untouched")),
        "core_untouched": sum(1 for x in rows if x["status"] == "untouched" and x["segment"] == "Core"),
        "top_targets": [{k2: x[k2] for k2 in ("account", "segment", "status", "p", "value", "expected",
                                              "open_value", "disagree")} for x in targets[:25]],
    }
    disagree = [x for x in rows if x["disagree"]]
    out["disagreements"] = {"count": len(disagree), "threshold": DISAGREE,
                            "examples": [{k2: x[k2] for k2 in ("account", "p_logistic", "p_forest", "segment")}
                                         for x in sorted(disagree, key=lambda x: -abs(x["p_logistic"] - x["p_forest"]))[:8]]}

    # ---- data quality ----
    out["data_quality"] = dq
    out["feature_labels"] = {f: spec[f][0] for f in feats}
    try:
        import sklearn
        out["versions"] = {"scikit-learn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__}
    except Exception:
        pass
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deals", required=True)
    ap.add_argument("--accounts")
    ap.add_argument("--json", default="segments.json")
    ap.add_argument("--won"); ap.add_argument("--lost")
    ap.add_argument("--features", help="extra account columns to model, comma separated")
    args = ap.parse_args()
    try:
        import sklearn  # noqa: F401
    except ImportError:
        sys.exit("scikit-learn is not installed. Run: pip install scikit-learn pandas numpy")
    extra = [c.strip() for c in args.features.split(",")] if args.features else None
    res = analyze(args.deals, args.accounts, args.won, args.lost, extra)
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    if res.get("stop"):
        print("STOP: " + res["stop"])
        if res.get("stages_found"): print("Stages found: " + ", ".join(res["stages_found"]))
        if res.get("columns_found"): print("Columns found: " + ", ".join(res["columns_found"]))
        sys.exit(1)
    mh, c = res["model_health"], res["counts"]
    print(f"{c['closed_deals']} closed deals ({c['won']} won) across {c['accounts_with_closed_deals']} accounts. "
          f"{c['untouched_accounts']} accounts with no deals yet.")
    print(f"Model check (AUC): logistic {mh['auc_logistic']}, forest {mh['auc_forest']}. "
          f"Probability from the {mh['primary']} model. Verdict: {mh['verdict']}.")
    for s in res["segments"]:
        print(f"  {s['segment']:<13} {s['accounts']:>4} accounts  {s['share_of_revenue']:.0%} of won revenue")
    for w in res["warnings"]: print("WARNING: " + w)
    print("Written to " + args.json)


if __name__ == "__main__":
    main()
