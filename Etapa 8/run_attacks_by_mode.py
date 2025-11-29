import os
import pandas as pd
import networkx as nx
import numpy as np
from tqdm import tqdm

GRAPH_DIR = "/home/automining/Pessoal/ORION/Etapa 2/graphs"
OUT_DIR = "/home/automining/Pessoal/ORION/Etapa 8"
os.makedirs(OUT_DIR, exist_ok=True)

# -------------------------
# Helper functions
# -------------------------
def largest_scc_size(G):
    if len(G) == 0:
        return 0
    sccs = list(nx.strongly_connected_components(G))
    return len(max(sccs, key=len)) if sccs else 0

def compute_auc(scc_list, V):
    """AUC normalized as used in the article."""
    return (100 / len(scc_list)) * sum(np.array(scc_list) / V)

def simulate_failures(G_initial, strategy_name):
    """Run a failure simulation for a single mode."""
    
    G = G_initial.copy()
    V = len(G)

    if strategy_name == "random":
        node_order = list(G.nodes())
        np.random.shuffle(node_order)

    elif strategy_name == "initial_degree":
        deg = dict(G.degree())
        node_order = sorted(deg, key=deg.get, reverse=True)

    elif strategy_name == "initial_betweenness":
        bc = nx.betweenness_centrality(G)
        node_order = sorted(bc, key=bc.get, reverse=True)

    elif strategy_name == "recalc_degree":
        node_order = []
        Gtemp = G.copy()
        while len(Gtemp) > 0:
            deg = dict(Gtemp.degree())
            target = max(deg, key=deg.get)
            node_order.append(target)
            Gtemp.remove_node(target)

    elif strategy_name == "recalc_betweenness":
        node_order = []
        Gtemp = G.copy()
        while len(Gtemp) > 0:
            bc = nx.betweenness_centrality(Gtemp)
            target = max(bc, key=bc.get)
            node_order.append(target)
            Gtemp.remove_node(target)

    else:
        raise ValueError("Estratégia desconhecida.")

    # simulate removals
    scc_sizes = []
    G_sim = G_initial.copy()

    for i, node in enumerate(node_order):
        G_sim.remove_node(node)
        scc_sizes.append(largest_scc_size(G_sim))

    return node_order, scc_sizes


# -------------------------
# Main process
# -------------------------
strategies = [
    "random",
    "initial_degree",
    "initial_betweenness",
    "recalc_degree",
    "recalc_betweenness"
]

results = []

print("\n🔍 Procurando grafos .gml em:", GRAPH_DIR)
files = [f for f in os.listdir(GRAPH_DIR) if f.endswith(".gml")]

if not files:
    print("❌ Nenhum arquivo .gml encontrado! Confira a pasta.")
    exit()

print("\n📌 Grafos detectados:")
for f in files:
    print(" -", f)

print("\n🚀 Iniciando análise por modo...\n")

for file in files:
    mode = file.replace(".gml", "").replace("_graph", "").upper()

    print(f"\n========================================================")
    print(f" MODO DETECTADO: {mode}")
    print(f" Arquivo: {file}")
    print("========================================================\n")

    G = nx.read_gml(os.path.join(GRAPH_DIR, file))
    V = len(G)

    print(f"📎 Total de nós: {V}")

    for strat in strategies:
        print(f"\n➡️ Executando estratégia: {strat}")

        _, scc_list = simulate_failures(G, strat)

        auc_value = compute_auc(scc_list, V)

        results.append({
            "mode": mode,
            "strategy": strat,
            "auc_normalized": auc_value,
            "total_nodes": V
        })


# -------------------------
# Save results
# -------------------------
df = pd.DataFrame(results)
csv_path = os.path.join(OUT_DIR, "results_modes_strategies.csv")
df.to_csv(csv_path, index=False)

print("\n\n✅ Arquivo salvo com sucesso em:")
print(csv_path)
print("\n🎉 Etapa 8 concluída!")
