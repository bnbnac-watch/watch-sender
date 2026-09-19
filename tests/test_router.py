import pytest

import router


@pytest.fixture
def dispatched(monkeypatch):
    calls = []

    async def fake_dispatch(dest, message):
        calls.append((dest, message))
    monkeypatch.setattr(router, "_dispatch", fake_dispatch)

    async def fail_get_destinations(crawler_id):
        raise AssertionError("운영 알림이 크롤러 destination을 조회하면 안 된다")
    monkeypatch.setattr(router.db, "get_destinations", fail_get_destinations)
    return calls


@pytest.fixture
def ops_destination(monkeypatch):
    dest = {"id": 9, "type": "slack", "config": {"url": "https://hooks.slack.com/ops"}}

    async def fake_get_destination(dest_id):
        return dest if dest_id == 9 else None
    monkeypatch.setattr(router.db, "get_destination", fake_get_destination)
    monkeypatch.setattr(router, "ALERT_DESTINATION_ID", 9)
    return dest


async def test_route_error_sends_only_to_alert_destination(dispatched, ops_destination):
    await router.route_error(4, "boom", 3)

    assert dispatched == [(ops_destination, "[4] 크롤러 오류 (3회 연속)\nboom")]


async def test_route_error_marks_auto_disable_in_message(dispatched, ops_destination):
    await router.route_error(4, "boom", 5, disabled=True)

    assert len(dispatched) == 1
    assert "자동 비활성화" in dispatched[0][1]


async def test_route_error_sends_nothing_when_alert_destination_unset(dispatched, monkeypatch):
    monkeypatch.setattr(router, "ALERT_DESTINATION_ID", None)

    await router.route_error(4, "boom", 3)

    assert dispatched == []


async def test_route_error_sends_nothing_when_alert_destination_missing_in_db(dispatched, monkeypatch):
    async def fake_get_destination(dest_id):
        return None
    monkeypatch.setattr(router.db, "get_destination", fake_get_destination)
    monkeypatch.setattr(router, "ALERT_DESTINATION_ID", 9)

    await router.route_error(4, "boom", 3)

    assert dispatched == []


async def test_route_recovered_sends_only_to_alert_destination(dispatched, ops_destination):
    await router.route_recovered(4, 3)

    assert dispatched == [(ops_destination, "[4] 크롤러 복구됨 (직전 3회 연속 실패 후 정상 실행)")]


async def test_route_recovered_sends_nothing_when_alert_destination_unset(dispatched, monkeypatch):
    monkeypatch.setattr(router, "ALERT_DESTINATION_ID", None)

    await router.route_recovered(4, 3)

    assert dispatched == []
