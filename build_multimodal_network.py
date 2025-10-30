import os
import math
import networkx as nx
from itertools import combinations

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================
GRAPH_FOLDER = "graphs"
OUTPUT_GRAPH = "graphs/multimodal_graph.gml"
DISTANCE_THRESHOLD = 150  # metros: distância máxima para considerar um hub
CONST_INTERMODAL_WEIGHT = 1.0  # peso constante das conexões intermodais (alternativa à distância)

# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================
def haversine(lon1, lat1, lon2, lat2):
    """Calcula a distância em metros entre duas coordenadas geográficas."""
    R = 6371000  # raio médio da Terra em metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def load_graphs(folder):
    """Carrega todos os grafos GML e devolve uma lista."""
    graphs = []
    for file in os.listdir(folder):
        if file.endswith(".gml"):
            path = os.path.join(folder, file)
            G = nx.read_gml(path)
            G.graph["source_file"] = file
            graphs.append(G)
            print(f"📂 Carregado: {file} ({len(G.nodes())} nós, {len(G.edges())} arestas)")
    return graphs

def merge_graphs(graphs):
    """Combina todos os grafos monocamada em um grafo multilayer."""
    M = nx.DiGraph()
    for G in graphs:
        mode = G.graph.get("mode", os.path.splitext(G.graph["source_file"])[0])
        for n, attrs in G.nodes(data=True):
            nid = f"{mode}_{n}"  # prefixo para evitar colisões de stop_id
            M.add_node(nid, **attrs, mode=mode)
        for u, v, attrs in G.edges(data=True):
            uid, vid = f"{mode}_{u}", f"{mode}_{v}"
            M.add_edge(uid, vid, **attrs, mode=mode)
    print(f"\n🔗 Camadas combinadas: {len(graphs)} grafos → {len(M.nodes())} nós totais")
    return M

def connect_intermodal_edges(M):
    """Cria conexões intermodais entre nós próximos de modos diferentes."""
    nodes = list(M.nodes(data=True))
    added = 0

    # compara cada par de modos diferentes
    for (id1, a1), (id2, a2) in combinations(nodes, 2):
        if a1.get("mode") == a2.get("mode"):
            continue
        if "x" not in a1 or "x" not in a2:
            continue

        d = haversine(a1["x"], a1["y"], a2["x"], a2["y"])
        if d <= DISTANCE_THRESHOLD:
            w = CONST_INTERMODAL_WEIGHT or d
            M.add_edge(id1, id2, intermodal=True, weight=w, mode_from=a1["mode"], mode_to=a2["mode"])
            M.add_edge(id2, id1, intermodal=True, weight=w, mode_from=a2["mode"], mode_to=a1["mode"])
            added += 2

    print(f"🚉 {added} arestas intermodais criadas (distância ≤ {DISTANCE_THRESHOLD} m)")
    return M

# ==========================================================
# EXECUÇÃO PRINCIPAL
# ==========================================================
def main():
    print("🔍 Construindo grafo multimodal (multilayer)...\n")
    graphs = load_graphs(GRAPH_FOLDER)
    M = merge_graphs(graphs)
    M = connect_intermodal_edges(M)
    nx.write_gml(M, OUTPUT_GRAPH)
    print(f"\n✅ Rede multimodal salva em: {OUTPUT_GRAPH}")
    print(f"📊 Total: {len(M.nodes())} nós | {len(M.edges())} arestas")

if __name__ == "__main__":
    main()
