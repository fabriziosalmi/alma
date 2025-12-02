"""Blueprint API routes."""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alma.core.database import get_session
from alma.core.state import diff_states
from alma.engines.fake import FakeEngine
from alma.middleware.auth import verify_api_key
from alma.models.blueprint import SystemBlueprintModel
from alma.schemas.blueprint import (
    DeploymentRequest,
    DeploymentResponse,
    SystemBlueprint,
    SystemBlueprintCreate,
    SystemBlueprintUpdate,
)

router = APIRouter(prefix="/blueprints", tags=["blueprints"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=SystemBlueprint, status_code=status.HTTP_201_CREATED)
async def create_blueprint(
    blueprint: SystemBlueprintCreate,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key),
) -> SystemBlueprint:
    """
    Create a new system blueprint.

    Args:
        blueprint: Blueprint data
        session: Database session

    Returns:
        Created blueprint
    """
    db_blueprint = SystemBlueprintModel(
        version=blueprint.version,
        name=blueprint.name,
        description=blueprint.description,
        resources=[r.model_dump() for r in blueprint.resources],
        blueprint_metadata=blueprint.metadata,
    )

    session.add(db_blueprint)
    await session.commit()
    await session.refresh(db_blueprint)

    return SystemBlueprint.model_validate(
        {
            **{k: v for k, v in db_blueprint.__dict__.items() if not k.startswith("_")},
            "metadata": db_blueprint.blueprint_metadata,
        }
    )


@router.get("/", response_model=list[SystemBlueprint])
async def list_blueprints(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> list[SystemBlueprint]:
    """
    List all system blueprints.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        session: Database session

    Returns:
        List of blueprints
    """
    result = await session.execute(select(SystemBlueprintModel).offset(skip).limit(limit))
    blueprints = result.scalars().all()
    return [
        SystemBlueprint.model_validate(
            {
                **{k: v for k, v in bp.__dict__.items() if not k.startswith("_")},
                "metadata": bp.blueprint_metadata,
            }
        )
        for bp in blueprints
    ]


@router.get("/{blueprint_id}", response_model=SystemBlueprint)
async def get_blueprint(
    blueprint_id: int,
    session: AsyncSession = Depends(get_session),
) -> SystemBlueprint:
    """
    Get a specific system blueprint.

    Args:
        blueprint_id: Blueprint ID
        session: Database session

    Returns:
        Blueprint data

    Raises:
        HTTPException: If blueprint not found
    """
    result = await session.execute(
        select(SystemBlueprintModel).where(SystemBlueprintModel.id == blueprint_id)
    )
    blueprint = result.scalar_one_or_none()

    if not blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint {blueprint_id} not found",
        )

    return SystemBlueprint.model_validate(
        {
            **{k: v for k, v in blueprint.__dict__.items() if not k.startswith("_")},
            "metadata": blueprint.blueprint_metadata,
        }
    )


@router.put("/{blueprint_id}", response_model=SystemBlueprint)
async def update_blueprint(
    blueprint_id: int,
    blueprint_update: SystemBlueprintUpdate,
    session: AsyncSession = Depends(get_session),
) -> SystemBlueprint:
    """
    Update a system blueprint.

    Args:
        blueprint_id: Blueprint ID
        blueprint_update: Updated blueprint data
        session: Database session

    Returns:
        Updated blueprint

    Raises:
        HTTPException: If blueprint not found
    """
    result = await session.execute(
        select(SystemBlueprintModel).where(SystemBlueprintModel.id == blueprint_id)
    )
    blueprint = result.scalar_one_or_none()

    if not blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint {blueprint_id} not found",
        )

    # Update fields
    update_data = blueprint_update.model_dump(exclude_unset=True)
    if "resources" in update_data:
        # Resources are already dicts from model_dump, or they might be ResourceDefinition objects
        resources = update_data["resources"]
        if resources and hasattr(resources[0], "model_dump"):
            update_data["resources"] = [r.model_dump() for r in resources]
        # else they're already dicts, keep as is

    for field, value in update_data.items():
        # Map metadata field to blueprint_metadata for the SQLAlchemy model
        if field == "metadata":
            blueprint.blueprint_metadata = value
        else:
            setattr(blueprint, field, value)

    await session.commit()
    await session.refresh(blueprint)

    return SystemBlueprint.model_validate(
        {
            **{k: v for k, v in blueprint.__dict__.items() if not k.startswith("_")},
            "metadata": blueprint.blueprint_metadata,
        }
    )


@router.delete("/{blueprint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blueprint(
    blueprint_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Delete a system blueprint.

    Args:
        blueprint_id: Blueprint ID
        session: Database session

    Raises:
        HTTPException: If blueprint not found
    """
    result = await session.execute(
        select(SystemBlueprintModel).where(SystemBlueprintModel.id == blueprint_id)
    )
    blueprint = result.scalar_one_or_none()

    if not blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint {blueprint_id} not found",
        )

    await session.delete(blueprint)
    await session.commit()


@router.post("/{blueprint_id}/deploy", response_model=DeploymentResponse)
async def deploy_blueprint(
    blueprint_id: int,
    deployment_request: DeploymentRequest,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key),
) -> DeploymentResponse:
    """
    Deploy a system blueprint using a declarative, plan-based workflow.
    """
    # 1. Get blueprint from DB
    db_blueprint = await session.get(SystemBlueprintModel, blueprint_id)
    if not db_blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint {blueprint_id} not found",
        )

    # Convert to the Pydantic schema for use with the new core logic
    blueprint_schema = SystemBlueprint.model_validate(
        {
            **{k: v for k, v in db_blueprint.__dict__.items() if not k.startswith("_")},
            "metadata": db_blueprint.blueprint_metadata,
        }
    )

    # 2. Get engine (currently only FakeEngine)
    # Future: Implement dynamic engine selection based on blueprint requirements
    engine = FakeEngine()

    try:
        # 3. Get current state from the infrastructure
        current_state = await engine.get_state(blueprint_schema)

        # 4. Calculate the plan by comparing desired vs. current state
        plan = diff_states(blueprint_schema, current_state)

        # 5. Handle dry run
        if deployment_request.dry_run:
            plan_summary = plan.generate_description()
            return DeploymentResponse(
                deployment_id="dry-run",
                status="validated",
                message="Dry run complete. The plan shows the actions that would be taken.",
                plan_summary=plan_summary,
            )

        # 6. Apply the plan
        if not plan.is_empty:
            await engine.apply(plan)
            await engine.destroy(plan)
            message = "Deployment complete."
        else:
            message = "No changes required. Infrastructure is already up-to-date."

        return DeploymentResponse(
            deployment_id=f"deploy-{blueprint_id}-{int(time.time())}",
            status="completed",
            message=message,
            plan_summary=plan.generate_description(),
            resources_created=[r.name for r in plan.to_create],
        )

    except Exception as e:
        logger.error(f"Deployment failed for blueprint {blueprint_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}",
        ) from e
