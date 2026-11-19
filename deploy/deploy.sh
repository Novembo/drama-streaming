#!/usr/bin/env bash
# Usage: ./deploy/deploy.sh v1.2.3
# Pull-based deploy of a PRE-BUILT, tagged image: backup -> migrate -> restart -> health gate -> rollback.
# A single API container means a few seconds of downtime while it restarts (not "zero downtime").
set -euo pipefail
cd "$(dirname "$0")/.."

TAG="${1:?usage: deploy.sh <tag>}"
[[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Tag must look like v1.2.3"; exit 1; }
[ -f .env ] || { echo ".env missing (copy .env.production.example)"; exit 1; }
set -a; . ./.env; set +a
: "${IMAGE_REPO:?set IMAGE_REPO in .env (e.g. ghcr.io/you/drama-benin-api)}"

COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env"
PREVIOUS="$(cat .last_good_tag 2>/dev/null || true)"
export API_IMAGE="$IMAGE_REPO:$TAG"

echo "==> 1/5 backup before touching the schema"
./deploy/backup.sh

echo "==> 2/5 pull $API_IMAGE"
$COMPOSE pull api migrate

echo "==> 3/5 migrate (additive migrations only: the old version must keep working during the switch)"
$COMPOSE up -d db redis
$COMPOSE run --rm migrate

echo "==> 4/5 restart api"
$COMPOSE up -d --no-deps api caddy

echo "==> 5/5 health gate"
for i in $(seq 1 30); do
  status="$(docker inspect --format '{{.State.Health.Status}}' "$($COMPOSE ps -q api)" 2>/dev/null || echo starting)"
  [ "$status" = "healthy" ] && { echo "$TAG" > .last_good_tag; echo "Deployed $TAG"; docker image prune -f >/dev/null; exit 0; }
  sleep 2
done

echo "!! $TAG did not become healthy"
if [ -n "$PREVIOUS" ]; then
  echo "Rolling back code to $PREVIOUS (database migrations are NOT reverted automatically)"
  export API_IMAGE="$IMAGE_REPO:$PREVIOUS"
  $COMPOSE up -d --no-deps api
fi
exit 1
