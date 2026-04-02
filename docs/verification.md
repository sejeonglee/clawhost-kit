# Verification

Use `scripts/run-verification.sh` to run the consolidated package checks and emit machine-readable artifacts.

```bash
scripts/run-verification.sh \
  --repo-url https://github.com/sejeonglee/llm-report-module \
  --artifacts-dir .artifacts/verification
```

It performs:

- Python test discovery over `tests/test_*.py`
- Python compile checks for all scripts/tools
- Bash syntax checks for the bootstrap, verification, and Docker harness scripts
- Generated-artifact validation by creating a real project-instance config and validating it against `tools/config_boundary.py` and `tools/runtime_isolation.py`
- Docker harness dry-run
- Live Docker harness execution with the repo URL injected at runtime

Use `--dry-run` to preview the verification plan without executing commands.

The dry-run JSON includes `repo_url_injection.forwarded_to` so automation can confirm the supplied repo URL is forwarded only through the generated-artifact validation and Docker harness steps at runtime.
