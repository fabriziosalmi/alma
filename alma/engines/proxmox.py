"""Proxmox VE engine implementation."""

from __future__ import annotations

from typing import Any

import httpx
from typing import cast

from alma.core.state import Plan, ResourceState
from alma.engines.base import Engine
from alma.schemas.blueprint import SystemBlueprint


class ProxmoxEngine(Engine):
    """
    Engine for Proxmox Virtual Environment.

    Manages VMs, containers, and storage through the Proxmox API.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize Proxmox engine.

        Args:
            config: Engine configuration
                - host: Proxmox host URL
                - username: API username (e.g., root@pam)
                - password: API password
                - verify_ssl: Whether to verify SSL certificates
                - node: Default Proxmox node name
        """
        super().__init__(config)
        self.host = self.config.get("host", "https://localhost:8006")
        self.username = self.config.get("username", "root@pam")
        self.password = self.config.get("password", "")
        self.verify_ssl = self.config.get("verify_ssl", True)
        self.node = self.config.get("node", "pve")
        self.ticket: str | None = None
        self.csrf_token: str | None = None

    async def _authenticate(self) -> bool:
        # ... (internal logic remains the same)
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            try:
                response = await client.post(
                    f"{self.host}/api2/json/access/ticket",
                    data={"username": self.username, "password": self.password},
                )
                response.raise_for_status()
                data = response.json()["data"]
                self.ticket = data["ticket"]
                self.csrf_token = data["CSRFPreventionToken"]
                return True
            except Exception as e:
                print(f"Authentication failed: {e}")
                return False

    async def _api_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> Any:
        # ... (internal logic remains the same)
        if not self.ticket:
            await self._authenticate()
        headers = {"CSRFPreventionToken": self.csrf_token}
        cookies = {"PVEAuthCookie": self.ticket}
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            url = f"{self.host}/api2/json/{endpoint}"
            response = await client.request(
                method=method,
                url=url,
                headers=cast(dict[str, str], headers),
                cookies=cast(dict[str, str], cookies),
                data=data,
            )
            response.raise_for_status()
            return response.json().get("data", {})

    async def _get_next_vmid(self) -> int:
        """Get next available VMID."""
        data = await self._api_request("GET", "cluster/nextid")
        return int(data)

    async def _get_vm_by_name(self, name: str) -> dict[str, Any] | None:
        """Find VM/CT by name."""
        # Check QEMU
        vms = await self._api_request("GET", f"nodes/{self.node}/qemu")
        for vm in vms:
            if vm.get("name") == name:
                vm["type"] = "qemu"
                return cast(dict[str, Any], vm)

        # Check LXC
        cts = await self._api_request("GET", f"nodes/{self.node}/lxc")
        for ct in cts:
            if ct.get("name") == name:
                ct["type"] = "lxc"
                return cast(dict[str, Any], ct)

        return None

    async def get_state(self, blueprint: SystemBlueprint) -> list[ResourceState]:
        """
        Get state of all Proxmox resources for a blueprint.
        """
        resources = []

        # Get all VMs and CTs
        try:
            vms = await self._api_request("GET", f"nodes/{self.node}/qemu")
            cts = await self._api_request("GET", f"nodes/{self.node}/lxc")
        except Exception as e:
            print(f"Failed to list resources: {e}")
            return []

        all_resources = vms + cts

        # Filter resources that match blueprint naming convention or just all?
        # For now, we return all resources that match names in the blueprint
        blueprint_names = {r.name for r in blueprint.resources}

        for res in all_resources:
            name = res.get("name")
            if name in blueprint_names:
                # Fetch detailed config
                vmid = res.get("vmid")
                res_type = "qemu" if res in vms else "lxc"

                try:
                    config = await self._api_request(
                        "GET", f"nodes/{self.node}/{res_type}/{vmid}/config"
                    )

                    resources.append(
                        ResourceState(
                            id=name, type="compute", config=config  # Generic type for now
                        )
                    )
                except Exception:
                    continue

        return resources

    async def apply(self, plan: Plan) -> None:
        """
        Deploy or update resources in Proxmox based on a plan.
        """
        if not await self._authenticate():
            raise ConnectionError("Failed to authenticate with Proxmox API")

        # Create new resources
        for resource_def in plan.to_create:
            print(f"Creating resource: {resource_def.name}")

            # We assume cloning from a template
            template_name = resource_def.specs.get("template")
            if not template_name:
                print(f"Skipping {resource_def.name}: No template specified")
                continue

            template = await self._get_vm_by_name(template_name)
            if not template:
                print(f"Skipping {resource_def.name}: Template '{template_name}' not found")
                continue

            new_vmid = await self._get_next_vmid()
            template_id = template.get("vmid")

            # Clone
            print(f"Cloning template {template_id} to VMID {new_vmid}...")
            await self._api_request(
                "POST",
                f"nodes/{self.node}/qemu/{template_id}/clone",
                data={"newid": new_vmid, "name": resource_def.name, "full": 1},
            )

            # Apply specs (CPU, Memory)
            # Wait for clone to finish? In async API, we might need to poll task.
            # For simplicity, we fire and forget config update (might fail if locked)
            # In production, we should wait for task completion.

            config_data = {}
            if "cpu" in resource_def.specs:
                config_data["cores"] = resource_def.specs["cpu"]
            if "memory" in resource_def.specs:
                # Convert GB to MB if needed, assuming specs are in MB or raw
                config_data["memory"] = resource_def.specs["memory"]

            if config_data:
                await self._api_request(
                    "POST", f"nodes/{self.node}/qemu/{new_vmid}/config", data=config_data
                )

            # Start VM
            await self._api_request("POST", f"nodes/{self.node}/qemu/{new_vmid}/status/start")

        # Update existing resources
        for current_state, resource_def in plan.to_update:
            print(f"Updating resource: {resource_def.name}")
            vm = await self._get_vm_by_name(resource_def.name)
            if not vm:
                continue

            vmid = vm.get("vmid")

            config_data = {}
            # Compare and update
            if "cpu" in resource_def.specs and str(resource_def.specs["cpu"]) != str(
                cast(dict[str, Any], current_state.config).get("cores")
            ):
                config_data["cores"] = resource_def.specs["cpu"]

            if config_data:
                await self._api_request(
                    "POST", f"nodes/{self.node}/qemu/{vmid}/config", data=config_data
                )

    async def destroy(self, plan: Plan) -> None:
        """
        Destroy Proxmox resources based on a plan.
        """
        if not await self._authenticate():
            raise ConnectionError("Failed to authenticate with Proxmox API")

        for resource_state in plan.to_delete:
            print(f"Destroying resource: {resource_state.id}")
            vm = await self._get_vm_by_name(resource_state.id)
            if not vm:
                print(f"Resource {resource_state.id} not found")
                continue

            vmid = vm.get("vmid")
            res_type = vm.get("type", "qemu")

            # Stop first
            try:
                await self._api_request("POST", f"nodes/{self.node}/{res_type}/{vmid}/status/stop")
            except Exception:
                pass  # Already stopped?

            # Delete
            await self._api_request("DELETE", f"nodes/{self.node}/{res_type}/{vmid}")

    async def health_check(self) -> bool:
        """
        Check Proxmox API connectivity.
        """
        try:
            return await self._authenticate()
        except Exception:
            return False

    def get_supported_resource_types(self) -> list[str]:
        """
        Get supported resource types.
        """
        return ["compute", "storage"]
