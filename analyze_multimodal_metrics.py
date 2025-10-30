import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================
GRAPH_FILE = "graphs/multimodal_graph.gml"
OUTPUT_METRICS = "graphs/metrics_summary.csv"
OUTPUT_PLOTS_DIR = "graphs/plots"
SAMPLE_SIZE = 5000  # limite para centralidade (para redes muito grandes)

# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_graph(path):
    print(f"📂 Carregando grafo: {path}")
    G = nx.read_gml(path)
    print(f"✅ {len(G.nodes())} nós | {len(G.edges())} arestas carregadas")
    return G

def compute_basic_metrics(G):
    print("\n📊 Calculando métricas básicas...")

    df = pd.DataFrame({
        "node": list(G.nodes()),
        "mode": [G.nodes[n].get("mode", "N/A") for n in G.nodes()],
        "in_degree": [G.in_degree(n) for n in G.nodes()],
        "out_degree": [G.out_degree(n) for n in G.nodes()]
    })

    # Centralidade de intermediação (amostragem se grafo grande)
    if len(G) > SAMPLE_SIZE:
        sample_nodes = np.random.choice(G.nodes(), SAMPLE_SIZE, replace=False)
        print(f"⚠️ Rede grande — amostrando {SAMPLE_SIZE} nós para betweenness.")
        bet_centrality = nx.betweenness_centrality_subset(G, sources=sample_nodes, targets=sample_nodes)
    else:
        bet_centrality = nx.betweenness_centrality(G, normalized=True)

    df["betweenness"] = df["node"].map(bet_centrality)
    return df

def analyze_components(G):
    print("\n🔗 Analisando componentes fortemente conectados (SCC)...")
    sccs = list(nx.strongly_connected_components(G))
    sizes = [len(c) for c in sccs]
    largest_scc = max(sccs, key=len)
    subG = G.subgraph(largest_scc).copy()

    print(f"🧩 {len(sccs)} componentes encontrados")
    print(f"➡️ Maior componente: {len(largest_scc)} nós")

    # Comprimento médio do caminho (APL)
    try:
        apl = nx.average_shortest_path_length(subG)
        print(f"📏 Comprimento médio do caminho (APL): {apl:.4f}")
    except nx.NetworkXError:
        apl = np.nan
        print("⚠️ APL não pôde ser calculado (componente desconectado)")

    return sizes, apl

def plot_distributions(df):
    print("\n📈 Gerando distribuições...")
    ensure_dir(OUTPUT_PLOTS_DIR)

    metrics = ["in_degree", "out_degree", "betweenness"]
    for m in metrics:
        plt.figure(figsize=(6,4))
        plt.hist(df[m], bins=40, color="steelblue", alpha=0.8)
        plt.title(f"Distribuição de {m}")
        plt.xlabel(m)
        plt.ylabel("Frequência")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_PLOTS_DIR, f"{m}_distribution.png"))
        plt.close()

    print(f"✅ Gráficos salvos em: {OUTPUT_PLOTS_DIR}")

def save_metrics_summary(df, scc_sizes, apl):
    print("\n💾 Salvando métricas...")
    df.describe().to_csv(OUTPUT_METRICS)

    summary = {
        "total_nodes": len(df),
        "mean_in_degree": df["in_degree"].mean(),
        "mean_out_degree": df["out_degree"].mean(),
        "mean_betweenness": df["betweenness"].mean(),
        "num_SCC": len(scc_sizes),
        "largest_SCC": max(scc_sizes),
        "APL": apl
    }

    pd.DataFrame([summary]).to_csv("graphs/network_summary.csv", index=False)
    print("✅ Métricas salvas em:")
    print(f"  - {OUTPUT_METRICS}")
    print(f"  - graphs/network_summary.csv")

# ==========================================================
# EXECUÇÃO PRINCIPAL
# ==========================================================
def main():
    print("🔍 Etapa 4 — Análise de métricas base da rede multimodal\n")

    G = load_graph(GRAPH_FILE)
    df = compute_basic_metrics(G)
    scc_sizes, apl = analyze_components(G)
    plot_distributions(df)
    save_metrics_summary(df, scc_sizes, apl)

    print("\n🏁 Concluído com sucesso!")

if __name__ == "__main__":
    main()
