
"""CLI commands for managing templates."""

import typer
from rich.console import Console
from rich.table import Table

console = Console()
templates_app = typer.Typer(name="templates", help="Manage infrastructure templates")

# Hardcoded for now, ideal would be to fetch from API
KNOWN_TEMPLATES = [
    {"name": "alpine", "os": "Alpine Linux", "desc": "Lightweight base image", "provider": "proxmox"},
    {"name": "ubuntu", "os": "Ubuntu 22.04", "desc": "Standard server OS", "provider": "proxmox"},
    {"name": "debian", "os": "Debian 12", "desc": "Stable base", "provider": "proxmox"},
    {"name": "nginx", "os": "Alpine+Nginx", "desc": "Web server container", "provider": "docker"},
    {"name": "postgres", "os": "Alpine+Postgres", "desc": "Database container", "provider": "docker"},
]

@templates_app.command("list")
def list_templates():
    """List available infrastructure templates."""
    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("OS", style="green")
    table.add_column("Description")
    table.add_column("Provider", style="magenta")

    for tmpl in KNOWN_TEMPLATES:
        table.add_row(tmpl["name"], tmpl["os"], tmpl["desc"], tmpl["provider"])

    console.print(table)
