"""Unit tests for the TerraformExporter."""

import unittest
from datetime import datetime

from alma.core.exporters.terraform import TerraformExporter
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition


class TestTerraformExporter(unittest.TestCase):
    def test_export_docker_compute_resource(self):
        """
        Tests that a blueprint with a single Docker compute resource is
        exported to valid HCL.
        """
        # 1. Create a sample blueprint
        blueprint = SystemBlueprint(
            id=1,
            name="docker-app-bp",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            resources=[
                ResourceDefinition(
                    name="my-web-server",
                    type="compute",
                    provider="docker",
                    specs={
                        "image": "nginx:1.21.6",
                        "ports": [8080],
                    },
                )
            ],
        )

        # 2. Instantiate the exporter and export the HCL
        exporter = TerraformExporter(blueprint)
        hcl_files = exporter.export()

        # 3. Assert the output is correct
        self.assertIn("main.tf", hcl_files)
        main_tf = hcl_files["main.tf"]

        # Check for the docker_image resource
        self.assertIn('resource "docker_image" "my_web_server_image"', main_tf)
        self.assertIn('name = "nginx:1.21.6"', main_tf)

        # Check for the docker_container resource
        self.assertIn('resource "docker_container" "my-web-server"', main_tf)
        self.assertIn("image = resource.docker_image.my_web_server_image.image_id", main_tf)

        # Check for port mapping
        self.assertIn("internal = 8080", main_tf)
        self.assertIn("external = 8080", main_tf)

    def test_exporter_handles_empty_blueprint(self):
        """
        Tests that the exporter doesn't fail with an empty list of resources.
        """
        blueprint = SystemBlueprint(
            id=2,
            name="empty-bp",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            resources=[],  # No resources
        )

        exporter = TerraformExporter(blueprint)
        hcl_files = exporter.export()

        self.assertIn("main.tf", hcl_files)
        # Check that no 'resource' blocks were created
        self.assertNotIn('resource "', hcl_files["main.tf"])

    def test_raises_error_on_null_blueprint(self):
        """
        Tests that the exporter raises a ValueError if initialized with None.
        """
        with self.assertRaises(ValueError):
            TerraformExporter(None)


if __name__ == "__main__":
    unittest.main()
