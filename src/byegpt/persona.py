"""
Persona module — synthesizes a ChatGPT conversation history into a
"Digital Passport" document that captures the user's communication style,
interests, and patterns for easy onboarding with a new AI assistant.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Any


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
                messages.append({
                    "text": text,
                    "timestamp": msg.get("create_time"),
                })
    return messages


def extract_topics(conversations: list[dict[str, Any]], top_n: int = 20) -> list[tuple[str, int]]:
    """Extract top topics from conversation titles using keyword frequency."""
    # Common stop words to filter out
    stop_words = frozenset({
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "not", "no", "so", "up",
        "out", "if", "about", "into", "through", "during", "before", "after",
        "above", "below", "between", "same", "than", "too", "very", "just",
        "how", "what", "which", "who", "whom", "this", "that", "these",
        "those", "i", "me", "my", "we", "our", "you", "your", "it", "its",
        "le", "la", "les", "de", "du", "des", "un", "une", "et", "en",
        "pour", "dans", "sur", "avec", "par", "est", "sont", "pas",
    })

    word_counts: Counter[str] = Counter()
    for conv in conversations:
        title = conv.get("title") or ""
        words = re.findall(r"[a-zA-ZÀ-ÿ]{3,}", title.lower())
        for word in words:
            if word not in stop_words:
                word_counts[word] += 1

    return word_counts.most_common(top_n)


def extract_subtopics(
    conversations: list[dict[str, Any]],
    topics: list[str],
    top_n: int = 3,
) -> dict[str, list[tuple[str, int]]]:
    """
    For each topic, filter conversations whose title contains that topic,
    then extract the top-N most frequent co-occurring keywords as subtopics.

    Returns a dict mapping topic -> [(subtopic_word, count), ...].
    """
    stop_words = frozenset({
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "not", "no", "so", "up",
        "out", "if", "about", "into", "through", "during", "before", "after",
        "above", "below", "between", "same", "than", "too", "very", "just",
        "how", "what", "which", "who", "whom", "this", "that", "these",
        "those", "i", "me", "my", "we", "our", "you", "your", "it", "its",
        "le", "la", "les", "de", "du", "des", "un", "une", "et", "en",
        "pour", "dans", "sur", "avec", "par", "est", "sont", "pas",
    })

    result: dict[str, list[tuple[str, int]]] = {}

    for topic in topics:
        topic_lower = topic.lower()
        # Filter conversations that belong to this topic
        filtered = [
            c for c in conversations
            if topic_lower in (c.get("title") or "").lower()
        ]

        # Count co-occurring keywords (excluding the topic word itself)
        word_counts: Counter[str] = Counter()
        for conv in filtered:
            title = conv.get("title") or ""
            words = re.findall(r"[a-zA-ZÀ-ÿ]{3,}", title.lower())
            for word in words:
                if word not in stop_words and word != topic_lower:
                    word_counts[word] += 1

        result[topic] = word_counts.most_common(top_n)

    return result


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
                break  # Count once per conversation
    return model_counts.most_common(10)


def generate_persona(conversations: list[dict[str, Any]]) -> str:
    """
    Generate a Digital Passport document from a ChatGPT conversation history.

    This creates a structured Markdown document that captures the user's
    communication patterns, interests, and style — designed to be given
    to a new AI assistant (like Gemini) for instant personalization.
    """
    total_convs = len(conversations)
    user_messages = _extract_user_messages(conversations)
    topics = extract_topics(conversations)
    activity = _analyze_activity(conversations)
    style = _analyze_communication_style(user_messages)
    models = _get_models_used(conversations)

    # Date range
    timestamps = [c.get("create_time") for c in conversations if c.get("create_time")]
    if timestamps:
        first_date = datetime.fromtimestamp(min(timestamps)).strftime("%Y-%m-%d")
        last_date = datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d")
        date_range = f"{first_date} → {last_date}"
    else:
        date_range = "Unknown"

    # Build the document
    lines: list[str] = []

    lines.append("---")
    lines.append('title: "Digital Passport — My AI Profile"')
    lines.append(f"generated: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("tags: [digital-passport, persona, ai-profile]")
    lines.append("---")
    lines.append("")
    lines.append("# 🛂 Digital Passport — My AI Profile")
    lines.append("")
    lines.append("> This document was auto-generated by **byeGPT** from your ChatGPT")
    lines.append("> conversation history. Give it to a new AI assistant so it can")
    lines.append("> understand your style and preferences instantly.")
    lines.append("")

    # Profile Summary
    lines.append("## 📊 Profile Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Conversations | {total_convs:,} |")
    lines.append(f"| Messages sent | {style['total_messages']:,} |")
    lines.append(f"| Active period | {date_range} |")
    lines.append(f"| Avg message length | {style['avg_length']:,} characters |")
    lines.append(f"| Questions ratio | {style['question_ratio']}% of messages |")
    lines.append("")

    # Models used
    if models:
        lines.append("## 🤖 Models Used")
        lines.append("")
        for model, count in models:
            lines.append(f"- **{model}** — {count:,} conversations")
        lines.append("")

    # Top Topics
    if topics:
        lines.append("## 🏷️ Top Topics")
        lines.append("")
        lines.append("Your most frequently discussed subjects:")
        lines.append("")
        for word, count in topics:
            bar = "█" * min(count, 30)
            lines.append(f"- **{word}** ({count}) {bar}")
        lines.append("")

    # Activity Timeline
    if activity:
        lines.append("## 📅 Activity Timeline")
        lines.append("")
        lines.append("| Month | Conversations |")
        lines.append("|---|---|")
        for month, count in activity:
            bar = "▓" * min(count // 2, 25)
            lines.append(f"| {month} | {count} {bar} |")
        lines.append("")

    # How to Talk to Me
    lines.append("## 💬 How to Talk to Me")
    lines.append("")
    lines.append("Based on the analysis of your conversation history, here's a")
    lines.append("primer you can share with a new AI assistant:")
    lines.append("")
    lines.append("> **Communication style:**")

    if style["avg_length"] > 500:
        lines.append("> I write detailed, thorough messages. I appreciate equally")
        lines.append("> detailed and comprehensive responses.")
    elif style["avg_length"] > 150:
        lines.append("> I write moderate-length messages. I like clear, well-structured")
        lines.append("> responses with good detail but not excessive verbosity.")
    else:
        lines.append("> I tend to be concise and direct. I prefer responses that get")
        lines.append("> to the point quickly.")

    lines.append(">")

    if style["question_ratio"] > 50:
        lines.append("> I'm highly inquisitive — I ask a lot of questions and")
        lines.append("> learn through dialogue.")
    elif style["question_ratio"] > 25:
        lines.append("> I balance between asking questions and giving instructions.")
    else:
        lines.append("> I tend to give instructions and context rather than asking")
        lines.append("> open-ended questions.")

    if topics:
        top_5 = ", ".join(w for w, _ in topics[:5])
        lines.append(">")
        lines.append(f"> **Key interests:** {top_5}")

    lines.append("")
    lines.append("---")
    lines.append("*Generated by [byeGPT](https://github.com/damie/byegpt)*")
    lines.append("")

    return "\n".join(lines)
