import pandas as pd

df = pd.read_csv("/home/automining/Pessoal/ORION/Etapa 8/auc_results_fixed.csv")

print("\n=== MÉDIA POR MODAL ===")
mode_mean = (
    df.groupby("mode")["AUC_percent"]
      .mean()
      .sort_values(ascending=False)
)
print(mode_mean)

print("\n=== MÉDIA POR ESTRATÉGIA ===")
strategy_mean = (
    df.groupby("strategy")["AUC_percent"]
      .mean()
      .sort_values()
)
print(strategy_mean)

print("\n=== MELHOR MODAL POR ESTRATÉGIA ===")
best_modes = (
    df.loc[df.groupby("strategy")["AUC_percent"].idxmax()][["strategy", "mode", "AUC_percent"]]
      .sort_values(by="AUC_percent", ascending=False)
)
print(best_modes)
