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

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
REFRESH_RATE_SECONDS = 1.5
MAX_CONSECUTIVE_ERRORS = 3
APP_VERSION = "0.1.0"

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
            self.http_client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=5.0)

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
            metrics_resp, iprs_resp = await asyncio.gather(
                self.http_client.get("/monitoring/metrics/summary"),
                self.http_client.get("/iprs/"),
                return_exceptions=True,
            )

            if isinstance(metrics_resp, httpx.ConnectError) or isinstance(
                iprs_resp, httpx.ConnectError
            ):
                raise httpx.ConnectError("API connection failed")

            metrics_resp.raise_for_status()
            iprs_resp.raise_for_status()

            self.metrics = metrics_resp.json()
            self.iprs = iprs_resp.json()
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
            self.logs.append(
                f"[dim]{time.strftime('%H:%M:%S')}[/] [red]API Error: {e.response.status_code} ({self.consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})[/]"
            )
        except Exception:
            self.api_status = "Disconnected"
            self.consecutive_errors += 1
            self.logs.append(
                f"[dim]{time.strftime('%H:%M:%S')}[/] [red]An unexpected error occurred[/]"
            )

    def _generate_mock_data(self):
        # (Mock data generation remains the same as previous version)
        self.api_status = "connected"
        self.metrics = {"llm": {"last_intent": "mock_intent"}, "system": {}}
        self.iprs = []
        self.logs.append(f"[dim]{time.strftime('%H:%M:%S')}[/] [cyan]Mock data generated[/]")

    def _render_header(self) -> Align:
        """Renders the dashboard header."""
        f = Figlet(font="slant")
        ascii_art = Text(f.renderText("ALMA"), style="bold cyan", justify="center")

        status_dot = "🟢" if self.api_status == "connected" else "🔴"
        status_text = Text(f"{status_dot} API: {self.api_status}", justify="right")
        version_text = Text(f"v{APP_VERSION}", justify="right", style="dim")

        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(width=25)
        grid.add_row(ascii_art, f"{status_text}\n{version_text}")

        return Align.center(grid, vertical="middle")

    def _render_llm_panel(self) -> Panel:
        """Renders the LLM Status panel."""
        title = "[bold]🧠 LLM Status[/]"
        if self.api_status != "connected" and not self.mock:
            return Panel(Spinner("dots", "Connecting..."), title=title, border_style="red")

        llm_metrics = self.metrics.get("llm", {})
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right", ratio=1)
        grid.add_row("Last Intent:", f"[bold magenta]{llm_metrics.get('last_intent', 'N/A')}[/]")
        grid.add_row("Tokens/sec:", f"{llm_metrics.get('tokens_per_second', 0):.2f}")
        grid.add_row("Total Tokens:", f"{llm_metrics.get('total_tokens', 0):,}")
        return Panel(grid, title=title, border_style="cyan")

    def _render_health_panel(self) -> Panel:
        """Renders the System Health panel."""
        title = "[bold]⚙️ System Health[/]"
        if self.api_status != "connected" and not self.mock:
            return Panel(Text("---", justify="center"), title=title, border_style="red")

        system_metrics = self.metrics.get("system", {})
        cpu = system_metrics.get("cpu_usage", 0)
        mem = system_metrics.get("memory_usage", 0)
        latency = system_metrics.get("avg_api_latency_ms", 0)

        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column(justify="right")
        grid.add_row("CPU Usage:", f"[{'green' if cpu < 70 else 'red'}]{cpu:.1f}%[/]")
        grid.add_row("Memory Usage:", f"[{'green' if mem < 70 else 'red'}]{mem:.1f}%[/]")
        grid.add_row("API Latency:", f"{latency:.0f} ms")
        return Panel(grid, title=title, border_style="cyan")

    def _render_ipr_panel(self) -> Panel:
        """Renders the Active Deployments/IPRs panel."""
        table = Table(box=None, expand=True)
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Title", style="magenta", ratio=2)
        table.add_column("Status", justify="center")
        table.add_column("Progress", justify="center", width=25)

        if self.iprs:
            for ipr in self.iprs:
                progress = Progress(
                    BarColumn(), TextColumn("{task.percentage:>3.0f}%"), expand=True
                )

                status_map = {
                    "pending_approval": "[yellow]Pending[/]",
                    "deploying": "[cyan]Deploying[/]",
                    "completed": "[green]Completed[/]",
                }
                status_text = status_map.get(ipr["status"], ipr["status"])
                task_id = progress.add_task(status_text, total=100)
                progress.update(task_id, completed=ipr.get("progress", 0))

                table.add_row(str(ipr["id"]), ipr["title"], status_text, progress)
        elif self.api_status == "connected":
            table.add_row(Text("No active deployments.", justify="center", style="dim"), span=4)

        return Panel(table, title="[bold]🚀 Active Deployments[/]", border_style="green")

    def _render_footer(self) -> Panel:
        """Renders the scrolling log footer."""
        log_text = "\n".join(self.logs)
        return Panel(log_text, title="[bold]📜 System Events[/]", border_style="dim")

    def render(self) -> Layout:
        """Renders the entire dashboard layout with fresh data."""
        self.layout["header"].update(self._render_header())
        self.layout["llm_status"].update(self._render_llm_panel())
        self.layout["system_health"].update(self._render_health_panel())
        self.layout["action"].update(self._render_ipr_panel())
        self.layout["footer"].update(self._render_footer())
        return self.layout

    async def run(self):
        """Run the dashboard's main async loop."""
        with Live(self.render(), screen=True, redirect_stderr=False, transient=True) as live:
            while self.consecutive_errors < MAX_CONSECUTIVE_ERRORS:
                await self.update_data()
                live.update(self.render())
                await asyncio.sleep(REFRESH_RATE_SECONDS)

        # If the loop breaks due to errors, run the recovery wizard
        self.run_recovery_wizard()

    def run_recovery_wizard(self):
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

        # --- Step 3: API Key ---
        self.console.print("\n[bold]Step 2: Enter the API Key[/]")
        api_key = Prompt.ask(
            "API Key", default="sk-dummy", password=(choice != "1" and choice != "2")
        )

        # --- Step 4: Save to .env ---
        if Confirm.ask("\nSave these settings to the `.env` file?", default=True):
            dotenv_path = find_dotenv()
            if not dotenv_path:
                # Create .env if it doesn't exist
                with open(".env", "w"):
                    pass
                dotenv_path = find_dotenv()

            set_key(dotenv_path, "OPENAI_BASE_URL", base_url)
            set_key(dotenv_path, "OPENAI_API_KEY", api_key)
            self.console.print("\n[bold green]✅ Configuration saved to .env file![/]")
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
):
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
