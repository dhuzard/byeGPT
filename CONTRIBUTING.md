# Contributing to byeGPT

First off, thank you for considering contributing to byeGPT! It's people like you that make byeGPT such a great tool.

## Where to Start

- **Issues**: If you find a bug, have a feature request, or want to ask a question, please [open an issue](https://github.com/damie/byegpt/issues).
- **Pull Requests**: Pull requests are very welcome! If you're fixing a bug, feel free to open a PR directly. If it's a new feature, please open an issue first to discuss it or check existing issues based on the `todo.md` roadmap.

## Local Development Setup

To set up your local development environment for byeGPT, follow these steps:

1. **Fork the repository** to your own GitHub account and clone it to your local machine:
   ```bash
   git clone https://github.com/YOUR_USERNAME/byegpt.git
   cd byegpt
   ```

2. **Install the project** in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install Intelligence Layer dependencies** (for ChromaDB and vector indexing features):
   ```bash
   pip install chromadb==0.4.15 sentence-transformers transformers
   ```

## Running Tests

All code changes must pass the test suite. We use `pytest`. To run the tests, simply execute:

```bash
pytest
```

For a coverage report:
```bash
pytest tests/ -v --cov=byegpt --cov-report=term-missing
```

Please make sure to write tests for any new features or bug fixes.

## Submitting a Pull Request

When you are ready to submit your code:

1. Create a new branch for your feature or fix (`git checkout -b feature/your-feature-name`).
2. Make your changes and commit them with clear, concise commit messages.
3. Push your branch to your fork (`git push origin feature/your-feature-name`).
4. Open a Pull Request from your branch to the `main` branch of this repository.
5. Fill out the provided Pull Request template.

## Code Style

- Write clean, readable Python code (target Python 3.10+).
- Use clear variable and function names.
- Type hint where appropriate.

Thank you for contributing!
