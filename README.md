# PhishGuard

Phishing URL detection and risk analysis with a static HTML/CSS/JavaScript frontend and a FastAPI backend.

## Windows setup

From PowerShell in the project folder:

```powershell
Set-Location "C:\Users\chand\OneDrive\Desktop\phishing-url-risk-detector\phishing-url-risk-detector"
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the backend in the first terminal:

```powershell
Set-Location "C:\Users\chand\OneDrive\Desktop\phishing-url-risk-detector\phishing-url-risk-detector"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Start the static frontend in a second terminal:

```powershell
Set-Location "C:\Users\chand\OneDrive\Desktop\phishing-url-risk-detector\phishing-url-risk-detector"
.\.venv\Scripts\python.exe -m http.server 5502 --bind 127.0.0.1
```

Open <http://127.0.0.1:5502/>. API documentation is available at <http://127.0.0.1:8000/docs>. Stop either server with `Ctrl+C`; rerun its command to restart it.

Run backend tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Model availability and validation

The compatible 400-tree `RandomForestClassifier` is available as `models/random_forest_url_final.joblib`. Its Git LFS pointer is in project commit `54ff827`; its SHA-256 was verified against the pointer, and its 25 fitted feature names match the current URL feature extractor. A real inference check on `https://www.python.org` completed successfully. The model is cached after its first load by each backend process.

No strict external evaluation report is present in the repository, and the historical final-training script references additional adaptation datasets that are not committed. Feature compatibility and inference were verified, but no independent accuracy, precision, recall, or F1 claim is made. Do not load model files from untrusted sources.

If the LFS artifact is not present in a checkout, retrieve only the project-pinned object from the local Git history:

```powershell
git lfs fetch --include="models/random_forest_url_final.joblib" origin 54ff827
New-Item -ItemType Directory -Path .\models -Force | Out-Null
Copy-Item .\.git\lfs\objects\d2\1c\d21c59a671d949ca178c8697f1f76c55d57e7f835affbea8ec0b2d2f81bd1166 .\models\random_forest_url_final.joblib
```

## Security checks and history

URL input is limited to 2048 characters, validated as HTTP or HTTPS, and rejected if it is malformed or contains credentials. DNS resolution is bounded to three seconds; every returned address must be globally routable, and private, loopback, link-local, multicast, and reserved destinations are rejected before TLS or ML processing. HTTPS certificate validation has a five-second connection timeout and connects to the already-resolved public address while retaining the hostname for SNI. HTTP scans explicitly report TLS as not checked. PhishGuard does not fetch submitted pages or follow redirects, so redirect destinations are never contacted; submitted web content is not executed.

The scan history database is `db.sqlite3` in the project folder. Dashboard statistics and history use this database. URL-term likelihood requires historical scans from both ML classes; TF-IDF cosine similarity compares URL tokens with prior scans. Scan records do not store observed hyperlinks, so graph edges and PageRank scores are intentionally unavailable rather than inferred from hostname similarity. No external search index is integrated. Each IR panel reports when its required history is insufficient.
