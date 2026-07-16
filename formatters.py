def format_items(crawler_id: str, items: list[dict]) -> str:
    lines = [f"[{crawler_id}] 새 글 {len(items)}개"]
    for item in items:
        if item.get("summary"):
            lines.append(f"• {item['title']}\n{item['summary']}")
        else:
            lines.append(f"• {item['title']}\n{item['url']}")
    return "\n".join(lines)


def format_error(crawler_id: str, error: str, fail_count: int) -> str:
    return f"[{crawler_id}] 크롤러 오류 ({fail_count}회 연속)\n{error}"


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
