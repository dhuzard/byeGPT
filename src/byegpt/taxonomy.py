from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Any

_STOP_WORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "shall",
        "not",
        "no",
        "so",
        "up",
        "out",
        "if",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "same",
        "than",
        "too",
        "very",
        "just",
        "how",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "it",
        "its",
        "le",
        "la",
        "les",
        "de",
        "du",
        "des",
        "un",
        "une",
        "et",
        "en",
        "pour",
        "dans",
        "sur",
        "avec",
        "par",
        "est",
        "sont",
        "pas",
    }
)


def conversation_uid(conversation: dict[str, Any], index: int) -> str:
    conv_id = str(conversation.get("id") or "").strip()
    if conv_id:
        return conv_id
    return f"conversation_{index + 1:05d}"


def extract_topics(conversations: list[dict[str, Any]], top_n: int = 20) -> list[tuple[str, int]]:
    word_counts: Counter[str] = Counter()
    for conversation in conversations:
        title = conversation.get("title") or ""
        words = re.findall(r"[a-zA-ZÀ-ÿ]{3,}", title.lower())
        for word in words:
            if word not in _STOP_WORDS:
                word_counts[word] += 1
    return word_counts.most_common(top_n)


def extract_subtopics(
    conversations: list[dict[str, Any]],
    topics: list[str],
    top_n: int = 3,
) -> dict[str, list[tuple[str, int]]]:
    result: dict[str, list[tuple[str, int]]] = {}
    for topic in topics:
        topic_lower = topic.lower()
        filtered = [
            conversation
            for conversation in conversations
            if topic_lower in (conversation.get("title") or "").lower()
        ]

        word_counts: Counter[str] = Counter()
        for conversation in filtered:
            title = conversation.get("title") or ""
            words = re.findall(r"[a-zA-ZÀ-ÿ]{3,}", title.lower())
            for word in words:
                if word not in _STOP_WORDS and word != topic_lower:
                    word_counts[word] += 1

        result[topic] = word_counts.most_common(top_n)

    return result


def _sample_message_text(conversation: dict[str, Any], limit: int = 300) -> str:
    mapping = conversation.get("mapping", {})
    snippets: list[str] = []
    for node in mapping.values():
        message = node.get("message")
        if not message:
            continue
        parts = message.get("content", {}).get("parts", [])
        for part in parts:
            if isinstance(part, str) and part.strip():
                snippets.append(part.strip())
                if sum(len(snippet) for snippet in snippets) >= limit:
                    return "\n".join(snippets)[:limit]
    return "\n".join(snippets)[:limit]


def _date_span(items: list[dict[str, Any]]) -> dict[str, str | None]:
    timestamps = [item.get("create_time") for item in items if item.get("create_time")]
    if not timestamps:
        return {"start": None, "end": None}
    return {
        "start": datetime.fromtimestamp(min(timestamps)).strftime("%Y-%m-%d"),
        "end": datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d"),
    }


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_") or "general"


def build_taxonomy(conversations: list[dict[str, Any]]) -> dict[str, Any]:
    topics = extract_topics(conversations, top_n=8)
    topic_names = [topic for topic, _ in topics]
    subtopics = extract_subtopics(conversations, topic_names, top_n=4)

    categories: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    for topic, topic_count in topics:
        topic_lower = topic.lower()
        category_conversations = [
            {
                **conversation,
                "_conversation_id": conversation_uid(conversation, index),
            }
            for index, conversation in enumerate(conversations)
            if topic_lower in (conversation.get("title") or "").lower()
        ]
        if not category_conversations:
            continue

        subcategory_payload: list[dict[str, Any]] = []
        remaining = category_conversations[:]
        for subtopic, _sub_count in subtopics.get(topic, []):
            subtopic_lower = subtopic.lower()
            matched = [
                conversation
                for conversation in remaining
                if subtopic_lower in (conversation.get("title") or "").lower()
            ]
            if not matched:
                continue

            matched_ids = [conversation["_conversation_id"] for conversation in matched]
            used_ids.update(matched_ids)
            subcategory_payload.append(
                {
                    "name": subtopic.title(),
                    "slug": _slugify(subtopic),
                    "count": len(matched),
                    "conversation_ids": matched_ids,
                    "conversations": [
                        {
                            "conversation_id": conversation["_conversation_id"],
                            "title": conversation.get("title") or "Untitled conversation",
                        }
                        for conversation in matched
                    ],
                    "representative_titles": [
                        conversation.get("title") or "Untitled conversation"
                        for conversation in matched[:4]
                    ],
                    "example_prompts": [
                        _sample_message_text(conversation) or (conversation.get("title") or "Untitled conversation")
                        for conversation in matched[:3]
                    ],
                    "date_span": _date_span(matched),
                    "confidence": 0.8,
                    "explanation": "Derived from recurring co-occurring title keywords within the main Core Interest.",
                }
            )
            remaining = [
                conversation
                for conversation in remaining
                if conversation["_conversation_id"] not in set(matched_ids)
            ]

        if remaining:
            remaining_ids = [conversation["_conversation_id"] for conversation in remaining]
            used_ids.update(remaining_ids)
            subcategory_payload.append(
                {
                    "name": "General",
                    "slug": "general",
                    "count": len(remaining),
                    "conversation_ids": remaining_ids,
                    "conversations": [
                        {
                            "conversation_id": conversation["_conversation_id"],
                            "title": conversation.get("title") or "Untitled conversation",
                        }
                        for conversation in remaining
                    ],
                    "representative_titles": [
                        conversation.get("title") or "Untitled conversation"
                        for conversation in remaining[:4]
                    ],
                    "example_prompts": [
                        _sample_message_text(conversation) or (conversation.get("title") or "Untitled conversation")
                        for conversation in remaining[:3]
                    ],
                    "date_span": _date_span(remaining),
                    "confidence": 0.55,
                    "explanation": "Conversations matched the Core Interest without a stronger subtopic title signal.",
                }
            )

        categories.append(
            {
                "name": topic.title(),
                "slug": _slugify(topic),
                "count": len(category_conversations),
                "date_span": _date_span(category_conversations),
                "representative_titles": [
                    conversation.get("title") or "Untitled conversation"
                    for conversation in category_conversations[:5]
                ],
                "confidence": 0.85,
                "explanation": "Derived from the same title-frequency extraction used in the passport Core Interests section.",
                "subcategories": subcategory_payload,
            }
        )

    uncategorized = []
    for index, conversation in enumerate(conversations):
        conversation_id = conversation_uid(conversation, index)
        if conversation_id not in used_ids:
            uncategorized.append(
                {
                    **conversation,
                    "_conversation_id": conversation_id,
                }
            )

    if uncategorized:
        categories.append(
            {
                "name": "Uncategorized",
                "slug": "uncategorized",
                "count": len(uncategorized),
                "date_span": _date_span(uncategorized),
                "representative_titles": [
                    conversation.get("title") or "Untitled conversation"
                    for conversation in uncategorized[:5]
                ],
                "confidence": 0.35,
                "explanation": "No strong Core Interest title keyword matched these conversations.",
                "subcategories": [
                    {
                        "name": "General",
                        "slug": "general",
                        "count": len(uncategorized),
                        "conversation_ids": [
                            conversation["_conversation_id"] for conversation in uncategorized
                        ],
                        "conversations": [
                            {
                                "conversation_id": conversation["_conversation_id"],
                                "title": conversation.get("title") or "Untitled conversation",
                            }
                            for conversation in uncategorized
                        ],
                        "representative_titles": [
                            conversation.get("title") or "Untitled conversation"
                            for conversation in uncategorized[:4]
                        ],
                        "example_prompts": [
                            _sample_message_text(conversation) or (conversation.get("title") or "Untitled conversation")
                            for conversation in uncategorized[:3]
                        ],
                        "date_span": _date_span(uncategorized),
                        "confidence": 0.35,
                        "explanation": "Fallback bucket for conversations outside the extracted Core Interests.",
                    }
                ],
            }
        )

    suggestions = []
    for category in categories[:3]:
        suggestions.append(
            {
                "title": f"{category['name']} Focus Notebook",
                "category": category["name"],
                "subcategories": [
                    subcategory["name"] for subcategory in category.get("subcategories", [])[:2]
                ],
            }
        )

    return {
        "version": "2.0",
        "total_conversations": len(conversations),
        "generated_from": "core_interests_title_taxonomy",
        "date_span": _date_span(conversations),
        "categories": categories,
        "suggested_notebooks": suggestions,
    }
