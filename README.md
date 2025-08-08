# Academic Paper Collector
This Python script collects academic papers from **DBLP** based on multiple keywords,  
retrieves **abstracts** from **Semantic Scholar**, and saves results both locally (CSV) and to **Google Sheets**.  
It supports **deduplication** and **incremental updates** for long-term usage.



## Features

- 🔍 Search multiple keywords in DBLP
- 📝 Retrieve abstracts from Semantic Scholar
- ♻️ Deduplicate by DOI or title
- ➕ Incremental updates (fetch only new papers)
- 📂 Save to both CSV and Google Sheets

---

## Requirements
- Python 3.8+
- Google Cloud project with **Google Sheets API** enabled
- `credentials.json` from your Google Service Account

---

## Installation
```bash
pip install requests gspread oauth2client
```

### Setup

1. **Google Sheets API**

    *  Go to Google Cloud Console, create a project

    *  Enable Google Sheets API

    *  Create a Service Account and download credentials.json

    *  Create a new Google Sheet and share it with the email from credentials.json (client_email)

2. **Edit CONFIG in the script**

    *  Add your keyword list in CONFIG["keywords"]

    *  Set CONFIG["google_credentials"] to your credentials.json path

    *  Set CONFIG["google_sheet_name"] to your desired Google Sheet name


---
## Usage
Run:

```bash
python main.py
```

* First run: Fetches all results for the keywords
* Later runs: Only fetches new papers (incremental update)

## Output

* Local CSV: papers_with_abstract.csv

* Google Sheets: Updated with latest papers

## Example CONFIG
```python
CONFIG = {
    "keywords": ["agentic recommendation", "personalized retrieval"],
    "max_results_per_keyword": 50,
    "output_file": "papers_with_abstract.csv",
    "dblp_delay": 0.2,
    "semantic_delay": 0.2,
    "google_sheet_name": "Literature Search Results",
    "google_credentials": "credentials.json"
}
```
## Notes

* Semantic Scholar API rate limit: ~100 requests/minute

* Deduplication uses DOI first, then title if DOI is missing

