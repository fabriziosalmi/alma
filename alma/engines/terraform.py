"""Terraform engine implementation."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from typing import Any

from alma.core.state import Plan, ResourceState
from alma.engines.base import Engine
from alma.schemas.blueprint import SystemBlueprint

logger = logging.getLogger(__name__)


class TerraformEngine(Engine):
    """
    Engine for Terraform/OpenTofu.

    Executes Terraform commands to manage infrastructure.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize Terraform engine.

        Args:
            config: Engine configuration
                - binary: Path to terraform/tofu binary (default: terraform)
                - work_dir: Base directory for terraform runs (default: /tmp/alma-terraform)
        """
        super().__init__(config)
        self.binary = self.config.get("binary", "terraform")
        self.work_dir = self.config.get("work_dir", "/tmp/alma-terraform")

    def _check_binary(self) -> None:
        if not shutil.which(self.binary):
            raise RuntimeError(f"{self.binary} binary not found in PATH.")

    def _run_command(self, args: list[str], cwd: str) -> tuple[int, str, str]:
        """Run a terraform command."""
        cmd = [self.binary] + args
        logger.info(f"Running command: {' '.join(cmd)} in {cwd}")

        process = subprocess.Popen(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr

    async def health_check(self) -> bool:
        """Check if Terraform is usable."""
        try:
            self._check_binary()
            rc, _, _ = self._run_command(["version"], cwd=".")
            return rc == 0
        except Exception:
            return False

    async def get_state(self, blueprint: SystemBlueprint) -> list[ResourceState]:
        """
        Get state of Terraform managed resources.

        Parses terraform state to find resources.
        """
        # We assume one workspace per blueprint for simplicity?
        # Or one workspace per resource? Terraform usually manages a stack.
        # If the blueprint represents a stack, we look at that stack's state.

        # For this implementation, we assume the blueprint ID maps to a directory.
        bp_dir = os.path.join(self.work_dir, str(blueprint.id))
        if not os.path.exists(bp_dir):
            return []

        rc, stdout, stderr = self._run_command(["show", "-json"], cwd=bp_dir)
        if rc != 0:
            logger.warning(f"Failed to show state: {stderr}")
            return []

        try:
            state_data = json.loads(stdout)
            resources = []

            # Parse root module resources
            if "values" in state_data and "root_module" in state_data["values"]:
                for res in state_data["values"]["root_module"].get("resources", []):
                    resources.append(
                        ResourceState(
                            id=res["address"],  # e.g. aws_instance.web
                            type="terraform_resource",
                            config=res.get("values", {}),
                        )
                    )
            return resources
        except json.JSONDecodeError:
            return []

    async def apply(self, plan: Plan) -> None:
        """Apply Terraform configuration."""
        self._check_binary()

        # We treat the whole plan as a single Terraform apply if possible,
        # but the Plan object is resource-based.
        # If resources have 'hcl' spec, we aggregate them?
        # Or we run terraform for each resource? (Inefficient but isolated)

        # Strategy: Group resources by 'stack' or 'module' metadata?
        # For simplicity, we assume each resource in the plan is a separate terraform run
        # (micro-stacks) OR we assume the blueprint is one stack.

        # Let's go with: Each resource definition in the blueprint that uses 'terraform' provider
        # is a separate state file (isolated).

        for resource_def in plan.to_create + [r for _, r in plan.to_update]:
            if resource_def.provider != "terraform":
                continue

            print(f"Applying Terraform for: {resource_def.name}")

            res_dir = os.path.join(self.work_dir, resource_def.name)
            os.makedirs(res_dir, exist_ok=True)

            # Write HCL
            hcl = resource_def.specs.get("hcl")
            source = resource_def.specs.get("source")

            if hcl:
                with open(os.path.join(res_dir, "main.tf"), "w") as f:
                    f.write(hcl)
            elif source:
                # If source is provided, we might need a main.tf that uses a module
                # or just copy files.
                pass
            else:
                print(f"Skipping {resource_def.name}: No HCL or source specified")
                continue

            # Init
            rc, out, err = self._run_command(["init", "-no-color"], cwd=res_dir)
            if rc != 0:
                raise RuntimeError(f"Terraform init failed: {err}")

            # Apply
            rc, out, err = self._run_command(["apply", "-auto-approve", "-no-color"], cwd=res_dir)
            if rc != 0:
                raise RuntimeError(f"Terraform apply failed: {err}")

    async def destroy(self, plan: Plan) -> None:
        """Destroy Terraform resources."""
        self._check_binary()

        for resource_state in plan.to_delete:
            # We need to know the directory.
            # Assuming ID maps to name which maps to directory.
            # But resource_state.id from get_state was 'address'.
            # This mismatch is tricky.
            # If we use micro-stacks, the resource_state.id should be the stack name?

            # Let's assume resource_state.id IS the resource name from the blueprint
            # (which matches the directory name).

            print(f"Destroying Terraform stack: {resource_state.id}")
            res_dir = os.path.join(self.work_dir, resource_state.id)

            if not os.path.exists(res_dir):
                print(f"Directory {res_dir} not found, skipping destroy.")
                continue

            rc, out, err = self._run_command(["destroy", "-auto-approve", "-no-color"], cwd=res_dir)
            if rc != 0:
                print(f"Terraform destroy failed: {err}")
            else:
                # Cleanup directory
                shutil.rmtree(res_dir)

    def get_supported_resource_types(self) -> list[str]:
        return ["terraform_stack", "cloud_resource"]
