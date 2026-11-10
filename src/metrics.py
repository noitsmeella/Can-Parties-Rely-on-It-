import numpy as np

def majority_acc(y_tr, y_te):
    """학습 세트에서 더 많은 쪽을 항상 답했을 때 평가 세트 정확도"""
    majority = int(np.mean(y_tr) >= 0.5)
    return float(np.mean(y_te == majority))

def brier(y, p):
    """확률 예측의 평균 제곱 오차. 0이 완벽, 낮을수록 좋음"""
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))

def base_rate_brier(y_tr, y_te):
    """항상 '학습 세트 투자자 비율'을 확률로 답했을 때의 Brier"""
    return brier(y_te, np.full(len(y_te), np.mean(y_tr)))

def ece(y, p, n_bins=5):
    """확신도 구간별로 |말한 확률 − 실제 비율|을 사건 수로 가중 평균"""
    y, p = np.asarray(y), np.asarray(p)
    idx = np.clip(np.digitize(p, np.linspace(0, 1, n_bins + 1)[1:-1]), 0, n_bins - 1)
    return float(sum((idx == b).mean() * abs(y[idx == b].mean() - p[idx == b].mean())
                     for b in range(n_bins) if (idx == b).any()))

def bootstrap_ci(fn, y, p, n=2000, seed=0):
    """평가 세트를 복원 추출로 2,000번 다시 뽑아 지표의 95% 구간을 구함"""
    y, p = np.asarray(y), np.asarray(p)
    rng = np.random.default_rng(seed)
    vals = [fn(y[i], p[i]) for i in (rng.integers(0, len(y), len(y)) for _ in range(n))]
    return np.percentile(vals, [2.5, 97.5])