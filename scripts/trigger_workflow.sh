#!/usr/bin/env bash
# Déclenche le workflow GitHub `ci-deploy.yml` via l'API
# Usage: GITHUB_TOKEN=ghp_xxx ./scripts/trigger_workflow.sh [ref]
set -euo pipefail
REF=${1:-main}
REPO=${REPO:-$(git config --get remote.origin.url || true)}
if [[ -z "$REPO" ]]; then
  echo "Impossible de déterminer le repo; exportez REPO='owner/repo' ou exécutez depuis un clone git" >&2
  exit 2
fi
# Convertir remote url en owner/repo si nécessaire
if [[ "$REPO" =~ git@github.com:(.*)\.git ]]; then
  REPO=${BASH_REMATCH[1]}
elif [[ "$REPO" =~ https://github.com/(.*)\.git ]]; then
  REPO=${BASH_REMATCH[1]}
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "Vous devez exporter GITHUB_TOKEN (PAT) avec scope 'repo' et 'workflow'" >&2
  exit 3
fi

echo "Déclenchement du workflow ci-deploy.yml sur ${REPO} à la ref ${REF}"
curl -sS -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${REPO}/actions/workflows/ci-deploy.yml/dispatches" \
  -d "{\"ref\": \"${REF}\"}"

echo "Requête envoyée. Vérifiez les actions GitHub." 
