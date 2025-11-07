# ==========================================================
# analyze_robustness.py — Análise de Robustez da Rede Multimodal
# ==========================================================
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================================
# 1. Carregar resultados
# ==========================================================
df = pd.read_csv("results_all_strategies.csv")

# Remover valores ausentes ou inválidos
df = df.dropna(subset=["fraction_removed", "largest_scc_size"])

# ==========================================================
# 2. Plotar robustez (Largest SCC vs Fraction Removed)
# ==========================================================
plt.figure(figsize=(10,6))
for strategy, group in df.groupby("strategy"):
    plt.plot(group["fraction_removed"], group["largest_scc_size"], label=strategy, linewidth=2)

plt.xlabel("Fração de nós removidos")
plt.ylabel("Tamanho da maior componente (SCC)")
plt.title("Curva de robustez da rede multimodal")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("robustness_curve_scc.png", dpi=300)
plt.show()

# ==========================================================
# 3. Plotar eficiência (APL vs Fraction Removed)
# ==========================================================
plt.figure(figsize=(10,6))
for strategy, group in df.groupby("strategy"):
    plt.plot(group["fraction_removed"], group["APL"], label=strategy, linewidth=2)

plt.xlabel("Fração de nós removidos")
plt.ylabel("Comprimento médio do caminho (APL)")
plt.title("Evolução da eficiência da rede sob falhas")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("robustness_curve_apl.png", dpi=300)
plt.show()

# ==========================================================
# 4. Estatísticas finais de colapso
# ==========================================================
summary = (
    df.groupby("strategy")
      .agg({
          "fraction_removed": "max",
          "largest_scc_size": "min",
          "APL": "max"
      })
      .rename(columns={
          "fraction_removed": "Frac. total removida",
          "largest_scc_size": "Menor SCC final",
          "APL": "Maior APL observado"
      })
)
print("\n📊 Resumo final por estratégia:\n")
print(summary)
summary.to_csv("robustness_summary.csv", index=True)
