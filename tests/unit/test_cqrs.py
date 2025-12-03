"""Unit tests for CQRS."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from alma.core.cqrs import InfrastructureProjector
from alma.core.events import Event
from alma.models.view import InfrastructureViewModel

class DeploymentStarted(Event):
    pass

@pytest.fixture
def mock_session_factory():
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None # No existing view
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    factory = MagicMock(return_value=mock_session)
    return factory

@pytest.mark.asyncio
async def test_projector_creates_view(mock_session_factory):
    projector = InfrastructureProjector(mock_session_factory)
    event = DeploymentStarted(aggregate_id="123", aggregate_type="blueprint")
    
    await projector.handle(event)
    
    mock_session = mock_session_factory.return_value
    mock_session.add.assert_called_once()
    args = mock_session.add.call_args[0][0]
    assert isinstance(args, InfrastructureViewModel)
    assert args.blueprint_id == 123
    assert args.status == "DEPLOYING"

@pytest.mark.asyncio
async def test_projector_updates_view(mock_session_factory):
    # Setup existing view
    existing_view = InfrastructureViewModel(blueprint_id=123, status="UNKNOWN")
    
    mock_session = mock_session_factory.return_value
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_view
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    projector = InfrastructureProjector(mock_session_factory)
    event = DeploymentStarted(aggregate_id="123", aggregate_type="blueprint")
    
    await projector.handle(event)
    
    assert existing_view.status == "DEPLOYING"
    # Should not add new view
    mock_session.add.assert_not_called()
