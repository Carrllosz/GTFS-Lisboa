import os
import zipfile
import pandas as pd
import networkx as nx

# ==========================================================
# CONFIGURAÇÕES (ajuste conforme o operador)
# ==========================================================
OPERATOR_NAME = "Rodoviária de Lisboa"
GTFS_FOLDER = "rodoviaria_lisboa_gtfs"
OUTPUT_GRAPH = "graphs/rodoviaria_lisboa_graph.gml"




# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================
def extract_latest_gtfs(folder):
    """Extrai o GTFS mais recente (último ZIP) da pasta."""
    zips = [f for f in os.listdir(folder) if f.endswith(".zip")]
    if not zips:
        raise FileNotFoundError(f"Nenhum arquivo ZIP encontrado em {folder}")
    latest_zip = sorted(zips)[-1]
    path_zip = os.path.join(folder, latest_zip)
    extract_dir = os.path.join(folder, "unzipped")
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(path_zip, "r") as z:
        z.extractall(extract_dir)
    print(f"📦 Extraído: {latest_zip}")
    return extract_dir

def load_gtfs_data(folder):
    """Carrega os principais arquivos GTFS em DataFrames."""
    stops = pd.read_csv(os.path.join(folder, "stops.txt"), dtype=str)
    stop_times = pd.read_csv(os.path.join(folder, "stop_times.txt"), dtype=str)
    trips = pd.read_csv(os.path.join(folder, "trips.txt"), dtype=str)
    routes = pd.read_csv(os.path.join(folder, "routes.txt"), dtype=str)
    return stops, stop_times, trips, routes

def build_graph(stops, stop_times, trips, routes, mode):
    """Cria o grafo direcionado (DiGraph) de um modo de transporte."""
    G = nx.DiGraph(mode=mode)

    # Mapeia coordenadas dos stops
    stop_coords = {
        row["stop_id"]: (float(row["stop_lon"]), float(row["stop_lat"]))
        for _, row in stops.iterrows()
    }

    # Junta informações de trip + rota
    stop_times = stop_times.merge(trips[["trip_id", "route_id"]], on="trip_id", how="left")

    # Cria arestas entre paragens consecutivas no mesmo trip
    for trip_id, group in stop_times.groupby("trip_id"):
        group = group.sort_values("stop_sequence")
        route_id = group["route_id"].iloc[0]
        for i in range(len(group) - 1):
            u = group.iloc[i]["stop_id"]
            v = group.iloc[i + 1]["stop_id"]
            if u != v:
                G.add_edge(u, v, line=route_id)

    # Adiciona atributos geográficos aos nós
    for stop_id, (lon, lat) in stop_coords.items():
        G.nodes[stop_id]["x"] = lon
        G.nodes[stop_id]["y"] = lat

    print(f"✅ Grafo criado: {len(G.nodes())} nós e {len(G.edges())} arestas.")
    return G

# ==========================================================
# EXECUÇÃO PRINCIPAL
# ==========================================================
def main():
    os.makedirs("graphs", exist_ok=True)
    folder = extract_latest_gtfs(GTFS_FOLDER)
    stops, stop_times, trips, routes = load_gtfs_data(folder)
    G = build_graph(stops, stop_times, trips, routes, OPERATOR_NAME)
    nx.write_gml(G, OUTPUT_GRAPH)
    print(f"💾 Salvo: {OUTPUT_GRAPH}")

if __name__ == "__main__":
    main()
