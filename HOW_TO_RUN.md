# How to Run PhishGuard on Windows

This project has a Python FastAPI backend and a static frontend. The frontend runs on port 5502 and the API runs on port 8000.

## 1) Open PowerShell in the project folder

```powershell
Set-Location "C:\Users\chand\OneDrive\Desktop\phishing-url-risk-detector\phishing-url-risk-detector"
```

## 2) Create the virtual environment and install dependencies

If this is the first time running the project, or if the environment is missing:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the environment already exists, skip the create step and just use the same install command when you want to refresh packages.

## 3) Start the backend

In one PowerShell window, run:

```powershell
Set-Location "C:\Users\chand\OneDrive\Desktop\phishing-url-risk-detector\phishing-url-risk-detector"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

You can also use the shortcut script:

```powershell
.\start_backend.ps1
```

The backend API is available at:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/

## 4) Start the frontend

In a second PowerShell window, run:

```powershell
Set-Location "C:\Users\chand\OneDrive\Desktop\phishing-url-risk-detector\phishing-url-risk-detector"
.\.venv\Scripts\python.exe -m http.server 5502 --bind 127.0.0.1
```

You can also use the shortcut script:

```powershell
.\start_frontend.ps1
```

Open the dashboard here:

- http://127.0.0.1:5502/

## 5) Stop the running servers

Press Ctrl+C in each terminal window that is running a server.

## 6) Run the tests

```powershell
Set-Location "C:\Users\chand\OneDrive\Desktop\phishing-url-risk-detector\phishing-url-risk-detector"
.\.venv\Scripts\python.exe -m pytest
```

## 7) If the model file is missing

This project uses a trained ML model stored in the `models` folder. If that model is not present in a fresh checkout, run:

```powershell
git lfs fetch --include="models/random_forest_url_final.joblib" origin 54ff827
New-Item -ItemType Directory -Path .\models -Force | Out-Null
Copy-Item .\.git\lfs\objects\d2\1c\d21c59a671d949ca178c8697f1f76c55d57e7f835affbea8ec0b2d2f81bd1166 .\models\random_forest_url_final.joblib
```

If Git LFS is not available, the project cannot use the trained model until that artifact is restored.

## 8) GitHub backup steps

To save your work safely:

```powershell
git status
git add .
git commit -m "PhishGuard update"
git push origin main
```

If your default branch is not `main`, replace it with the actual branch name shown by `git branch`.

## 9) Common troubleshooting

- Backend fails to start: verify that the `.venv` folder exists and that `requirements.txt` was installed.
- Frontend stays blank: make sure the backend is running on port 8000 and the static server is running on port 5502.
- URL rejected as a private or local destination: this is intentional. The app blocks private or loopback addresses before scanning.
- Model unavailable: restore the model from Git LFS before scanning.

## Quick start

The simplest beginner flow is:

```powershell
Set-Location "C:\Users\chand\OneDrive\Desktop\phishing-url-risk-detector\phishing-url-risk-detector"
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\start_backend.ps1
```

Then open a second PowerShell window and run:

```powershell
Set-Location "C:\Users\chand\OneDrive\Desktop\phishing-url-risk-detector\phishing-url-risk-detector"
.\start_frontend.ps1
```

Then open http://127.0.0.1:5502/ in the browser.
