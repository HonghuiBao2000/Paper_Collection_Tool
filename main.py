import requests
import csv
import time
from pathlib import Path
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ========================
# 配置
# ========================
CONFIG = {
    "keywords": ["learnable item tokenization"],
    "max_results_per_keyword": 50,
    "output_file": "papers_with_abstract.csv",
    "dblp_delay": 0.2,
    "semantic_delay": 0.2,
    "google_sheet_name": "Literature Search Results",
    "google_credentials": "credentials.json"
}

# ========================
# DBLP API
# ========================
def fetch_from_dblp(keyword, max_results=50):
    url = f"https://dblp.org/search/publ/api?q={keyword.replace(' ', '%20')}&h={max_results}&format=json"
    res = requests.get(url)
    data = res.json()

    papers = []
    for hit in data["result"]["hits"]["hit"]:
        info = hit["info"]
        papers.append({
            "title": info.get("title", ""),
            "authors": ", ".join(a["text"] for a in info.get("authors", {}).get("author", [])) \
                       if "authors" in info else "",
            "year": info.get("year", ""),
            "doi": info.get("doi", ""),
            "ee": info.get("ee", ""),
            "abstract": None
        })
    return papers

# ========================
# Semantic Scholar API
# ========================
def fetch_abstract_from_semanticscholar(doi=None, title=None):
    if doi:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,abstract"
    elif title:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={title}&limit=1&fields=title,abstract"
    else:
        return None

    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()

    if doi:
        return data.get("abstract", None)
    else:
        papers = data.get("data", [])
        if papers:
            return papers[0].get("abstract", None)
    return None

# ========================
# 数据处理
# ========================
def merge_deduplicate(papers):
    seen = set()
    deduped = []
    for p in papers:
        key = p["doi"].lower() if p["doi"] else p["title"].strip().lower()
        if key not in seen:
            seen.add(key)
            deduped.append(p)
    return deduped

def load_existing_papers(path):
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_to_csv(papers, filename):
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "authors", "year", "doi", "ee", "abstract"])
        writer.writeheader()
        writer.writerows(papers)

def save_to_google_sheet(papers, sheet_name, creds_path):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)

    try:
        sheet = client.open(sheet_name).sheet1
        sheet.clear()
    except gspread.SpreadsheetNotFound:
        sh = client.create(sheet_name)
        sh.share(creds.service_account_email, perm_type="user", role="writer")
        sheet = sh.sheet1

    headers = ["title", "authors", "year", "doi", "ee", "abstract"]
    sheet.append_row(headers)
    for p in papers:
        sheet.append_row([p.get(col, "") for col in headers])

# ========================
# 主流程
# ========================
def main():
    existing_papers = load_existing_papers(CONFIG["output_file"])
    existing_keys = {p["doi"].lower() if p["doi"] else p["title"].strip().lower() for p in existing_papers}

    all_papers = existing_papers.copy()

    for keyword in CONFIG["keywords"]:
        print(f"🔍 搜索关键词: {keyword}")
        papers = fetch_from_dblp(keyword, CONFIG["max_results_per_keyword"])
        time.sleep(CONFIG["dblp_delay"])

        # 只处理新论文
        new_papers = [p for p in papers if (p["doi"].lower() if p["doi"] else p["title"].strip().lower()) not in existing_keys]

        for p in new_papers:
            abs_text = None
            if p["doi"]:
                abs_text = fetch_abstract_from_semanticscholar(doi=p["doi"])
            if not abs_text:
                abs_text = fetch_abstract_from_semanticscholar(title=p["title"])
            p["abstract"] = abs_text
            time.sleep(CONFIG["semantic_delay"])
            existing_keys.add(p["doi"].lower() if p["doi"] else p["title"].strip().lower())

        all_papers.extend(new_papers)

    all_papers = merge_deduplicate(all_papers)

    save_to_csv(all_papers, CONFIG["output_file"])
    # save_to_google_sheet(all_papers, CONFIG["google_sheet_name"], CONFIG["google_credentials"])

    print(f"✅ 共收集 {len(all_papers)} 篇论文（已保存到 CSV 和 Google Sheets）")

if __name__ == "__main__":
    main()
