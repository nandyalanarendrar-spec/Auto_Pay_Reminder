"""Test configuration.

Tests that sign up a throwaway user in the real Supabase project are marked `live_db`.
CI runs everything else (`pytest -m "not live_db"`); run the whole suite locally with plain `pytest`.
"""
import pytest

LIVE_DB_FIXTURES = {"user", "test_user"}


def pytest_collection_modifyitems(items):
    for item in items:
        if LIVE_DB_FIXTURES & set(item.fixturenames):
            item.add_marker(pytest.mark.live_db)
