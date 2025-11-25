#!/bin/bash
set -e

export PGDATA=/var/lib/postgresql/data

echo "Starting replica setup..."

# Wait for primary to be ready
echo "Waiting for primary database..."
until PGPASSWORD=${POSTGRES_PASSWORD} pg_isready -h ${PRIMARY_HOST} -p ${PRIMARY_PORT} -U ${POSTGRES_USER} 2>/dev/null
do
  echo "Primary is unavailable - sleeping"
  sleep 2
done

echo "Primary database is ready!"

# Check if this is the first run (data directory is empty or only has lost+found)
if [ ! -s "${PGDATA}/PG_VERSION" ]; then
    echo "Data directory is empty or uninitialized. Setting up replica..."
    
    # Clean the data directory
    rm -rf ${PGDATA}/*
    rm -rf ${PGDATA}/.[!.]*
    
    # Create base backup from primary
    echo "Running pg_basebackup from primary..."
    PGPASSWORD=${REPLICATION_PASSWORD} pg_basebackup \
        -h ${PRIMARY_HOST} \
        -p ${PRIMARY_PORT} \
        -U ${REPLICATION_USER} \
        -D ${PGDATA} \
        -Fp \
        -Xs \
        -P \
        -R
    
    echo "Base backup completed successfully!"
    
    # Ensure proper permissions
    chown -R postgres:postgres ${PGDATA}
    chmod 700 ${PGDATA}
else
    echo "Data directory already contains data. Skipping pg_basebackup."
fi

# Start PostgreSQL as the postgres user
echo "Starting PostgreSQL in hot standby mode..."
exec gosu postgres postgres -c config_file=/var/lib/postgresql/data/postgresql.conf