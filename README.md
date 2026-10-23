# CivicTrack — Community Issue Reporting System

CivicTrack is a lightweight web application for reporting and tracking local community issues. This educational DevOps project demonstrates Git/GitHub, Jenkins, Docker, and Selenium browser automation.

## Features
- Report issues with title, category, location, and description.
- Track status: **Open**, **In Progress**, or **Resolved**.
- Filter by status and view summary counts.
- Persist reports in SQLite.
- Health endpoint at `/health`.
- Responsive dashboard and Selenium end-to-end browser tests.
- Jenkins pipeline builds the image, launches isolated containers, runs browser tests, archives screenshots/logs, and cleans up.

## Stack
Python 3.12, Flask, SQLite, Git/GitHub, Jenkins Declarative Pipeline, Docker, Selenium Standalone Chrome. No paid APIs are required.

## Run locally
Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux / WSL: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Run with Docker
```bash
docker build -t civictrack:local .
docker run --rm -p 5000:5000 -v civictrack-data:/data civictrack:local
```
Open http://localhost:5000. The named volume persists the SQLite database. Health check: http://localhost:5000/health.

## Jenkins setup
1. Use a Jenkins agent with Docker CLI access to a Docker daemon.
2. Create a Pipeline job using **Pipeline script from SCM** and this repository's Git URL.
3. Set the script path to `Jenkinsfile`.
4. Run **Build Now** and inspect the stage view and console output.

The pipeline creates a build-specific Docker network and archives Selenium screenshots and diagnostic logs. Docker socket access effectively grants privileged host access, so run this educational pipeline only on a trusted local/private Jenkins agent.

## Evidence screenshots
Capture genuine evidence from your environment—never fake test results:
- GitHub repository and commit history.
- CivicTrack dashboard and a submitted issue.
- Source code in your editor.
- `docker images` and `docker ps` output.
- Jenkins stage view and console output from an actual run.
- Archived Selenium screenshots and logs.

See [SCREENSHOT_GUIDE.md](SCREENSHOT_GUIDE.md) for the checklist.

## Project structure
```text
CivicTrack/
├── app.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── Jenkinsfile
├── templates/index.html
├── static/style.css
├── tests/test_civictrack.py
└── SCREENSHOT_GUIDE.md
```

## Scope and limitations
This is a demonstrator, not a production public reporting service. It has no accounts, uploads, notifications, or public deployment. Before exposing it to the internet, add authentication, CSRF protection, rate limiting, a backup/migration strategy, and a production server.

For educational use. Add a license if you plan to distribute the project.
