FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates git tmux \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY . /workspace

ENTRYPOINT ["bash", "/workspace/docker/harness-entrypoint.sh"]
