#!/bin/bash
set -e

DOCKER_BIN=$(which podman || which docker)
IMAGE_TAG="localhost/ucp-sovereign-middleware:latest"

export SREN_SIGNING_KEY=${SREN_SIGNING_KEY:-$(openssl rand -hex 32)}

$DOCKER_BIN build -t "$IMAGE_TAG" .

$DOCKER_BIN rm -f ucp-bunker || true

$DOCKER_BIN run -d \
  --name ucp-bunker \
  --read-only=true \
  --tmpfs /tmp:rw,nosuid,nodev \
  --cap-drop=ALL \
  --security-opt="no-new-privileges:true" \
  -e SREN_SIGNING_KEY="$SREN_SIGNING_KEY" \
  "$IMAGE_TAG"

sleep 2
$DOCKER_BIN logs ucp-bunker
