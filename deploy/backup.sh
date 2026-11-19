#!/usr/bin/env bash
# Nightly cron (host):  15 2 * * *  cd /opt/drama-benin && ./deploy/backup.sh
# Copy /var/backups/drama OFF the server too (object storage / another VPS), otherwise it is not a backup.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
DEST="${BACKUP_DIR:-/var/backups/drama}"
install -d -m 700 "$DEST"
FILE="$DEST/drama-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose -f docker-compose.prod.yml --env-file .env exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$FILE"
chmod 600 "$FILE"
find "$DEST" -name 'drama-*.dump' -mtime +14 -delete
echo "Backup written: $FILE"
# Restore:  docker compose ... exec -T db pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists < file.dump
