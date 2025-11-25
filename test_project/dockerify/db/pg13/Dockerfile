FROM postgres:13.5

# Set environment variables for PostgreSQL
# These are used by the entrypoint script to initialize the database
# ENV POSTGRES_DB=fastpg_db
# ENV POSTGRES_USER=postgres
# ENV POSTGRES_PASSWORD=ASd78hASlpmvC8vbd

# Optional: Copy initialization scripts
# Any .sql or .sh files placed in this directory will be executed
# when the container starts and the database is initialized.
# For example, create a 'init.sql' file in the same directory as the Dockerfile
# and uncomment the following line:
COPY dockerify/db/extensions.sql /docker-entrypoint-initdb.d/01_extensions.sql
COPY dockerify/db/pg13/init.sql /docker-entrypoint-initdb.d/
COPY dockerify/db/pg13/replication.sh /docker-entrypoint-initdb.d/05_replication.sh
