#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_REPL_USER:?POSTGRES_REPL_USER is required for replica setup}"
: "${POSTGRES_REPL_PASSWORD:?POSTGRES_REPL_PASSWORD is required for replica setup}"
: "${POSTGRES_PRIMARY_HOST:?POSTGRES_PRIMARY_HOST is required for replica setup}"
POSTGRES_PRIMARY_PORT=${POSTGRES_PRIMARY_PORT:-5432}

export PGPASSWORD="$POSTGRES_REPL_PASSWORD"

# Wait until primary is ready to accept replication connections
until pg_isready -h "$POSTGRES_PRIMARY_HOST" -p "$POSTGRES_PRIMARY_PORT" -U "$POSTGRES_REPL_USER"; do
  echo "Waiting for primary at ${POSTGRES_PRIMARY_HOST}:${POSTGRES_PRIMARY_PORT}..."
  sleep 1
done

PGDATA="${PGDATA:-/var/lib/postgresql/data}"

# Initialize replica data directory using pg_basebackup if empty
if [ ! -s "$PGDATA/PG_VERSION" ]; then
  rm -rf "$PGDATA"
  pg_basebackup -D "$PGDATA" -X stream -P -h "$POSTGRES_PRIMARY_HOST" -p "$POSTGRES_PRIMARY_PORT" \
    -U "$POSTGRES_REPL_USER" --slot=fastpg_replica --create-slot

  cat >> "$PGDATA/postgresql.auto.conf" <<EOF
primary_conninfo = 'host=${POSTGRES_PRIMARY_HOST} port=${POSTGRES_PRIMARY_PORT} user=${POSTGRES_REPL_USER} password=${POSTGRES_REPL_PASSWORD} application_name=fastpg_replica'
primary_slot_name = 'fastpg_replica'
hot_standby = on
EOF

  touch "$PGDATA/standby.signal"
fi

unset PGPASSWORD

exec docker-entrypoint.sh postgres
