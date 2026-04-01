# Docker Harness

`docker/harness.Dockerfile` and `scripts/run-docker-harness.sh` provide an isolated verification surface for Clawhost Kit.

## Goals

- validate host bootstrap planning and dry-run install behavior in a disposable container
- validate project-instance `create`, `start`, and `status` using a repo URL supplied at runtime
- keep the target repo URL out of the image build context and inject it only at `docker run` time

## Usage

```bash
scripts/run-docker-harness.sh \
  --repo-url https://github.com/sejeonglee/llm-report-module \
  --artifacts-dir .artifacts/docker-harness
```

Add `--dry-run` to preview the `docker build` / `docker run` commands without executing Docker.
Artifacts are written to the host-mounted artifacts directory as JSON/log files.
