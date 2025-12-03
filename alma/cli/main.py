"""CLI interface for ALMA using Typer."""

import asyncio
from typing import Optional

import httpx
import typer
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from alma import __version__
from alma.core.config import get_settings

app = typer.Typer(
    name="alma",
    help="ALMA: The Soul of Your Infrastructure.",
    add_completion=False,
)
console = Console()
settings = get_settings()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"ALMA version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode with full stack traces",
    ),
) -> None:
    """ALMA: The Soul of Your Infrastructure."""
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        settings.debug = True
        console.print("[yellow]Debug mode enabled - full stack traces will be shown[/yellow]")


@app.command()
def serve(
    host: str = typer.Option(settings.api_host, "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(settings.api_port, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
) -> None:
    """
    Start the ALMA API server.
    """
    import uvicorn

    console.print(f"[green]Starting ALMA API server on {host}:{port}[/green]")
    uvicorn.run(
        "alma.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def deploy(
    blueprint_file: str = typer.Argument(..., help="Path to blueprint YAML file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate only, do not deploy"),
    engine: Optional[str] = typer.Option(None, "--engine", "-e", help="Engine to use"),
) -> None:
    """
    Deploy a system blueprint.
    """
    from alma.engines.fake import FakeEngine

    console.print(f"[blue]Loading blueprint from {blueprint_file}[/blue]")

    # Load blueprint
    try:
        with open(blueprint_file) as f:
            blueprint = yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: Blueprint file not found: {blueprint_file}[/red]")
        raise typer.Exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]Error parsing YAML: {e}[/red]")
        raise typer.Exit(1)

    # Get engine
    engine_instance = FakeEngine()

    # Deploy
    async def _deploy() -> None:
        try:
            # Validate
            await engine_instance.validate_blueprint(blueprint)
            console.print("[green]✓ Blueprint is valid[/green]")

            if dry_run:
                console.print("[yellow]Dry-run mode: skipping actual deployment[/yellow]")
                return

            # Deploy
            console.print("[blue]Deploying resources...[/blue]")
            result = await engine_instance.deploy(blueprint)

            if result.status.value == "completed":
                console.print(f"[green]✓ {result.message}[/green]")
                if result.resources_created:
                    console.print("\n[green]Resources created:[/green]")
                    for resource in result.resources_created:
                        console.print(f"  • {resource}")
            else:
                console.print(f"[red]✗ Deployment failed: {result.message}[/red]")
                raise typer.Exit(1)

        except ValueError as e:
            console.print(f"[red]✗ Validation error: {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]✗ Deployment error: {e}[/red]")
            raise typer.Exit(1)

    asyncio.run(_deploy())


@app.command()
def status() -> None:
    """
    Show infrastructure status.
    """
    console.print("[blue]Checking infrastructure status...[/blue]")

    table = Table(title="Infrastructure Status")
    table.add_column("Resource", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")

    # Placeholder - would query actual resources
    table.add_row("web-server-01", "compute", "running")
    table.add_row("db-server-01", "compute", "running")
    table.add_row("load-balancer", "network", "running")

    console.print(table)


@app.command()
def rollback(
    deployment_id: str = typer.Argument(..., help="Deployment ID to rollback"),
    target: Optional[str] = typer.Option(None, "--to", help="Target state to rollback to"),
) -> None:
    """
    Rollback a deployment.
    """
    console.print(f"[yellow]Rolling back deployment {deployment_id}[/yellow]")

    async def _rollback() -> None:
        from alma.engines.fake import FakeEngine

        engine = FakeEngine()
        try:
            success = await engine.rollback(deployment_id, target)
            if success:
                console.print("[green]✓ Rollback completed successfully[/green]")
            else:
                console.print("[red]✗ Rollback failed[/red]")
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]✗ Rollback error: {e}[/red]")
            raise typer.Exit(1)

    asyncio.run(_rollback())


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    path: Optional[str] = typer.Option(".", "--path", "-p", help="Path to create project"),
) -> None:
    """
    Initialize a new ALMA project.
    """
    import os

    project_path = os.path.join(path, name)
    console.print(f"[blue]Creating new ALMA project: {name}[/blue]")
    console.print(f"[blue]Location: {project_path}[/blue]")

    # Create directories
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, "blueprints"), exist_ok=True)

    # Create example blueprint
    example_blueprint = {
        "version": "1.0",
        "name": f"{name}-example",
        "description": "Example blueprint",
        "resources": [
            {
                "type": "compute",
                "name": "example-server",
                "provider": "fake",
                "specs": {"cpu": 2, "memory": "4GB", "storage": "50GB"},
            }
        ],
    }

    blueprint_file = os.path.join(project_path, "blueprints", "example.yaml")
    with open(blueprint_file, "w") as f:
        yaml.dump(example_blueprint, f, default_flow_style=False)

    console.print("[green]✓ Project created successfully[/green]")
    console.print(f"[green]  Example blueprint: {blueprint_file}[/green]")


@app.command("chat")
def chat(message: str):
    """
    Talk to the ALMA Cognitive Engine.
    """
    host = "127.0.0.1" if settings.api_host == "0.0.0.0" else settings.api_host
    api_url = f"http://{host}:{settings.api_port}{settings.api_prefix}"

    # Prepare authentication headers
    headers = {}
    if settings.api_key:
        headers["X-API-Key"] = settings.api_key

    # Show a spinner while thinking
    with console.status("[bold green]Thinking...", spinner="dots"):
        try:
            response = httpx.post(
                f"{api_url}/conversation/chat",
                json={"message": message},
                headers=headers,
                timeout=30.0,
            )

            # Handle authentication errors
            if response.status_code == 403:
                console.print(
                    "[bold red]🛑 Authentication Error:[/bold red] Invalid or missing API Key.\n"
                    "[yellow]Please check ALMA_API_KEY in your .env file.[/yellow]"
                )
                return

            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError as e:
            console.print(f"[bold red]Error connecting to ALMA API at {api_url}:[/bold red] {e}")
            console.print(
                "[yellow]Please ensure the API server is running (`alma serve`).[/yellow]"
            )
            return
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                console.print(
                    "[bold red]🛑 Authentication Error:[/bold red] Invalid or missing API Key.\n"
                    "[yellow]Please check ALMA_API_KEY in your .env file.[/yellow]"
                )
            else:
                console.print(f"[bold red]HTTP Error:[/bold red] {e}")
            return
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
            return

    # Check for Safety Block (Cognitive Engine)
    if isinstance(data, dict) and data.get("risk_assessment") == "BLOCKED":
        console.print(
            Panel(data.get("response", ""), title="🛑 SECURITY OVERRIDE", border_style="red bold")
        )
        return

    # Standard Response
    # If it returns a blueprint, show it in a box
    if isinstance(data, dict) and data.get("blueprint"):
        console.print(
            Panel(yaml.dump(data["blueprint"]), title="🏗️ Blueprint Generated", border_style="blue")
        )

    # Text response
    if isinstance(data, dict) and data.get("response"):
        console.print(Markdown(data.get("response", "")))
    elif isinstance(data, str):
        console.print(Markdown(data))


if __name__ == "__main__":
    app()
