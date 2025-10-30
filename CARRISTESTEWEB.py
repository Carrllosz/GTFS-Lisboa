import os
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================
BASE_URL = "https://transitfeeds.com/p/carris/1000"
DOWNLOAD_DIR = "carris_gtfs"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AutominingScript/3.1)"}
MAX_PAGES = 100       # limite de segurança (~86 páginas)
MAX_WORKERS = 6       # número de downloads simultâneos
TIMEOUT = 30          # timeout por requisição (segundos)
RETRIES = 3           # número de tentativas por arquivo

# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def get_page(url):
    """Obtém o HTML da página com tratamento de erro."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"⚠️ Erro ao carregar {url}: {e}")
        return None

def sanitize_filename(name):
    """Remove caracteres inválidos e normaliza o nome do arquivo."""
    name = re.sub(r"[^\w\-]", "_", name)
    return name.strip("_")

def parse_versions(html):
    """Extrai lista de versões e links de download."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "table"})
    if not table:
        return []

    rows = table.find_all("tr")[1:]  # pula cabeçalho
    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        date = cols[0].get_text(strip=True)
        size = cols[1].get_text(strip=True)
        routes = cols[2].get_text(strip=True)
        download_link = None

        for a in cols[3].find_all("a"):
            if "Download" in a.text:
                download_link = urljoin(BASE_URL, a["href"])
                break

        if download_link:
            safe_date = sanitize_filename(date)
            filename = f"{safe_date}.zip"
            data.append({
                "date": date,
                "size": size,
                "routes": routes,
                "download": download_link,
                "filename": filename
            })
    return data

def download_file(item, max_retries=RETRIES):
    """Baixa um arquivo ZIP com verificação e tentativas."""
    url = item["download"]
    dest = os.path.join(DOWNLOAD_DIR, item["filename"])

    # pula se já existe e parece completo
    if os.path.exists(dest) and os.path.getsize(dest) > 50_000:
        return f"✅ Já existe: {item['filename']}"

    for attempt in range(1, max_retries + 1):
        try:
            with requests.get(url, headers=HEADERS, stream=True, timeout=TIMEOUT) as r:
                r.raise_for_status()
                total_length = int(r.headers.get("Content-Length", 0))
                written = 0
                tmp_path = dest + ".part"

                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            written += len(chunk)

                # Verifica integridade pelo tamanho baixado
                if total_length and abs(written - total_length) > 1024:
                    raise IOError(f"Tamanho inconsistente: esperado {total_length}, baixado {written}")

                os.replace(tmp_path, dest)
                return f"💾 OK: {item['filename']} ({written/1024:.1f} KB)"

        except Exception as e:
            print(f"⚠️ Tentativa {attempt} falhou em {item['filename']}: {e}")
            time.sleep(2)

    return f"❌ Falha após {max_retries} tentativas: {item['filename']}"

# ==========================================================
# EXECUÇÃO PRINCIPAL
# ==========================================================
def main():
    ensure_dir(DOWNLOAD_DIR)
    all_data = []
    page = 1
    start_time = time.time()

    print("🔍 Iniciando scraping das versões GTFS da Carris...\n")

    while page <= MAX_PAGES:
        url = f"{BASE_URL}?p={page}"
        html = get_page(url)
        if not html:
            break

        data = parse_versions(html)
        if not data:
            print(f"❌ Nenhum dado encontrado na página {page}. Fim da lista.")
            break

        print(f"📄 Página {page}: {len(data)} versões encontradas.")
        all_data.extend(data)
        page += 1
        time.sleep(0.4)  # pequena pausa entre páginas

    print(f"\n📦 Total de versões encontradas: {len(all_data)}\n")

    # ======================================================
    # DOWNLOAD PARALELO
    # ======================================================
    print("🚀 Iniciando downloads simultâneos...\n")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_file, item): item for item in all_data}
        for future in as_completed(futures):
            print(future.result())

    total_time = time.time() - start_time
    print(f"\n✅ Concluído! {len(all_data)} arquivos processados em {total_time:.1f}s.")
    print("📁 Pasta:", os.path.abspath(DOWNLOAD_DIR))

# ==========================================================
if __name__ == "__main__":
    main()
