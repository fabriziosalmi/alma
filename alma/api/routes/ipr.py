"""API routes for Infrastructure Pull Requests (IPR)."""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer

from alma.core.database import get_session
from alma.models.ipr import InfrastructurePullRequestModel, IPRStatus
from alma.models.blueprint import SystemBlueprintModel
from alma.schemas.ipr import (
    IPR,
    IPRCreate,
    IPRUpdate,
    IPRReview,
    IPRListResponse,
)
from alma.engines.fake import FakeEngine

router = APIRouter(prefix="/ipr", tags=["Infrastructure Pull Requests"])


@router.post("/", response_model=IPR, status_code=status.HTTP_201_CREATED)
async def create_ipr(
    ipr: IPRCreate,
    session: AsyncSession = Depends(get_session),
) -> IPR:
    """
    Create a new Infrastructure Pull Request.

    Args:
        ipr: IPR data
        session: Database session

    Returns:
        Created IPR
    """
    # Get blueprint
    result = await session.execute(
        select(SystemBlueprintModel).where(SystemBlueprintModel.id == ipr.blueprint_id)
    )
    blueprint = result.scalar_one_or_none()

    if not blueprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blueprint {ipr.blueprint_id} not found",
        )

    # Create blueprint snapshot
    blueprint_snapshot = {
        "id": blueprint.id,
        "version": blueprint.version,
        "name": blueprint.name,
        "description": blueprint.description,
        "resources": blueprint.resources,
        "metadata": blueprint.metadata,
    }

    # Create IPR
    db_ipr = InfrastructurePullRequestModel(
        title=ipr.title,
        description=ipr.description,
        blueprint_id=ipr.blueprint_id,
        blueprint_snapshot=blueprint_snapshot,
        changes_summary=ipr.changes_summary,
        status=IPRStatus.PENDING,
        created_by=ipr.created_by,
    )

    session.add(db_ipr)
    await session.commit()
    await session.refresh(db_ipr)

    return IPR.model_validate(db_ipr)


@router.get("/", response_model=IPRListResponse)
async def list_iprs(
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> IPRListResponse:
    """
    List all Infrastructure Pull Requests.

    Args:
        status_filter: Optional status filter
        skip: Number of records to skip
        limit: Maximum number of records to return
        session: Database session

    Returns:
        List of IPRs with statistics
    """
    # Build query
    query = select(InfrastructurePullRequestModel)

    if status_filter:
        query = query.where(InfrastructurePullRequestModel.status == status_filter)

    query = query.offset(skip).limit(limit)

    # Get IPRs
    result = await session.execute(query)
    iprs = result.scalars().all()

    # Get statistics
    stats_result = await session.execute(
        select(
            func.count(InfrastructurePullRequestModel.id).label("total"),
            func.sum(
                func.cast(
                    InfrastructurePullRequestModel.status == IPRStatus.PENDING,
                    Integer,
                )
            ).label("pending"),
            func.sum(
                func.cast(
                    InfrastructurePullRequestModel.status == IPRStatus.APPROVED,
                    Integer,
                )
            ).label("approved"),
            func.sum(
                func.cast(
                    InfrastructurePullRequestModel.status == IPRStatus.DEPLOYED,
                    Integer,
                )
            ).label("deployed"),
        )
    )
    stats = stats_result.one()

    return IPRListResponse(
        iprs=[IPR.model_validate(ipr) for ipr in iprs],
        total=stats.total or 0,
        pending=stats.pending or 0,
        approved=stats.approved or 0,
        deployed=stats.deployed or 0,
    )


@router.get("/{ipr_id}", response_model=IPR)
async def get_ipr(
    ipr_id: int,
    session: AsyncSession = Depends(get_session),
) -> IPR:
    """
    Get a specific Infrastructure Pull Request.

    Args:
        ipr_id: IPR ID
        session: Database session

    Returns:
        IPR data
    """
    result = await session.execute(
        select(InfrastructurePullRequestModel).where(InfrastructurePullRequestModel.id == ipr_id)
    )
    ipr = result.scalar_one_or_none()

    if not ipr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPR {ipr_id} not found",
        )

    return IPR.model_validate(ipr)


@router.put("/{ipr_id}", response_model=IPR)
async def update_ipr(
    ipr_id: int,
    ipr_update: IPRUpdate,
    session: AsyncSession = Depends(get_session),
) -> IPR:
    """
    Update an Infrastructure Pull Request.

    Args:
        ipr_id: IPR ID
        ipr_update: Updated IPR data
        session: Database session

    Returns:
        Updated IPR
    """
    result = await session.execute(
        select(InfrastructurePullRequestModel).where(InfrastructurePullRequestModel.id == ipr_id)
    )
    ipr = result.scalar_one_or_none()

    if not ipr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPR {ipr_id} not found",
        )

    # Only allow updates if status is PENDING
    if ipr.status != IPRStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update IPR with status {ipr.status}",
        )

    # Update fields
    update_data = ipr_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ipr, field, value)

    await session.commit()
    await session.refresh(ipr)

    return IPR.model_validate(ipr)


@router.post("/{ipr_id}/review", response_model=IPR)
async def review_ipr(
    ipr_id: int,
    review: IPRReview,
    session: AsyncSession = Depends(get_session),
) -> IPR:
    """
    Review an Infrastructure Pull Request.

    Args:
        ipr_id: IPR ID
        review: Review decision
        session: Database session

    Returns:
        Updated IPR
    """
    result = await session.execute(
        select(InfrastructurePullRequestModel).where(InfrastructurePullRequestModel.id == ipr_id)
    )
    ipr = result.scalar_one_or_none()

    if not ipr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPR {ipr_id} not found",
        )

    # Only allow review if status is PENDING
    if ipr.status != IPRStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review IPR with status {ipr.status}",
        )

    # Update IPR
    ipr.status = IPRStatus.APPROVED if review.approved else IPRStatus.REJECTED
    ipr.reviewed_by = review.reviewed_by
    ipr.review_comments = review.review_comments
    ipr.reviewed_at = datetime.utcnow()

    await session.commit()
    await session.refresh(ipr)

    return IPR.model_validate(ipr)


@router.post("/{ipr_id}/deploy", response_model=IPR)
async def deploy_ipr(
    ipr_id: int,
    session: AsyncSession = Depends(get_session),
) -> IPR:
    """
    Deploy an approved Infrastructure Pull Request.

    Args:
        ipr_id: IPR ID
        session: Database session

    Returns:
        Updated IPR with deployment information
    """
    result = await session.execute(
        select(InfrastructurePullRequestModel).where(InfrastructurePullRequestModel.id == ipr_id)
    )
    ipr = result.scalar_one_or_none()

    if not ipr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPR {ipr_id} not found",
        )

    # Only deploy approved IPRs
    if ipr.status != IPRStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only deploy approved IPRs. Current status: {ipr.status}",
        )

    # Get engine and deploy
    engine = FakeEngine()
    blueprint = ipr.blueprint_snapshot

    try:
        deploy_result = await engine.deploy(blueprint)

        if deploy_result.status.value == "completed":
            ipr.status = IPRStatus.DEPLOYED
            ipr.deployment_id = deploy_result.metadata.get("deployment_id")
            ipr.deployed_at = datetime.utcnow()
        else:
            ipr.status = IPRStatus.FAILED
            ipr.metadata = {
                "error": deploy_result.message,
                "failed_resources": deploy_result.resources_failed,
            }

        await session.commit()
        await session.refresh(ipr)

    except Exception as e:
        ipr.status = IPRStatus.FAILED
        ipr.metadata = {"error": str(e)}
        await session.commit()
        await session.refresh(ipr)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}",
        )

    return IPR.model_validate(ipr)


@router.delete("/{ipr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_ipr(
    ipr_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Cancel a pending Infrastructure Pull Request.

    Args:
        ipr_id: IPR ID
        session: Database session
    """
    result = await session.execute(
        select(InfrastructurePullRequestModel).where(InfrastructurePullRequestModel.id == ipr_id)
    )
    ipr = result.scalar_one_or_none()

    if not ipr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPR {ipr_id} not found",
        )

    # Only cancel pending IPRs
    if ipr.status not in [IPRStatus.PENDING, IPRStatus.APPROVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel IPR with status {ipr.status}",
        )

    ipr.status = IPRStatus.CANCELLED
    await session.commit()
