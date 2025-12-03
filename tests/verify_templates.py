import sys
from pathlib import Path

# Add project root to path
sys.path.append(".")

from alma.core.templates import BlueprintTemplates, TemplateCategory


def test_templates_loading():
    print("\n--- Testing Dynamic Templates Loading ---")

    # 1. Test get_all_templates
    templates = BlueprintTemplates.get_all_templates()
    print(f"Loaded {len(templates)} templates.")
    assert len(templates) > 0, "No templates loaded!"

    # 2. Test get_template
    t_id = "simple-web-app"
    template = BlueprintTemplates.get_template(t_id)
    print(f"Retrieved template '{t_id}': {template['name']}")
    assert template["name"] == "simple-web-app"
    assert template["category"] == "web"

    # 3. Test customization
    custom = BlueprintTemplates.customize_template(t_id, {"instance_count": 3})
    compute_nodes = [r for r in custom["resources"] if r["type"] == "compute"]
    print(f"Customized instance count: {len(compute_nodes)} (Expected > 2)")
    assert len(compute_nodes) >= 3

    print("✓ Dynamic Templates Verified")


if __name__ == "__main__":
    test_templates_loading()
