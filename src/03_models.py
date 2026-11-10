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