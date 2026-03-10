# 🚀 byeGPT

> **Migrate your entire ChatGPT history to Gemini-optimized Markdown — in seconds.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/damie/byegpt/actions/workflows/ci.yml/badge.svg)](https://github.com/damie/byegpt/actions)

---

## Why byeGPT?

Switching from ChatGPT to Gemini? You shouldn't lose your conversation history. **byeGPT** converts your ChatGPT data export into clean, structured Markdown files optimized for Gemini's context window.

| Problem | byeGPT Solution |
|---|---|
| Gemini's context window has a ~7MB limit per file | Auto-splits into perfectly-sized chunks |
| ChatGPT exports are raw JSON blobs | Converts to clean, readable Markdown |
| Thinking blocks (O1/GPT-5) clutter the output | Collapsed Obsidian callouts keep it clean |
| Attachments are scattered with random filenames | Extracted & linked with proper relative paths |
| You want Gemini to "know you" instantly | **Digital Passport** synthesizes your AI profile |

---

## ⚡ Quick Start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/damie/byegpt.git
cd byegpt

# Install (editable mode)
pip install -e .
```

### 2. Export your ChatGPT data

Go to [ChatGPT Settings → Data Controls → Export Data](https://chatgpt.com/#settings/DataControls). You'll receive a `.zip` file via email.

### 3. Convert

```bash
# Convert instantly — byeGPT auto-detects conversations.json or your export .zip!
byegpt convert

# Or generate your Digital Passport
byegpt persona
```

That's it! Your files are in `./gemini_history/`, ready to upload to Gemini.

---

## ✨ Features

- 📦 **ZIP & JSON support** — Feed it `.zip` or `conversations.json` directly
- ✨ **Zero-config auto-detect** — Automatically finds your export file in the current folder
- 📏 **Smart splitting** — Files respect Gemini's ~7MB context window (configurable)
- 📎 **Attachment extraction** — Images extracted to `assets/` with relative Markdown links
- 💭 **Thinking blocks** — GPT-5/O1 reasoning rendered as collapsed Obsidian callouts
- 📋 **YAML frontmatter** — Title, date, model, tags — searchable in Obsidian/Logseq
- 🧬 **Code blocks** — Properly fenced with language tags
- 📊 **Execution output** — Preserved in labeled code blocks
- 🛂 **Digital Passport** — AI profile document capturing your communication style
- 🎨 **Beautiful CLI** — Rich progress bars, spinners, and colorful output

---

## 📖 CLI Reference

### `byegpt convert`

```bash
byegpt convert [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--input`, `-i` | *(auto)* | Path to `.zip` or `conversations.json` |
| `--output`, `-o` | `./gemini_history` | Output folder for Markdown files |
| `--split-size`, `-s` | `7MB` | Max file size per Markdown file |
| `--no-thinking` | `false` | Exclude thinking/reasoning blocks |
| `--no-attachments` | `false` | Skip attachment extraction |

### `byegpt persona`

```bash
byegpt persona [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--input`, `-i` | *(required)* | Path to `.zip` or `conversations.json` |
| `--output`, `-o` | `./digital_passport.md` | Output file path |

### General

```bash
byegpt --version    # Show version
byegpt --help       # Show help
```

---

## 🧭 Data Flow

```mermaid
graph LR
    A["📦 ChatGPT Export<br/>.zip / .json"] --> B["🔍 Parser<br/>parser.py"]
    B --> C["📎 Attachment<br/>Extractor"]
    B --> D["🌳 Message Tree<br/>Builder"]
    C --> E["📁 assets/"]
    D --> F["✍️ Formatter<br/>formatter.py"]
    F --> G["📝 Markdown Files<br/>≤ 7MB each"]
    F --> H["💭 Thinking<br/>Callouts"]
    F --> I["📋 YAML<br/>Frontmatter"]
    B --> J["🛂 Persona<br/>persona.py"]
    J --> K["📄 Digital<br/>Passport"]
```

---

## 🛂 Digital Passport

The `persona` command analyzes your entire ChatGPT history and generates a **Digital Passport** — a structured document capturing:

- **📊 Profile Summary** — Total conversations, messages, date range
- **🏷️ Top Topics** — Your most discussed subjects
- **🤖 Models Used** — Which AI models you've used
- **📅 Activity Timeline** — Monthly conversation frequency
- **💬 Communication Style** — Message length, question ratio, style primer

> Share this document with Gemini and it'll understand your preferences instantly!

---

## 🧪 Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=byegpt --cov-report=term-missing
```

---

## 📄 Output Format

Each generated Markdown file includes:

```markdown
---
title: "My Conversation Title"
date: 2024-03-10
model: gpt-4o
tags: [chatgpt-export, archive]
---

# My Conversation Title (2024-03-10)

**USER:**
What is the meaning of life?

**ASSISTANT:**
The meaning of life is a philosophical question...

> [!abstract]- 💭 Thinking Process
> Let me consider this from multiple angles...
> First, from a philosophical standpoint...
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest tests/ -v`)
4. Commit your changes
5. Open a Pull Request

---

## 📜 License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ for everyone migrating to Gemini<br/>
  <sub>byeGPT v2.0.0</sub>
</p>
