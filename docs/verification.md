# Verification

Use `scripts/run-verification.sh` to run the consolidated package checks and emit machine-readable artifacts.

```bash
scripts/run-verification.sh \
  --repo-url https://github.com/sejeonglee/llm-report-module \
  --artifacts-dir .artifacts/verification
```

It performs:

- Python test discovery over `tests/test_*.py`
- Python compile check for the instance lifecycle CLI
- Bash syntax checks for the bootstrap and Docker harness scripts
- Docker harness dry-run
- Live Docker harness execution with the repo URL injected at runtime

Use `--dry-run` to preview the verification plan without executing commands.
