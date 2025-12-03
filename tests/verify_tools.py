import sys
from pathlib import Path

# Add project root to path
sys.path.append(".")

from alma.core.tools import InfrastructureTools


def test_tools_loading():
    print("\n--- Testing Decoupled Tools Loading ---")

    # 1. Test get_available_tools
    tools = InfrastructureTools.get_available_tools()
    print(f"Loaded {len(tools)} tools.")
    assert len(tools) > 0, "No tools loaded!"

    # 2. Check for specific tool
    tool_names = [t["name"] for t in tools]
    print(f"Found tools: {tool_names[:3]}...")
    assert "create_blueprint" in tool_names
    assert "validate_blueprint" in tool_names

    # 3. Check structure
    create_bp = next(t for t in tools if t["name"] == "create_blueprint")
    assert "parameters" in create_bp
    assert "properties" in create_bp["parameters"]

    print("✓ Decoupled Tools Verified")


if __name__ == "__main__":
    test_tools_loading()
