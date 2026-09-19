import main


async def test_error_endpoint_defaults_disabled_to_false(monkeypatch):
    calls = []

    async def fake_route_error(crawler_id, error, fail_count, disabled=False):
        calls.append((crawler_id, error, fail_count, disabled))
    monkeypatch.setattr(main.router, "route_error", fake_route_error)

    await main.error(main.ErrorRequest(crawler_id=4, error="boom", fail_count=3))

    assert calls == [(4, "boom", 3, False)]


async def test_error_endpoint_passes_disabled_flag(monkeypatch):
    calls = []

    async def fake_route_error(crawler_id, error, fail_count, disabled=False):
        calls.append(disabled)
    monkeypatch.setattr(main.router, "route_error", fake_route_error)

    await main.error(main.ErrorRequest(crawler_id=4, error="boom", fail_count=5, disabled=True))

    assert calls == [True]


async def test_recovered_endpoint_routes_to_router(monkeypatch):
    calls = []

    async def fake_route_recovered(crawler_id, previous_fail_count):
        calls.append((crawler_id, previous_fail_count))
    monkeypatch.setattr(main.router, "route_recovered", fake_route_recovered)

    await main.recovered(main.RecoveredRequest(crawler_id=4, previous_fail_count=3))

    assert calls == [(4, 3)]
