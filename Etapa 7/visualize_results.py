#!/usr/bin/env python3
"""
visualize_results_v3.py
Gera todas as figuras da Etapa 7 (Estilo artigo) a partir dos CSVs já gerados.
- metrics_summary.csv  (para distribuição de grau e betweenness)
- results_all_strategies.csv (para curvas por iteração: SCC, APL, componentes)
- failure_impact_summary.csv (opcional: para gráficos agregados)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
import sys

# -------------------------
# Config global (estilo)
# -------------------------
sns.set_style("whitegrid")
plt.rcParams.update({
    "figure.figsize": (9, 6),
    "axes.titlesize": 16,
    "axes.labelsize": 13,
    "legend.fontsize": 11,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "lines.linewidth": 2,
    "savefig.dpi": 300,
})

# -------------------------
# Paths (ajuste se necessário)
# -------------------------
BASE = Path.cwd()
METRICS_CSV = BASE / "/home/automining/Pessoal/ORION/Etapa 2/graphs/metrics_summary.csv"
RESULTS_CSV = Path("/home/automining/Pessoal/ORION/Etapa 5/results_all_strategies.csv")
IMPACT_SUMMARY_CSV = BASE / "/home/automining/Pessoal/ORION/Etapa 6/failure_impact_summary.csv"  # opcional

OUTDIR = BASE / "figures"
OUTDIR.mkdir(exist_ok=True)

# -------------------------
# Helpers
# -------------------------
def find_col(df_cols, patterns):
    """Retorna a primeira coluna do df_cols que case com qualquer regex em patterns (case-insensitive)."""
    import re
    for p in patterns:
        for col in df_cols:
            if re.search(p, col, re.IGNORECASE):
                return col
    return None

def safe_read_csv(path):
    if not path.exists():
        print(f"Arquivo não encontrado: {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"Erro ao ler {path}: {e}")
        return None

# -------------------------
# 1) Ler métricas por nó (degree, betweenness)
# -------------------------
metrics = safe_read_csv(METRICS_CSV)
if metrics is None:
    print("Não foi possível carregar metrics_summary.csv — verifique o caminho e o arquivo.")
else:
    # Normaliza nomes de colunas
    cols = list(metrics.columns)
    col_in = find_col(cols, [r"in[_\s-]*degree", r"in_degree", r"inDegree"])
    col_out = find_col(cols, [r"out[_\s-]*degree", r"out_degree", r"outDegree"])
    col_deg = find_col(cols, [r"^\s*degree\s*$", r"deg$"])
    col_bet = find_col(cols, [r"betweenness", r"between"])

    # Calcular degree se não existir
    if col_deg:
        degree_series = metrics[col_deg]
    else:
        if col_in and col_out:
            degree_series = pd.to_numeric(metrics[col_in], errors="coerce").fillna(0) + pd.to_numeric(metrics[col_out], errors="coerce").fillna(0)
        elif col_in:
            degree_series = pd.to_numeric(metrics[col_in], errors="coerce").fillna(0)
        elif col_out:
            degree_series = pd.to_numeric(metrics[col_out], errors="coerce").fillna(0)
        else:
            # tentar encontrar uma coluna de contagem (index?) ou abortar
            print("Aviso: não foi encontrada coluna de grau (in/out/degree). Alguns gráficos de grau serão pulados.")
            degree_series = None

    bet_series = None
    if col_bet:
        bet_series = pd.to_numeric(metrics[col_bet], errors="coerce").fillna(0)
    else:
        print("Aviso: não foi encontrada coluna de betweenness. Gráfico de betweenness será pulado.")

    # Plot: Distribuição de grau (log-log style)
    if degree_series is not None:
        plt.figure()
        # Use log bins for heavy-tailed distributions
        vals = degree_series[degree_series > 0]
        if len(vals) == 0:
            print("Nenhum valor positivo de grau para plotar.")
        else:
            minv = vals.min()
            maxv = vals.max()
            bins = np.logspace(np.log10(max(minv,1)), np.log10(maxv if maxv>1 else 2), 40)
            plt.hist(vals, bins=bins, color="#1f77b4", alpha=0.8)
            plt.xscale("log")
            plt.yscale("log")
            plt.xlabel("Grau (log)")
            plt.ylabel("Frequência (log)")
            plt.title("Distribuição do Grau (log-log)")
            plt.tight_layout()
            plt.savefig(OUTDIR / "distribution_degree_loglog.png")
            plt.close()
            print("Gerado: distribution_degree_loglog.png")

    # Plot: Distribuição betweenness (log-log)
    if bet_series is not None:
        plt.figure()
        vals = bet_series[bet_series > 0]
        if len(vals) == 0:
            print("Nenhum valor positivo de betweenness para plotar.")
        else:
            minv = vals.min()
            maxv = vals.max()
            bins = np.logspace(np.log10(max(minv,1e-12)), np.log10(maxv if maxv>1e-12 else 1e-12), 40)
            plt.hist(vals, bins=bins, color="#ff7f0e", alpha=0.8)
            plt.xscale("log")
            plt.yscale("log")
            plt.xlabel("Betweenness (log)")
            plt.ylabel("Frequência (log)")
            plt.title("Distribuição da Centralidade de Intermediação (log-log)")
            plt.tight_layout()
            plt.savefig(OUTDIR / "distribution_betweenness_loglog.png")
            plt.close()
            print("Gerado: distribution_betweenness_loglog.png")

# -------------------------
# 2) Ler resultados da simulação (curvas por iteração)
# -------------------------
results = safe_read_csv(RESULTS_CSV)
if results is None:
    print("Não foi possível carregar results_all_strategies.csv — verifique o caminho e o arquivo.")
    sys.exit(0)

# Normaliza nomes para facilitar
results.columns = [c.strip().lower() for c in results.columns]

# Detectar colunas importantes (variações de nome toleradas)
col_fraction = find_col(results.columns, [r"fraction", r"fraction_removed", r"frac"])
col_nodes_remaining = find_col(results.columns, [r"nodes_remaining", r"nodes", r"remaining"])
col_largest_scc = find_col(results.columns, [r"largest_scc", r"largest_scc_size", r"largest", r"scc"])
col_apl = find_col(results.columns, [r"apl", r"average_shortest", r"avg_path", r"average_path"])
col_strategy = find_col(results.columns, [r"strategy", r"method", r"type"])
col_num_components = find_col(results.columns, [r"num_components", r"components", r"isolated", r"n_comp"])

# Exibir detecção
print("\nColunas detectadas no results CSV:")
print("fraction ->", col_fraction)
print("nodes_remaining ->", col_nodes_remaining)
print("largest_scc ->", col_largest_scc)
print("apl ->", col_apl)
print("strategy ->", col_strategy)
print("num_components ->", col_num_components)

# Checagem mínima
if col_fraction is None or col_largest_scc is None or col_strategy is None:
    print("Erro: colunas essenciais não encontradas no results CSV. Precisa de 'fraction' / 'largest_scc' / 'strategy'.")
    sys.exit(1)

# Converte colunas numéricas
results[col_fraction] = pd.to_numeric(results[col_fraction], errors="coerce")
results[col_largest_scc] = pd.to_numeric(results[col_largest_scc], errors="coerce")
if col_apl:
    results[col_apl] = pd.to_numeric(results[col_apl], errors="coerce")
if col_nodes_remaining:
    results[col_nodes_remaining] = pd.to_numeric(results[col_nodes_remaining], errors="coerce")
if col_num_components:
    results[col_num_components] = pd.to_numeric(results[col_num_components], errors="coerce")

# Se não existir num_components, calcular a partir de nodes_remaining e largest_scc
if col_num_components is None and col_nodes_remaining:
    # Consideramos "componentes isolados" = nodes_remaining - largest_scc (como proxy)
    results["num_components_est"] = results[col_nodes_remaining] - results[col_largest_scc]
    col_num_components = "num_components_est"

# Renomear cols para conveniência
results = results.rename(columns={
    col_fraction: "fraction_removed",
    col_largest_scc: "largest_scc",
    col_apl: "apl" if col_apl else "apl",
    col_strategy: "strategy",
    col_num_components: "num_components"
})

# Ordenar
results = results.sort_values(by=["strategy", "fraction_removed"])

# -------------------------
# 3) Plot: SCC × fração removida (normalizada por V e também raw)
# -------------------------
# V = número total de nós inicial (tomamos o maior nodes_remaining presente no dataset)
V = None
if "nodes_remaining" in results.columns:
    V = results["nodes_remaining"].max()
else:
    # se não houver nodes_remaining, usamos a maior_scc inicial como proxy (não ideal)
    V = results["largest_scc"].max()

# Normaliza SCC entre 0 e 1 (tau_i / V)
results["scc_norm"] = results["largest_scc"] / V

plt.figure()
sns.lineplot(data=results, x="fraction_removed", y="scc_norm", hue="strategy", marker="o")
plt.title("Tamanho da Maior SCC (normalizado) × Fração de Nós Removidos")
plt.xlabel("Fração de Nós Removidos")
plt.ylabel("SCC normalizada (τᵢ / V)")
plt.legend(title="Estratégia", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig(OUTDIR / "scc_vs_fraction_normalized.png")
plt.close()
print("Gerado: scc_vs_fraction_normalized.png")

# Também plot raw (tamanho absoluto)
plt.figure()
sns.lineplot(data=results, x="fraction_removed", y="largest_scc", hue="strategy", marker="o")
plt.title("Tamanho da Maior SCC × Fração de Nós Removidos (absoluto)")
plt.xlabel("Fração de Nós Removidos")
plt.ylabel("Tamanho da maior SCC (nós)")
plt.legend(title="Estratégia", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()
plt.savefig(OUTDIR / "scc_vs_fraction_raw.png")
plt.close()
print("Gerado: scc_vs_fraction_raw.png")

# -------------------------
# 4) Plot: APL × fração removida
# -------------------------
if "apl" in results.columns:
    plt.figure()
    sns.lineplot(data=results, x="fraction_removed", y="apl", hue="strategy", marker="o")
    plt.title("APL × Fração de Nós Removidos")
    plt.xlabel("Fração de Nós Removidos")
    plt.ylabel("Average Path Length (APL)")
    plt.legend(title="Estratégia", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(OUTDIR / "apl_vs_fraction.png")
    plt.close()
    print("Gerado: apl_vs_fraction.png")
else:
    print("Coluna APL não encontrada nos resultados; pulando gráfico de APL.")

# -------------------------
# 5) Plot: Componentes isolados × fração / iteração
# -------------------------
# Se houver coluna num_components plotamos; caso contrário usamos (nodes_remaining - largest_scc)
if "num_components" in results.columns:
    plt.figure()
    sns.lineplot(data=results, x="fraction_removed", y="num_components", hue="strategy")
    plt.title("Componentes isolados × Fração de nós removidos")
    plt.xlabel("Fração removida")
    plt.ylabel("Componentes isolados")
    plt.legend(title="Estratégia", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(OUTDIR / "components_vs_fraction.png")
    plt.close()
    print("Gerado: components_vs_fraction.png")
else:
    print("num_components não disponível; usando nodes_remaining - largest_scc como proxy.")
    results["components_proxy"] = results["nodes_remaining"] - results["largest_scc"]
    plt.figure()
    sns.lineplot(data=results, x="fraction_removed", y="components_proxy", hue="strategy")
    plt.title("Componentes isolados (proxy) × Fração de nós removidos")
    plt.xlabel("Fração removida")
    plt.ylabel("Componentes isolados (proxy)")
    plt.legend(title="Estratégia", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(OUTDIR / "components_vs_fraction_proxy.png")
    plt.close()
    print("Gerado: components_vs_fraction_proxy.png")

# -------------------------
# 6) Gráficos agregados a partir de failure_impact_summary.csv (opcional)
# -------------------------
impact = safe_read_csv(IMPACT_SUMMARY_CSV)
if impact is not None:
    impact.columns = [c.strip().lower() for c in impact.columns]
    # AUC (qualquer coluna contendo auc)
    auc_col = find_col(impact.columns, [r"auc"])
    if auc_col:
        plt.figure()
        sns.barplot(data=impact, x="strategy", y=auc_col, palette="Blues_d")
        plt.title("AUC Normalizada por Estratégia")
        plt.xlabel("Estratégia")
        plt.ylabel("AUC Normalizada (%)")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        plt.savefig(OUTDIR / "auc_by_strategy.png")
        plt.close()
        print("Gerado: auc_by_strategy.png")

    # mean_scc_norm / mean_apl if existem
    if "mean_scc_norm" in impact.columns:
        plt.figure()
        sns.barplot(data=impact, x="strategy", y="mean_scc_norm", palette="GnBu_d")
        plt.title("Mean SCC Normalizada por Estratégia")
        plt.xlabel("Estratégia")
        plt.ylabel("Mean SCC Normalizada")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        plt.savefig(OUTDIR / "mean_scc_norm_by_strategy.png")
        plt.close()
        print("Gerado: mean_scc_norm_by_strategy.png")
    if "mean_apl" in impact.columns:
        plt.figure()
        sns.barplot(data=impact, x="strategy", y="mean_apl", palette="OrRd_r")
        plt.title("Mean APL por Estratégia")
        plt.xlabel("Estratégia")
        plt.ylabel("Mean APL")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        plt.savefig(OUTDIR / "mean_apl_by_strategy.png")
        plt.close()
        print("Gerado: mean_apl_by_strategy.png")

print("\nTodas as figuras foram geradas em:", OUTDIR)
