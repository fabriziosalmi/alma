"""Proxmox VE engine for managing virtual machines and containers."""

import asyncio
from typing import Any, Dict, List, Optional
import httpx

from ai_cdn.engines.base import (
    Engine,
    DeploymentResult,
    DeploymentStatus,
    ResourceState,
    ResourceStatus,
)


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
        """
        Authenticate with Proxmox API.

        Returns:
            True if authentication successful
        """
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            try:
                response = await client.post(
                    f"{self.host}/api2/json/access/ticket",
                    data={
                        "username": self.username,
                        "password": self.password,
                    },
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
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated API request to Proxmox.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request data

        Returns:
            API response data
        """
        if not self.ticket:
            await self._authenticate()

        headers = {
            "CSRFPreventionToken": self.csrf_token,
        }
        cookies = {
            "PVEAuthCookie": self.ticket,
        }

        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            url = f"{self.host}/api2/json/{endpoint}"
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                cookies=cookies,
                data=data,
            )
            response.raise_for_status()
            return response.json().get("data", {})

    async def validate_blueprint(self, blueprint: Dict[str, Any]) -> bool:
        """
        Validate blueprint for Proxmox deployment.

        Args:
            blueprint: System blueprint to validate

        Returns:
            True if valid

        Raises:
            ValueError: If blueprint is invalid
        """
        # Basic validation
        if "version" not in blueprint:
            raise ValueError("Blueprint missing 'version' field")
        if "name" not in blueprint:
            raise ValueError("Blueprint missing 'name' field")
        if "resources" not in blueprint:
            raise ValueError("Blueprint missing 'resources' field")

        # Validate resource types
        supported_types = {"compute", "storage"}
        for resource in blueprint.get("resources", []):
            if resource.get("type") not in supported_types:
                raise ValueError(
                    f"Unsupported resource type: {resource.get('type')}. "
                    f"Proxmox engine supports: {supported_types}"
                )

            # Validate compute resources have required specs
            if resource.get("type") == "compute":
                specs = resource.get("specs", {})
                if "cpu" not in specs:
                    raise ValueError(f"Compute resource '{resource.get('name')}' missing CPU spec")
                if "memory" not in specs:
                    raise ValueError(
                        f"Compute resource '{resource.get('name')}' missing memory spec"
                    )

        return True

    async def deploy(self, blueprint: Dict[str, Any]) -> DeploymentResult:
        """
        Deploy resources to Proxmox.

        Args:
            blueprint: System blueprint to deploy

        Returns:
            DeploymentResult with deployment status
        """
        await self.validate_blueprint(blueprint)

        # Authenticate
        if not await self._authenticate():
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                message="Failed to authenticate with Proxmox API",
                resources_failed=[r.get("name", "unknown") for r in blueprint["resources"]],
            )

        resources_created = []
        resources_failed = []
        deployment_id = f"proxmox-{blueprint['name']}"

        for resource in blueprint.get("resources", []):
            resource_name = resource.get("name", "unnamed")
            resource_type = resource.get("type")

            try:
                if resource_type == "compute":
                    await self._deploy_vm(resource)
                    resources_created.append(resource_name)
                elif resource_type == "storage":
                    # TODO: Implement storage deployment
                    resources_failed.append(resource_name)
                else:
                    resources_failed.append(resource_name)
            except Exception as e:
                print(f"Failed to deploy resource {resource_name}: {e}")
                resources_failed.append(resource_name)

        status = (
            DeploymentStatus.COMPLETED
            if len(resources_failed) == 0
            else DeploymentStatus.FAILED
        )

        return DeploymentResult(
            status=status,
            message=f"Deployed {len(resources_created)} resources, {len(resources_failed)} failed",
            resources_created=resources_created,
            resources_failed=resources_failed,
            metadata={"deployment_id": deployment_id},
        )

    async def _deploy_vm(self, resource: Dict[str, Any]) -> str:
        """
        Deploy a VM to Proxmox.

        Args:
            resource: Resource definition

        Returns:
            VM ID
        """
        specs = resource.get("specs", {})

        # Extract VM configuration
        vm_config = {
            "vmid": self._get_next_vmid(),  # TODO: Implement
            "name": resource.get("name"),
            "cores": specs.get("cpu", 1),
            "memory": self._parse_memory(specs.get("memory", "512MB")),
            "ostype": "l26",  # Linux 2.6+
        }

        # TODO: Make actual API call to create VM
        # await self._api_request("POST", f"nodes/{self.node}/qemu", data=vm_config)

        return str(vm_config["vmid"])

    def _parse_memory(self, memory_str: str) -> int:
        """
        Parse memory string to MB.

        Args:
            memory_str: Memory string (e.g., "4GB", "512MB")

        Returns:
            Memory in MB
        """
        memory_str = memory_str.upper().strip()
        if memory_str.endswith("GB"):
            return int(float(memory_str[:-2]) * 1024)
        elif memory_str.endswith("MB"):
            return int(memory_str[:-2])
        else:
            return int(memory_str)  # Assume MB

    def _get_next_vmid(self) -> int:
        """
        Get next available VM ID.

        Returns:
            Next VMID
        """
        # TODO: Query Proxmox for next available ID
        return 100

    async def get_state(self, resource_id: str) -> ResourceState:
        """
        Get state of a Proxmox resource.

        Args:
            resource_id: Resource ID (VMID)

        Returns:
            Resource state
        """
        # TODO: Implement actual state retrieval
        return ResourceState(
            resource_id=resource_id,
            resource_type="compute",
            status=ResourceStatus.RUNNING,
            properties={},
            metadata={},
        )

    async def destroy(self, resource_id: str) -> bool:
        """
        Destroy a Proxmox resource.

        Args:
            resource_id: Resource ID (VMID)

        Returns:
            True if successful
        """
        # TODO: Implement actual VM deletion
        # await self._api_request("DELETE", f"nodes/{self.node}/qemu/{resource_id}")
        return True

    async def rollback(self, deployment_id: str, target_state: Optional[str] = None) -> bool:
        """
        Rollback Proxmox deployment.

        Args:
            deployment_id: Deployment ID
            target_state: Target state to rollback to

        Returns:
            True if successful
        """
        # TODO: Implement rollback logic
        return True

    async def health_check(self) -> bool:
        """
        Check Proxmox API connectivity.

        Returns:
            True if healthy
        """
        try:
            return await self._authenticate()
        except Exception:
            return False

    def get_supported_resource_types(self) -> List[str]:
        """
        Get supported resource types.

        Returns:
            List of supported types
        """
        return ["compute", "storage"]
