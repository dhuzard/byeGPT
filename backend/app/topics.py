from __future__ import annotations

from typing import Any

from byegpt.taxonomy import build_taxonomy


def build_topic_laboratory(conversations: list[dict[str, Any]]) -> dict[str, Any]:
    taxonomy = build_taxonomy(conversations)
    topics = []
    for category in taxonomy.get("categories", []):
        topics.append(
            {
                "topic": category["name"],
                "slug": category["slug"],
                "count": category["count"],
                "titles": category.get("representative_titles", []),
                "subcategories": [
                    {
                        "name": subcategory["name"],
                        "slug": subcategory["slug"],
                        "count": subcategory["count"],
                        "titles": subcategory.get("representative_titles", []),
                        "conversation_ids": subcategory.get("conversation_ids", []),
                    }
                    for subcategory in category.get("subcategories", [])
                ],
            }
        )

    return {
        "topics": topics,
        "total_conversations": taxonomy.get("total_conversations", len(conversations)),
        "taxonomy_version": taxonomy.get("version", "2.0"),
        "suggested_notebooks": taxonomy.get("suggested_notebooks", []),
    }
