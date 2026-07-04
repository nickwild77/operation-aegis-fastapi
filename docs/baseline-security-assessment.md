# Operation Aegis: Baseline Security Assessment

## Status

This document describes the initial intentionally vulnerable state of the
FastAPI application before security hardening and DevSecOps automation.

The baseline must never be deployed to an external or production environment.

## Baseline reference

- Git tag: `baseline-vulnerable`
- Application framework: FastAPI
- Python version: 3.12
- Container port: 8080
- Security controls: not implemented
- CI/CD security gates: not implemented

## Baseline findings

| ID | Severity | Finding | Location | Planned control |
|---|---|---|---|---|
| AEGIS-001 | Critical | Hardcoded authentication secret | `main.py` | Gitleaks, Semgrep, environment-based configuration |
| AEGIS-002 | Critical | SQL query constructed using untrusted input | `main.py:/users` | Parameterized query, CodeQL, Semgrep, SonarQube |
| AEGIS-003 | High | Arbitrary file read / path traversal | `main.py:/read_file` | Path validation, allowlisted storage directory, SAST |
| AEGIS-004 | Medium | Internal exception details returned to the client | `main.py:/read_file` | Safe exception handling and generic error responses |
| AEGIS-005 | High | Unrestricted file upload | `main.py:/upload` | File type, size and path validation |
| AEGIS-006 | High | Token passed through URL query parameters | `main.py:/secure-data` | Authorization header and secure token validation |
| AEGIS-007 | Medium | Unhandled application exception | `main.py:/error` | Central exception handler and structured logging |
| AEGIS-008 | High | Container runs as root | `Dockerfile` | Non-root runtime user |
| AEGIS-009 | Medium | Non-reproducible `apt upgrade` during image build | `Dockerfile` | Minimal pinned base image and deterministic build |
| AEGIS-010 | Medium | Entire repository copied into image | `Dockerfile` | Restricted COPY instructions and `.dockerignore` |
| AEGIS-011 | Low | README documents port 80 while image uses 8080 | `README.md`, `Dockerfile` | Documentation correction |
| AEGIS-012 | Unknown | Dependencies have not been assessed for known CVEs | `requirements.txt` | pip-audit, Trivy, Dependabot |

## Existing test limitation

The original tests verify application functionality but do not provide a
security guarantee.

Some tests explicitly confirm vulnerable behavior, including:

- SQL injection payload propagation;
- access using a hardcoded token;
- arbitrary local file access;
- unrestricted file upload;
- unhandled exceptions.

These tests will be rewritten during the application-hardening phase.

## Baseline execution

The application was built with:

```bash
docker build -t operation-aegis:baseline .
It was run with:

docker run -d \
  --name operation-aegis-baseline \
  -p 8080:8080 \
  operation-aegis:baseline
```
Baseline endpoints
Method	Path	Purpose
GET	/	Basic application response
GET	/users	Intentionally vulnerable SQL construction
GET	/read_file	Intentionally vulnerable file access
GET	/error	Intentional unhandled exception
POST	/upload	Intentionally unrestricted upload
GET	/secure-data	Intentionally weak authentication
GET	/openapi.json	OpenAPI specification
GET	/docs	Swagger UI
Remediation strategy

The remediation will be implemented incrementally:

Establish local quality and secret checks.
Refactor and harden the FastAPI application.
Add unit and security regression tests.
Add SAST and SonarQube analysis.
Add SCA and container scanning.
Add secret scanning.
Add DAST using OWASP ZAP.
Add reporting, notifications, and GitHub security gates.
