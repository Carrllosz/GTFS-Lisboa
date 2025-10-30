# ==========================================================
# simulate_failures.py — Simulação de falhas na rede multimodal
# ==========================================================
import networkx as nx
import random
import numpy as np
import pandas as pd
from tqdm import tqdm

# ==========================================================
# Funções auxiliares
# ==========================================================
def largest_scc_size(G):
    """Retorna o tamanho da maior componente fortemente conectada."""
    if G.number_of_nodes() == 0:
        return 0
    scc = max(nx.strongly_connected_components(G), key=len)
    return len(scc)

def avg_path_length_safe(G):
    """Calcula comprimento médio do caminho apenas se a rede for conectada."""
    try:
        largest_cc = max(nx.strongly_connected_components(G), key=len)
        subG = G.subgraph(largest_cc)
        return nx.average_shortest_path_length(subG)
    except Exception:
        return np.nan

def simulate_removal(G, strategy, step=0.05):
    """
    Executa uma simulação de remoção de nós segundo a estratégia especificada.
    Retorna DataFrame com métricas em cada etapa.
    """
    G = G.copy()
    n = G.number_of_nodes()
    results = []

    # Estratégias baseadas em métricas iniciais
    if strategy == "random":
        nodes_order = random.sample(list(G.nodes()), n)
    elif strategy == "initial_degree":
        nodes_order = sorted(G.degree, key=lambda x: x[1], reverse=True)
        nodes_order = [n for n, _ in nodes_order]
    elif strategy == "initial_betweenness":
        bet = nx.betweenness_centrality(G)
        nodes_order = sorted(bet.items(), key=lambda x: x[1], reverse=True)
        nodes_order = [n for n, _ in nodes_order]
    elif strategy == "multimodal_hubs":
        nodes_order = [n for n, data in G.nodes(data=True) if data.get("is_hub", False)]
        others = [n for n in G.nodes if n not in nodes_order]
        nodes_order += others
    else:
        nodes_order = list(G.nodes())

    remove_step = max(1, int(n * step))
    removed = 0

    for i in tqdm(range(0, n, remove_step), desc=f"{strategy}"):
        # Estratégias que recalculam métricas
        if strategy == "recalc_degree" and i > 0:
            degs = sorted(G.degree, key=lambda x: x[1], reverse=True)
            nodes_order = [n for n, _ in degs]
        elif strategy == "recalc_betweenness" and i > 0 and i % (n * 0.05) == 0:
            bet = nx.betweenness_centrality(G)
            nodes_order = sorted(bet.items(), key=lambda x: x[1], reverse=True)
            nodes_order = [n for n, _ in nodes_order]

        batch = nodes_order[i : i + remove_step]
        G.remove_nodes_from(batch)
        removed += len(batch)

        fraction_removed = removed / n
        lcc_size = largest_scc_size(G)
        apl = avg_path_length_safe(G)
        results.append({
            "fraction_removed": fraction_removed,
            "nodes_remaining": G.number_of_nodes(),
            "largest_scc_size": lcc_size,
            "APL": apl,
        })

    return pd.DataFrame(results)

# ==========================================================
# Execução principal
# ==========================================================
def main():
    # Carregar grafo multimodal (ajuste o caminho conforme seu arquivo)
    G = nx.read_gml("/home/automining/Pessoal/ORION/graphs/multimodal_graph.gml")


    strategies = [
        "random",
        "initial_degree",
        "initial_betweenness",
        "recalc_degree",
        "recalc_betweenness",
        "multimodal_hubs"
    ]

    all_results = {}
    for s in strategies:
        print(f"\n🚀 Simulando: {s}")
        df = simulate_removal(G, s)
        df["strategy"] = s
        all_results[s] = df
        df.to_csv(f"results_{s}.csv", index=False)

    # Combina tudo em um só arquivo
    combined = pd.concat(all_results.values(), ignore_index=True)
    combined.to_csv("results_all_strategies.csv", index=False)
    print("\n✅ Resultados salvos em results_all_strategies.csv")

if __name__ == "__main__":
    main()
