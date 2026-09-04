from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Any


class ObjectIndex:
    """Persistent, thread-safe local index of R2 object metadata."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS objects (
                    account_id TEXT NOT NULL,
                    bucket TEXT NOT NULL,
                    key TEXT NOT NULL,
                    key_folded TEXT NOT NULL,
                    size INTEGER NOT NULL DEFAULT 0,
                    etag TEXT NOT NULL DEFAULT '',
                    last_modified TEXT,
                    storage_class TEXT NOT NULL DEFAULT 'STANDARD',
                    PRIMARY KEY (account_id, bucket, key)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS object_search "
                "ON objects(account_id, bucket, key_folded)"
            )

    @staticmethod
    def _values(account_id: str, bucket: str, item: dict[str, Any]) -> tuple[Any, ...]:
        key = str(item["key"])
        return (
            account_id,
            bucket,
            key,
            key.casefold(),
            max(0, int(item.get("size") or 0)),
            str(item.get("etag") or ""),
            item.get("last_modified"),
            str(item.get("storage_class") or "STANDARD"),
        )

    def replace_bucket(
        self, account_id: str, bucket: str, objects: Iterable[dict[str, Any]]
    ) -> None:
        values = [self._values(account_id, bucket, item) for item in objects]
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM objects WHERE account_id = ? AND bucket = ?",
                (account_id, bucket),
            )
            connection.executemany(
                """
                INSERT INTO objects (
                    account_id, bucket, key, key_folded, size, etag,
                    last_modified, storage_class
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )

    def retain_buckets(self, account_id: str, buckets: Iterable[str]) -> None:
        names = list(buckets)
        with self._lock, self._connect() as connection:
            if not names:
                connection.execute("DELETE FROM objects WHERE account_id = ?", (account_id,))
                return
            placeholders = ",".join("?" for _ in names)
            connection.execute(
                f"DELETE FROM objects WHERE account_id = ? AND bucket NOT IN ({placeholders})",
                (account_id, *names),
            )

    def upsert(self, account_id: str, bucket: str, item: dict[str, Any]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO objects (
                    account_id, bucket, key, key_folded, size, etag,
                    last_modified, storage_class
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id, bucket, key) DO UPDATE SET
                    key_folded = excluded.key_folded,
                    size = excluded.size,
                    etag = excluded.etag,
                    last_modified = excluded.last_modified,
                    storage_class = excluded.storage_class
                """,
                self._values(account_id, bucket, item),
            )

    def move(
        self,
        account_id: str,
        bucket: str,
        source_key: str,
        destination_key: str,
        *,
        fallback: dict[str, Any] | None = None,
    ) -> None:
        with self._lock, self._connect() as connection:
            source = connection.execute(
                """
                SELECT size, etag, last_modified, storage_class FROM objects
                WHERE account_id = ? AND bucket = ? AND key = ?
                """,
                (account_id, bucket, source_key),
            ).fetchone()
            connection.execute(
                "DELETE FROM objects WHERE account_id = ? AND bucket = ? AND key IN (?, ?)",
                (account_id, bucket, source_key, destination_key),
            )
            if source is None and fallback is None:
                return
            item = dict(source) if source is not None else dict(fallback or {})
            item["key"] = destination_key
            connection.execute(
                """
                INSERT INTO objects (
                    account_id, bucket, key, key_folded, size, etag,
                    last_modified, storage_class
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(account_id, bucket, item),
            )

    def delete(self, account_id: str, bucket: str, keys: Iterable[str]) -> None:
        values = [(account_id, bucket, key) for key in keys]
        if not values:
            return
        with self._lock, self._connect() as connection:
            connection.executemany(
                "DELETE FROM objects WHERE account_id = ? AND bucket = ? AND key = ?",
                values,
            )

    def delete_bucket(self, account_id: str, bucket: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM objects WHERE account_id = ? AND bucket = ?",
                (account_id, bucket),
            )

    def search(
        self,
        account_id: str,
        bucket: str,
        query: str,
        offset: int = 0,
        *,
        limit: int = 100,
    ) -> dict[str, Any]:
        normalized = query.strip().casefold()
        if not normalized:
            raise ValueError("検索文字列を入力してください。")
        offset = max(0, int(offset))
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT key, size, etag, last_modified, storage_class
                FROM objects
                WHERE account_id = ? AND bucket = ? AND instr(key_folded, ?) > 0
                ORDER BY key_folded, key
                LIMIT ? OFFSET ?
                """,
                (account_id, bucket, normalized, limit + 1, offset),
            ).fetchall()
        has_more = len(rows) > limit
        objects = [
            {
                "key": row["key"],
                "name": row["key"].rsplit("/", 1)[-1],
                "size": row["size"],
                "etag": row["etag"],
                "last_modified": row["last_modified"],
                "storage_class": row["storage_class"],
            }
            for row in rows[:limit]
        ]
        return {
            "objects": objects,
            "next_token": str(offset + limit) if has_more else None,
            "scanned": 0,
        }
