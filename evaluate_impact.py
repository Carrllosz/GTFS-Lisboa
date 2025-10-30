# ==========================================================
# evaluate_impact.py — Avaliar impacto das falhas
# ==========================================================
import pandas as pd
import numpy as np

# ==========================================================
# 1. Carregar resultados da Etapa 5
# ==========================================================
df = pd.read_csv("results_all_strategies.csv")

# ==========================================================
# 2. Calcular métricas adicionais
# ==========================================================
# Número de componentes isolados (IC): nós restantes - maior SCC
df["isolated_components"] = df["nodes_remaining"] - df["largest_scc_size"]

# Normalizar tamanho da SCC em relação ao total original
V = df["nodes_remaining"].max()  # número inicial de nós
df["SCC_normalized"] = df["largest_scc_size"] / V

# ==========================================================
# 3. Calcular AUC (área sob a curva normalizada)
# ==========================================================
def calc_auc_normalized(subdf):
    """Calcula AUC_normalized = (100/χ) * sum(τ_i / V)"""
    chi = len(subdf)
    auc = (100 / chi) * np.sum(subdf["SCC_normalized"])
    return auc

auc_results = (
    df.groupby("strategy")
      .apply(calc_auc_normalized)
      .reset_index()
      .rename(columns={0: "AUC_normalized"})
)

# ==========================================================
# 4. Calcular métricas finais médias
# ==========================================================
summary = (
    df.groupby("strategy")
      .agg({
          "SCC_normalized": "mean",
          "APL": "mean",
          "isolated_components": "mean"
      })
      .reset_index()
      .rename(columns={
          "SCC_normalized": "Mean_SCC_norm",
          "APL": "Mean_APL",
          "isolated_components": "Mean_IC"
      })
)

# Juntar tudo
final_results = pd.merge(auc_results, summary, on="strategy")

# ==========================================================
# 5. Salvar resultados
# ==========================================================
final_results.to_csv("failure_impact_summary.csv", index=False)

print("\n📊 Impacto das falhas por estratégia:\n")
print(final_results.round(4))
print("\n✅ Resultados salvos em 'failure_impact_summary.csv'")
