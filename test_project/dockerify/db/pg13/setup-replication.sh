#!/bin/bash
set -e

# Create replication user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER ${POSTGRES_REPLICATION_USER:-replicator} WITH REPLICATION ENCRYPTED PASSWORD '${POSTGRES_REPLICATION_PASSWORD:-repl_password_123}';
EOSQL

# Update pg_hba.conf to allow replication connections
echo "host replication ${POSTGRES_REPLICATION_USER:-replicator} all md5" >> "$PGDATA/pg_hba.conf"