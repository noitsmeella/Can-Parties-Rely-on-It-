import re
import numpy as np
import pandas as pd
from pathlib import Path

RAW = Path("data/raw/isds_navigator.xlsx")
O  = "STATUS/OUTCOME OF ORIGINAL PROCEEDINGS"
BF = "IIA BREACHES FOUND"      # 결과 정보: 레이블 B에만 사용, 피처 금지
BA = "IIA BREACHES ALLEGED"    # 청구 유형: 피처로 사용

def load():
    df = pd.read_excel(RAW, header=11)                 
    df.columns = [c.strip() for c in df.columns]       
    df = df[pd.to_numeric(df["NO."], errors="coerce").notna()].copy()  
    df["year"] = df["YEAR OF INITIATION"].astype(int)
    return df


LABEL_A = {   # 1 = 투자자 승소, 0 = 그 외 판정
    "Decided in favour of investor": 1,
    "Decided in favour of State": 0,
    "Neither investor nor the State (liability found but no damages awarded)": 0,
}
EXCLUDE = {"Pending", "Settled", "Discontinued for unknown reasons", "Data not available"}

def label(df):
    unknown = set(df[O]) - set(LABEL_A) - EXCLUDE
    assert not unknown, f"매핑되지 않은 결과 값: {unknown}"     # 새 값이 있으면 여기서 멈춤
    df[df[O].isin(["Settled", "Discontinued for unknown reasons"])].to_csv("data/settled.csv", index=False)
    d = df[df[O].isin(LABEL_A)].copy()
    d["label_a"] = d[O].map(LABEL_A)
    d["in_label_b"] = d[BF].ne("None - jurisdiction declined")  # 관할 각하가 아니면 B에 포함
    return d

TRAIN_END, TEST_END = 2014, 2018   # DECISIONS D-03

def split(d):
    tr = d[d.year < TRAIN_END].copy()
    te = d[(d.year >= TRAIN_END) & (d.year <= TEST_END)].copy()
    return tr, te

def usd(text):
    """'800.00 USD' → 800.0,  '11.00 EUR (12.50 USD)' → 12.5,  그 외 → NaN"""
    s = str(text)
    m = re.search(r"\(([\d.,]+)\s*USD\)", s) or re.match(r"\s*([\d.,]+)\s*USD", s)
    return float(m.group(1).replace(",", "")) if m else np.nan

def add_amount(d):
    amt = d["AMOUNT CLAIMED (EXPRESSED IN MILLIONS)"].map(usd)
    d["amount_missing"] = amt.isna().astype(int)
    d["log_amount"] = np.log1p(amt)          # 결측은 NaN으로 둠 (0으로 채우지 않기)
    return d

def claim_list(cell):
    if pd.isna(cell) or "not available" in str(cell).lower():
        return None                           # 결측
    return [x.strip() for x in str(cell).split(";") if x.strip()]

def add_claims(tr, te, k=6):
    for d in (tr, te):
        d["_claims"] = d[BA].map(claim_list)
        d["n_claims"] = d["_claims"].map(lambda xs: len(xs) if xs else np.nan)
    top = tr["_claims"].dropna().explode().value_counts().head(k).index   # 학습 세트에서만 고름
    for d in (tr, te):
        for i, c in enumerate(top):
            d[f"claim_{i}"] = d["_claims"].map(lambda xs: int(c in xs) if xs else 0)
        d.drop(columns="_claims", inplace=True)
    return list(top)


def forum(s):
    s = str(s)
    if s.startswith("ICSID AF"): return "ICSID_AF"
    if s.startswith("ICSID"):    return "ICSID"
    if s.startswith("UNCITRAL"): return "UNCITRAL"
    if s.startswith("SCC"):      return "SCC"
    return "other"

def add_cats(d):
    d["forum"] = d["ARBITRAL RULES"].map(forum)
    d["sector"] = d["ECONOMIC SECTOR"].astype(str).str.split(" - ").str[0]   # Primary / Secondary / Tertiary
    return d

import country_converter as coco

def add_country(tr, te, min_n=5):
    names = pd.concat([tr, te])["RESPONDENT STATE"].unique()
    region = dict(zip(names, coco.convert(list(names), to="continent", not_found="unknown")))
    print("지역 못 찾음:", [n for n, r in region.items() if r == "unknown"])   # 수작업으로 고칠 목록
    rare = tr["RESPONDENT STATE"].value_counts().loc[lambda s: s < min_n].index  # 학습 세트 기준
    for d in (tr, te):
        d["resp_region"] = d["RESPONDENT STATE"].map(region)
        d["respondent"] = d["RESPONDENT STATE"].where(~d["RESPONDENT STATE"].isin(rare), "other")

KEEP = ["NO.", "SHORT CASE NAME", "year", "label_a", "in_label_b",           # 식별·레이블
        "respondent", "resp_region", "HOME STATE OF INVESTOR", "forum", "sector",
        "n_claims", "log_amount", "amount_missing"]                           # 피처

def save(tr, te, top):
    cols = KEEP + [f"claim_{i}" for i in range(len(top))]
    tr[cols].to_csv("data/train.csv", index=False)
    te[cols].to_csv("data/test.csv", index=False)
    rows = []
    for name, d in [("train", tr), ("test", te)]:
        rows.append({"set": name, "n": len(d), "investor_share": round(d.label_a.mean(), 3),
                     "n_label_b": int(d.in_label_b.sum()),
                     **d.forum.value_counts().add_prefix("forum_").to_dict()})
    pd.DataFrame(rows).to_csv("results/split_summary.csv", index=False)

if __name__ == "__main__":
    d = label(load())
    tr, te = split(d)
    for x in (tr, te):
        add_amount(x); add_cats(x)
    top = add_claims(tr, te)
    add_country(tr, te)
    save(tr, te, top)
    print(f"train {len(tr)} | test {len(te)} | top claims: {top}")