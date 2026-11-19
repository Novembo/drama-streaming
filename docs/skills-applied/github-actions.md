---
name: github-actions
description: "Create secure GitHub Actions workflows: caching, least-privilege permissions, pinned actions, deployment with OIDC or protected secrets. Use when setting up CI/CD on GitHub, deploying from a workflow without leaking cloud credentials, or fixing a failing workflow."
---

# GitHub Actions

## Workflow
1. Inspect repository conventions, branch strategy, existing workflows, and deployment target.
2. Define triggers narrowly and avoid duplicate workflow runs.
3. Use least-privilege permissions at workflow/job level.
4. Pin third-party actions to full commit SHAs when supply-chain assurance is required.
5. Cache dependencies safely using lockfile-based keys.
6. Separate test, build, publish, and deploy stages with explicit dependencies.
7. Protect environments and secrets; never print credentials.
8. Validate YAML and explain required repository/environment configuration.

## Rules
- Do not expose secrets to untrusted pull-request code.
- Avoid `pull_request_target` with checkout/execution of untrusted code.
- Set timeouts and concurrency controls where appropriate.
- Use artifacts for handoff between jobs rather than rebuilding inconsistently.
- Make deployments auditable and support rollback.
- Never claim a workflow passed without an actual run.

## Examples
```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read              # least privilege; grant more per job only when needed
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt
      - run: ruff check . && pytest -q
```
Pin third-party actions to a full commit SHA for sensitive workflows, never echo secrets, avoid `pull_request_target` with untrusted code, and use environment protection rules for deployment jobs.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
