#!/bin/bash
# Script to check replication status

echo "=== MASTER STATUS ==="
docker exec obscura_postgres_master psql -U postgres -d obscura_db -c "SELECT * FROM pg_stat_replication;"

echo "=== SLAVE 1 STATUS ==="
docker exec obscura_postgres_slave1 psql -U postgres -d obscura_db -c "SELECT * FROM pg_stat_wal_receiver;"

echo "=== SLAVE 2 STATUS ==="
docker exec obscura_postgres_slave2 psql -U postgres -d obscura_db -c "SELECT * FROM pg_stat_wal_receiver;"

echo "=== LAG CHECK ==="
docker exec obscura_postgres_master psql -U postgres -d obscura_db -c "
SELECT
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) AS lag
FROM pg_stat_replication;
"