"""
Integration test for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from aicdn.api.main import app


client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AI-CDN Controller API"
    assert data["status"] == "operational"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_create_blueprint():
    """Test creating a blueprint"""
    blueprint_data = {
        "apiVersion": "cdn-ng.io/v1",
        "kind": "SystemBlueprint",
        "metadata": {
            "name": "test-blueprint",
            "version": "v1"
        },
        "spec": {
            "resources": []
        }
    }
    
    response = client.post("/blueprints", json=blueprint_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "test-blueprint"
    assert data["status"] == "created"


def test_list_blueprints():
    """Test listing blueprints"""
    response = client.get("/blueprints")
    assert response.status_code == 200
    data = response.json()
    assert "blueprints" in data
    assert "total" in data


def test_deploy_blueprint():
    """Test deploying a blueprint"""
    # First create a blueprint
    blueprint_data = {
        "apiVersion": "cdn-ng.io/v1",
        "kind": "SystemBlueprint",
        "metadata": {
            "name": "deploy-test",
            "version": "v1"
        },
        "spec": {
            "resources": [
                {
                    "kind": "ComputeNode",
                    "name": "test-node",
                    "spec": {
                        "cpu": 2,
                        "memory": "4Gi"
                    }
                }
            ]
        }
    }
    
    create_response = client.post("/blueprints", json=blueprint_data)
    blueprint_id = create_response.json()["id"]
    
    # Deploy it
    deploy_response = client.post(f"/blueprints/{blueprint_id}/deploy")
    assert deploy_response.status_code == 200
    data = deploy_response.json()
    assert data["status"] == "deployed"
    assert len(data["results"]) == 1


def test_dry_run_blueprint():
    """Test dry-run of a blueprint"""
    # Create a blueprint
    blueprint_data = {
        "apiVersion": "cdn-ng.io/v1",
        "kind": "SystemBlueprint",
        "metadata": {
            "name": "dry-run-test",
            "version": "v1"
        },
        "spec": {
            "resources": [
                {
                    "kind": "ComputeNode",
                    "name": "dry-node",
                    "spec": {
                        "cpu": 2,
                        "memory": "4Gi"
                    }
                }
            ]
        }
    }
    
    create_response = client.post("/blueprints", json=blueprint_data)
    blueprint_id = create_response.json()["id"]
    
    # Dry run
    dry_run_response = client.post(f"/blueprints/{blueprint_id}/dry-run")
    assert dry_run_response.status_code == 200
    data = dry_run_response.json()
    assert data["dry_run"] is True
    assert "plan" in data
