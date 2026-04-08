"""
Persona module - synthesizes a ChatGPT conversation history into a
"Digital Passport" document that captures the user's communication style,
interests, and patterns for easy onboarding with a new AI assistant.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Any

from byegpt.taxonomy import build_taxonomy, extract_subtopics, extract_topics


def _extract_user_messages(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract all user messages from conversations with metadata."""
    messages = []
    for conv in conversations:
        mapping = conv.get("mapping", {})
        for node in mapping.values():
            msg = node.get("message")
            if not msg:
                continue
            if msg.get("author", {}).get("role") != "user":
                continue
            content = msg.get("content", {})
            parts = content.get("parts", [])
            text = "".join(p for p in parts if isinstance(p, str)).strip()
            if text:
                messages.append(
                    {
                        "text": text,
                        "timestamp": msg.get("create_time"),
                    }
                )
    return messages


def _analyze_activity(conversations: list[dict[str, Any]]) -> list[tuple[str, int]]:
    """Analyze monthly conversation frequency."""
    monthly: Counter[str] = Counter()
    for conv in conversations:
        ts = conv.get("create_time")
        if ts:
            try:
                dt = datetime.fromtimestamp(ts)
                month_key = dt.strftime("%Y-%m")
                monthly[month_key] += 1
            except (OSError, ValueError):
                continue
    return sorted(monthly.items())


def _analyze_communication_style(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze user communication patterns."""
    if not messages:
        return {
            "avg_length": 0,
            "median_length": 0,
            "question_ratio": 0,
            "total_messages": 0,
        }

    lengths = [len(m["text"]) for m in messages]
    questions = sum(1 for m in messages if "?" in m["text"])

    return {
        "avg_length": int(sum(lengths) / len(lengths)),
        "median_length": sorted(lengths)[len(lengths) // 2],
        "question_ratio": round(questions / len(messages) * 100, 1),
        "total_messages": len(messages),
    }


def _get_models_used(conversations: list[dict[str, Any]]) -> list[tuple[str, int]]:
    """Count which models were used across conversations."""
    model_counts: Counter[str] = Counter()
    for conv in conversations:
        mapping = conv.get("mapping", {})
        for node in mapping.values():
            msg = node.get("message")
            if not msg:
                continue
            slug = msg.get("metadata", {}).get("model_slug", "")
            if slug:
                model_counts[slug] += 1
                break
    return model_counts.most_common(10)


def _build_style_bullets(style: dict[str, Any]) -> list[str]:
    bullets: list[str] = []

    avg_length = style["avg_length"]
    question_ratio = style["question_ratio"]

    if avg_length >= 500:
        bullets.append("Prefers deep, detailed responses with visible reasoning and structure.")
    elif avg_length >= 180:
        bullets.append("Prefers concise structure with enough depth to act immediately.")
    else:
        bullets.append("Prefers direct responses that get to the point quickly.")

    if question_ratio >= 45:
        bullets.append("Uses dialogue to explore ideas and benefits from iterative back-and-forth.")
    elif question_ratio >= 20:
        bullets.append("Mixes questions with instructions and usually wants practical follow-through.")
    else:
        bullets.append("Mostly gives instructions and context rather than open-ended questions.")

    if avg_length >= 250 and question_ratio < 20:
        bullets.append("Values decisive execution over speculative brainstorming.")

    return bullets


def _build_interest_bullets(
    topics: list[tuple[str, int]],
    subtopics: dict[str, list[tuple[str, int]]],
) -> list[str]:
    bullets: list[str] = []
    for topic, count in topics[:5]:
        related = ", ".join(word for word, _ in subtopics.get(topic, [])[:3])
        if related:
            bullets.append(f"{topic.title()} ({count} chats) with recurring angles around {related}.")
        else:
            bullets.append(f"{topic.title()} ({count} chats).")
    return bullets


def generate_persona(
    conversations: list[dict[str, Any]],
    taxonomy: dict[str, Any] | None = None,
) -> str:
    """
    Generate a Digital Passport document from a ChatGPT conversation history.
    """
    total_convs = len(conversations)
    taxonomy = taxonomy or build_taxonomy(conversations)
    user_messages = _extract_user_messages(conversations)
    topics = extract_topics(conversations)
    top_topic_names = [topic for topic, _ in topics[:5]]
    subtopics = extract_subtopics(conversations, top_topic_names)
    activity = _analyze_activity(conversations)
    style = _analyze_communication_style(user_messages)
    models = _get_models_used(conversations)

    timestamps = [c.get("create_time") for c in conversations if c.get("create_time")]
    if timestamps:
        first_date = datetime.fromtimestamp(min(timestamps)).strftime("%Y-%m-%d")
        last_date = datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d")
        date_range = f"{first_date} -> {last_date}"
    else:
        date_range = "Unknown"

    style_bullets = _build_style_bullets(style)
    interest_bullets = _build_interest_bullets(topics, subtopics)

    lines: list[str] = []
    lines.append("---")
    lines.append('title: "Digital Passport - My AI Profile"')
    lines.append(f"generated: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("tags: [digital-passport, persona, ai-profile]")
    lines.append("---")
    lines.append("")
    lines.append("# Digital Passport")
    lines.append("")
    lines.append("A compact handoff profile distilled from prior ChatGPT conversations.")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Conversations | {total_convs:,} |")
    lines.append(f"| Messages sent | {style['total_messages']:,} |")
    lines.append(f"| Active period | {date_range} |")
    lines.append(f"| Avg message length | {style['avg_length']:,} characters |")
    lines.append(f"| Median message length | {style['median_length']:,} characters |")
    lines.append(f"| Questions ratio | {style['question_ratio']}% |")
    lines.append("")

    if models:
        lines.append("## Models Used")
        lines.append("")
        for model, count in models[:5]:
            lines.append(f"- {model}: {count:,} conversations")
        lines.append("")

    lines.append("## Collaboration Style")
    lines.append("")
    for bullet in style_bullets:
        lines.append(f"- {bullet}")
    lines.append("")

    if interest_bullets:
        lines.append("## Core Interests")
        lines.append("")
        for bullet in interest_bullets:
            lines.append(f"- {bullet}")
        lines.append("")

    if activity:
        lines.append("## Activity Timeline")
        lines.append("")
        lines.append("| Month | Conversations |")
        lines.append("|---|---|")
        for month, count in activity[-12:]:
            lines.append(f"| {month} | {count} |")
        lines.append("")

    lines.append("## Knowledge Map")
    lines.append("")
    for category in taxonomy.get("categories", [])[:5]:
        subcategory_names = ", ".join(
            subcategory["name"]
            for subcategory in category.get("subcategories", [])[:3]
        )
        if subcategory_names:
            lines.append(
                f"- {category['name']} ({category['count']} chats) with subcategories: {subcategory_names}."
            )
        else:
            lines.append(f"- {category['name']} ({category['count']} chats).")
    if taxonomy.get("suggested_notebooks"):
        lines.append("")
        lines.append("Suggested thematic notebooks:")
        lines.append("")
        for suggestion in taxonomy["suggested_notebooks"][:3]:
            subcategories = ", ".join(suggestion.get("subcategories", [])) or "General"
            lines.append(f"- {suggestion['title']}: {subcategories}")
        lines.append("")

    lines.append("## Working Prompt")
    lines.append("")
    lines.append("Use this profile when assisting this user:")
    lines.append("")
    lines.append("- Match their preferred level of detail and bias toward actionable output.")
    if topics:
        lines.append(
            f"- Expect recurring interest in: {', '.join(topic.title() for topic, _ in topics[:5])}."
        )
    if style["question_ratio"] >= 25:
        lines.append("- Leave room for iteration and refinement instead of assuming one-shot finality.")
    else:
        lines.append("- Default to direct execution and only ask questions when the decision materially changes the result.")
    lines.append("- Keep structure clear, concrete, and easy to scan.")
    lines.append("")
    lines.append("---")
    lines.append("*Generated by [byeGPT](https://github.com/damie/byegpt)*")
    lines.append("")

    return "\n".join(lines)
