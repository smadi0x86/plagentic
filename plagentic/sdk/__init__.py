"""
Plagentic SDK - Core Library for Agent-Driven Infrastructure Provisioning

This is the main SDK that provides programmatic access to Plagentic's
agent-driven infrastructure provisioning capabilities.

Usage:
    from plagentic.sdk import Agent, AgentTeam, Task
    
    # Create an agent
    agent = Agent(name="Infrastructure-Engineer", model=model, tools=tools)
    
    # Create a team
    team = AgentTeam.from_dict(team_config)
    
    # Execute a task
    result = team.execute(Task("Deploy AWS VPC"))
"""

# Core SDK Components
from plagentic.sdk.core.agent import Agent
from plagentic.sdk.core.team import AgentTeam
from plagentic.sdk.core.task import Task
from plagentic.sdk.core.result import TeamResult, AgentExecutionResult
from plagentic.sdk.core.context import TeamContext

# Model System
from plagentic.sdk.models.modelFactory import ModelFactory
from plagentic.sdk.models.llm.baseModel import LLMModel

# Tool System
from plagentic.sdk.tools.baseTool import BaseTool
from plagentic.sdk.tools.toolManager import ToolManager

# Common Utilities
from plagentic.sdk.common.config.configManager import config, load_config

__version__ = "0.1.0"

__all__ = [
    # Core Components
    "Agent",
    "AgentTeam", 
    "Task",
    "TeamResult",
    "AgentExecutionResult",
    "TeamContext",
    
    # Model System
    "ModelFactory",
    "BaseModel",
    
    # Tool System
    "BaseTool",
    "ToolManager",
    
    # Configuration
    "ConfigManager",
]
