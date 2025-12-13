"""Proxmox VE engine implementation."""

from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Any, cast

import httpx

from alma.core.state import Plan, ResourceState, diff_states
from alma.engines.base import Engine
from alma.schemas.blueprint import SystemBlueprint

from alma.core.resilience import CircuitBreaker, CircuitBreakerOpenException

logger = logging.getLogger(__name__)


class ProxmoxEngine(Engine):
    """
    Engine for Proxmox Virtual Environment.

    Manages VMs, containers, and storage through the Proxmox API.
    Supports SSH execution via standard 'ssh' (assumes key-based auth).
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize Proxmox engine.

        Args:
            config: Engine configuration
                - host: Proxmox host URL (or IP)
                - username: API username (e.g., root@pam)
                - password: API password (for token generation only)
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
        self.use_ssh: bool = False
        
        # Resilience: Circuit Breaker for API calls
        self.circuit_breaker = CircuitBreaker(
            name="ProxmoxAPI",
            failure_threshold=5,
            recovery_timeout=30
        )

    async def _authenticate(self) -> bool:
        """Authenticate with Proxmox API."""
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=10.0) as client:
                response = await client.post(
                    f"{self.host}/api2/json/access/ticket",
                    data={"username": self.username, "password": self.password},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                self.ticket = data.get("ticket")
                self.csrf_token = data.get("CSRFPreventionToken")
                
                if not self.ticket or not self.csrf_token:
                    logger.error("Authentication failed: Missing ticket or CSRF token.")
                    return False
                
                self.use_ssh = False
                logger.info("Successfully authenticated with Proxmox API.")
                return True
        except Exception as e:
            logger.error(f"API Authentication failed: {e}")
            # We no longer fallback to insecure SSH automatically.
            return False

    def _extract_ip(self, url: str) -> str:
        """Extract IP from URL."""
        if "://" in url:
            return url.split("://")[1].split(":")[0]
        return url

    async def _run_ssh_command(self, command: list[str]) -> str:
        """
        Run a command on the Proxmox host via SSH using key-based auth.
        
        Args:
            command: List of command parts to execute on the remote host.
        """
        host_ip = self._extract_ip(self.host)
        user = self.username.split("@")[0]
        
        # Construct SSH command without password
        ssh_cmd = [
            "ssh",
            "-o", "BatchMode=yes",  # Fail if password is required
            "-o", "ConnectTimeout=10",
            f"{user}@{host_ip}",
        ] + command
        
        try:
            # Run in a thread to verify blocking I/O doesn't freeze the loop
            process = await asyncio.create_subprocess_exec(
                *ssh_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"SSH Command failed: {error_msg}")
                raise Exception(f"SSH Command failed: {error_msg}")
                
            return stdout.decode().strip()
        except Exception as e:
            logger.error(f"SSH execution error: {e}")
            raise

    async def _api_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> Any:
        """Make an authenticated API request."""
        if self.use_ssh:
             raise NotImplementedError("Cannot use _api_request in SSH mode")
            
        if not self.ticket:
            if not await self._authenticate():
                 raise ConnectionError("Authentication failed")

        headers = {"CSRFPreventionToken": self.csrf_token}
        cookies = {"PVEAuthCookie": self.ticket}
        
        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=30.0) as client:
            url = f"{self.host}/api2/json/{endpoint}"
            
            async def _do_request():
                response = await client.request(
                    method=method,
                    url=url,
                    headers=cast(dict[str, str], headers),
                    cookies=cast(dict[str, str], cookies),
                    data=data,
                )
                response.raise_for_status()
                return response.json().get("data", {})

            try:
                # Wrap request with Circuit Breaker
                return await self.circuit_breaker.call(_do_request)
            except CircuitBreakerOpenException:
                logger.error("Proxmox API Circuit Breaker is OPEN. Failing fast.")
                raise ConnectionError("Proxmox API is temporarily unavailable (Circuit Broken).")
            except httpx.HTTPStatusError as e:
                logger.error(f"API Request failed: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"API Connection error: {e}")
                raise

    async def _wait_for_task(self, upid: str, timeout: int = 300) -> bool:
        """
        Wait for a Proxmox task (UPID) to complete.
        
        Args:
            upid: Task ID
            timeout: Maximum wait time in seconds
        """
        logger.info(f"Waiting for task {upid}...")
        start_time = asyncio.get_running_loop().time()
        
        try:
            task_node = upid.split(":")[1]
        except IndexError:
            task_node = self.node

        while (asyncio.get_running_loop().time() - start_time) < timeout:
            try:
                status = await self._api_request("GET", f"nodes/{task_node}/tasks/{upid}/status")
                if status.get("status") == "stopped":
                    exit_status = status.get("exitstatus")
                    if exit_status == "OK":
                        logger.info(f"Task {upid} completed successfully.")
                        return True
                    else:
                        logger.error(f"Task {upid} failed with exit status: {exit_status}")
                        return False
            except Exception as e:
                logger.warning(f"Transient error checking task status: {e}")
            
            await asyncio.sleep(2)  # Simple backoff buffer
            
        logger.error(f"Timeout waiting for task {upid}")
        return False

    async def _get_next_vmid(self) -> int:
        """Get next available VMID."""
        if self.use_ssh:
            # We need to construct the command list for SSH
            out = await self._run_ssh_command(["pvesh", "get", "/cluster/nextid", "--output-format", "json"])
            return int(out)
        
        data = await self._api_request("GET", "cluster/nextid")
        return int(data)

    async def _get_vm_by_name(self, name: str) -> dict[str, Any] | None:
        """Find VM/CT by name."""
        # API Implementation
        try:
            vms = await self._api_request("GET", f"nodes/{self.node}/qemu")
            for vm in vms:
                if vm.get("name") == name:
                    vm["type"] = "qemu"
                    return cast(dict[str, Any], vm)

            cts = await self._api_request("GET", f"nodes/{self.node}/lxc")
            for ct in cts:
                if ct.get("name") == name:
                    ct["type"] = "lxc"
                    return cast(dict[str, Any], ct)
        except Exception as e:
            logger.error(f"Error fetching VM list: {e}")
            
        return None

    async def list_resources(self) -> list[dict[str, Any]]:
        """List all resources (VMs and CTs)."""
        resources = []
        try:
            vms = await self._api_request("GET", f"nodes/{self.node}/qemu")
            for vm in vms:
                vm["type"] = "qemu"
                resources.append(vm)
        except Exception as e:
            logger.warning(f"Failed to fetch QEMU via API: {e}")

        try:
            cts = await self._api_request("GET", f"nodes/{self.node}/lxc")
            for ct in cts:
                ct["type"] = "lxc"
                resources.append(ct)
        except Exception as e:
            logger.warning(f"Failed to fetch LXC via API: {e}") 
            
        return resources

    async def get_state(self, blueprint: SystemBlueprint) -> list[ResourceState]:
        """Get the current state of resources defined in the blueprint."""
        try:
            vms = await self._api_request("GET", f"nodes/{self.node}/qemu")
        except Exception:
            vms = []
            
        try:
            cts = await self._api_request("GET", f"nodes/{self.node}/lxc")
        except Exception:
            cts = []
            
        all_resources = (vms or []) + (cts or [])
        blueprint_names = {r.name for r in blueprint.resources}
        resources = []
        
        for res in all_resources:
            name = res.get("name")
            if name in blueprint_names:
                # Normalize Data to match ResourceDefinition specs
                # Proxmox returns 'maxmem' in bytes -> Convert to MB
                memory_mb = res.get("maxmem", 0) // 1024 // 1024
                # Proxmox returns 'maxcpu' or 'cpus' -> CPU cores
                cpu_cores = res.get("maxcpu") or res.get("cpus", 1)
                
                normalized_config = {
                    "memory": memory_mb,
                    "cpu": cpu_cores,
                    # Add other specs as needed, e.g. status
                    "status": res.get("status")
                }
                
                resources.append(ResourceState(id=name, type="compute", config=normalized_config))
        return resources

    async def reconcile(self, blueprint: SystemBlueprint) -> None:
        """
        Reconcile current state with the desired blueprint.
        Detects drift and automatically applies necessary changes.
        """
        logger.info("Starting reconciliation...")
        
        # 1. Get Actual State
        current_state = await self.get_state(blueprint)
        
        # 2. Diff against Blueprint
        plan = diff_states(blueprint, current_state)
        
        if plan.is_empty:
             logger.info("Infrastructure is already consistent. No action needed.")
             return

        # 3. Apply Plan (Self-Healing)
        logger.warning(f"Drift detected! Applying corrections:\n{plan.generate_description()}")
        await self.apply(plan)
        logger.info("Reconciliation complete.")

    async def apply(self, plan: Plan) -> None:
        """Apply plan to Proxmox infrastructure."""
        if not await self._authenticate():
            raise ConnectionError("Failed to authenticate with Proxmox API")

        # Handle Creation
        for resource_def in plan.to_create:
            logger.info(f"Creating resource: {resource_def.name}")
            template_name = resource_def.specs.get("template")
            if not template_name:
                logger.warning(f"No template specified for {resource_def.name}, skipping.")
                continue

            # Check if template is a VM (Clone) or LXC (Create)
            template = await self._get_vm_by_name(template_name)
            new_vmid = await self._get_next_vmid()
            template_id = template.get("vmid") if template else None

            if not template_id and template_name:
                # LXC Create
                logger.info(f"Creating LXC {new_vmid} from {template_name}")
                storage = "local-lvm" 
                ostemplate = f"local:vztmpl/{template_name}-3.18-x86_64.tar.zst"
                if template_name == "alpine":
                     ostemplate = "local:vztmpl/alpine-3.22-default_20250617_amd64.tar.xz"
                
                data = {
                    "vmid": new_vmid,
                    "ostemplate": ostemplate,
                    "hostname": resource_def.name,
                    "storage": storage,
                    "memory": resource_def.specs.get("memory", 512),
                    "cores": resource_def.specs.get("cpu", 1),
                    "net0": "name=eth0,bridge=vmbr0,ip=dhcp",
                    "unprivileged": 1
                }
                upid = await self._api_request("POST", f"nodes/{self.node}/lxc", data=data)
                
                if isinstance(upid, str) and upid.startswith("UPID:"):
                    await self._wait_for_task(upid)
                
                await self._api_request("POST", f"nodes/{self.node}/lxc/{new_vmid}/status/start")
                continue

            if template_id:
                # VM Clone
                logger.info(f"Cloning VM {template_id} -> {new_vmid}")
                await self._api_request("POST", f"nodes/{self.node}/qemu/{template_id}/clone", 
                                     data={"newid": new_vmid, "name": resource_def.name, "full": 1})
                
                # Apply Specs config to cloned VM
                update_data = {}
                if "cpu" in resource_def.specs:
                    update_data["cores"] = resource_def.specs["cpu"]
                if "memory" in resource_def.specs:
                    update_data["memory"] = resource_def.specs["memory"]
                
                if update_data:
                    await self._api_request("POST", f"nodes/{self.node}/qemu/{new_vmid}/config", data=update_data)

                # Start
                await self._api_request("POST", f"nodes/{self.node}/qemu/{new_vmid}/status/start")

        # Handle Updates
        for old, new_def in plan.to_update:
            logger.info(f"Updating resource: {old.id}")
            vm = await self._get_vm_by_name(old.id)
            if not vm:
                logger.warning(f"Resource {old.id} not found for update.")
                continue
            
            vmid = vm.get("vmid")
            res_type = vm.get("type", "qemu")
            
            update_data = {}
            if "cpu" in new_def.specs and new_def.specs["cpu"] != old.config.get("cores"):
                update_data["cores"] = new_def.specs["cpu"]
            
            if "memory" in new_def.specs: # Simplify comparison, just apply
                 update_data["memory"] = new_def.specs["memory"]

            if update_data:
                await self._api_request("POST", f"nodes/{self.node}/{res_type}/{vmid}/config", data=update_data)


    async def destroy(self, plan: Plan) -> None:
        """Destroy resources in the plan."""
        if not await self._authenticate():
            raise ConnectionError("Failed to authenticate")

        for resource_state in plan.to_delete:
            vm = await self._get_vm_by_name(resource_state.id)
            if not vm:
                continue
            vmid = vm.get("vmid")
            
            logger.info(f"Destroying {resource_state.id} ({vmid})")
            
            res_type = vm.get("type", "qemu")
            try:
                await self._api_request("POST", f"nodes/{self.node}/{res_type}/{vmid}/status/stop")
                await asyncio.sleep(2) 
            except Exception as e:
                logger.warning(f"Failed to stop {vmid}: {e}")
                
            try:
                await self._api_request("DELETE", f"nodes/{self.node}/{res_type}/{vmid}")
            except Exception as e:
                 logger.error(f"Failed to destroy {vmid}: {e}")

    async def health_check(self) -> bool:
        try:
            return await self._authenticate()
        except Exception:
            return False

    def get_supported_resource_types(self) -> list[str]:
        return ["compute", "storage"]

    async def download_template(self, storage: str, template: str) -> bool:
        """
        Download a template to specific storage.
        Warning: This uses API 'download-url' if available or tries SSH.
        """
        logger.info(f"Downloading template {template} to {storage}...")
        
        # API Implementation for known templates
        url = None
        filename = None
        if "alpine" in template:
            # TODO: Move this to a configuration or external source
            url = "http://download.proxmox.com/images/system/alpine-3.22-default_20250617_amd64.tar.xz"
            filename = "alpine-3.22-default_20250617_amd64.tar.xz"
        
        if url:
            try:
                upid = await self._api_request("POST", f"nodes/{self.node}/storage/{storage}/download-url", data={
                    "content": "vztmpl",
                    "filename": filename,
                    "url": url
                })
            
                if isinstance(upid, str) and upid.startswith("UPID:"):
                    success = await self._wait_for_task(upid)
                    if not success:
                          logger.error("Templates download task reported failure.")
                          return False
                    return True
            except Exception as e:
                logger.error(f"API Download failed: {e}")
                return False
        
        logger.warning(f"No API URL known for template {template}, and SSH fallback for pveam is restricted.")
        return False
