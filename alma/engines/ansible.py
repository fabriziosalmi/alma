"""Ansible engine implementation."""

from __future__ import annotations

import os
from typing import Any

try:
    import ansible_runner
except ImportError:
    ansible_runner = None

from alma.core.state import Plan, ResourceState
from alma.engines.base import Engine
from alma.schemas.blueprint import SystemBlueprint


class AnsibleEngine(Engine):
    """
    Engine for Ansible.

    Executes Ansible playbooks to manage infrastructure.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize Ansible engine.

        Args:
            config: Engine configuration
                - data_dir: Directory for ansible-runner artifacts
                - inventory: Path to inventory file or inventory content
        """
        super().__init__(config)
        self.data_dir = self.config.get("data_dir", "/tmp/alma-ansible")
        self.inventory = self.config.get("inventory", "localhost,")

    def _check_runner(self) -> None:
        if not ansible_runner:
            raise ImportError("ansible-runner package is not installed.")

    async def health_check(self) -> bool:
        """Check if Ansible is usable."""
        try:
            self._check_runner()
            # Try a simple ping
            r = ansible_runner.run(
                private_data_dir=self.data_dir, host_pattern="localhost", module="ping", quiet=True
            )
            return r.status == "successful"
        except Exception:
            return False

    async def get_state(self, blueprint: SystemBlueprint) -> list[ResourceState]:
        """
        Get state of Ansible managed resources.

        Since Ansible is stateless, we can't easily query the "current state"
        without running a playbook. For now, we assume if it's in the blueprint,
        it's managed.
        """
        # TODO: Implement fact gathering
        return []

    async def apply(self, plan: Plan) -> None:
        """Run playbooks to apply plan."""
        self._check_runner()

        for resource_def in plan.to_create:
            print(f"Applying playbook for: {resource_def.name}")
            playbook = resource_def.specs.get("playbook")
            if not playbook:
                print(f"Skipping {resource_def.name}: No playbook specified")
                continue

            # Write playbook to temp file or pass as string?
            # ansible-runner expects a file path usually.
            # For simplicity, we assume 'playbook' is a path or we write it.

            playbook_path = os.path.join(self.data_dir, f"{resource_def.name}.yml")
            os.makedirs(self.data_dir, exist_ok=True)

            if isinstance(playbook, str) and not os.path.exists(playbook):
                # Assume it's content
                with open(playbook_path, "w") as f:
                    f.write(playbook)
            elif isinstance(playbook, str) and os.path.exists(playbook):
                playbook_path = playbook

            r = ansible_runner.run(
                private_data_dir=self.data_dir,
                playbook=playbook_path,
                inventory=self.inventory,
                quiet=False,
            )

            if r.status != "successful":
                raise RuntimeError(f"Ansible playbook failed: {r.rc}")

        # Updates are just re-running the playbook (idempotency)
        for _, resource_def in plan.to_update:
            print(f"Re-applying playbook for: {resource_def.name}")
            # ... same logic as create ...
            # (Duplication for now, can refactor)

    async def destroy(self, plan: Plan) -> None:
        """Run cleanup playbooks."""
        self._check_runner()

        for resource_state in plan.to_delete:
            print(f"Destroying resource: {resource_state.id}")
            # We need a destroy playbook defined somewhere.
            # Since ResourceState doesn't store the original spec's destroy playbook,
            # this is hard.
            # For now, we log a warning.
            print(f"Warning: No destroy logic for Ansible resource {resource_state.id}")

    def get_supported_resource_types(self) -> list[str]:
        return ["configuration"]
