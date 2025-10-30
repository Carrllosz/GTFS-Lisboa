import os, time, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://transitfeeds.com/p/fertagus/1001"
DOWNLOAD_DIR = "fertagus_gtfs"
MAX_PAGES = 116
# resto igual


HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AutominingScript/3.1)"}
MAX_WORKERS = 6
TIMEOUT = 30
RETRIES = 3

def ensure_dir(p): os.makedirs(p, exist_ok=True)
def sanitize(n): return re.sub(r"[^\w\-]", "_", n).strip("_")

def get_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"⚠️ Erro ao carregar {url}: {e}")
        return None

def parse_versions(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "table"})
    if not table: return []
    rows = table.find_all("tr")[1:]
    data = []
    for r in rows:
        c = r.find_all("td")
        if len(c) < 4: continue
        date = c[0].get_text(strip=True)
        link = None
        for a in c[3].find_all("a"):
            if "Download" in a.text:
                link = urljoin(BASE_URL, a["href"])
                break
        if link:
            data.append({"date": date, "download": link, "filename": f"{sanitize(date)}.zip"})
    return data

def download_file(item):
    url, fn = item["download"], item["filename"]
    dest = os.path.join(DOWNLOAD_DIR, fn)
    if os.path.exists(dest) and os.path.getsize(dest) > 50_000:
        return f"✅ Já existe: {fn}"
    for attempt in range(1, RETRIES + 1):
        try:
            with requests.get(url, headers=HEADERS, stream=True, timeout=TIMEOUT) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                tmp = dest + ".part"
                written = 0
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk); written += len(chunk)
                if total and abs(written - total) > 1024:
                    raise IOError("Tamanho inconsistente")
                os.replace(tmp, dest)
                return f"💾 OK: {fn} ({written/1024:.1f} KB)"
        except Exception as e:
            print(f"⚠️ Tentativa {attempt} falhou em {fn}: {e}")
            time.sleep(2)
    return f"❌ Falha: {fn}"

def main():
    ensure_dir(DOWNLOAD_DIR)
    all_data, page = [], 1
    print(f"🔍 Coletando versões GTFS - {BASE_URL}\n")
    while page <= MAX_PAGES:
        html = get_page(f"{BASE_URL}?p={page}")
        if not html: break
        d = parse_versions(html)
        if not d: break
        print(f"📄 Página {page}: {len(d)} versões")
        all_data.extend(d); page += 1; time.sleep(0.4)
    print(f"\n📦 Total: {len(all_data)} versões\n")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for f in as_completed([ex.submit(download_file, i) for i in all_data]):
            print(f.result())
    print(f"\n✅ Concluído! Arquivos em: {os.path.abspath(DOWNLOAD_DIR)}")

if __name__ == "__main__": main()
