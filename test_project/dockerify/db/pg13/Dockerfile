FROM postgres:13.5

COPY dockerify/db/pg13/init.sql /docker-entrypoint-initdb.d/
COPY dockerify/db/pg13/setup-replication.sh /docker-entrypoint-initdb.d/

RUN chmod +x /docker-entrypoint-initdb.d/setup-replication.sh