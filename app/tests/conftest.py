"""
Test configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Provide a test client"""
    return TestClient(app)


@pytest.fixture
def sample_scenario_data():
    """Sample scenario data for testing"""
    return {
        "title": "Oil Market Test",
        "root_event": "Strait of Hormuz closes",
        "target_event": "Oil prices increase",
        "mode": "validate",
    }
