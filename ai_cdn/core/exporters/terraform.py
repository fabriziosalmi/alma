"""
Terraform HCL code exporter.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List

from jinja2 import Environment, FileSystemLoader

from ai_cdn.schemas.blueprint import SystemBlueprint, ResourceDefinition

logger = logging.getLogger(__name__)

# The path to the Jinja2 templates, relative to the project root.
# This assumes the exporter is run from the project root.
TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "terraform"


class TerraformExporter:
    """
    Exports a SystemBlueprint to a set of Terraform HCL files.
    """

    def __init__(self, blueprint: SystemBlueprint):
        if not blueprint:
            raise ValueError("A valid SystemBlueprint must be provided.")
        self.blueprint = blueprint
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def export(self) -> Dict[str, str]:
        """
        Renders the blueprint into a dictionary of Terraform file contents.

        Returns:
            A dictionary where keys are filenames (e.g., "main.tf") and
            values are the rendered HCL code as strings.
        """
        logger.info(f"Starting Terraform export for blueprint '{self.blueprint.name}'...")
        
        processed_resources = self._process_resources()
        
        main_tf_content = self.jinja_env.get_template("main.tf.j2").render(
            resources=processed_resources
        )
        
        logger.info("Terraform export complete.")
        
        return {
            "main.tf": main_tf_content
            # provider.tf and outputs.tf could be rendered here as well
        }

    def _process_resources(self) -> List[Dict[str, Any]]:
        """
        Processes blueprint resources into a format suitable for the Jinja2 template.
        """
        processed = []
        
        # This logic is complex because a single 'compute' resource in our blueprint
        # maps to *two* terraform resources: a docker_image and a docker_container.
        # We need to create the image resource first and give it a name the container can reference.
        
        for resource in self.blueprint.resources:
            if resource.provider == "docker" and resource.type == "compute":
                # 1. Create the docker_image resource representation
                image_resource_name = f"{resource.name}_image".replace("-", "_")
                image_resource = {
                    "name": image_resource_name,
                    "tf_type": "docker_image",
                    "specs": {"image": resource.specs.get("image")},
                }
                processed.append(image_resource)

                # 2. Create the docker_container resource representation
                container_resource = {
                    "name": resource.name,
                    "tf_type": "docker_container",
                    "specs": resource.specs,
                    "image_resource_name": image_resource_name, # So we can reference the image
                }
                processed.append(container_resource)

            elif resource.provider == "proxmox":
                # Future implementation for Proxmox
                # 'compute' -> 'proxmox_vm_qemu'
                logger.warning(f"Proxmox provider for resource '{resource.name}' is not yet supported.")
                pass
                
            else:
                logger.warning(
                    f"Unsupported provider '{resource.provider}' or type '{resource.type}' "
                    f"for resource '{resource.name}'."
                )

        return processed
