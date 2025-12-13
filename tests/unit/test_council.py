"""Unit tests for The Council."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from alma.core.agent.council import Council, Agent, AgentMessage
from alma.schemas.council import InfrastructureDraft

@pytest.fixture
def mock_llm():
    mock = AsyncMock()
    mock.generate.return_value = '{"test": "value"}'
    return mock

@pytest.fixture
def council(mock_llm):
    with patch("alma.core.agent.council.get_llm", new=AsyncMock(return_value=mock_llm)):
        return Council()

class TestAgent:
    @pytest.mark.asyncio
    async def test_speak_simple(self, mock_llm):
        """Test agent speaking without schema."""
        agent = Agent("TestBot", "Tester", "Just testing", "blue")
        
        with patch("alma.core.agent.council.get_llm", new=AsyncMock(return_value=mock_llm)):
            mock_llm.generate.return_value = "Hello World"
            response = await agent.speak("Context", "Say hi")
            assert response == "Hello World"
            
            # Verify prompt content
            args, _ = mock_llm.generate.call_args
            prompt = args[0]
            assert "TestBot" in prompt
            assert "Tester" in prompt
            assert "Just testing" in prompt

    @pytest.mark.asyncio
    async def test_speak_with_schema_success(self, mock_llm):
        """Test agent speaking with Pydantic schema."""
        agent = Agent("Archie", "Architect", "Design", "blue")
        
        valid_json = '{"name": "MyDraft", "description": "Test", "resources": []}'
        mock_llm.generate.return_value = valid_json
        
        with patch("alma.core.agent.council.get_llm", new=AsyncMock(return_value=mock_llm)):
            result = await agent.speak("Ctx", "Task", response_model=InfrastructureDraft)
            assert isinstance(result, InfrastructureDraft)
            assert result.name == "MyDraft"

    @pytest.mark.asyncio
    async def test_speak_with_schema_failure_retry(self, mock_llm):
        """Test agent failing schema validation raises exception."""
        agent = Agent("Archie", "Architect", "Design", "blue")
        
        mock_llm.generate.return_value = '{"invalid": "json"}'
        
        with patch("alma.core.agent.council.get_llm", new=AsyncMock(return_value=mock_llm)):
            with pytest.raises(Exception): # Pydantic ValidationError
                await agent.speak("Ctx", "Task", response_model=InfrastructureDraft)

class TestCouncil:
    @pytest.mark.asyncio
    async def test_convene_success(self, council, mock_llm):
        """Test successful council meeting."""
        # 1. Draft
        # 2. SecOps (Parallel)
        # 3. FinOps (Parallel)
        # 4. Final
        
        draft = InfrastructureDraft(name="Draft", description="D", resources=[])
        sec = MagicMock() # Mock Pydantic models with simple objects or proper ones
        # Actually easier to just return proper JSON strings for the mock to parse
        
        mock_llm.generate.side_effect = [
            draft.model_dump_json(),
            '{"safe": true, "vulnerabilities": [], "summary": "Safe"}', # Sec
            '{"total_monthly_cost": 100, "items": [], "savings_suggestions": []}', # Fin
            '{"blueprint": ' + draft.model_dump_json() + ', "approved": true, "reasoning": "Yes"}' # Final
        ]
        
        result = await council.convene("Launch app")
        
        assert result.final_blueprint is not None
        assert len(result.transcript) == 4
        assert result.transcript[0].agent_name == "Architect"
        assert result.transcript[0].role == "proposal"

    @pytest.mark.asyncio
    async def test_convene_failure_graceful(self, council, mock_llm):
        """Test council handles crash gracefully."""
        # Force failure on first call
        mock_llm.generate.side_effect = Exception("LLM Down")
        
        result = await council.convene("Launch app")
        
        assert result.final_blueprint is None
        # Should have an error entry in transcript
        assert result.transcript[-1].role == "error"
        assert "LLM Down" in result.transcript[-1].content
