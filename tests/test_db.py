import json

import db


class _FakeConn:
    def __init__(self, row):
        self._row = row
        self.calls = []

    async def fetchrow(self, query, *args):
        self.calls.append((query, args))
        return self._row


class _FakeAcquire:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _FakeAcquire(self._conn)


async def test_get_destination_returns_parsed_config(monkeypatch):
    conn = _FakeConn({"id": 9, "type": "slack", "config": json.dumps({"url": "https://x"})})
    monkeypatch.setattr(db, "_pool", _FakePool(conn))

    dest = await db.get_destination(9)

    assert dest == {"id": 9, "type": "slack", "config": {"url": "https://x"}}
    assert conn.calls[0][1] == (9,)


async def test_get_destination_returns_none_when_missing(monkeypatch):
    monkeypatch.setattr(db, "_pool", _FakePool(_FakeConn(None)))

    assert await db.get_destination(9) is None
