# 🗺️ byeGPT Roadmap & TODO

This document outlines the vision for the future of **byeGPT**. We are transforming a static archive into a dynamic "Intelligence Layer." Whether you are a developer, a data scientist, or a power user, we invite you to help build the ultimate personal memory vault.

## 🚀 Upcoming Features (Next Phases)

### Phase 9: The Agentic RAG
- [ ] **`byegpt chat`**: Start an interactive session to "talk to your history."
- [ ] **LLM Integration**: Optional hooks for Gemini/GPT-4 to answer complex questions based on retrieved context.
- [ ] **Conversation Linking**: Use LLMs to find "related conversations" across your history and add cross-links.

### Phase 10: Advanced Visualization
- [ ] **Obsidian Graph Optimization**: Customize tags and metadata to make the visual graph even more useful.
- [ ] **Timeline View**: Generate a visual timeline of your AI interactions over the years.
- [ ] **Data Export Formats**: Support for Logseq, Notion, and other knowledge bases.

### Refinements & Performance
- [ ] **Incremental Indexing**: Only index new files since the last `byegpt index` run.
- [ ] **Advanced Chunking**: Improve semantic chunking (e.g., chunking by message or topic rather than just file size).
- [ ] **Multi-Model Support**: Allow users to choose different embedding models (local or API-based).

---

## 🤝 Contributing

We love contributions! Whether it's a bug fix, a new feature, or better documentation, here is how you can help:

1.  **Check the Issues**: Look for open issues or feature requests.
2.  **Submit a PR**:
    - Fork the repository.
    - Create a feature branch (`git checkout -b feature/amazing-feature`).
    - Run the existing tests (`pytest`).
    - Commit your changes and open a Pull Request.
3.  **Share Ideas**: Open a Discussion if you have a "wild" idea for the Intelligence Layer.

### Development Setup
```bash
pip install -e ".[dev]"
pytest
```

---

<p align="center">
  Building the future of personal data management, together.<br/>
  <sub>Let's make our history useful again.</sub>
</p>
