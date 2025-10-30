import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

sns.set(style="whitegrid", font_scale=1.2)
plt.rcParams["figure.figsize"] = (8, 5)

impact = pd.read_csv("failure_impact_summary.csv")
os.makedirs("figures", exist_ok=True)

print("\n📊 Colunas disponíveis:", list(impact.columns), "\n")

# === 1️⃣ GRÁFICO DE BARRAS – SCC NORMALIZADA ===
if "mean_scc_norm" in impact.columns:
    plt.figure()
    sns.barplot(data=impact, x="strategy", y="mean_scc_norm", palette="Blues_d")
    plt.title("Tamanho Normalizado da Maior SCC por Estratégia")
    plt.xlabel("Estratégia de Remoção")
    plt.ylabel("SCC Normalizada")
    plt.xticks(rotation=25, ha='right')
    plt.tight_layout()
    plt.savefig("figures/scc_norm_por_estrategia.png", dpi=300)
    plt.close()

# === 2️⃣ GRÁFICO DE BARRAS – APL ===
if "mean_apl" in impact.columns:
    plt.figure()
    sns.barplot(data=impact, x="strategy", y="mean_apl", palette="Oranges_d")
    plt.title("Comprimento Médio do Caminho (APL) por Estratégia")
    plt.xlabel("Estratégia de Remoção")
    plt.ylabel("APL Médio")
    plt.xticks(rotation=25, ha='right')
    plt.tight_layout()
    plt.savefig("figures/apl_por_estrategia.png", dpi=300)
    plt.close()

# === 3️⃣ GRÁFICO DE BARRAS – AUC (se existir) ===
for col in impact.columns:
    if "auc" in col.lower():
        plt.figure()
        sns.barplot(data=impact, x="strategy", y=col, palette="Greens_d")
        plt.title(f"AUC Normalizada por Estratégia ({col})")
        plt.xlabel("Estratégia de Remoção")
        plt.ylabel("AUC Normalizada (%)")
        plt.xticks(rotation=25, ha='right')
        plt.tight_layout()
        plt.savefig(f"figures/{col}_por_estrategia.png", dpi=300)
        plt.close()

print("✅ Figuras salvas na pasta 'figures/' com sucesso!")
