import formatters


def test_format_error_keeps_existing_layout():
    message = formatters.format_error(4, "render 실패", 3)

    assert message == "[4] 크롤러 오류 (3회 연속)\nrender 실패"


def test_format_error_flags_auto_disable():
    message = formatters.format_error(4, "render 실패", 5, disabled=True)

    assert message.startswith("[4] 크롤러 오류 (5회 연속)\nrender 실패")
    assert "자동 비활성화" in message


def test_format_recovery_reports_previous_failure_streak():
    message = formatters.format_recovery(4, 3)

    assert message == "[4] 크롤러 복구됨 (직전 3회 연속 실패 후 정상 실행)"
