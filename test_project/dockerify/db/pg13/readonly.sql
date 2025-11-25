-- Mark this instance as read-only after initialization to mimic a replica.
ALTER SYSTEM SET default_transaction_read_only = on;
SELECT pg_reload_conf();
