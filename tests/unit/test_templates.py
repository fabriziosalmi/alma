"""Tests for blueprint templates."""

import pytest
from alma.core.templates import BlueprintTemplates, TemplateCategory


class TestBlueprintTemplates:
    """Tests for blueprint template generation."""

    def test_list_templates(self) -> None:
        """Test listing all templates."""
        templates = BlueprintTemplates.list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0

        # Check template structure
        template = templates[0]
        assert "id" in template
        assert "name" in template
        assert "category" in template
        assert "description" in template

    def test_list_templates_by_category(self) -> None:
        """Test filtering templates by category."""
        web_templates = BlueprintTemplates.list_templates(category=TemplateCategory.WEB)
        assert isinstance(web_templates, list)
        assert all(t["category"] == TemplateCategory.WEB for t in web_templates)

    def test_get_template_simple_web(self) -> None:
        """Test getting simple web app template."""
        template = BlueprintTemplates.get_template("simple-web-app")
        assert template is not None
        assert template["name"] == "simple-web-app"
        assert "resources" in template
        assert len(template["resources"]) > 0

    def test_get_template_ha_web(self) -> None:
        """Test getting HA web app template."""
        template = BlueprintTemplates.get_template("ha-web-app")
        assert template is not None
        assert "resources" in template

    def test_get_template_kubernetes(self) -> None:
        """Test getting Kubernetes template."""
        template = BlueprintTemplates.get_template("kubernetes-cluster")
        assert template is not None
        assert "resources" in template

    def test_get_template_microservices(self) -> None:
        """Test getting microservices template."""
        template = BlueprintTemplates.get_template("microservices")
        assert template is not None
        assert "resources" in template

    def test_get_template_data_pipeline(self) -> None:
        """Test getting data pipeline template."""
        template = BlueprintTemplates.get_template("data-pipeline")
        assert template is not None
        assert "resources" in template

    def test_get_nonexistent_template(self) -> None:
        """Test getting a template that doesn't exist."""
        with pytest.raises(ValueError, match="not found"):
            BlueprintTemplates.get_template("nonexistent-template")

    def test_customize_template(self) -> None:
        """Test customizing a template."""
        params = {"instance_count": 5, "cpu": 8, "memory": "16GB"}
        customized = BlueprintTemplates.customize_template("simple-web-app", params)
        assert customized is not None
        assert "resources" in customized

    def test_all_templates_have_required_fields(self) -> None:
        """Test that all templates have required fields."""
        templates = BlueprintTemplates.list_templates()
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "category" in template
            assert "description" in template
            assert "complexity" in template
