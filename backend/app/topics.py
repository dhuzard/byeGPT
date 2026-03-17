from __future__ import annotations

from collections import defaultdict
from typing import Any

from byegpt.persona import extract_topics


def build_topic_laboratory(conversations: list[dict[str, Any]]) -> dict[str, Any]:
    top_topics = [topic for topic, _ in extract_topics(conversations, top_n=8)]
    groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"topic": "Uncategorized", "count": 0, "titles": []}
    )

    for conversation in conversations:
        title = (conversation.get("title") or "Untitled conversation").strip()
        lowered = title.lower()
        assigned = "Uncategorized"
        for topic in top_topics:
            if topic.lower() in lowered:
                assigned = topic.title()
                break

        groups[assigned]["topic"] = assigned
        groups[assigned]["count"] += 1
        if len(groups[assigned]["titles"]) < 5:
            groups[assigned]["titles"].append(title)

    topics = sorted(
        groups.values(),
        key=lambda item: (-item["count"], item["topic"]),
    )

    return {
        "topics": topics,
        "total_conversations": len(conversations),
    }
