
"""
Integration test for Council Schema Enforcement.
Verifies that the Council passes the correct schema to the LLM,
and that the LocalStudioLLM constructs the correct API payload.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from alma.core.agent.council import Council
from alma.core.llm_service import LocalStudioLLM
from alma.core.config import settings

@pytest.mark.asyncio
async def test_council_schema_passing():
    """Verify Council passes schema to Architect's final step."""
    
    # Mock LLM to spy on generate calls
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = '{"test": "blueprint"}'
    
    # Patch get_llm to return our mock
    with patch("alma.core.agent.council.get_llm", new=AsyncMock(return_value=mock_llm)):
        council = Council()
        
        # We need to simulate the state where we are at the final step
        # But Council.convene is monolithic. Let's just run convene and check the LAST call.
        
        # Mock the intermediate steps to return dummy text
        mock_llm.generate.side_effect = [
            "Blueprint Proposal", # Architect Draft
            "Security Critique",  # SecOps
            "Cost Analysis",      # FinOps
            '{"final": "blueprint"}' # Architect Final
        ]
        
        await council.convene("Build a test app")
        
        # Check call args
        assert mock_llm.generate.call_count == 4
        
        # Get the final call (Architect Final Synthesis)
        final_call_args = mock_llm.generate.call_args_list[-1]
        _, kwargs = final_call_args
        
        # Verify schema presence
        assert "schema" in kwargs
        schema = kwargs["schema"]
        
        # Verify schema structure (basic checks)
        assert schema["type"] == "object"
        assert "resources" in schema["properties"]
        assert "required" in schema

@pytest.mark.asyncio
async def test_local_studio_payload_construction():
    """Verify LocalStudioLLM constructs correct JSON schema payload."""
    
    llm = LocalStudioLLM(base_url="http://mock-url", model_name="test-model")
    
    test_schema = {"type": "object", "properties": {"foo": {"type": "string"}}}
    
    # Mock httpx client
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "{}"}}]
        }
        mock_client.post.return_value = mock_response
        
        await llm.generate("Test prompt", schema=test_schema)
        
        # Verify post payload
        call_args = mock_client.post.call_args
        url, kwargs = call_args
        json_body = kwargs["json"]
        
        assert "response_format" in json_body
        rf = json_body["response_format"]
        assert rf["type"] == "json_schema"
        assert rf["json_schema"]["schema"] == test_schema
        assert rf["json_schema"]["strict"] is True

if __name__ == "__main__":
    # Manually run if executed as script
    pass
