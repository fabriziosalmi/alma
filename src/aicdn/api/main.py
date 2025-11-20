"""
FastAPI application and endpoints
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from aicdn.models.blueprint import SystemBlueprint
from aicdn.engines.fake import FakeEngine
import uuid
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="ALMA Controller API",
    description="Infrastructure as Conversation - Declarative infrastructure orchestration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# In-memory storage for MVP (will be replaced with PostgreSQL)
blueprints_db: dict[str, dict] = {}
fake_engine = FakeEngine()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "ALMA Controller API",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {"blueprints": "/blueprints", "docs": "/docs", "health": "/health"},
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/blueprints", status_code=status.HTTP_201_CREATED)
async def create_blueprint(blueprint: SystemBlueprint):
    """
    Create a new SystemBlueprint

    This endpoint validates and stores a blueprint definition.
    The blueprint is not deployed until the deploy endpoint is called.
    """
    blueprint_id = str(uuid.uuid4())

    blueprints_db[blueprint_id] = {
        "id": blueprint_id,
        "blueprint": blueprint.model_dump(),
        "status": "created",
        "created_at": datetime.utcnow().isoformat(),
        "deployed_at": None,
        "deployment_status": None,
    }

    return {
        "id": blueprint_id,
        "name": blueprint.metadata.name,
        "status": "created",
        "message": f"Blueprint '{blueprint.metadata.name}' created successfully",
    }


@app.get("/blueprints")
async def list_blueprints():
    """List all blueprints"""
    return {
        "blueprints": [
            {
                "id": bp_id,
                "name": bp_data["blueprint"]["metadata"]["name"],
                "status": bp_data["status"],
                "created_at": bp_data["created_at"],
            }
            for bp_id, bp_data in blueprints_db.items()
        ],
        "total": len(blueprints_db),
    }


@app.get("/blueprints/{blueprint_id}")
async def get_blueprint(blueprint_id: str):
    """Get a specific blueprint by ID"""
    if blueprint_id not in blueprints_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Blueprint {blueprint_id} not found"
        )

    return blueprints_db[blueprint_id]


@app.post("/blueprints/{blueprint_id}/deploy")
async def deploy_blueprint(blueprint_id: str):
    """
    Deploy a blueprint

    This triggers the actual provisioning of resources defined in the blueprint.
    Uses the FakeEngine for MVP - will be replaced with real engines.
    """
    if blueprint_id not in blueprints_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Blueprint {blueprint_id} not found"
        )

    bp_data = blueprints_db[blueprint_id]
    blueprint = bp_data["blueprint"]

    # Update status to deploying
    bp_data["status"] = "deploying"
    bp_data["deployed_at"] = datetime.utcnow().isoformat()

    # Deploy each resource using FakeEngine (for now)
    deployment_results = []
    for resource in blueprint["spec"]["resources"]:
        result = await fake_engine.deploy(resource)
        deployment_results.append(
            {
                "resource": resource["name"],
                "status": result.status.value,
                "endpoint": result.endpoint,
            }
        )

    # Update final status
    bp_data["status"] = "deployed"
    bp_data["deployment_status"] = deployment_results

    return {
        "blueprint_id": blueprint_id,
        "name": blueprint["metadata"]["name"],
        "status": "deployed",
        "results": deployment_results,
        "message": "Blueprint deployed successfully",
    }


@app.delete("/blueprints/{blueprint_id}")
async def delete_blueprint(blueprint_id: str):
    """
    Delete (destroy) a blueprint and all its resources
    """
    if blueprint_id not in blueprints_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Blueprint {blueprint_id} not found"
        )

    bp_data = blueprints_db[blueprint_id]
    blueprint = bp_data["blueprint"]

    # Destroy each resource
    if bp_data.get("deployment_status"):
        for resource in blueprint["spec"]["resources"]:
            await fake_engine.destroy(resource)

    # Remove from database
    del blueprints_db[blueprint_id]

    return {"message": f"Blueprint {blueprint_id} deleted successfully"}


@app.post("/blueprints/{blueprint_id}/dry-run")
async def dry_run_blueprint(blueprint_id: str):
    """
    Perform a dry run to show what would be deployed

    This is a "Wow Factor" feature that shows the impact of deployment
    without actually creating resources.
    """
    if blueprint_id not in blueprints_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Blueprint {blueprint_id} not found"
        )

    bp_data = blueprints_db[blueprint_id]
    blueprint = bp_data["blueprint"]

    # Run dry-run for each resource
    dry_run_results = []
    for resource in blueprint["spec"]["resources"]:
        result = await fake_engine.dry_run(resource)
        dry_run_results.append({"resource": resource["name"], "plan": result})

    return {
        "blueprint_id": blueprint_id,
        "name": blueprint["metadata"]["name"],
        "dry_run": True,
        "plan": dry_run_results,
        "message": "This is what would be deployed (no resources created)",
    }
