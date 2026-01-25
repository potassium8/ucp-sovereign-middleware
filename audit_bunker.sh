#!/bin/bash
echo "--- [SREN AUDIT REPORT] ---"
if ! podman ps -a | grep -q ucp-bunker; then
    echo "ERREUR : Le conteneur ucp-bunker n'existe pas. Lance ./deploy.sh d'abord."
    exit 1
fi

echo -n "1. Filesystem Immutability: "
podman inspect ucp-bunker --format '{{.HostConfig.ReadonlyRootfs}}'

echo -n "2. Privileges Dropped:      "
podman inspect ucp-bunker --format '{{.HostConfig.CapDrop}}'

echo -n "3. Security Options:        "
podman inspect ucp-bunker --format '{{.HostConfig.SecurityOpt}}'

echo -n "4. Memory Usage:           "
podman stats ucp-bunker --no-stream --format "{{.MemUsage}}"
echo "---------------------------"
