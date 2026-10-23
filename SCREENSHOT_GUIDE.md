# CivicTrack Screenshot Evidence Checklist

Capture evidence from the actual running project. Do not manufacture browser output, Jenkins status, or test results.

## Application and Selenium
- [ ] Dashboard in a browser.
- [ ] Selenium screenshot `01-dashboard.png`.
- [ ] `02-issue-created.png`: report submitted.
- [ ] `03-status-updated.png`: status changed to In Progress.
- [ ] `04-persisted-after-reload.png`: status remains after refresh.

The pipeline archives the generated Selenium screenshots and diagnostic logs when configured and run.

## Git/GitHub
- [ ] Repository page with files.
- [ ] Commit history showing project implementation.
- [ ] A source file open in GitHub or your editor.

## Docker
After building and running locally, capture real output from:
```bash
docker images
docker ps
docker logs civictrack-app
``
The Jenkins pipeline removes temporary containers after each build, so run the app locally for a separate `docker ps` screenshot.

## Jenkins
- [ ] Stage view from the actual build.
- [ ] Console output with the actual Selenium test summary.
- [ ] Build artifacts page containing screenshots/logs.

## Run locally in Docker
```bash
docker build -t civictrack:local .
docker run --rm --name civictrack-app -p 5000:5000 -v civictrack-data:/data civictrack:local
```
Open http://localhost:5000. Never include secrets or access tokens in screenshots.
