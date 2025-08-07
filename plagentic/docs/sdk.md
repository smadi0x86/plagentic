# Plagentic SDK Documentation

## Overview

The Plagentic SDK provides programmatic access to agent-driven infrastructure provisioning capabilities. Use it to integrate Plagentic into Python applications, build custom tools, or create automated infrastructure workflows.

## Installation

```python
from plagentic.sdk import Agent, AgentTeam, Task, ModelFactory
```

## Basic Usage

```python
# Create a model
model_factory = ModelFactory()
model = model_factory.get_model("claude-3-5-sonnet-20241022")

# Create an agent
agent = Agent(
    name="Infrastructure-Engineer",
    model=model,
    system_prompt="You are an AWS infrastructure expert.",
    tools=["terminal", "saveFile"]
)

# Create a team from config
team_config = {
    "agents": [{
        "name": "Infrastructure-Engineer", 
        "role": "AWS Expert",
        "system_prompt": "Design secure, scalable AWS infrastructure.",
        "tools": ["terminal", "saveFile"]
    }],
    "model": {"name": "claude-3-5-sonnet-20241022"}
}

team = AgentTeam.from_dict(team_config)

# Execute a task
task = Task("Create a VPC with public and private subnets")
result = team.execute(task)

# Handle results
if result.status == "success":
    print(f"Task completed: {result.summary}")
else:
    print(f"Task failed: {result.error}")
```

## Core Components

### Agent
Individual AI agent with specific capabilities and tools.

```python
agent = Agent(
    name="security-specialist",
    model=model,
    system_prompt="Focus on security best practices",
    tools=["terminal", "saveFile", "searchGoogle"]
)
```

### AgentTeam
Coordinated group of agents working together.

```python
team = AgentTeam.from_dict(team_config)
result = team.execute(Task("Deploy secure AWS environment"))
```

### Task
Work item for agents to execute.

```python
task = Task(
    description="Create AWS VPC with security groups",
    context={"region": "us-west-2", "environment": "production"}
)
```

## Built-in Tools

- **terminal**: Execute system commands
- **saveFile**: File system operations  
- **searchGoogle**: Web search capabilities
- **browser**: Browser automation (optional dependency)

## Custom Tools

Create custom tools by extending BaseTool:

```python
from plagentic.sdk.tools import BaseTool

class CustomTool(BaseTool):
    name = "custom_tool"
    description = "My custom tool"
    
    def execute(self, input_data):
        return {"result": "success"}
```

## Error Handling

```python
try:
    result = team.execute(task)
    if result.status == "success":
        print(f"Success: {result.summary}")
    else:
        print(f"Failed: {result.error}")
except Exception as e:
    print(f"Execution error: {e}")
```
