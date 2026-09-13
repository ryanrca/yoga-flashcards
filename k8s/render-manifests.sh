#!/usr/bin/env bash
# Render the Helm chart to plain manifests for `kubectl apply -f`.
#
# The chart stays the single source of truth; this just flattens it. Output is
# gitignored because it embeds a generated Secret.
set -euo pipefail

RELEASE="${RELEASE:-yoga-flashcards}"
NAMESPACE="${NAMESPACE:-yoga-flashcards}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${OUT:-$HERE/manifests}"

rm -rf "$OUT"
mkdir -p "$OUT"

helm template "$RELEASE" "$HERE/helm" \
  --namespace "$NAMESPACE" \
  --output-dir "$OUT" \
  "$@"

echo "Rendered to $OUT"
echo "Apply with: kubectl apply -n $NAMESPACE -R -f $OUT"
