#!/usr/bin/env bash
# Runs once on `mda deploy` / `mda dev`; the result is saved as a snapshot that every new
# thread's sandbox starts from. Rebuilt only when this file changes.
set -euo pipefail

# Tools the agent can use with `execute` (e.g. to convert reports or draw charts).
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq pandoc python3-pandas python3-matplotlib > /dev/null

# Seed the working directory with a report template.
mkdir -p /workspace/templates
cat > /workspace/templates/report.md <<'EOF'
# <Title>

## Summary

## Findings

## Sources
EOF
