"""API routes for System Blueprints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ai_cdn.core.database import get_session
from ai_cdn.models.blueprint import SystemBlueprintModel
from ai_cdn.schemas.blueprint import (
    SystemBlueprint,
    SystemBlueprintCreate,
    SystemBlueprintUpdate,
    DeploymentRequest,
    DeploymentResponse,
)
from ai_cdn.core.config import get_settings
from ai_cdn.engines.fake import FakeEngine

router = APIRouter(prefix="/blueprints", tags=["blueprints"])
settings = get_settings()


@router.post("/", response_model=SystemBlueprint, status_code=status.HTTP_201_CREATED)
async def create_blueprint(
    blueprint: SystemBlueprintCreate,
    session: AsyncSession = Depends(get_session),
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
        metadata=blueprint.metadata,
    )

    session.add(db_blueprint)
    await session.commit()
    await session.refresh(db_blueprint)

    return SystemBlueprint.model_validate(db_blueprint)


@router.get("/", response_model=List[SystemBlueprint])
async def list_blueprints(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> List[SystemBlueprint]:
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
    return [SystemBlueprint.model_validate(bp) for bp in blueprints]


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

    return SystemBlueprint.model_validate(blueprint)


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
        update_data["resources"] = [r.model_dump() for r in update_data["resources"]]

    for field, value in update_data.items():
        setattr(blueprint, field, value)

    await session.commit()
    await session.refresh(blueprint)

    return SystemBlueprint.model_validate(blueprint)


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
) -> DeploymentResponse:
    """
    Deploy a system blueprint.

    Args:
        blueprint_id: Blueprint ID
        deployment_request: Deployment configuration
        session: Database session

    Returns:
        Deployment result

    Raises:
        HTTPException: If blueprint not found or deployment fails
    """
    # Get blueprint
    result = await session.execute(
        select(SystemBlueprintModel).where(SystemBlueprintModel.id == blueprint_id)
    )
    blueprint = result.scalar_one_or_none()

    if not blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint {blueprint_id} not found",
        )

    # Convert to dict for engine
    blueprint_dict = {
        "version": blueprint.version,
        "name": blueprint.name,
        "description": blueprint.description,
        "resources": blueprint.resources,
        "metadata": blueprint.metadata,
    }

    # Get engine (currently only FakeEngine)
    engine = FakeEngine()

    # Validate blueprint
    try:
        await engine.validate_blueprint(blueprint_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid blueprint: {str(e)}",
        )

    # Deploy or dry-run
    if deployment_request.dry_run:
        return DeploymentResponse(
            deployment_id="dry-run",
            status="validated",
            message="Blueprint is valid (dry-run mode)",
            resources_created=[],
            resources_failed=[],
        )

    # Actual deployment
    try:
        result = await engine.deploy(blueprint_dict)
        return DeploymentResponse(
            deployment_id=result.metadata.get("deployment_id", "unknown"),
            status=result.status.value,
            message=result.message,
            resources_created=result.resources_created,
            resources_failed=result.resources_failed,
            metadata=result.metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}",
        )
