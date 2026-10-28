pipeline {
    agent any
    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    environment {
        IMAGE_NAME = 'civictrack-ci'
        APP_CONTAINER = 'civictrack-app-ci'
        SELENIUM_CONTAINER = 'civictrack-selenium-ci'
        NETWORK_NAME = "civictrack-net-${BUILD_NUMBER}"
    }
    stages {
        stage('Checkout & Verify') {
            steps {
                checkout scm
                sh '''
                    set -eu
                    test -f app.py
                    test -f Dockerfile
                    test -f requirements.txt
                    test -f tests/test_civictrack.py
                    python3 -m py_compile app.py tests/test_civictrack.py
                    echo "Required files exist and Python syntax checks passed."
                '''
            }
        }
        stage('Build Docker Image') {
            steps {
                sh '''
                    set -eu
                    docker build --pull -t "$IMAGE_NAME:$BUILD_NUMBER" .
                    docker tag "$IMAGE_NAME:$BUILD_NUMBER" "$IMAGE_NAME:latest"
                '''
            }
        }
        stage('Start Test Environment') {
            steps {
                sh '''
                    set -eu
                    mkdir -p artifacts
                    docker network create "$NETWORK_NAME"
                    docker run -d --name "$APP_CONTAINER" --network "$NETWORK_NAME" \
                      -e DB_PATH=/tmp/civictrack-ci.db "$IMAGE_NAME:$BUILD_NUMBER"
                    docker run -d --name "$SELENIUM_CONTAINER" --network "$NETWORK_NAME" \
                      --shm-size=1g selenium/standalone-chrome:4.27.0

                    app_ready=0
                    for attempt in $(seq 1 40); do
                      if docker exec "$APP_CONTAINER" python -c \
                        "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)" \
                        >/dev/null 2>&1; then app_ready=1; break; fi
                      sleep 2
                    done
                    if [ "$app_ready" -ne 1 ]; then docker logs "$APP_CONTAINER"; echo "App not healthy"; exit 1; fi

                    selenium_ready=0
                    for attempt in $(seq 1 60); do
                      if docker exec "$APP_CONTAINER" python -c \
                        "import json,urllib.request; d=json.load(urllib.request.urlopen('http://$SELENIUM_CONTAINER:4444/status',timeout=3)); raise SystemExit(0 if d.get('value',{}).get('ready') else 1)" \
                        >/dev/null 2>&1; then selenium_ready=1; break; fi
                      sleep 2
                    done
                    if [ "$selenium_ready" -ne 1 ]; then docker logs "$SELENIUM_CONTAINER"; echo "Selenium not ready"; exit 1; fi
                    echo "Application and Selenium are ready."
                '''
            }
        }

        stage('Selenium End-to-End Tests') {
            steps {
                sh '''
                    set -eu

                    TEST_IMAGE="civictrack-tests:$BUILD_NUMBER"
                    TEST_CONTAINER="civictrack-test-runner-$BUILD_NUMBER"

                    docker build --pull \
                      -t "$TEST_IMAGE" \
                      -f- . <<'DOCKERFILE'
FROM python:3.12-slim
WORKDIR /workspace
COPY tests/ ./tests/
RUN pip install --no-cache-dir selenium==4.34.2 \
    && mkdir -p /artifacts
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
DOCKERFILE

                    set +e
                    docker run --name "$TEST_CONTAINER" \
                      --network "$NETWORK_NAME" \
                      -e APP_URL="http://$APP_CONTAINER:5000" \
                      -e SELENIUM_REMOTE_URL="http://$SELENIUM_CONTAINER:4444/wd/hub" \
                      -e SCREENSHOT_DIR=/artifacts \
                      "$TEST_IMAGE"
                    test_status=$?
                    set -e

                    mkdir -p artifacts
                    docker cp "$TEST_CONTAINER:/artifacts/." \
                      "$WORKSPACE/artifacts/" || true

                    docker rm -f "$TEST_CONTAINER" >/dev/null 2>&1 || true
                    docker image rm "$TEST_IMAGE" >/dev/null 2>&1 || true

                    exit "$test_status"
                '''
            }
        }
    }
    post {
        always {
            sh '''
                set +e
                mkdir -p artifacts
                docker logs "$APP_CONTAINER" > artifacts/civictrack-app.log 2>&1
                docker logs "$SELENIUM_CONTAINER" > artifacts/selenium.log 2>&1
                docker rm -f "$APP_CONTAINER" "$SELENIUM_CONTAINER" >/dev/null 2>&1
                docker network rm "$NETWORK_NAME" >/dev/null 2>&1
                docker image ls "$IMAGE_NAME" > artifacts/docker-images.txt 2>&1
            '''
            archiveArtifacts artifacts: 'artifacts/**', allowEmptyArchive: true, fingerprint: true
            sh 'docker image rm "$IMAGE_NAME:$BUILD_NUMBER" >/dev/null 2>&1 || true'
        }
        success { echo 'CivicTrack pipeline passed. Review archived screenshots and logs.' }
        failure { echo 'CivicTrack pipeline failed. Inspect stage logs and archived diagnostics.' }
    }
}
