"""Connection management: one reused connection, parameterized queries only."""
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

from .config import DbConfig, load_config
from .errors import AppError, friendly


class Database:
    def __init__(self, config: DbConfig | None = None):
        self.config = config or load_config()
        self._conn = None

    # -- connection -------------------------------------------------------
    def connect(self):
        if self._conn is not None and not self._conn.closed:
            return self._conn
        cfg = self.config
        try:
            self._conn = psycopg2.connect(
                host=cfg.host, port=cfg.port, dbname=cfg.dbname,
                user=cfg.user, password=cfg.password, connect_timeout=5,
                # search path: our schema first, public for pgcrypto's crypt()
                options=f"-c search_path={cfg.schema},public",
            )
        except psycopg2.Error as exc:
            raise friendly(exc) from exc
        return self._conn

    def test_connection(self) -> None:
        """Raise AppError unless the DB is reachable and the schema exists."""
        rows = self.query(
            "SELECT COUNT(*) AS n FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = ANY(%s)",
            (self.config.schema, ["gaminghubs", "wallets", "players",
                                  "gametransactions", "walletholders", "walletreviews"]),
        )
        if rows[0]["n"] < 6:
            raise AppError(
                f"Connected, but the '{self.config.schema}' schema is missing tables. "
                "Load the GameVerse schema first."
            )

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # -- helpers ------------------------------------------------------------
    @contextmanager
    def transaction(self):
        """Yields a dict cursor; commits on success, rolls back on any error."""
        conn = self.connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                yield cur
            conn.commit()
        except Exception as exc:
            conn.rollback()
            raise friendly(exc) from exc

    def query(self, sql: str, params=()) -> list[dict]:
        with self.transaction() as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def query_one(self, sql: str, params=()) -> dict | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def execute(self, sql: str, params=()) -> int:
        with self.transaction() as cur:
            cur.execute(sql, params)
            return cur.rowcount
