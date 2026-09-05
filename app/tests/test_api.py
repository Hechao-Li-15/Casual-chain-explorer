"""
Tests for scenario API endpoints
"""

import pytest


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_scenario(client, sample_scenario_data):
    """Test creating a new scenario"""
    response = client.post("/api/scenarios", json=sample_scenario_data)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == sample_scenario_data["title"]
    assert data["root_event"] == sample_scenario_data["root_event"]
    assert data["mode"] == sample_scenario_data["mode"]
    assert "id" in data
    assert data["current_version"] == 1


def test_get_scenario(client, sample_scenario_data):
    """Test retrieving a scenario"""
    # Create first
    create_response = client.post("/api/scenarios", json=sample_scenario_data)
    scenario_id = create_response.json()["id"]

    # Retrieve
    response = client.get(f"/api/scenarios/{scenario_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == scenario_id
    assert data["root_event"] == sample_scenario_data["root_event"]


def test_get_nonexistent_scenario(client):
    """Test retrieving a non-existent scenario"""
    response = client.get("/api/scenarios/fake_id")
    assert response.status_code == 404


def test_generate_causal_chain_hormuz(client, sample_scenario_data):
    """Test generating a causal chain for Hormuz event"""
    # Create scenario with Hormuz event
    hormuz_data = {
        "title": "Hormuz Closure Test",
        "root_event": "Strait of Hormuz closes",
        "mode": "discover",
    }
    create_response = client.post("/api/scenarios", json=hormuz_data)
    scenario_id = create_response.json()["id"]

    # Generate chain
    response = client.post(f"/api/scenarios/{scenario_id}/generate")
    assert response.status_code == 200

    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    # Phase 2 returns mocked Hormuz chain with 6 nodes
    assert len(data["nodes"]) == 6
    assert len(data["edges"]) == 5
    assert data["nodes"][0]["label"] == "Strait of Hormuz closes for 2 weeks"


def test_generate_causal_chain_generic(client):
    """Test generating a generic causal chain"""
    # Create scenario with unknown event
    generic_data = {
        "title": "Generic Event Test",
        "root_event": "Some random event happens",
        "mode": "discover",
    }
    create_response = client.post("/api/scenarios", json=generic_data)
    scenario_id = create_response.json()["id"]

    # Generate chain
    response = client.post(f"/api/scenarios/{scenario_id}/generate")
    assert response.status_code == 200

    data = response.json()
    assert len(data["nodes"]) == 4  # Generic chain
    assert len(data["edges"]) == 3
    assert data["nodes"][0]["label"] == "Some random event happens"


def test_validate_thesis(client):
    """Test validating a thesis"""
    # Create scenario
    scenario_data = {
        "title": "Validation Test",
        "root_event": "Strait of Hormuz closes",
        "target_event": "Oil prices increase",
        "mode": "validate",
    }
    create_response = client.post("/api/scenarios", json=scenario_data)
    scenario_id = create_response.json()["id"]

    # Validate thesis
    response = client.post(
        f"/api/scenarios/{scenario_id}/validate",
        json={"event_a": "Strait of Hormuz closes", "event_b": "Oil prices increase"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["verdict"] in ["strong", "plausible", "weak", "unsupported"]
    assert "explanation" in data
    assert "confidence" in data
    assert "causal_path" in data


def test_generate_thesis(client):
    """Test generating a trade thesis"""
    # Create scenario
    scenario_data = {
        "title": "Thesis Test",
        "root_event": "Strait of Hormuz closes",
        "mode": "discover",
    }
    create_response = client.post("/api/scenarios", json=scenario_data)
    scenario_id = create_response.json()["id"]

    # Generate causal chain first
    client.post(f"/api/scenarios/{scenario_id}/generate")

    # Generate thesis
    response = client.post(f"/api/scenarios/{scenario_id}/thesis")
    assert response.status_code == 200

    data = response.json()
    assert data["scenario_id"] == scenario_id
    assert "thesis" in data
    assert "expected_effect" in data
    assert "potential_trade" in data
    assert "catalysts" in data
    assert "invalidation_conditions" in data
    assert "confidence" in data
    assert "risks" in data


def test_list_versions(client, sample_scenario_data):
    """Test listing scenario versions"""
    # Create scenario
    create_response = client.post("/api/scenarios", json=sample_scenario_data)
    scenario_id = create_response.json()["id"]

    # List versions
    response = client.get(f"/api/scenarios/{scenario_id}/versions")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_restore_version(client, sample_scenario_data):
    """Test restoring a prior version of a scenario"""
    create_response = client.post("/api/scenarios", json=sample_scenario_data)
    scenario_id = create_response.json()["id"]

    # Seed a versioned change by mutating the scenario graph directly via the repo is
    # not accessible through the API, so we create an explicit version in the in-memory repo.
    scenario = client.get(f"/api/scenarios/{scenario_id}").json()
    version_response = client.get(f"/api/scenarios/{scenario_id}/versions")
    assert version_response.status_code == 200
    assert version_response.json() == []

    # The restore endpoint should accept a valid historical version and return the scenario state.
    restore_response = client.post(f"/api/scenarios/{scenario_id}/versions/v1/restore")
    assert restore_response.status_code == 200
    data = restore_response.json()
    assert data["id"] == scenario_id
    assert data["graph"]["nodes"] == []
    assert data["graph"]["edges"] == []
