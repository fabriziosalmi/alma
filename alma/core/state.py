# alma/core/state.py

# """State management for infrastructure resources."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from alma.schemas.blueprint import ResourceDefinition as Resource

# Adapt to the existing schema by importing ResourceDefinition and aliasing it.
from alma.schemas.blueprint import SystemBlueprint

logger = logging.getLogger(__name__)


class ResourceState(BaseModel):
    """
    Represents the actual state of a single resource as reported by an engine.
    This is a standardized format that all engines must return from get_state().
    The 'id' of a ResourceState must correspond to the 'name' of a ResourceDefinition.
    """

    id: str = Field(
        ...,
        description="Unique identifier for the resource, matching the blueprint's resource name.",
    )
    type: str = Field(..., description="The type of the resource (e.g., 'compute', 'network').")
    config: dict[str, Any] = Field(
        ..., description="The current configuration of the resource from the engine."
    )


class Plan(BaseModel):
    """
    Represents the execution plan after comparing desired and current states.
    This object is the primary input for the user approval (IPR) step.
    """

    # Allow arbitrary types like the aliased Resource
    model_config = {"arbitrary_types_allowed": True}

    to_create: list[Resource] = Field(
        default_factory=list, description="List of resources to be created."
    )
    to_update: list[tuple[ResourceState, Resource]] = Field(
        default_factory=list,
        description="List of (current, desired) tuples for resources to be updated.",
    )
    to_delete: list[ResourceState] = Field(
        default_factory=list, description="List of resources to be deleted."
    )

    @property
    def is_empty(self) -> bool:
        """Returns True if the plan has no actions."""
        return not (self.to_create or self.to_update or self.to_delete)

    def generate_description(self) -> str:
        """Generates a human-readable summary of the plan for IPR."""
        if self.is_empty:
            return "No changes needed; the infrastructure is already up-to-date."

        parts = []
        if self.to_create:
            parts.append(f"{len(self.to_create)} to create")
        if self.to_update:
            parts.append(f"{len(self.to_update)} to modify")
        if self.to_delete:
            parts.append(f"{len(self.to_delete)} to destroy")

        summary = f"Plan: {', '.join(parts)}."

        details = []
        # Use .name for desired resources (ResourceDefinition) and .id for current/deleted (ResourceState)
        for r in self.to_create:
            details.append(f"  + Create {r.name} (type: {r.type})")
        for _, r in self.to_update:
            details.append(f"  ~ Modify {r.name} (type: {r.type})")
        for r in self.to_delete:
            details.append(f"  - Destroy {r.id} (type: {r.type})")

        return f"{summary}\n\nDetails:\n" + "\n".join(details)

    def to_rich_string(self) -> str:
        """Generates a rich-formatted string representation of the plan for CLI output."""
        if self.is_empty:
            return "[bold green]✓ No changes. Your infrastructure is up-to-date.[/bold green]"

        lines = ["[bold]Execution Plan:[/bold]"]

        if self.to_create:
            lines.append("\n[bold green]Resources to CREATE:[/]")
            for resource in self.to_create:
                lines.append(f"  [green][+][/] [bold]{resource.name}[/] ({resource.type})")
                for key, value in resource.specs.items():
                    lines.append(f"      {key}: [cyan]{value}[/]")

        if self.to_update:
            lines.append("\n[bold yellow]Resources to MODIFY:[/]")
            for current, desired in self.to_update:
                lines.append(f"  [yellow][~][/] [bold]{desired.name}[/] ({desired.type})")
                lines.append(f"      [red]- config[/]: {current.config}")
                lines.append(f"      [green]+ config[/]: {desired.specs}")

        if self.to_delete:
            lines.append("\n[bold red]Resources to DESTROY:[/]")
            for resource in self.to_delete:
                lines.append(f"  [red][-][/] [bold]{resource.id}[/] ({resource.type})")
                lines.append("      (Resource will be permanently deleted)")

        summary = f"Plan: {len(self.to_create)} to create, {len(self.to_update)} to change, {len(self.to_delete)} to destroy."
        lines.append(f"\n[bold]Summary:[/bold] {summary}")

        return "\n".join(lines)


def diff_states(desired_blueprint: SystemBlueprint, current_states: list[ResourceState]) -> Plan:
    """
    Compares the desired state (blueprint) with the current state (from an engine)
    and produces a plan of actions.
    """
    logger.info("Starting state diff to calculate execution plan...")

    # Map desired resources by their 'name'
    desired_resources: dict[str, Resource] = {res.name: res for res in desired_blueprint.resources}
    # Map current resources by their 'id'
    current_resources: dict[str, ResourceState] = {res.id: res for res in current_states}

    desired_ids = set(desired_resources.keys())
    current_ids = set(current_resources.keys())

    to_create_ids = desired_ids - current_ids
    to_delete_ids = current_ids - desired_ids
    to_check_ids = desired_ids.intersection(current_ids)

    plan = Plan()

    for res_id in sorted(to_create_ids):
        plan.to_create.append(desired_resources[res_id])
    logger.info(f"Found {len(plan.to_create)} resources to create.")

    for res_id in sorted(to_delete_ids):
        plan.to_delete.append(current_resources[res_id])
    logger.info(f"Found {len(plan.to_delete)} resources to delete.")

    updates_found = 0
    for res_id in sorted(to_check_ids):
        desired_res = desired_resources[res_id]
        current_res = current_resources[res_id]

        # The engine's reported 'config' should match the blueprint's 'specs'.
        if desired_res.specs != current_res.config:
            plan.to_update.append((current_res, desired_res))
            updates_found += 1

    logger.info(f"Found {updates_found} resources to potentially update.")
    logger.info("State diff complete. Plan generated.")

    return plan
