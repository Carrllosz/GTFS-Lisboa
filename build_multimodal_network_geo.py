import os
import math
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, LineString
from itertools import combinations

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================
GRAPH_FOLDER = "graphs"
OUTPUT_GRAPH = "graphs/multimodal_graph.gml"
OUTPUT_GEOJSON_NODES = "graphs/multimodal_nodes.geojson"
OUTPUT_GEOJSON_EDGES = "graphs/multimodal_edges.geojson"
OUTPUT_GPKG = "graphs/multimodal_network.gpkg"

DISTANCE_THRESHOLD = 150  # metros: distância máxima entre modos
CONST_INTERMODAL_WEIGHT = 1.0  # peso das conexões intermodais (ou 0 para usar distância)

# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================
def haversine(lon1, lat1, lon2, lat2):
    """Distância em metros entre duas coordenadas geográficas."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def load_graphs(folder):
    """Carrega todos os grafos GML da pasta."""
    graphs = []
    for file in os.listdir(folder):
        if file.endswith(".gml") and not file.startswith("multimodal"):
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
            nid = f"{mode}_{n}"  # prefixo evita colisão
            M.add_node(nid, **attrs, mode=mode)
        for u, v, attrs in G.edges(data=True):
            uid, vid = f"{mode}_{u}", f"{mode}_{v}"
            M.add_edge(uid, vid, **attrs, mode=mode)
    print(f"\n🔗 {len(graphs)} grafos → {len(M.nodes())} nós totais")
    return M

def connect_intermodal_edges(M):
    """Cria arestas intermodais entre nós próximos de modos diferentes."""
    nodes = list(M.nodes(data=True))
    added = 0

    for (id1, a1), (id2, a2) in combinations(nodes, 2):
        if a1.get("mode") == a2.get("mode"):
            continue
        if "x" not in a1 or "y" not in a2:
            continue

        d = haversine(a1["x"], a1["y"], a2["x"], a2["y"])
        if d <= DISTANCE_THRESHOLD:
            w = CONST_INTERMODAL_WEIGHT or d
            M.add_edge(id1, id2, intermodal=True, weight=w,
                       mode_from=a1["mode"], mode_to=a2["mode"], distance_m=d)
            M.add_edge(id2, id1, intermodal=True, weight=w,
                       mode_from=a2["mode"], mode_to=a1["mode"], distance_m=d)
            added += 2

    print(f"🚉 {added} arestas intermodais criadas (≤ {DISTANCE_THRESHOLD} m)")
    return M

# ==========================================================
# EXPORTAÇÕES GEOGRÁFICAS
# ==========================================================
def export_geodata(M):
    """Exporta nós e arestas para GeoJSON e GeoPackage."""
    print("\n🌍 Exportando camadas geográficas...")

    # ---- NÓS ----
    nodes_data = []
    for n, attrs in M.nodes(data=True):
        if "x" in attrs and "y" in attrs:
            nodes_data.append({
                "id": n,
                "mode": attrs.get("mode", "N/A"),
                "geometry": Point(attrs["x"], attrs["y"])
            })
    gdf_nodes = gpd.GeoDataFrame(nodes_data, crs="EPSG:4326")

    # ---- ARESTAS ----
    edges_data = []
    for u, v, attrs in M.edges(data=True):
        nu, nv = M.nodes[u], M.nodes[v]
        if "x" in nu and "x" in nv:
            geom = LineString([(nu["x"], nu["y"]), (nv["x"], nv["y"])])
            edges_data.append({
                "source": u,
                "target": v,
                "mode": attrs.get("mode", "N/A"),
                "intermodal": attrs.get("intermodal", False),
                "weight": attrs.get("weight", 1.0),
                "geometry": geom
            })
    gdf_edges = gpd.GeoDataFrame(edges_data, crs="EPSG:4326")

    # ---- EXPORTA ----
    gdf_nodes.to_file(OUTPUT_GEOJSON_NODES, driver="GeoJSON")
    gdf_edges.to_file(OUTPUT_GEOJSON_EDGES, driver="GeoJSON")
    gdf_nodes.to_file(OUTPUT_GPKG, layer="nodes", driver="GPKG")
    gdf_edges.to_file(OUTPUT_GPKG, layer="edges", driver="GPKG")

    print(f"✅ GeoJSON exportado: {OUTPUT_GEOJSON_NODES}, {OUTPUT_GEOJSON_EDGES}")
    print(f"✅ GeoPackage exportado: {OUTPUT_GPKG}")

# ==========================================================
# EXECUÇÃO PRINCIPAL
# ==========================================================
def main():
    print("🔍 Construindo grafo multimodal (multilayer) + exportando para GIS...\n")
    graphs = load_graphs(GRAPH_FOLDER)
    M = merge_graphs(graphs)
    M = connect_intermodal_edges(M)
    nx.write_gml(M, OUTPUT_GRAPH)
    print(f"\n💾 Grafo multimodal salvo em: {OUTPUT_GRAPH}")
    export_geodata(M)
    print(f"\n📊 Total: {len(M.nodes())} nós | {len(M.edges())} arestas")

if __name__ == "__main__":
    main()
