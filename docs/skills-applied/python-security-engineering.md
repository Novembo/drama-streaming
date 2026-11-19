---
name: python-security-engineering
description: "Secure Python applications: SSRF, path traversal, unsafe deserialization, injection, secrets, authentication and authorization, runtime config. Use when hardening, implementing, or reviewing a Python web service or API; for a line-by-line audit use security-code-review-python."
---

# Python Security Engineering

## Workflow
1. Assume inputs, dependencies, files, queues, model output, and external services are untrusted; enforce security in trusted code and infrastructure, not in comments or the UI.
2. Validate type, size, format, and business invariants at every trust boundary.
3. Authenticate, then authorize each action on each resource; enforce tenant and object scope in the data-access path and test for IDOR and privilege escalation.
4. Protect secrets (secret manager or injected environment, scoped and rotated) and keep them out of code, logs, and errors.
5. Harden outbound and file handling: timeouts and response-size limits on HTTP, SSRF controls, safe archive extraction, upload checks, template and redirect safety.
6. Keep dependencies locked and scanned (see `software-supply-chain-security`).
7. Verify with SAST, dependency and secret scanning, DAST where exposed, and targeted abuse tests.

## Rules
- Parameterize SQL; avoid `eval`, shell interpolation, and unsafe deserialization (`pickle`, unsafe YAML).
- Use maintained crypto and password-hashing libraries; never design custom crypto; compare secrets with `hmac.compare_digest`.
- Use the `secrets` module for tokens, not `random`.
- Do not claim compliance because a scanner passed.
- For a line-by-line review of risky patterns see `security-code-review-python`.

## Example (runnable: confine a path to a directory)
```python
# runnable
from pathlib import Path
import tempfile

def safe_child(root: Path, name: str) -> Path:
    base = root.resolve()
    candidate = (base / name).resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError("path outside allowed directory")
    return candidate

root = Path(tempfile.mkdtemp())
assert safe_child(root, "report.pdf").name == "report.pdf"
for bad in ("../secret.txt", "/etc/passwd", "a/../../x"):
    try:
        safe_child(root, bad)
    except ValueError:
        continue
    raise AssertionError(bad)
print("ok")
```
Path normalization is not a full sandbox: also consider symlinks and race conditions per the threat model.

## Verification
Record findings by exploitability and impact, add a regression test per fixed issue, and state what was not reviewed.

## Related

Language-neutral design vs implementation, or adjacent scope: `security-code-review-python`, `software-supply-chain-security`. Load the one that matches the task; load several only when the work spans them.

## Standards

Delivery workflow, quality gates and the completion report: follow `senior-engineering-standards` (included in the `core` profile).
