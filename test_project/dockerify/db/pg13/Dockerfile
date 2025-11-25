FROM postgres:13.5

# Set environment variables for PostgreSQL
# These are used by the entrypoint script to initialize the database

# Optional: Copy initialization scripts
# Any .sql or .sh files placed in this directory will be executed
# when the container starts and the database is initialized.
# For example, create a 'init.sql' file in the same directory as the Dockerfile
# and uncomment the following line:
COPY dockerify/db/pg13/init.sql /docker-entrypoint-initdb.d/