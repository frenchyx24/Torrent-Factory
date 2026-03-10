#!/usr/bin/env bash
# Script E2E réel : crée un fichier test, appelle l'API pour générer un vrai .torrent
# Prérequis: le serveur doit être démarré localement (http://localhost:5000)
set -euo pipefail
API_URL=${API_URL:-http://localhost:5000}
DATA_DIR=${DATA_DIR:-./data}
MOVIES_DIR="$DATA_DIR/movies"
OUT_DIR_DEFAULT="$DATA_DIR/torrents/movies"
mkdir -p "$MOVIES_DIR" "$OUT_DIR_DEFAULT"
TEST_NAME="e2e_test_movie_$(date +%s)"
TEST_FILE="$MOVIES_DIR/$TEST_NAME.txt"
# Créer un petit fichier réel
echo "e2e test content" > "$TEST_FILE"
# Appeler l'API pour ajouter la tâche
echo "Creating task for $TEST_NAME"
resp=$(curl -s -X POST "$API_URL/api/tasks/add" -H "Content-Type: application/json" -d "{\"tasks\":[{\"name\":\"$TEST_NAME\", \"lang_tag\":\"MULTI\"}], \"type\": \"movies\"}")
echo "API response: $resp"
# Extraire l'ID de la tâche depuis /api/tasks/list (dernier ajouté)
echo "Polling task list..."
for i in {1..60}; do
  sleep 1
  tasks=$(curl -s "$API_URL/api/tasks/list")
  # chercher la tâche par nom
  id=$(echo "$tasks" | jq -r ".[] | select(.name==\"$TEST_NAME\") | .id" | head -n1 || true)
  if [ -n "$id" ]; then
    echo "Found task id: $id"
    break
  fi
done
if [ -z "${id:-}" ]; then
  echo "Task not found in list; abort" >&2
  exit 2
fi
# Poll status
for i in {1..300}; do
  sleep 1
  st=$(curl -s "$API_URL/api/tasks/list" | jq -r ".[] | select(.id==\"$id\") | .status" || true)
  echo "Status: ${st:-unknown}"
  if [ "$st" = "completed" ]; then
    echo "Task completed"
    break
  fi
  if [ "$st" = "cancelled" ] || [ "$st" = "failed" ]; then
    echo "Task failed/cancelled" >&2
    exit 3
  fi
done
# Vérifier la présence du fichier .torrent
torrent_name="$TEST_NAME.torrent"
if [ -f "$OUT_DIR_DEFAULT/$torrent_name" ]; then
  echo "Torrent trouvé: $OUT_DIR_DEFAULT/$torrent_name"
  ls -lh "$OUT_DIR_DEFAULT/$torrent_name"
  exit 0
else
  echo "Torrent non trouvé dans $OUT_DIR_DEFAULT" >&2
  echo "Contenu du dossier $OUT_DIR_DEFAULT:" >&2
  ls -la "$OUT_DIR_DEFAULT" >&2 || true
  exit 4
fi
