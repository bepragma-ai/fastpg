#!/bin/bash
set -euo pipefail

if [[ -z "${POSTGRES_REPLICATION_USER:-}" || -z "${POSTGRES_REPLICATION_PASSWORD:-}" ]]; then
  echo "Replication env vars not set; skipping replication setup."
  exit 0
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  DO
  $$
  BEGIN
    IF NOT EXISTS (
      SELECT FROM pg_roles WHERE rolname = '${POSTGRES_REPLICATION_USER}'
    ) THEN
      CREATE ROLE ${POSTGRES_REPLICATION_USER} WITH LOGIN REPLICATION PASSWORD '${POSTGRES_REPLICATION_PASSWORD}';
    ELSE
      ALTER ROLE ${POSTGRES_REPLICATION_USER} WITH LOGIN REPLICATION PASSWORD '${POSTGRES_REPLICATION_PASSWORD}';
    END IF;
  END
  $$;

  SELECT pg_create_physical_replication_slot('fastpg_replica')
  WHERE NOT EXISTS (
    SELECT 1 FROM pg_replication_slots WHERE slot_name = 'fastpg_replica'
  );
EOSQL

echo "host replication ${POSTGRES_REPLICATION_USER} 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
