#!/usr/bin/env python3
# analisar_etapa8_fixed.py
# Leitura robusta do CSV de resultados e análise da Etapa 8.
# Funciona tanto com CSVs por iteração (fraction_removed + largest_scc)
# quanto com CSVs agregados que já contêm auc_normalized / auc.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# -----------------------
# Configurações / Paths
# -----------------------
CSV_PATH = Path("/home/automining/Pessoal/ORION/Etapa 8/results_modes_strategies.csv")
OUT_DIR = Path("/home/automining/Pessoal/ORION/Etapa 8")
FIG_DIR = OUT_DIR / "analysis_figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

if not CSV_PATH.exists():
    print("Arquivo não encontrado:", CSV_PATH)
    sys.exit(1)

print("Lendo CSV:", CSV_PATH)
df = pd.read_csv(CSV_PATH)

# Normalizar nomes de coluna para facilitar busca
cols = {c.lower().strip(): c for c in df.columns}
lower_cols = set(cols.keys())

# Helper para detectar coluna equivalente
def pick(*candidates):
    for c in candidates:
        if c.lower() in lower_cols:
            return cols[c.lower()]
    return None

# Colunas possíveis
col_fraction = pick("fraction_removed", "fraction", "frac", "fraction_removed (%)", "step")
col_largest_scc = pick("largest_scc", "largest_scc_size", "scc", "lcc", "largest_component")
col_auc_norm = pick("auc_normalized", "auc_norm", "auc_normalised", "auc (%)", "auc")
col_auc = pick("auc", "auc_normalized", "AUC")  # fallback
col_mode = pick("mode", "network", "layer")
col_strategy = pick("strategy", "method", "attack")

# Branch: se temos curvas por iteração -> calcular AUC por (mode, strategy)
if col_fraction and col_largest_scc:
    print("Formato detectado: curvas por iteração (fraction_removed + largest_scc). Calculando AUC por grupo...")
    # garantir colunas numéricas
    df[col_fraction] = pd.to_numeric(df[col_fraction], errors="coerce")
    df[col_largest_scc] = pd.to_numeric(df[col_largest_scc], errors="coerce")

    if col_mode and col_strategy:
        group_keys = [col_mode, col_strategy]
    elif col_strategy:
        group_keys = [col_strategy]
        print("Aviso: coluna 'mode' não encontrada — calculando AUC por estratégia apenas.")
    else:
        group_keys = []

    def calc_auc_group(g):
        # normalizar SCC por V máximo do grupo (ou por maior valor observado)
        y = g[col_largest_scc].values
        x = g[col_fraction].values
        if len(x) < 2:
            return np.nan
        # normaliza por max do grupo para obter tau_i / V
        maxv = np.nanmax(y) if np.nanmax(y) > 0 else 1.0
        y_norm = y / maxv
        auc = np.trapz(y_norm, x)
        # converter para escala 0-100 (como no artigo/implementação usada anteriormente)
        return 100.0 * auc

    auc_series = df.groupby(group_keys).apply(calc_auc_group).reset_index()
    auc_series.columns = group_keys + ["AUC_percent"]
    auc_df = auc_series.copy()

else:
    # Branch: CSV já contém AUC agregado
    if col_auc_norm or col_auc:
        use_col = col_auc_norm if col_auc_norm else col_auc
        print(f"Formato detectado: CSV já contém AUC ({use_col}). Usando esses valores.")
        # garantir coluna de modo/strategy
        if not col_mode or not col_strategy:
            print("Erro: o CSV precisa conter colunas identificadoras 'mode' e 'strategy' para esta análise.")
            print("Colunas encontradas:", list(df.columns))
            sys.exit(1)
        # copiar e renomear
        auc_df = df[[cols[col_mode.lower()], cols[col_strategy.lower()], use_col]].copy()
        auc_df.columns = ["mode", "strategy", "AUC_percent"]
        # se AUC vier já em 0-1 (values <= 1) convertemos para percentagem
        if auc_df["AUC_percent"].max() <= 1.0:
            auc_df["AUC_percent"] = auc_df["AUC_percent"] * 100.0
    else:
        print("Formato do CSV não reconhecido. Colunas encontradas:", list(df.columns))
        print("Esperado: ou [fraction_removed + largest_scc] por iteração, ou [auc_normalized/auc] agregado.")
        sys.exit(1)

# Agora temos auc_df com colunas: mode?, strategy?, AUC_percent
# Garantir colunas mode/strategy presentes
if "mode" not in auc_df.columns:
    if col_mode:
        auc_df = auc_df.rename(columns={cols[col_mode.lower()]: "mode"})
    else:
        # criar modo genérico se não existe
        auc_df["mode"] = "UNKNOWN"

if "strategy" not in auc_df.columns:
    if col_strategy:
        auc_df = auc_df.rename(columns={cols[col_strategy.lower()]: "strategy"})
    else:
        auc_df["strategy"] = "UNKNOWN"

# Converter nomes para string
auc_df["mode"] = auc_df["mode"].astype(str)
auc_df["strategy"] = auc_df["strategy"].astype(str)
auc_df["AUC_percent"] = pd.to_numeric(auc_df["AUC_percent"], errors="coerce")

# Salvar csv de saída
out_csv = OUT_DIR / "auc_results_fixed.csv"
auc_df.to_csv(out_csv, index=False)
print("AUC consolidado salvo em:", out_csv)

# Análises: média por modo, identificação
mode_mean = auc_df.groupby("mode")["AUC_percent"].mean().sort_values(ascending=False)
strategy_mean = auc_df.groupby("strategy")["AUC_percent"].mean().sort_values()

# Identificações
modo_mais_resiliente = mode_mean.index[0]
modo_mais_vulneravel = mode_mean.index[-1]
estrategia_mais_danosa = strategy_mean.index[0]  # menor AUC = mais danosa

# Imprimir resumo
print("\nResumo da Etapa 8 — AUC (em percentagem, maior = mais resiliente):\n")
print("Modo mais resiliente:", modo_mais_resiliente, "→ AUC médio =", mode_mean.iloc[0])
print("Modo mais vulnerável:", modo_mais_vulneravel, "→ AUC médio =", mode_mean.iloc[-1])
print("Estratégia mais danosa (menor AUC médio):", estrategia_mais_danosa, "→ AUC médio =", strategy_mean.iloc[0])

# Salvar resumo
summary_out = OUT_DIR / "auc_summary_fixed.csv"
summary_df = pd.DataFrame({
    "mode": mode_mean.index,
    "AUC_mean": mode_mean.values
})
summary_df.to_csv(summary_out, index=False)

strategy_out = OUT_DIR / "strategy_auc_summary_fixed.csv"
strategy_df = pd.DataFrame({
    "strategy": strategy_mean.index,
    "AUC_mean": strategy_mean.values
})
strategy_df.to_csv(strategy_out, index=False)

print("\nArquivos salvos:")
print(" -", out_csv)
print(" -", summary_out)
print(" -", strategy_out)

# -----------------------
# Plots (salva em FIG_DIR)
# -----------------------
sns.set(style="whitegrid")

# 1. AUC por modo (média)
plt.figure(figsize=(10,6))
order = mode_mean.index
sns.barplot(x=mode_mean.values, y=mode_mean.index, palette="viridis")
plt.xlabel("AUC médio (%)")
plt.ylabel("Modo")
plt.title("AUC médio por modo (maior = mais resiliente)")
plt.tight_layout()
plt.savefig(FIG_DIR / "auc_by_mode_fixed.png")
plt.close()

# 2. AUC por estratégia
plt.figure(figsize=(10,6))
sns.barplot(x=strategy_mean.values, y=strategy_mean.index, palette="magma")
plt.xlabel("AUC médio (%)")
plt.ylabel("Estratégia")
plt.title("AUC médio por estratégia (menor = mais danosa)")
plt.tight_layout()
plt.savefig(FIG_DIR / "auc_by_strategy_fixed.png")
plt.close()

# 3. Heatmap modo x estratégia (AUC)
pivot = auc_df.pivot_table(index="mode", columns="strategy", values="AUC_percent")
plt.figure(figsize=(10, max(4, 0.4 * len(pivot.index))))
sns.heatmap(pivot, annot=True, fmt=".2f", cmap="RdYlGn_r")
plt.title("Heatmap: AUC (%) por modo × estratégia")
plt.tight_layout()
plt.savefig(FIG_DIR / "heatmap_mode_strategy_fixed.png")
plt.close()

print("\nGráficos salvos em:", FIG_DIR)
print("\nAnálise concluída com sucesso.")
