"""Proxmox VE engine for managing virtual machines and containers."""

from typing import Any, Dict, List, Optional
import httpx

from ai_cdn.core.state import Plan, ResourceState
from ai_cdn.engines.base import Engine
from ai_cdn.schemas.blueprint import SystemBlueprint


class ProxmoxEngine(Engine):
    """
    Engine for Proxmox Virtual Environment.

    Manages VMs, containers, and storage through the Proxmox API.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
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
        self.ticket: Optional[str] = None
        self.csrf_token: Optional[str] = None

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
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # ... (internal logic remains the same)
        if not self.ticket:
            await self._authenticate()
        headers = {"CSRFPreventionToken": self.csrf_token}
        cookies = {"PVEAuthCookie": self.ticket}
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            url = f"{self.host}/api2/json/{endpoint}"
            response = await client.request(
                method=method, url=url, headers=headers, cookies=cookies, data=data
            )
            response.raise_for_status()
            return response.json().get("data", {})

    async def get_state(self, blueprint: SystemBlueprint) -> List[ResourceState]:
        """
        Get state of all Proxmox resources for a blueprint.
        
        TODO: Implement actual state retrieval. This would involve listing all VMs/CTs
        and filtering them based on a naming convention or tag derived from the blueprint.
        For each found resource, it should construct a ResourceState object.
        """
        # For now, returns an empty list, indicating no resources exist.
        return []

    async def apply(self, plan: Plan) -> None:
        """
        Deploy or update resources in Proxmox based on a plan.
        
        TODO: Implement the logic to create/update VMs and other resources.
        """
        if not await self._authenticate():
            raise ConnectionError("Failed to authenticate with Proxmox API")

        for resource_def in plan.to_create:
            # TODO: Add logic to create a VM/CT from resource_def
            print(f"Fake creating resource: {resource_def.name}")
        
        for _, resource_def in plan.to_update:
            # TODO: Add logic to update a VM/CT from resource_def
            print(f"Fake updating resource: {resource_def.name}")
        
        return

    async def destroy(self, plan: Plan) -> None:
        """
        Destroy Proxmox resources based on a plan.
        
        TODO: Implement actual VM/CT deletion.
        """
        if not await self._authenticate():
            raise ConnectionError("Failed to authenticate with Proxmox API")
            
        for resource_state in plan.to_delete:
            # TODO: Add logic to delete a VM/CT using resource_state.id
            print(f"Fake deleting resource: {resource_state.id}")

        return

    async def health_check(self) -> bool:
        """
        Check Proxmox API connectivity.
        """
        try:
            return await self._authenticate()
        except Exception:
            return False

    def get_supported_resource_types(self) -> List[str]:
        """
        Get supported resource types.
        """
        return ["compute", "storage"]