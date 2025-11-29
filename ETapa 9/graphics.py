# === Script 2 — Gráficos Comparativos da Etapa 9 ===
import pandas as pd
import matplotlib.pyplot as plt

# Carregar arquivo atualizado
df = pd.read_csv("/home/automining/Pessoal/ORION/Etapa 8/auc_results_fixed.csv")

# Evitar warnings
plt.rcParams.update({'figure.figsize': (10, 5), 'font.size': 12})

# ============================
# 1. Gráfico — AUC por Modal
# ============================
mode_mean = df.groupby("mode")["AUC_percent"].mean().sort_values()

plt.figure()
mode_mean.plot(kind="barh")
plt.xlabel("AUC (%)")
plt.title("Robustez Média por Modal (AUC%) — Etapa 9")
plt.tight_layout()
plt.savefig("plot_auc_por_modal.png", dpi=300)

# ============================
# 2. Gráfico — AUC por Estratégia
# ============================
strategy_mean = df.groupby("strategy")["AUC_percent"].mean().sort_values()

plt.figure()
strategy_mean.plot(kind="barh")
plt.xlabel("AUC (%)")
plt.title("Robustez Média por Estratégia de Remoção — Etapa 9")
plt.tight_layout()
plt.savefig("plot_auc_por_estrategia.png", dpi=300)

# ============================
# 3. Melhor modal por estratégia
# ============================
best_per_strategy = df.loc[df.groupby("strategy")["AUC_percent"].idxmax()]

plt.figure(figsize=(10, 6))
plt.barh(best_per_strategy["strategy"], best_per_strategy["AUC_percent"])
plt.xlabel("AUC (%)")
plt.title("Melhor Modal por Estratégia — Etapa 9")
plt.tight_layout()
plt.savefig("plot_best_modal_por_estrategia.png", dpi=300)

print("Gráficos gerados com sucesso!")
