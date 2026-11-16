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

EVALUATE_TEST = True   # B단계에서만 True로 바꾼다 (평가 세트는 한 번만 연다)

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


# ===================== 평가 세트 1회 평가 =====================
if EVALUATE_TEST:
    import matplotlib
    matplotlib.use("Agg")                  # 창을 띄우지 않고 파일로만 저장
    import matplotlib.pyplot as plt
    from sklearn.inspection import permutation_importance
    from metrics import brier, ece, bootstrap_ci

    X_te = test[FEATURES]
    acc_fn = lambda y, p: float(np.mean((p >= 0.5) == (y == 1)))   # p ≥ 0.5면 투자자로 예측

    perf, probs = [], []
    for name, est in fitted.items():
        p = est.predict_proba(X_te)[:, 1]
        acc_lo, acc_hi = bootstrap_ci(acc_fn, y_te, p)
        br_lo, br_hi = bootstrap_ci(brier, y_te, p)
        row = {"model": name, "n": len(y_te),
               "accuracy": round(acc_fn(y_te, p), 3), "acc_ci": [round(acc_lo, 3), round(acc_hi, 3)],
               "brier": round(brier(y_te, p), 4), "brier_ci": [round(br_lo, 4), round(br_hi, 4)],
               "ece": round(ece(y_te, p), 4),
               "mean_confidence": round(float(np.maximum(p, 1 - p).mean()), 3)}
        # D-06 기준: 정확도 구간 하한 > 다수결 정확도  또는  Brier 구간 상한 < 기저율 Brier
        row["beats_baseline"] = bool(acc_lo > acc or br_hi < bb)
        perf.append(row)
        probs.append(pd.DataFrame({"case_id": test["NO."], "model": name, "p_investor": p, "y": y_te}))
        print(f"[TEST] {name}: acc {row['accuracy']} {row['acc_ci']}  Brier {row['brier']} {row['brier_ci']}  "
              f"ECE {row['ece']}  beats baseline: {row['beats_baseline']}")
    print(f"[BASELINE] majority acc {acc:.3f}  base-rate Brier {bb:.4f}")

    pd.DataFrame(perf).to_csv("results/model_performance.csv", index=False)
    pd.concat(probs).to_csv("results/model_probs.csv", index=False)

    # 피처 중요도: 피처 하나를 섞었을 때 Brier가 얼마나 나빠지는가 (저장소용 그림)
    imp = permutation_importance(fitted["logreg"], X_te, y_te, scoring="neg_brier_score",
                                 n_repeats=20, random_state=0)
    order = np.argsort(imp.importances_mean)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.barh(np.array(FEATURES)[order], imp.importances_mean[order],
            xerr=imp.importances_std[order], color="#888")
    ax.set_xlabel("Increase in Brier score when the feature is shuffled")
    ax.set_title("Permutation importance (logistic regression, test set)")
    fig.tight_layout(); fig.savefig("figures/feature_importance.png", dpi=200)
    print("saved figures/feature_importance.png")