"""GCP Agents - Summoner: CLI entry point.

Usage::

    # Run the research agent
    python main.py research "What are the latest trends in LLM agents?"

    # Run the data processing agent
    python main.py process --prefix raw-data/

    # Show loaded configuration
    python main.py config
"""

from __future__ import annotations

import sys

import click
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agents.specialized_agents.research_agent import ResearchAgent
from agents.specialized_agents.data_processing_agent import DataProcessingAgent
from config import load_config

console = Console()

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)


@click.group()
@click.option("--config", "config_path", default=None, help="Path to config YAML.")
@click.pass_context
def cli(ctx: click.Context, config_path: str | None) -> None:
    """GCP Agents - Summoner: Autonomous AI agents on Google Cloud."""
    ctx.ensure_object(dict)
    ctx.obj["settings"] = load_config(config_path)


@cli.command()
@click.argument("query")
@click.pass_context
def research(ctx: click.Context, query: str) -> None:
    """Run the research agent with a QUERY."""
    settings = ctx.obj["settings"]
    agent = ResearchAgent(settings)

    console.print(Panel(f"[bold]Research Query:[/bold] {query}", title="Summoner"))
    result = agent.run(query)

    if result.success:
        console.print("\n[bold green]Research Complete[/bold green]\n")
        for question, answer in result.output.items():
            console.print(f"[bold]{question}[/bold]")
            console.print(f"  {answer}\n")
    else:
        console.print(f"[bold red]Failed:[/bold red] {result.error}")
        sys.exit(1)


@cli.command()
@click.option("--prefix", default="", help="GCS source prefix to process.")
@click.pass_context
def process(ctx: click.Context, prefix: str) -> None:
    """Run the data processing agent on files in GCS."""
    settings = ctx.obj["settings"]
    agent = DataProcessingAgent(settings, source_prefix=prefix)

    console.print(Panel(f"[bold]Source prefix:[/bold] {prefix or '(root)'}", title="Summoner"))
    result = agent.run(f"Process files under {prefix or 'bucket root'}")

    if result.success:
        console.print(f"[bold green]Processed {result.output['count']} files[/bold green]")
        for f in result.output["processed_files"]:
            console.print(f"  -> {f}")
    else:
        console.print(f"[bold red]Failed:[/bold red] {result.error}")
        sys.exit(1)


@cli.command("config")
@click.pass_context
def show_config(ctx: click.Context) -> None:
    """Display the current configuration."""
    settings = ctx.obj["settings"]
    table = Table(title="Summoner Configuration")
    table.add_column("Section", style="cyan")
    table.add_column("Setting", style="green")
    table.add_column("Value")

    cfg = settings.model_dump()
    for section, values in cfg.items():
        if isinstance(values, dict):
            for key, val in values.items():
                display = str(val) if val else "(not set)"
                table.add_row(section, key, display)
        else:
            table.add_row("", section, str(values))

    console.print(table)


if __name__ == "__main__":
    cli()
