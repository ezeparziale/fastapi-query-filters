#!/usr/bin/env bash

set -euo pipefail

# Usage:
#   scripts/test-matrix.sh
#   scripts/test-matrix.sh tests/integration/sqlalchemy/test_json_key_operators.py
#
# Notes:
# - Assumes DB containers are already up (e.g. docker compose up -d).
# - Uses TEST_DATABASE_URL so the same pytest suite runs on each backend.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found"
  exit 1
fi

TEST_TARGETS=("$@")
if [ ${#TEST_TARGETS[@]} -eq 0 ]; then
  TEST_TARGETS=("tests")
fi

# Match compose.yaml credentials/ports
PG_HOST="${PG_HOST:-127.0.0.1}"
PG_PORT="${PG_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-postgres}"

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL8_PORT="${MYSQL8_PORT:-3306}"
MYSQL9_PORT="${MYSQL9_PORT:-3307}"
MYSQL_USER="${MYSQL_USER:-mysql}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-mysql}"
MYSQL_DATABASE="${MYSQL_DATABASE:-mysql}"

wait_for_postgres() {
  python3 - "$PG_HOST" "$PG_PORT" "$POSTGRES_USER" "$POSTGRES_PASSWORD" "$POSTGRES_DB" <<'PY'
import sys
import time
import psycopg

host, port, user, password, db = sys.argv[1:]
dsn = f"postgresql://{user}:{password}@{host}:{port}/{db}"
for _ in range(30):
    try:
        with psycopg.connect(dsn):
            print("PostgreSQL is ready")
            raise SystemExit(0)
    except Exception:
        time.sleep(2)
raise SystemExit(1)
PY
}

wait_for_mysql() {
  local port="$1"
  python3 - "$MYSQL_HOST" "$port" "$MYSQL_USER" "$MYSQL_PASSWORD" "$MYSQL_DATABASE" <<'PY'
import sys
import time
import pymysql

host, port, user, password, database = sys.argv[1:]
port = int(port)
for _ in range(30):
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )
        conn.close()
        print(f"MySQL on port {port} is ready")
        raise SystemExit(0)
    except Exception:
        time.sleep(2)
raise SystemExit(1)
PY
}

run_suite() {
  local name="$1"
  local db_url="$2"

  echo
  echo "========================================"
  echo "Running tests on: $name"
  echo "TEST_DATABASE_URL=$db_url"
  echo "========================================"

  TEST_DATABASE_URL="$db_url" python3 -m pytest "${TEST_TARGETS[@]}"
}

# SQLite
run_suite "sqlite" "sqlite:///:memory:"

# PostgreSQL 18 (default local port 5432)
wait_for_postgres
run_suite "postgres18" "postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${PG_HOST}:${PG_PORT}/${POSTGRES_DB}"

# MySQL 8 (default local port 3306)
wait_for_mysql "$MYSQL8_PORT"
run_suite "mysql8" "mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:${MYSQL8_PORT}/${MYSQL_DATABASE}"

# MySQL 9 (expected local port 3307 to run alongside MySQL 8)
wait_for_mysql "$MYSQL9_PORT"
run_suite "mysql9" "mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:${MYSQL9_PORT}/${MYSQL_DATABASE}"

echo
echo "Matrix completed successfully."
