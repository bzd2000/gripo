"""Shared pytest fixtures."""

import pytest

from tracker.db import Database


@pytest.fixture
def db() -> Database:
    """Return an in-memory Database instance for testing."""
    return Database(path=":memory:")
