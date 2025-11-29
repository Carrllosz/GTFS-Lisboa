# === Script 3 — Geração Automática da Análise Interpretativa ===
import pandas as pd

df = pd.read_csv("/home/automining/Pessoal/ORION/Etapa 8/auc_results_fixed.csv")

# Médias
mode_mean = df.groupby("mode")["AUC_percent"].mean().sort_values(ascending=False)
strategy_mean = df.groupby("strategy")["AUC_percent"].mean().sort_values()
best = df.loc[df.groupby("strategy")["AUC_percent"].idxmax()]

# Criar texto final
texto = []

texto.append("=== INTERPRETAÇÃO FINAL — ETAPA 9 ===\n")

texto.append("\n1. Robustez por Modal (AUC%)\n")
for mode, val in mode_mean.items():
    texto.append(f"- {mode}: {val:.3f}%")

texto.append("\n\n2. Robustez por Estratégia de Remoção\n")
for st, val in strategy_mean.items():
    texto.append(f"- {st}: {val:.3f}%")

texto.append("\n\n3. Melhor Modal por Estratégia")
for idx, row in best.iterrows():
    texto.append(f"- {row['strategy']} → {row['mode']} ({row['AUC_percent']:.3f}%)")

# Interpretação conceitual
texto.append("""

4. Interpretação Geral

- Estratégias recalculadas (recalc_degree / recalc_betweenness)
  são as mais destrutivas, pois sempre removem o nó mais crítico atual.

- Remoções baseadas em betweenness afetam hubs estruturais,
  provocando fragmentação rápida da rede.

- Remoção aleatória é a menos danosa, pois afeta principalmente
  nós periféricos com pouca centralidade.

- Modais ferroviários (especialmente FERTAGUS e TRANSTEJO) 
  demonstram maior resiliência estrutural.

- Modais rodoviários (TST, RODOVIÁRIA, SULFERTAGUS) 
  são os mais vulneráveis, com baixa redundância.

Conclusão:
A rede multimodal de Lisboa apresenta comportamento típico
de redes complexas heterogêneas: robusta a falhas aleatórias,
mas altamente vulnerável a ataques direcionados que removem hubs.
""")

# Salvar arquivo
with open("interpretacao_final.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(texto))

print("interpretacao_final.txt gerado com sucesso!")
