# Operation Aegis FastAPI

[![Security Scans Passing](https://github.com/nickwild77/operation-aegis-fastapi/actions/workflows/pr.yml/badge.svg)](https://github.com/nickwild77/operation-aegis-fastapi/actions/workflows/pr.yml)
[![Secret Scanning](https://github.com/nickwild77/operation-aegis-fastapi/actions/workflows/secrets-scan.yml/badge.svg)](https://github.com/nickwild77/operation-aegis-fastapi/actions/workflows/secrets-scan.yml)

This project sets up a simple FastAPI application (with some vulnerabilites) within a Docker container. It uses the official Python runtime and includes all necessary configurations to deploy a FastAPI app with Docker. The container will expose the app on port 80 and automatically run the FastAPI app on startup.

## Requirements

- Docker
- Python 3.12+
- FastAPI
- Uvicorn

## Features

- **Dockerized FastAPI application**: A containerized setup for easy deployment.
- **Python 3.12.5 runtime**: Uses the latest stable Python version as a base.
- **Efficient package installation**: Installs required dependencies via `requirements.txt`.
- **Operation Aegis security gates**: Pull requests are checked with SonarQube, Trivy, pip-audit, OWASP ZAP, Dependency Review, and Gitleaks.

## Operation Aegis security pipeline

The project uses GitHub Actions and SonarQube to block unsafe changes before
merge.

| Layer | Implementation | Feedback |
|---|---|---|
| SAST | SonarQube GitHub integration on pull requests and `main` | SonarQube pull request check |
| SCA | Trivy image scanning, pip-audit, GitHub Dependency Review, Dependabot | Code Scanning SARIF, PR comments, workflow logs |
| DAST | OWASP ZAP API scan against an ephemeral Docker deployment | Workflow artifact and check result |
| Secrets | PR Gitleaks gate, standalone Gitleaks workflow, pre-commit Gitleaks hook, detect-secrets baseline | Consolidated PR report, SARIF artifact, Code Scanning upload |
| Reporting | PR security summary, GitHub Issues, Markdown/JSON report artifacts, SBOM artifacts, release attestations | GitHub Actions summary, PR comments, artifacts, GitHub Security |

Security architecture and operating notes are documented in
[`docs/operation-aegis-security.md`](docs/operation-aegis-security.md).

## Project Structure

```bash
gcp-python-fastapi/
├── Dockerfile
├── requirements.txt
├── main.py  # FastAPI app entry point
└── ...
```

- **Dockerfile**: Configures the Docker container for the FastAPI app.
- **requirements.txt**: Specifies the required Python dependencies for the application.
- **main.py**: The entry point for the FastAPI application (Make sure to include this file in the project structure).

## Setup and Installation

### 1. Clone the repository

If you haven't cloned the project yet, use the following command:

```bash
git clone https://github.com/your-username/python-fastapi.git
cd python-fastapi
```

### 2. Build the Docker image

To build the Docker image, run the following command in the root of the project directory:

```bash
docker build -t operation-aegis:phase3 .
```

### 3. Run the Docker container

After the image is built, run the container:

```bash
docker run --env-file .env -p 80:8080 operation-aegis:phase3
```

This command will run the FastAPI app on port 80 of your localhost.

### 4. Access the app

Once the container is running, you can access the FastAPI application by navigating to:

```
http://localhost:80
```

## Dependencies

The project uses the following Python packages, which are listed in the `requirements.txt` file:

- `fastapi`: The core framework for building the API.
- `uvicorn`: ASGI server to run the FastAPI application.

To install dependencies locally, use the following:

```bash
pip install -r requirements.txt
```

## Notes

- This setup assumes that your FastAPI app’s entry point is `main.py`, and the FastAPI application instance is named `app`. If your app is structured differently, you may need to modify the `CMD` directive in the Dockerfile accordingly.
- The container will expose the application on port 80. If you want to use a different port, adjust the `EXPOSE` and `CMD` directives in the Dockerfile.
