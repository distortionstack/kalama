import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

df = pd.read_csv("results.csv")   # คอลัมน์: predicted_high(0/1), exploited(0/1)

y_pred = df["predicted_high"]
y_true = df["exploited"]

print("Precision:", precision_score(y_true, y_pred))   # ที่บอกว่าอันตราย อันตรายจริงกี่ %
print("Recall   :", recall_score(y_true, y_pred))      # อันตรายจริงเราจับได้กี่ %
print("F1       :", f1_score(y_true, y_pred))
