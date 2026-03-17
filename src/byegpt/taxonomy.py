from __future__ import annotations

import re
from collections import Counter, defaultdict
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


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-ZÀ-ÿ]{3,}", text.lower())
        if token not in _STOP_WORDS
    ]


def _sample_message_text(conversation: dict[str, Any], limit: int = 1200) -> str:
    chunks: list[str] = []
    mapping = conversation.get("mapping", {})
    for node in mapping.values():
        message = node.get("message")
        if not message:
            continue
        role = message.get("author", {}).get("role")
        if role not in {"user", "assistant"}:
            continue
        parts = message.get("content", {}).get("parts", [])
        for part in parts:
            if isinstance(part, str) and part.strip():
                chunks.append(part.strip())
                if sum(len(chunk) for chunk in chunks) >= limit:
                    return "\n".join(chunks)[:limit]
    return "\n".join(chunks)[:limit]


def _date_span(conversations: list[dict[str, Any]]) -> dict[str, str | None]:
    timestamps = [conv.get("create_time") for conv in conversations if conv.get("create_time")]
    if not timestamps:
        return {"start": None, "end": None}
    return {
        "start": datetime.fromtimestamp(min(timestamps)).strftime("%Y-%m-%d"),
        "end": datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d"),
    }


def _conversation_record(conversation: dict[str, Any], index: int) -> dict[str, Any]:
    title = (conversation.get("title") or "Untitled conversation").strip()
    sample_text = _sample_message_text(conversation)
    return {
        "conversation_id": conversation_uid(conversation, index),
        "title": title,
        "title_tokens": _tokenize(title),
        "sample_text": sample_text,
        "sample_tokens": _tokenize(sample_text),
        "create_time": conversation.get("create_time"),
        "example_prompt": sample_text.splitlines()[0][:220] if sample_text else title,
    }


def _top_category_terms(records: list[dict[str, Any]], limit: int = 8) -> list[str]:
    counts: Counter[str] = Counter()
    for record in records:
        for token in record["title_tokens"]:
            counts[token] += 2
        for token in record["sample_tokens"][:24]:
            counts[token] += 1
    return [token for token, _ in counts.most_common(limit)]


def _assign_category(record: dict[str, Any], categories: list[str]) -> tuple[str, float, str]:
    scores: dict[str, int] = {}
    combined = record["title_tokens"] + record["sample_tokens"]
    for category in categories:
        score = 0
        score += record["title_tokens"].count(category) * 3
        score += combined.count(category)
        if score:
            scores[category] = score

    if not scores:
        return "uncategorized", 0.35, "No dominant recurring keyword; placed in Uncategorized."

    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    confidence = min(0.95, 0.45 + best_score * 0.1)
    return (
        best_category,
        round(confidence, 2),
        "Assigned from recurring title keywords reinforced by sampled conversation text.",
    )


def build_taxonomy(conversations: list[dict[str, Any]]) -> dict[str, Any]:
    records = [_conversation_record(conversation, index) for index, conversation in enumerate(conversations)]
    top_categories = _top_category_terms(records)

    category_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    category_meta: dict[str, dict[str, Any]] = {}

    for record in records:
        category, confidence, explanation = _assign_category(record, top_categories)
        category_groups[category].append(record)
        category_meta.setdefault(
            category,
            {
                "confidence": confidence,
                "explanation": explanation,
            },
        )

    categories_payload: list[dict[str, Any]] = []
    for category_name, category_records in sorted(
        category_groups.items(),
        key=lambda item: (-len(item[1]), item[0]),
    ):
        subtopic_counts: Counter[str] = Counter()
        for record in category_records:
            for token in record["title_tokens"] + record["sample_tokens"][:20]:
                if token == category_name or token in _STOP_WORDS:
                    continue
                subtopic_counts[token] += 1

        subtopic_names = [token for token, _ in subtopic_counts.most_common(4)]
        subcategories_map: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for record in category_records:
            assigned_subcategory = "general"
            for token in subtopic_names:
                if token in record["title_tokens"] or token in record["sample_tokens"]:
                    assigned_subcategory = token
                    break
            subcategories_map[assigned_subcategory].append(record)

        subcategories_payload: list[dict[str, Any]] = []
        for subcategory_name, subcategory_records in sorted(
            subcategories_map.items(),
            key=lambda item: (-len(item[1]), item[0]),
        ):
            example_titles = [record["title"] for record in subcategory_records[:4]]
            conversation_ids = [record["conversation_id"] for record in subcategory_records]
            example_prompts = [
                record["example_prompt"]
                for record in subcategory_records
                if record["example_prompt"]
            ][:3]
            subcategory_conversations = [
                {
                    "conversation_id": record["conversation_id"],
                    "title": record["title"],
                }
                for record in subcategory_records
            ]
            subcategories_payload.append(
                {
                    "name": subcategory_name.replace("_", " ").title(),
                    "slug": subcategory_name,
                    "count": len(subcategory_records),
                    "conversation_ids": conversation_ids,
                    "conversations": subcategory_conversations,
                    "representative_titles": example_titles,
                    "example_prompts": example_prompts,
                    "date_span": _date_span(
                        [
                            {"create_time": record["create_time"]}
                            for record in subcategory_records
                        ]
                    ),
                    "confidence": round(
                        min(0.95, 0.5 + len(subcategory_records) * 0.08),
                        2,
                    ),
                    "explanation": (
                        "Grouped by repeated secondary keywords inside the category."
                        if subcategory_name != "general"
                        else "Fallback bucket for category items without a stronger secondary term."
                    ),
                }
            )

        categories_payload.append(
            {
                "name": category_name.replace("_", " ").title(),
                "slug": category_name,
                "count": len(category_records),
                "date_span": _date_span(
                    [{"create_time": record["create_time"]} for record in category_records]
                ),
                "representative_titles": [record["title"] for record in category_records[:5]],
                "confidence": category_meta[category_name]["confidence"],
                "explanation": category_meta[category_name]["explanation"],
                "subcategories": subcategories_payload,
            }
        )

    suggestions = []
    for category in categories_payload[:3]:
        top_subcategories = [sub["name"] for sub in category["subcategories"][:2]]
        suggestions.append(
            {
                "title": f"{category['name']} Focus Notebook",
                "category": category["name"],
                "subcategories": top_subcategories,
            }
        )

    return {
        "version": "2.0",
        "total_conversations": len(conversations),
        "generated_from": "hybrid_metadata_content",
        "date_span": _date_span(conversations),
        "categories": categories_payload,
        "suggested_notebooks": suggestions,
    }
