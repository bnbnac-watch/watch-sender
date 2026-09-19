def format_items(crawler_id: str, items: list[dict]) -> str:
    lines = [f"[{crawler_id}] 새 글 {len(items)}개"]
    for item in items:
        body = item["summary"] if item.get("summary") else item["url"]
        if item.get("image_grid_url"):
            body = f"{body}\n{item['image_grid_url']}"
        lines.append(f"• {item['title']}\n{body}")
    return "\n".join(lines)


def format_error(crawler_id: str, error: str, fail_count: int, disabled: bool = False) -> str:
    message = f"[{crawler_id}] 크롤러 오류 ({fail_count}회 연속)\n{error}"
    if disabled:
        message += "\n⚠ 연속 실패로 자동 비활성화됨 — 원인 해결 후 watch-admin에서 다시 활성화 필요"
    return message


def format_recovery(crawler_id: str, previous_fail_count: int) -> str:
    return f"[{crawler_id}] 크롤러 복구됨 (직전 {previous_fail_count}회 연속 실패 후 정상 실행)"


def split_message(message: str, max_chars: int) -> list[str]:
    if len(message) <= max_chars:
        return [message]
    chunks = []
    current = []
    current_len = 0
    for line in message.splitlines(keepends=True):
        if current_len + len(line) > max_chars and current:
            chunks.append("".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)
    if current:
        chunks.append("".join(current))
    return chunks
