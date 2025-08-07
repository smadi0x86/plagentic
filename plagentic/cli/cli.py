#!/usr/bin/env python3
"""
Plagentic CLI - Agentic AI Infrastructure Provisioning Platform
"""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional

from plagentic.sdk.common import logger, load_config
from plagentic.sdk.core import AgentTeam, Task
from plagentic.sdk.tools.toolManager import ToolManager

console = Console()
app = typer.Typer(
    name="plagentic",
    help="Agentic AI Infrastructure Provisioning Platform",
    no_args_is_help=True,
    rich_markup_mode="rich"
)

def get_teams_directory():
    """Get the correct teams directory path for both local and Docker environments"""
    # verify if we're in Docker (teams mounted at /app/teams)
    docker_teams = Path("/app/teams")
    if docker_teams.exists():
        return docker_teams
    
    # Check local teams directory
    local_teams = Path("teams")
    if local_teams.exists():
        return local_teams
    
    # Default to local path for creation
    return local_teams

def init_plagentic(quiet=False):
    """Initialize Plagentic configuration and tools"""
    try:
        # Load configuration
        load_config()
        
        # Load tools using package-based loading (works in both local and Docker)
        ToolManager().load_tools()
        
        return True
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error initializing Plagentic: {e}[/red]")
        return False

def save_execution_results(team_name: str, task: str, result) -> str:
    """Save execution results to file and return file path"""
    import json
    from datetime import datetime
    
    # Create results directory
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{team_name}_{timestamp}.json"
    results_file = results_dir / filename
    
    # Save results as JSON
    result_data = {
        "timestamp": timestamp,
        "team": team_name,
        "task": task,
        "status": result.status,
        "final_output": result.final_output,
        "execution_log": getattr(result, 'execution_log', []),
        "metadata": {
            "duration": getattr(result, 'duration', None),
            "agents_used": getattr(result, 'agents_used', []),
            "tools_used": getattr(result, 'tools_used', [])
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(result_data, f, indent=2, default=str)
    
    return str(results_file)

@app.command("list")
def list_teams():
    """List all available agent teams"""
    if not init_plagentic():
        raise typer.Exit(1)
    
    try:
        teams_dir = get_teams_directory()
        if not teams_dir.exists():
            console.print("[yellow]No teams directory found. Create one with your team configurations.[/yellow]")
            return
        
        team_files = list(teams_dir.glob("*.yaml")) + list(teams_dir.glob("*.yml"))
        
        if not team_files:
            console.print("[yellow]No team configuration files found in teams/ directory.[/yellow]")
            return
        
        table = Table(title="Available Agent Teams")
        table.add_column("Team File", style="cyan")
        table.add_column("Status", style="green")
        
        for team_file in team_files:
            table.add_row(team_file.stem, "✓ Available")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing teams: {e}[/red]")
        raise typer.Exit(1)

@app.command("run")
def run_team(
    team: str = typer.Argument(..., help="Name of the team to run"),
    task: Optional[str] = typer.Option(None, "-t", "--task", help="Task description to execute"),
    config_file: Optional[str] = typer.Option(None, "-c", "--config", help="Custom config file path"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose logging")
):
    """Run a specific agent team with a task"""
    # Initialize with quiet mode unless verbose is explicitly requested
    if not init_plagentic(quiet=not verbose):
        raise typer.Exit(1)
    
    if verbose:
        logger.setLevel("DEBUG")
    
    try:
        teams_dir = get_teams_directory()
        team_file = None
        
        for ext in [".yaml", ".yml"]:
            potential_file = teams_dir / f"{team}{ext}"
            if potential_file.exists():
                team_file = potential_file
                break
        
        if not team_file:
            console.print(f"[red]Team configuration '{team}' not found in teams/ directory[/red]")
            raise typer.Exit(1)
        
        console.print(f"[green]Loading team: {team}[/green]")
        
        with open(team_file, 'r') as f:
            import yaml
            team_config = yaml.safe_load(f)
        
        # Create team from config
        agent_team = AgentTeam.from_dict(team_config)
        
        # Create task
        if not task:
            task = typer.prompt("Enter task description")
        
        task_obj = Task(content=task)
        
        console.print(f"[blue]Executing task: {task}[/blue]")
        console.print("[dim]Working...[/dim]")
        
        result = agent_team.run(task_obj)
        
        results_file = save_execution_results(team, task, result)
        
        if result.status == "completed":
            console.print(Panel(
                f"[green]✓ Task completed successfully![/green]\n\n" +
                f"📄 Full results saved to: {results_file}\n" +
                f"📋 Summary: {result.final_output[:200]}{'...' if len(result.final_output) > 200 else ''}",
                title="Execution Result",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[red]✗ Task failed![/red]\n\nStatus: {result.status}\n\n" +
                f"📄 Full details saved to: {results_file}\n" +
                f"Error: {result.final_output or 'No output available'}",
                title="Execution Error",
                border_style="red"
            ))
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]Error running team: {e}[/red]")
        raise typer.Exit(1)

@app.command("init")
def init_project(
    name: str = typer.Argument(..., help="Project name"),
    path: Optional[str] = typer.Option(".", "-p", "--path", help="Project path")
):
    """Initialize a new Plagentic project"""
    import shutil
    from pathlib import Path
    
    project_path = Path(path) / name
    
    try:
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "teams").mkdir(exist_ok=True)
        (project_path / "workspace").mkdir(exist_ok=True)
        
        # Find the template files from the package root
        current_dir = Path(__file__).parent.parent.parent
        config_template = current_dir / "config-template.yaml"
        team_template = current_dir / "teams" / "team-template.yaml"
        
        # Copy config template
        if config_template.exists():
            shutil.copy2(config_template, project_path / "config.yaml")
            console.print(f"[green]✓[/green] Copied config template to config.yaml")
        else:
            console.print(f"[yellow]⚠[/yellow] Config template not found, creating basic config")
            # Minimal fallback config
            basic_config = '''
# Plagentic Configuration
# Copy API keys from your environment or set them here

# Model Configuration
models:
  claude:
    api_key: "${ANTHROPIC_API_KEY}"
    api_base: "https://api.anthropic.com/v1"
  openai:
    api_key: "${OPENAI_API_KEY}"
    api_base: "https://api.openai.com/v1"
  deepseek:
    api_key: "${DEEPSEEK_API_KEY}"
    api_base: "https://api.deepseek.com/v1"

# Tool Configuration  
tools:
  terminal:
    enabled: true
  saveFile:
    enabled: true
    base_path: "./workspace"
'''
            with open(project_path / "config.yaml", 'w') as f:
                f.write(basic_config.strip())
        
        if team_template.exists():
            shutil.copy2(team_template, project_path / "teams" / "team-template.yaml")
            console.print(f"[green]✓[/green] Copied team template to teams/team-template.yaml")
        else:
            console.print(f"[yellow]⚠[/yellow] Team template not found")
        
        console.print(Panel(
            f"[green]✓ Project '{name}' initialized successfully![/green]\n\n"
            f"Project path: {project_path}\n"
            f"Config: config.yaml (configure your API keys)\n"
            f"Team template: teams/team-template.yaml\n"
            f"Workspace: workspace/ (for saving results)\n\n"
            f"Next steps:\n"
            f"1. Configure API keys in config.yaml\n"
            f"2. Customize teams/team-template.yaml for your needs\n"
            f"3. Run: plagentic list (from project directory)\n"
            f"4. Run: plagentic run team-template -t 'Your task description'\n",
            title="Project Initialized",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]Error initializing project: {e}[/red]")
        raise typer.Exit(1)

@app.command("version")
def show_version():
    """Show Plagentic version"""
    console.print("[bold blue]Plagentic[/bold blue] version [green]0.1.0[/green]")
    console.print("Agentic AI Infrastructure Provisioning Platform")

@app.callback()
def main():
    """
    Plagentic - Agentic AI Infrastructure Provisioning Platform
    
    A powerful AI-driven tool for managing cloud infrastructure through intelligent agents.
    """
    pass

def cli_main():
    """Entry point for the CLI"""
    app()

if __name__ == "__main__":
    cli_main()
