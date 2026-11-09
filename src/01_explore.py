"""Phase 0 — reconnaissance of the UNCTAD ISDS Navigator release.

Run from the repository root:
    python src/01_explore.py [path/to/file.xlsx]

Pass 1 (no column names known): lists every sheet and column, its type,
missing rate, and the most frequent values of short text columns, and
guesses which columns hold outcome, year, arbitrators, amounts and forum.

Pass 2: copy the real column names into COLS below and run again to get
the checklist numbers (outcome counts, cutoff table, missing rates).

All output is also written to results/explore_report.txt.
"""
import sys
from pathlib import Path

import pandas as pd

RAW = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/isds_navigator.xlsx")
OUT = Path("results/explore_report.txt")

# Set from pass 1. Both the 31/07/2019 and 31/12/2023 releases have 11 note
# lines above the header (row index 11). Where a column was renamed between
# releases, list both names; the first one present is used.
SHEET = None       # None = first sheet
HEADER_ROW = 11
COLS = {
    "outcome": "STATUS/OUTCOME OF ORIGINAL PROCEEDINGS",
    "outcome_detail": ["IIA BREACHES FOUND", "BREACHES FOUND"],  # jurisdiction declined vs merits dismissed
    "year": "YEAR OF INITIATION",
    "year_end": None,                     # not in this release
    "arbitrators": "ARBITRATORS",
    "amount_claimed": "AMOUNT CLAIMED (EXPRESSED IN MILLIONS)",
    "amount_awarded": "AMOUNT AWARDED (OR SETTLED FOR) (EXPRESSED IN MILLIONS)",
    "forum": "ARBITRAL RULES",
}
AWARD_PREFIXES = ("Decided", "Neither")   # outcomes that end in an award
MISSING_TEXT = "Data not available|Not applicable|None recorded"
CUTOFFS = (2009, 2010, 2011, 2012, 2013, 2014)

# Keywords used to guess columns in pass 1.
HINTS = {
    "outcome": ["outcome", "status", "result", "decided"],
    "year": ["year", "initiat", "date", "registered"],
    "arbitrators": ["arbitrator", "tribunal", "president", "chair"],
    "amount": ["amount", "usd", "claimed", "awarded", "compensation", "damages"],
    "forum": ["forum", "institution", "rules", "icsid", "uncitral"],
}

lines: list[str] = []


def log(*parts) -> None:
    text = " ".join(str(p) for p in parts)
    lines.append(text)
    print(text)


def section(title: str) -> None:
    log("\n" + "=" * 70)
    log(title)
    log("=" * 70)


def load(xl: pd.ExcelFile) -> pd.DataFrame:
    df = xl.parse(SHEET if SHEET is not None else xl.sheet_names[0], header=HEADER_ROW)
    df.columns = [str(c).strip() for c in df.columns]
    first = df.columns[0]
    return df[pd.to_numeric(df[first], errors="coerce").notna()].copy()  # drop trailing notes


def resolve(df: pd.DataFrame) -> None:
    """Replace list entries in COLS with the first column name present in df."""
    for key, val in COLS.items():
        if isinstance(val, list):
            COLS[key] = next((v for v in val if v in df.columns), None)
    log("Columns used:", {k: v for k, v in COLS.items() if v})


def missing(s: pd.Series) -> pd.Series:
    return s.isna() | s.astype(str).str.contains(MISSING_TEXT, case=False)


def pass1(xl: pd.ExcelFile) -> pd.DataFrame:
    section(f"FILE  {RAW}")
    log("Sheets:", xl.sheet_names)

    for sheet in xl.sheet_names:
        df = xl.parse(sheet, header=HEADER_ROW if sheet == xl.sheet_names[0] else 0)
        section(f"SHEET '{sheet}'  {df.shape[0]} rows x {df.shape[1]} cols")
        for col in df.columns:
            s = df[col]
            miss = s.isna().mean()
            nuniq = s.nunique(dropna=True)
            log(f"  {str(col)[:55]:55} {str(s.dtype):9} missing={miss:6.1%}  unique={nuniq}")
        # short text columns: show top values (likely categorical)
        for col in df.columns:
            s = df[col]
            if s.dtype == object and 1 < s.nunique(dropna=True) <= 40:
                log(f"\n  -- top values: {col}")
                for val, n in s.value_counts(dropna=False).head(15).items():
                    log(f"     {n:5}  {val}")

    df = load(xl)
    section("COLUMN GUESSES (check by eye; copy real names into COLS)")
    for key, words in HINTS.items():
        hits = [c for c in df.columns if any(w in str(c).lower() for w in words)]
        log(f"  {key:12} -> {hits}")
    log("\n  Sample of 3 rows:")
    log(df.head(3).T.to_string())
    return df


def pass2(df: pd.DataFrame) -> None:
    c = COLS

    section("1. OUTCOME VALUES")
    oc = df[c["outcome"]]
    log(oc.value_counts(dropna=False).to_string())
    decided = df[oc.astype(str).str.startswith(AWARD_PREFIXES)]
    log(f"\nCases ending in an award (decided + neither): {len(decided)}")
    log(f"Gate (>= 300): {'PASS' if len(decided) >= 300 else 'FAIL'}")

    if c["outcome_detail"]:
        section("2. STATE WINS — jurisdiction vs merits")
        state = decided[decided[c["outcome"]].str.contains("favour of state", case=False, na=False)]
        log(state[c["outcome_detail"]].value_counts(dropna=False).to_string())
        jur = decided[c["outcome_detail"]].eq("None - jurisdiction declined")
        lab = decided[c["outcome"]].str.contains("favour of investor", case=False)
        log(f"\nlabel_a (all award cases):           n={len(decided)}  investor share={lab.mean():.1%}")
        log(f"label_b (excl. jurisdiction declined): n={(~jur).sum()}  investor share={lab[~jur].mean():.1%}")

    section("3. ARBITRATORS")
    if c["arbitrators"]:
        a = df[c["arbitrators"]]
        log(f"missing: all {missing(a).mean():.1%} / award cases {missing(a[decided.index]).mean():.1%}")
        log("5 samples:")
        for v in a[decided.index][~missing(a[decided.index])].sample(5, random_state=0):
            log("  |", repr(v)[:200])
    else:
        log("no arbitrator column set")

    section("4. YEARS")
    y = pd.to_numeric(df[c["year"]], errors="coerce")
    log(y.describe().to_string())
    log("\nCases per 5-year bin:")
    log(pd.cut(y, range(1985, 2030, 5), right=False).value_counts().sort_index().to_string())
    log("\nAward cases per 5-year bin (watch the last bins: right truncation):")
    log(pd.cut(pd.to_numeric(decided[c["year"]]), range(1985, 2030, 5), right=False).value_counts().sort_index().to_string())

    section("5. CUTOFF CANDIDATES (award cases only, split on year of initiation)")
    dy = pd.to_numeric(decided[c["year"]], errors="coerce")
    inv = decided[c["outcome"]].str.contains("favour of investor", case=False, na=False)  # not "investor": would match "Neither investor nor the State"
    jur = decided[c["outcome_detail"]].eq("None - jurisdiction declined") if c["outcome_detail"] else pd.Series(False, index=decided.index)
    log(f"{'cutoff':>7} {'A_train':>8} {'A_test':>7} {'A_tr_pos':>9} {'A_te_pos':>9} {'B_train':>8} {'B_test':>7}")
    for cut in CUTOFFS:
        tr, te = dy < cut, dy >= cut
        log(f"{cut:>7} {tr.sum():>8} {te.sum():>7} {inv[tr].mean():>9.1%} {inv[te].mean():>9.1%} {(tr & ~jur).sum():>8} {(te & ~jur).sum():>7}")
    log("Requirement: train >= 200, test >= 80")

    section("6. AMOUNTS")
    for key in ("amount_claimed", "amount_awarded"):
        if c[key]:
            m = missing(df[c[key]])
            log(f"{key:15} missing: all {m.mean():.1%} / award cases {m[decided.index].mean():.1%}")
    log("(amount_awarded is outcome information — never use as a feature)")

    if c["forum"]:
        section("7. FORUM")
        log(df[c["forum"]].value_counts(dropna=False).to_string())

    section("MANUAL CHECK")
    log(f"Investor wins by script: {inv.sum()}  -> compare with an Excel filter count")
    log(f"State wins by script:    {decided[c['outcome']].str.contains('favour of state', case=False).sum()}")


def main() -> None:
    if not RAW.exists():
        sys.exit(f"File not found: {RAW}\nDownload the Navigator release and save it there.")
    xl = pd.ExcelFile(RAW)
    df = pass1(xl)
    if COLS["outcome"] and COLS["year"]:
        resolve(df)
        pass2(df)
    else:
        section("PASS 2 SKIPPED")
        log("Set COLS['outcome'] and COLS['year'] at the top of this script, then rerun.")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved {OUT}")


if __name__ == "__main__":
    main()
