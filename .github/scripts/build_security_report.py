#!/usr/bin/env python3
"""Build Operation Aegis security reports from workflow and GitHub check data."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

REPORT_DIR = Path("reports")


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def load_json(path: str, default: dict[str, Any]) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return default

    with file_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def normalize_result(result: str) -> str:
    result = (result or "unknown").lower()

    if result == "success":
        return "passed"
    if result in {"failure", "failed", "timed_out", "action_required"}:
        return "failed"
    if result in {"cancelled", "canceled"}:
        return "cancelled"
    if result == "skipped":
        return "skipped"
    if result in {"queued", "in_progress", "requested", "waiting", "pending"}:
        return "pending"

    return result


def conclusion_from_check_run(check_run: dict[str, Any]) -> str:
    if check_run.get("status") != "completed":
        return normalize_result(str(check_run.get("status", "pending")))

    return normalize_result(str(check_run.get("conclusion", "unknown")))


def conclusion_from_status(status: dict[str, Any]) -> str:
    state = str(status.get("state", "unknown")).lower()

    if state == "success":
        return "passed"
    if state in {"failure", "error"}:
        return "failed"
    if state == "pending":
        return "pending"

    return state


def find_sonar_result(
    check_runs: dict[str, Any],
    commit_status: dict[str, Any],
) -> dict[str, str]:
    for check_run in check_runs.get("check_runs", []):
        haystack = " ".join(
            [
                str(check_run.get("name", "")),
                str(check_run.get("app", {}).get("name", "")),
                str(check_run.get("details_url", "")),
            ]
        ).lower()

        if "sonar" in haystack:
            return {
                "name": str(check_run.get("name", "SonarQube")),
                "status": conclusion_from_check_run(check_run),
                "details_url": str(check_run.get("details_url", "")),
                "source": "github-check-run",
            }

    for status in commit_status.get("statuses", []):
        haystack = " ".join(
            [
                str(status.get("context", "")),
                str(status.get("description", "")),
                str(status.get("target_url", "")),
            ]
        ).lower()

        if "sonar" in haystack:
            return {
                "name": str(status.get("context", "SonarQube")),
                "status": conclusion_from_status(status),
                "details_url": str(status.get("target_url", "")),
                "source": "commit-status",
            }

    return {
        "name": "SonarQube",
        "status": "not_found",
        "details_url": "",
        "source": "github-checks-api",
    }


def status_badge(status: str) -> str:
    labels = {
        "passed": "passed",
        "failed": "failed",
        "cancelled": "cancelled",
        "skipped": "skipped",
        "pending": "pending",
        "not_found": "not found",
    }
    return labels.get(status, status)


def markdown_link(label: str, url: str) -> str:
    if not url:
        return label
    return f"[{label}]({url})"


def build_reports() -> dict[str, Any]:
    check_runs = load_json("check-runs.json", {"check_runs": []})
    commit_status = load_json("commit-status.json", {"statuses": []})
    sonar = find_sonar_result(check_runs, commit_status)

    run_url = (
        f"{env('GITHUB_SERVER_URL', 'https://github.com')}/"
        f"{env('GITHUB_REPOSITORY')}/actions/runs/{env('GITHUB_RUN_ID')}"
    )
    pr_url = (
        f"{env('GITHUB_SERVER_URL', 'https://github.com')}/"
        f"{env('GITHUB_REPOSITORY')}/pull/{env('PR_NUMBER')}"
    )

    controls = [
        {
            "layer": "Build",
            "control": "Docker image build",
            "tooling": "Docker",
            "status": normalize_result(env("BUILD_RESULT")),
            "details": run_url,
        },
        {
            "layer": "Quality",
            "control": "Linting and formatting",
            "tooling": "Pylint, Black",
            "status": normalize_result(env("LINT_RESULT")),
            "details": run_url,
        },
        {
            "layer": "SAST",
            "control": "Static application security testing",
            "tooling": sonar["name"],
            "status": sonar["status"],
            "details": sonar["details_url"],
            "source": sonar["source"],
        },
        {
            "layer": "SCA and DAST",
            "control": "Unit tests, Trivy, pip-audit, OWASP ZAP",
            "tooling": "pytest, Trivy, pip-audit, OWASP ZAP",
            "status": normalize_result(env("UNIT_SEC_RESULT")),
            "details": run_url,
        },
        {
            "layer": "Secrets",
            "control": "Committed secret detection",
            "tooling": "Gitleaks",
            "status": normalize_result(env("SECRET_RESULT")),
            "details": run_url,
        },
    ]

    failed_controls = [
        control
        for control in controls
        if control["status"] in {"failed", "failure", "timed_out", "action_required"}
    ]

    payload = {
        "repository": env("GITHUB_REPOSITORY"),
        "pull_request": env("PR_NUMBER"),
        "pull_request_url": pr_url,
        "head_sha": env("HEAD_SHA"),
        "workflow_run_url": run_url,
        "has_failures": bool(failed_controls),
        "controls": controls,
        "failed_controls": failed_controls,
    }

    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "security-report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    markdown = render_markdown_report(payload)
    (REPORT_DIR / "security-report.md").write_text(markdown, encoding="utf-8")
    (REPORT_DIR / "security-comment.md").write_text(
        "<!-- operation-aegis-security-summary -->\n" + markdown,
        encoding="utf-8",
    )
    (REPORT_DIR / "security-issue.md").write_text(
        render_issue_body(payload),
        encoding="utf-8",
    )

    return payload


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "## Operation Aegis security report",
        "",
        f"- Pull request: {markdown_link('#' + payload['pull_request'], payload['pull_request_url'])}",
        f"- Head SHA: `{payload['head_sha']}`",
        f"- Workflow run: {markdown_link('GitHub Actions', payload['workflow_run_url'])}",
        "",
        "| Layer | Control | Tooling | Status | Details |",
        "|---|---|---|---|---|",
    ]

    for control in payload["controls"]:
        details = markdown_link("open", control.get("details", ""))
        lines.append(
            "| {layer} | {control} | {tooling} | {status} | {details} |".format(
                layer=control["layer"],
                control=control["control"],
                tooling=control["tooling"],
                status=status_badge(control["status"]),
                details=details,
            )
        )

    lines.extend(
        [
            "",
            "Reports and evidence:",
            "",
            "- Trivy SARIF is uploaded to GitHub Code Scanning.",
            "- SBOM, ZAP, Gitleaks SARIF, and this consolidated report are uploaded as workflow artifacts.",
            "- SonarQube status is pulled from GitHub Checks or commit statuses for the PR head SHA.",
        ]
    )

    if payload["failed_controls"]:
        lines.extend(["", "Failed controls:", ""])
        for control in payload["failed_controls"]:
            lines.append(f"- {control['layer']}: {control['control']} ({control['tooling']})")
    else:
        lines.extend(["", "No failed Operation Aegis controls were detected in this report."])

    return "\n".join(lines) + "\n"


def render_issue_body(payload: dict[str, Any]) -> str:
    lines = [
        "<!-- operation-aegis-security-issue -->",
        "## Operation Aegis security failure",
        "",
        f"Pull request: {markdown_link('#' + payload['pull_request'], payload['pull_request_url'])}",
        f"Head SHA: `{payload['head_sha']}`",
        f"Workflow run: {markdown_link('GitHub Actions', payload['workflow_run_url'])}",
        "",
        "The following controls are failing and need review before merge:",
        "",
    ]

    for control in payload["failed_controls"]:
        lines.append(
            "- {layer}: {control} ({tooling}) - {details}".format(
                layer=control["layer"],
                control=control["control"],
                tooling=control["tooling"],
                details=markdown_link("details", control.get("details", "")),
            )
        )

    lines.extend(
        [
            "",
            "The pull request security summary and `operation-aegis-security-report` artifact contain the full report.",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_reports()
    github_output = env("GITHUB_OUTPUT")

    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as output:
            output.write(f"has_failures={str(payload['has_failures']).lower()}\n")


if __name__ == "__main__":
    main()
