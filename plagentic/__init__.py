# First, set environment variables before any imports
import os

os.environ["BROWSER_USE_LOGGING_LEVEL"] = "error"

# Then import logging and configure it
import logging

logging.getLogger("browser_use").setLevel(logging.ERROR)
logging.getLogger("root").setLevel(logging.ERROR)

# Now import the rest
"""
Plagentic - Infrastructure Provisioning Tool

Agent-driven, cloud-agnostic platform engineering with AI-powered infrastructure provisioning.

 SDK Usage (Programmatic):
    from plagentic.sdk import Agent, AgentTeam, Task
    
    # Create and execute agent teams programmatically
    team = AgentTeam.from_dict(config)
    result = team.execute(Task("Deploy AWS infrastructure"))

 CLI Usage (Command Line):
    plagentic run aws-infrastructure -t "Deploy VPC with subnets"
    plagentic list teams
    plagentic --help

For more information, see:
- SDK Documentation: https://github.com/smadi0x86/plagentic/blob/main/docs/sdk.md
- CLI Documentation: https://github.com/smadi0x86/plagentic/blob/main/docs/cli.md
"""

# Import SDK for programmatic access
from plagentic import sdk

# Import CLI for command-line access  
from plagentic import cli

__version__ = "0.1.0"

# Main exports point to SDK for backward compatibility
from plagentic.sdk import (
    Agent,
    AgentTeam, 
    Task,
    TeamResult,
    AgentExecutionResult,
    TeamContext,
    ModelFactory,
    BaseTool,
    ToolManager,
    config,
    load_config,
)

__all__ = [
    # Main SDK Components
    'Agent',
    'AgentTeam',
    'Task', 
    'TeamResult',
    'AgentExecutionResult',
    'TeamContext',
    'ModelFactory',
    'BaseTool',
    'ToolManager',
    'ConfigManager',
    
    # Modules
    'sdk',
    'cli',
]
