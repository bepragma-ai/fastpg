#!/bin/bash
set -e

# Wait for primary to be ready
until pg_isready -h ${PRIMARY_HOST} -p ${PRIMARY_PORT} -U ${PGUSER}
do
  echo "Waiting for primary database to be ready..."
  sleep 2
done

# Remove any existing data
rm -rf ${PGDATA}/*

# Create base backup from primary
PGPASSWORD=${REPLICATION_PASSWORD} pg_basebackup -h ${PRIMARY_HOST} -p ${PRIMARY_PORT} -U ${REPLICATION_USER} -D ${PGDATA} -Fp -Xs -R

# Set proper permissions
chmod 700 ${PGDATA}

# Start PostgreSQL in standby mode
exec postgres