import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))   # 같은 폴더의 metrics.py를 불러오기 위해
from metrics import majority_acc, base_rate_brier

train = pd.read_csv("data/train.csv")
test = pd.read_csv("data/test.csv")
y_tr, y_te = train.label_a.to_numpy(), test.label_a.to_numpy()

acc = majority_acc(y_tr, y_te)
bb = base_rate_brier(y_tr, y_te)
lines = [f"train n={len(y_tr)} investor share={y_tr.mean():.3f}",
         f"test  n={len(y_te)} investor share={y_te.mean():.3f}",
         f"MAJORITY ACCURACY (always 'State'): {acc:.3f}",
         f"BASE-RATE BRIER (always p={y_tr.mean():.3f}): {bb:.4f}"]
Path("results/baseline.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))


# ===================== 모델 =====================
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

EVALUATE_TEST = False   # B단계에서만 True로 바꾼다 (평가 세트는 한 번만 연다)

# 1) 피처: 범주형 4개 + 숫자형 9개
CAT = ["respondent", "resp_region", "forum", "sector"]
NUM = ["n_claims", "log_amount", "amount_missing"] + [c for c in train.columns if c.startswith("claim_")]
FEATURES = CAT + NUM

# 2) 전처리: 범주형은 원-핫, 숫자형은 결측 채우기 + 결측 표시 + 표준화
pre = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
    ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                      ("sc", StandardScaler())]), NUM),
])

# 3) 모델 2개와 각자의 후보 설정
MODELS = {
    "logreg": (LogisticRegression(max_iter=2000), {"m__C": [0.1, 1, 10]}),
    "gbm": (GradientBoostingClassifier(random_state=0, learning_rate=0.05, n_estimators=200, subsample=0.8),
            {"m__max_depth": [2, 3]}),
}

# 4) 학습 세트를 연도순으로 정렬 → 시간 순 교차검증 (과거로 학습, 바로 다음 시기로 검증)
train = train.sort_values("year").reset_index(drop=True)
X_tr, y_tr = train[FEATURES], train.label_a.to_numpy()
cv = TimeSeriesSplit(n_splits=4)

fitted, cv_rows = {}, []
for name, (model, grid) in MODELS.items():
    gs = GridSearchCV(Pipeline([("pre", pre), ("m", model)]), grid, cv=cv, scoring="neg_brier_score")
    gs.fit(X_tr, y_tr)
    fitted[name] = gs.best_estimator_          # 가장 좋은 설정으로 학습 세트 전체에 다시 학습된 모델
    cv_rows.append({"model": name, "best_params": gs.best_params_, "cv_brier": round(-gs.best_score_, 4)})
    print(f"[CV] {name}: best {gs.best_params_}  cv Brier {-gs.best_score_:.4f}")
pd.DataFrame(cv_rows).to_csv("results/cv_results.csv", index=False)

from sklearn.dummy import DummyClassifier
from sklearn.model_selection import cross_val_score
prior_cv = -cross_val_score(DummyClassifier(strategy="prior"), X_tr, y_tr, cv=cv,
                            scoring="neg_brier_score").mean()
cv_rows.append({"model": "prior_only", "best_params": {}, "cv_brier": round(prior_cv, 4)})
print(f"[CV] prior-only baseline: cv Brier {prior_cv:.4f}")