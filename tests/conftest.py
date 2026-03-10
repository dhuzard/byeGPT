"""Shared test fixtures."""

import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_conversations():
    """Load the sample conversations test fixture."""
    with open(FIXTURES_DIR / "sample_conversations.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def single_conversation(sample_conversations):
    """Return the first (feature-rich) test conversation."""
    return sample_conversations[0]


@pytest.fixture
def tmp_output(tmp_path):
    """Provide a temporary output directory."""
    out = tmp_path / "output"
    out.mkdir()
    return out
