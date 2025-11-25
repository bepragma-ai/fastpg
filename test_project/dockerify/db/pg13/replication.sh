#!/usr/bin/env bash
set -euo pipefail

# Configure replication settings and user on the primary database.
# Runs during initial database provisioning inside the container.

: "${POSTGRES_REPL_USER:?POSTGRES_REPL_USER is required for replication setup}"
: "${POSTGRES_REPL_PASSWORD:?POSTGRES_REPL_PASSWORD is required for replication setup}"

# Ensure replication role exists
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v rep_user="$POSTGRES_REPL_USER" -v rep_password="$POSTGRES_REPL_PASSWORD" <<'EOSQL'
DO $$
DECLARE
    rep_user text := :'rep_user';
    rep_password text := :'rep_password';
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = rep_user) THEN
        EXECUTE format('CREATE ROLE %I WITH REPLICATION LOGIN PASSWORD %L;', rep_user, rep_password);
    ELSE
        EXECUTE format('ALTER ROLE %I WITH REPLICATION LOGIN PASSWORD %L;', rep_user, rep_password);
    END IF;
END$$;
EOSQL

# Allow the replica to connect for replication
cat >> "$PGDATA/pg_hba.conf" <<'HBA_EOF'
host replication ${POSTGRES_REPL_USER} 0.0.0.0/0 md5
HBA_EOF

# Enable replication settings on the primary
cat >> "$PGDATA/postgresql.auto.conf" <<'CONF_EOF'
listen_addresses = '*'
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = '64MB'
CONF_EOF
