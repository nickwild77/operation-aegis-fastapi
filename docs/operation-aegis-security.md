# Operation Aegis Security Automation

Operation Aegis protects the FastAPI service with automated checks that run on
pull requests and on changes merged to `main`.

## Security gates

| Control | Tooling | Trigger | Blocking condition | Output |
|---|---|---|---|---|
| SAST | SonarQube GitHub integration | Pull requests and merges to `main` | SonarQube quality gate failure | SonarQube PR check and dashboard |
| SCA for dependency changes | GitHub Dependency Review | Pull requests that change dependency files | High or critical vulnerable dependency | Pull request summary comment |
| SCA for container images | Trivy | Pull requests and `main` pipeline | High or critical OS/library CVE | SARIF in GitHub Code Scanning |
| Python dependency audit | pip-audit | Pull requests and `main` pipeline | Known vulnerable Python dependency | Workflow log |
| DAST | OWASP ZAP API scan | Pull requests and `main` pipeline | ZAP action failure | Workflow artifact |
| Secret scanning | Gitleaks | Pull requests, pushes to `main`, weekly schedule, manual runs | Committed secret detected | SARIF artifact, Code Scanning upload, PR report |
| Release integrity | GitHub artifact attestations and SBOM | Pushes to `main` and version tags | Workflow failure | Registry attestations and SBOM artifact |

## SonarQube

SonarQube is connected in GitHub outside this repository's workflow files. It
publishes a pull request check and a `main` branch check for static application
security testing.

The SonarQube check is part of the required review signal for Operation Aegis.
Repository administrators should keep it required in branch protection alongside
the GitHub Actions checks.

## Secret handling

Runtime secrets are not stored in source control. Local development values live
in `.env`, which is ignored by Git. CI/CD secrets are supplied through GitHub
Encrypted Secrets and are only passed to jobs that need them.

The `Secret Scanning` workflow runs Gitleaks with full Git history available.
For pull requests the PR workflow scans the pull request commit range so
historical baseline findings do not block unrelated changes. Push, scheduled,
and manual runs scan the repository history through the standalone `Secret
Scanning` workflow.

## Feedback and reporting

Developers receive feedback in five places:

- GitHub check status on the pull request.
- Pull request comments from Dependency Review and the Operation Aegis security
  summary.
- GitHub Issues opened automatically when the consolidated PR report has failed
  controls.
- GitHub Actions job summaries and uploaded artifacts, including
  `security-report.md` and `security-report.json`.
- GitHub Code Scanning for SARIF-compatible findings.

The README badge named `Security Scans Passing` links to the pull request
security workflow status.
