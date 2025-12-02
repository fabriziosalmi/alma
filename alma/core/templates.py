"""Infrastructure templates and blueprint generation."""

from __future__ import annotations

import logging
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class TemplateCategory(str, Enum):
    """Blueprint template categories."""

    WEB = "web"
    DATABASE = "database"
    MICROSERVICES = "microservices"
    DATA = "data"
    ML = "ml"
    SECURITY = "security"
    NETWORKING = "networking"
    MONITORING = "monitoring"


class BlueprintTemplates:
    """
    Library of pre-built blueprint templates for common patterns.

    Templates are loaded dynamically from alma/config/blueprints.yaml.
    """

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_templates() -> dict[str, dict[str, Any]]:
        """
        Load templates from YAML configuration file.
        Cached to prevent repeated disk I/O.
        """
        try:
            # Resolve path relative to this file
            base_path = Path(__file__).parent.parent
            config_path = base_path / "config" / "blueprints.yaml"
            
            if not config_path.exists():
                logger.error(f"Blueprints configuration not found at {config_path}")
                return {}

            with open(config_path, "r") as f:
                templates = yaml.safe_load(f)
                
            logger.info(f"Loaded {len(templates)} blueprints from {config_path}")
            return templates or {}
            
        except Exception as e:
            logger.error(f"Failed to load blueprints: {e}")
            return {}

    @staticmethod
    def get_all_templates() -> list[dict[str, Any]]:
        """
        Get list of all available templates.

        Returns:
            List of template metadata
        """
        templates = BlueprintTemplates._load_templates()
        return [
            {
                "id": t_id,
                "name": t_data.get("name"),
                "category": t_data.get("category"),
                "description": t_data.get("description"),
                "complexity": t_data.get("complexity"),
                "estimated_cost": t_data.get("estimated_cost"),
            }
            for t_id, t_data in templates.items()
        ]

    @staticmethod
    def get_template(template_id: str) -> dict[str, Any]:
        """
        Get specific template blueprint.

        Args:
            template_id: Template identifier

        Returns:
            Blueprint template

        Raises:
            ValueError: If template not found
        """
        # Map common aliases to actual template IDs
        template_aliases = {
            "kubernetes-cluster": "microservices-k8s",
            "microservices": "microservices-k8s",
        }

        # Use alias if available
        actual_template_id = template_aliases.get(template_id, template_id)
        
        templates = BlueprintTemplates._load_templates()

        if actual_template_id not in templates:
            raise ValueError(f"Template '{template_id}' not found")

        return templates[actual_template_id]

    @staticmethod
    def list_templates(category: TemplateCategory | None = None) -> list[dict[str, Any]]:
        """
        List all available templates, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of template metadata
        """
        templates = BlueprintTemplates.get_all_templates()

        if category:
            templates = [t for t in templates if t["category"] == category]

        return templates

    @staticmethod
    def customize_template(template_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Customize a template with provided parameters.

        Args:
            template_id: Template identifier
            parameters: Customization parameters (e.g., instance_count, cpu_per_instance)

        Returns:
            Customized blueprint
        """
        template = BlueprintTemplates.get_template(template_id)
        blueprint = template.copy()

        # Apply common customizations
        if "instance_count" in parameters:
            # Scale compute resources
            compute_resources = [
                r for r in blueprint.get("resources", []) if r.get("type") == "compute"
            ]
            if compute_resources and len(compute_resources) > 0:
                # Replicate the first compute resource
                base_resource = compute_resources[0].copy()
                new_resources = []
                for r in blueprint.get("resources", []):
                    if r.get("type") != "compute":
                        new_resources.append(r)

                for i in range(parameters["instance_count"]):
                    resource = base_resource.copy()
                    resource["name"] = f"{base_resource['name']}-{i+1}"
                    new_resources.append(resource)

                blueprint["resources"] = new_resources

        if "cpu_per_instance" in parameters:
            for resource in blueprint.get("resources", []):
                if resource.get("type") == "compute" and "specs" in resource:
                    resource["specs"]["cpu"] = parameters["cpu_per_instance"]

        if "memory_per_instance" in parameters:
            for resource in blueprint.get("resources", []):
                if resource.get("type") == "compute" and "specs" in resource:
                    resource["specs"]["memory"] = parameters["memory_per_instance"]

        if "environment" in parameters:
            if "metadata" not in blueprint:
                blueprint["metadata"] = {}
            blueprint["metadata"]["environment"] = parameters["environment"]

        return blueprint
