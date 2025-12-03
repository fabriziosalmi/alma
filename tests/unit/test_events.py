"""Unit tests for Event Sourcing."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import pytest
from alma.core.events import Event, EventBus, EventStore
from alma.models.event import EventModel

class SampleEvent(Event):
    payload_data: str

@pytest.fixture
def mock_session_factory():
    mock_session = MagicMock()
    # Ensure __aenter__ returns the session itself
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    # Ensure __aexit__ is awaitable
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    # The factory returns the session (not awaitable itself, but the context manager is async)
    factory = MagicMock(return_value=mock_session)
    return factory

@pytest.fixture
def event_store(mock_session_factory):
    return EventStore(mock_session_factory)

@pytest.fixture
def event_bus(event_store):
    return EventBus(event_store)

@pytest.mark.asyncio
async def test_event_store_append(event_store, mock_session_factory):
    event = SampleEvent(aggregate_id="1", aggregate_type="test", payload_data="foo")
    
    await event_store.append(event)
    
    mock_session = mock_session_factory.return_value
    mock_session.add.assert_called_once()
    args = mock_session.add.call_args[0][0]
    assert isinstance(args, EventModel)
    assert args.aggregate_id == "1"
    assert args.payload["payload_data"] == "foo"

@pytest.mark.asyncio
async def test_event_bus_publish(event_bus, event_store):
    event = SampleEvent(aggregate_id="1", aggregate_type="test", payload_data="foo")
    
    handler = AsyncMock()
    handler.__name__ = "mock_handler"  # Fix AttributeError
    
    event_bus.subscribe(SampleEvent, handler)
    
    # Mock store append to avoid DB calls
    event_store.append = AsyncMock()
    
    await event_bus.publish(event)
    
    event_store.append.assert_called_once_with(event)
    handler.assert_called_once_with(event)
