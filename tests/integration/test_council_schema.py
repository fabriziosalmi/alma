"""
Integration test for Council Schema Enforcement.
"""

import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from alma.core.agent.council import Council
from alma.schemas.council import (
    InfrastructureDraft,
    SecurityCritique,
    CostAnalysis,
    FinalDecree,
    InfrastructureResource,
    Vulnerability,
    CostItem
)

@pytest.mark.asyncio
async def test_council_schema_flow():
    """Verify Council flow with strict schemas."""

    # PREPARE MOCK DATA
    draft_obj = InfrastructureDraft(
        name="Test",
        description="Desc",
        resources=[
            InfrastructureResource(type="compute", name="web", provider="proxmox", specs={"cpu": 2})
        ]
    )
    
    sec_obj = SecurityCritique(
        safe=True,
        vulnerabilities=[],
        summary="Secure"
    )
    
    fin_obj = CostAnalysis(
        total_monthly_cost=10.0,
        items=[],
        savings_suggestions=[]
    )
    
    final_obj = FinalDecree(
        blueprint=draft_obj,
        approved=True,
        reasoning="LGTM"
    )

    # MOCK LLM
    mock_llm = AsyncMock()
    # Sequence: Draft -> Sec/Fin (Parallel order unrelated) -> Final
    # Since Sec/Fin are parallel, side_effect might be racy if strictly ordered, 
    # but asyncio.gather usually schedules in order of awaitables passed.
    # Architect(Draft) -> SecOps -> FinOps -> Architect(Final)
    # Note: gather(sec, fin) -> usually sec then fin if tasks start immediately.
    
    mock_llm.generate.side_effect = [
        draft_obj.model_dump_json(),
        sec_obj.model_dump_json(),
        fin_obj.model_dump_json(),
        final_obj.model_dump_json()
    ]

    with patch("alma.core.agent.council.get_llm", new=AsyncMock(return_value=mock_llm)):
        council = Council()
        result = await council.convene("Build app")

        assert result.final_blueprint is not None
        assert result.final_blueprint["name"] == "Test"
        
        # Verify call count (4 interactions)
        assert mock_llm.generate.call_count == 4
        
        # Verify Schemas were passed
        # Call 1: Draft
        _, kwargs1 = mock_llm.generate.call_args_list[0]
        assert "schema" in kwargs1
        assert "InfrastructureDraft" in json.dumps(kwargs1["schema"])

        # Call 4: Final
        _, kwargs4 = mock_llm.generate.call_args_list[3]
        assert "schema" in kwargs4
        assert "FinalDecree" in json.dumps(kwargs4["schema"])
