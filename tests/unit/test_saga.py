"""Unit tests for Saga Pattern."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from alma.core.saga import SagaOrchestrator, SagaStep
from alma.models.saga import SagaStateModel


class MockStep(SagaStep):
    def __init__(self, name, should_fail=False):
        self.name = name
        self.should_fail = should_fail
        self.executed = False
        self.compensated = False

    async def execute(self, context):
        if self.should_fail:
            raise RuntimeError("Step failed")
        self.executed = True

    async def compensate(self, context):
        self.compensated = True


@pytest.fixture
def mock_session_factory():
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    # Create a properly initialized state
    mock_state = SagaStateModel(
        saga_id="test-saga", correlation_id="test-corr", status="RUNNING", history=[], payload={}
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_state
    mock_session.execute = AsyncMock(return_value=mock_result)

    factory = MagicMock(return_value=mock_session)
    return factory


@pytest.mark.asyncio
async def test_saga_success(mock_session_factory):
    step1 = MockStep("step1")
    step2 = MockStep("step2")
    orchestrator = SagaOrchestrator(mock_session_factory, [step1, step2])

    await orchestrator.execute("corr-1", {})

    assert step1.executed
    assert step2.executed
    assert not step1.compensated
    assert not step2.compensated


@pytest.mark.asyncio
async def test_saga_rollback(mock_session_factory):
    step1 = MockStep("step1")
    step2 = MockStep("step2", should_fail=True)
    orchestrator = SagaOrchestrator(mock_session_factory, [step1, step2])

    with pytest.raises(RuntimeError):
        await orchestrator.execute("corr-2", {})

    assert step1.executed
    # Step 2 failed during execution
    assert step1.compensated
    assert (
        not step2.compensated
    )  # Failed step usually doesn't need compensation if it didn't complete, or depends on logic. Here we compensate *completed* steps.
