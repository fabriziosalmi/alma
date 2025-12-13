"""
A real-time monitoring dashboard for the ALMA system, built with Rich.
Includes a self-healing/setup wizard for initial configuration.
"""

import asyncio
import time
from collections import deque
from typing import Any

import httpx
import typer
from dotenv import find_dotenv, set_key
from pyfiglet import Figlet
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.prompt import Confirm, Prompt
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from alma.core.config import get_settings

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
REFRESH_RATE_SECONDS = 1.5
MAX_CONSECUTIVE_ERRORS = 3
APP_VERSION = "0.1.0"
settings = get_settings()

# --- Main Application Class ---


class DashboardApp:
    """A real-time monitoring dashboard and recovery wizard application."""

    def __init__(self, mock: bool = False):
        self.mock = mock
        self.console = Console()
        self.layout = self.generate_layout()

        # State
        self.api_status: str = "connecting"
        self.consecutive_errors: int = 0
        self.metrics: dict[str, Any] = {}
        self.iprs: list[dict[str, Any]] = []
        self.logs: deque[str] = deque(maxlen=10)

        # HTTP client for real mode
        if not self.mock:
            headers = {}
            if settings.api_key:
                headers["X-API-Key"] = settings.api_key
            self.http_client = httpx.AsyncClient(
                base_url=API_BASE_URL, timeout=5.0, headers=headers
            )

    def generate_layout(self) -> Layout:
        """Defines the visual layout of the dashboard."""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=5),
            Layout(ratio=1, name="main"),
            Layout(size=7, name="footer"),
        )
        layout["main"].split_row(
            Layout(name="brain"),
            Layout(name="action", ratio=2),
        )
        layout["brain"].split(Layout(name="llm_status"), Layout(name="system_health"))
        return layout

    async def update_data(self) -> None:
        """Fetches new data from the API or generates mock data."""
        if self.mock:
            self._generate_mock_data()
            return

        try:
            metrics_resp, iprs_resp, infra_resp = await asyncio.gather(
                self.http_client.get("/monitoring/metrics/summary"),
                self.http_client.get("/iprs/"),
                self.http_client.get("/monitoring/stats/infrastructure"),
                return_exceptions=True,
            )

            if isinstance(metrics_resp, Exception):
                raise metrics_resp
            if isinstance(iprs_resp, Exception):
                raise iprs_resp
            # infra_resp might fail if Proxmox down, handle gracefully
            
            assert isinstance(metrics_resp, httpx.Response)
            assert isinstance(iprs_resp, httpx.Response)

            metrics_resp.raise_for_status()
            iprs_resp.raise_for_status()

            self.metrics = metrics_resp.json()
            self.iprs = iprs_resp.json()
            
            if isinstance(infra_resp, httpx.Response) and infra_resp.status_code == 200:
                self.infra = infra_resp.json()
            else:
                self.infra = {"nodes": []}

            self.api_status = "connected"
            self.consecutive_errors = 0  # Reset on success
            self.logs.append(f"[dim]{time.strftime('%H:%M:%S')}[/] [green]✨ Data refreshed[/]")

        except (httpx.ConnectError, httpx.TimeoutException):
            self.api_status = "Disconnected"
            self.consecutive_errors += 1
            self.logs.append(
                f"[dim]{time.strftime('%H:%M:%S')}[/] [bold red]API connection failed ({self.consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})[/]"
            )
        except httpx.HTTPStatusError as e:
            self.api_status = "Disconnected"
            self.consecutive_errors += 1
            if e.response.status_code == 403:
                self.logs.append(
                    f"[dim]{time.strftime('%H:%M:%S')}[/] [bold red]🛑 Authentication Error: Invalid API Key ({self.consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})[/]"
                )
            else:
                self.logs.append(
                    f"[dim]{time.strftime('%H:%M:%S')}[/] [red]API Error: {e.response.status_code} ({self.consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})[/]"
                )
        except Exception:
            self.api_status = "Disconnected"
            self.consecutive_errors += 1
            # self.logs.append(
            #    f"[dim]{time.strftime('%H:%M:%S')}[/] [red]An unexpected error occurred[/]"
            # )

    def _generate_mock_data(self) -> None:
        # (Mock data generation remains the same as previous version)
        self.api_status = "connected"
        self.metrics = {"llm": {"last_intent": "mock_intent"}, "system": {}}
        self.iprs = []
        self.infra = {"nodes": [
            {"data": {"label": "mock-vm-1", "subLabel": "qemu • running", "icon": "Server", "colorClass": "bg-green-500/20"}},
            {"data": {"label": "mock-db", "subLabel": "lxc • stopped", "icon": "Database", "colorClass": "bg-red-500/20"}}
        ]}
        self.logs.append(f"[dim]{time.strftime('%H:%M:%S')}[/] [cyan]Mock data generated[/]")

    def generate_layout(self) -> Layout:
        """Defines the visual layout of the dashboard."""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=5),
            Layout(ratio=1, name="main"),
            Layout(size=7, name="footer"),
        )
        layout["main"].split_row(
            Layout(name="left_col", ratio=1),
            Layout(name="right_col", ratio=2),
        )
        layout["left_col"].split(
            Layout(name="llm_status", size=10),
            Layout(name="system_health")
        )
        layout["right_col"].split(
            Layout(name="action", ratio=1),
            Layout(name="resources", ratio=2)
        )
        return layout

    def _render_resources_panel(self) -> Panel:
        """Renders the Infrastructure Resources panel."""
        table = Table(box=None, expand=True, show_header=False)
        table.add_column("Icon", width=3)
        table.add_column("Name", style="bold white")
        table.add_column("Type/Status", style="dim")
        
        nodes = self.infra.get("nodes", [])
        # Filter out internet node
        nodes = [n for n in nodes if n.get("id") != "internet"]
        
        if nodes:
            for node in nodes:
                data = node.get("data", {})
                label = data.get("label", "Unknown")
                sub = data.get("subLabel", "")
                icon = "📦" if data.get("icon") == "Database" else "🖥️"
                
                status_color = "green" if "running" in sub else "red"
                
                table.add_row(
                    icon, 
                    label, 
                    f"[{status_color}]{sub}[/]"
                )
        else:
             table.add_row("❓", "No resources found", "[dim]Check provider connection[/]")
             
        return Panel(table, title="[bold]🏗️ Infrastructure[/]", border_style="blue")
    
    # ... existing render methods ...

    def render(self) -> Layout:
        """Renders the entire dashboard layout with fresh data."""
        self.layout["header"].update(self._render_header())
        self.layout["llm_status"].update(self._render_llm_panel())
        self.layout["system_health"].update(self._render_health_panel())
        self.layout["action"].update(self._render_ipr_panel())
        self.layout["resources"].update(self._render_resources_panel())
        self.layout["footer"].update(self._render_footer())
        return self.layout

    # ... run methods ...


    async def run(self) -> None:
        """Run the dashboard's main async loop."""
        with Live(self.render(), screen=True, redirect_stderr=False, transient=True) as live:
            while self.consecutive_errors < MAX_CONSECUTIVE_ERRORS:
                await self.update_data()
                live.update(self.render())
                await asyncio.sleep(REFRESH_RATE_SECONDS)

        # If the loop breaks due to errors, run the recovery wizard
        self.run_recovery_wizard()

    def run_recovery_wizard(self) -> None:
        """A guided setup process for when the API is unreachable."""
        self.console.clear()
        self.console.print(
            Panel(
                Text(
                    "🧠 ALMA Core is unreachable. Let's set this up.",
                    justify="center",
                    style="bold yellow",
                ),
                title="[bold cyan]Setup Wizard[/]",
                border_style="cyan",
            )
        )

        # --- Step 1: Server URL (for future use, we assume localhost for now) ---
        # server_url = Prompt.ask("[bold]Step 1: Enter the API Server URL[/]", default="http://localhost:8000")

        # --- Step 2: AI Brain Configuration ---
        self.console.print("\n[bold]Step 1: Configure the AI Brain (LLM Provider)[/]")
        self.console.print("This should be an OpenAI-compatible API endpoint.")

        menu = Table(show_header=False, box=None)
        menu.add_column()
        menu.add_column()
        menu.add_row("1", "Ollama (Local)")
        menu.add_row("2", "LMStudio (Local)")
        menu.add_row("3", "OpenAI (Cloud)")
        menu.add_row("4", "Custom (Gemini, DeepSeek, etc.)")
        self.console.print(menu)

        provider_map = {
            "1": "http://localhost:11434/v1",
            "2": "http://localhost:1234/v1",
            "3": "https://api.openai.com/v1",
        }

        choice = Prompt.ask("Choose a provider", choices=["1", "2", "3", "4"], default="1")

        base_url = provider_map.get(choice)
        if choice == "4":
            base_url = Prompt.ask("[bold]Enter the custom OpenAI-compatible Base URL[/]")

        # --- Step 3: LLM API Key ---
        self.console.print("\n[bold]Step 2: Enter the LLM API Key[/]")
        llm_api_key = Prompt.ask(
            "LLM API Key", default="sk-dummy", password=(choice != "1" and choice != "2")
        )

        # --- Step 4: ALMA API Key ---
        self.console.print("\n[bold]Step 3: ALMA API Key Configuration[/]")
        self.console.print("This key is used to authenticate requests to ALMA API endpoints.")

        import secrets

        default_alma_key = secrets.token_urlsafe(32)

        alma_api_key = Prompt.ask(
            "🔑 Enter ALMA API Key (or press Enter to generate new random key)",
            default=default_alma_key,
        )

        # --- Step 5: Save to .env ---
        if Confirm.ask("\nSave these settings to the `.env` file?", default=True):
            dotenv_path = find_dotenv()
            if not dotenv_path:
                # Create .env if it doesn't exist
                with open(".env", "w"):
                    pass
                dotenv_path = find_dotenv()

            set_key(str(dotenv_path), "OPENAI_BASE_URL", str(base_url))
            set_key(dotenv_path, "OPENAI_API_KEY", llm_api_key)
            set_key(dotenv_path, "ALMA_API_KEY", alma_api_key)
            set_key(dotenv_path, "ALMA_AUTH_ENABLED", "true")

            self.console.print("\n[bold green]✅ Configuration saved to .env file![/]")
            self.console.print(f"[dim]ALMA API Key: {alma_api_key[:8]}...{alma_api_key[-8:]}[/]")
            self.console.print(
                "Please restart the server (`python run_server.py`) to apply changes."
            )
        else:
            self.console.print("\n[yellow]Aborted. No changes were saved.[/]")


# --- CLI Command ---

app = typer.Typer()


@app.command(name="dashboard")
def dashboard_command(
    mock: bool = typer.Option(False, "--mock", help="Run dashboard with mock data.")
) -> None:
    """Launch the ALMA real-time monitoring dashboard."""
    dashboard = DashboardApp(mock=mock)
    try:
        asyncio.run(dashboard.run())
    except KeyboardInterrupt:
        print("\nDashboard closed. Goodbye!")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    app()
