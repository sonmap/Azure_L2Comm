#!/usr/bin/env bash
# Preserve the original nine positional arguments; target Azure AKS.
set -euo pipefail
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/run-aks.sh" "$@"
