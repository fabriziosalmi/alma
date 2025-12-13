
"""CLI for The Council."""

import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.live import Live
from rich.spinner import Spinner
from rich.layout import Layout
from rich.table import Table

from alma.core.agent.council import Council, AgentMessage

console = Console()
council_app = typer.Typer(name="council", help="Summon the Multi-Agent Council")

@council_app.command("convene")
def convene(intent: str = typer.Argument(..., help="What do you want to build?")):
    """
    Summon the Council to debate and design your infrastructure.
    """
    council = Council()
    
    console.print(Panel.fit(f"[bold yellow]🔔 The Council Has Been Summoned[/]\nTopic: [cyan]{intent}[/]", border_style="yellow"))

    async def run_session():
        # We manually orchestrate the sequence here for the "Live" effect if we wanted, 
        # but for simplicity we'll run it and print progressively.
        # Actually, let's just run it standard and utilize the return.
        
        with console.status("[bold green]Agents are deliberating...[/]", spinner="dots") as status:
            result = await council.convene(intent)
            return result

    result = asyncio.run(run_session())

        # Pretty print the transcript
    for msg in result.transcript:
        color = "blue"
        title = msg.agent_name
        if msg.agent_name == "SecOps":
            color = "red"
            icon = "🛡️"
        elif msg.agent_name == "FinOps":
            color = "green"
            icon = "💰"
        else:
            color = "blue"
            icon = "🏗️"
        
        content_to_print = msg.content
        if isinstance(content_to_print, dict):
            # Convert structured content to pretty JSON or YAML for display
            import json
            content_to_print = f"```json\n{json.dumps(content_to_print, indent=2)}\n```"

        console.print(Panel(
            Markdown(str(content_to_print)),
            title=f"{icon} [bold {color}]{title}[/]",
            border_style=color,
            subtitle=msg.role.upper()
        ))

    # Print Final Blueprint
    console.print(Panel(
        Syntax(str(result.final_blueprint), "json", theme="monokai", word_wrap=True),
        title="[bold white]📜 Final Decree (Blueprint)[/]",
        border_style="white"
    ))

if __name__ == "__main__":
    council_app()
