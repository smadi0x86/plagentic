# Plagentic

Agent driven infrastructure provisioning platform, create teams using YAML definitions to execute tasks including but not limited to web browsing, terminal commands and all things that has a custom MCP server.

Declare agents and the tools they have access to in the team YAML file, then run a task with a team.

> [!Warning]
> This project is still in development and not yet ready for production use, I don't believe we reached a point where AI is safe to manage infrastructure but I think it's fun to try.

## Quick Start

### Installation

#### Option 1: Quick Install (Recommended)

```bash
git clone https://github.com/smadi0x86/plagentic.git
cd plagentic
./install.sh

# Install browser dependencies (GNU/Linux)
sudo apt-get update && sudo apt-get install -y libnspr4 libnss3
uv run python -m playwright install
```

#### Option 2: Manual Install

```bash
git clone https://github.com/smadi0x86/plagentic.git
cd plagentic

curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --extra full

# Install browser dependencies (GNU/Linux)
sudo apt-get update && sudo apt-get install -y libnspr4 libnss3
uv run python -m playwright install
```

### Configuration

```bash
# Copy and edit config
cp config-template.yaml config.yaml
# Add your LLM API key to config.yaml
```

### Basic Usage

```bash
# List available teams
plagentic list teams

# Run a task with a team
plagentic run <team-name> -t "Your task description"

# Examples
plagentic run tool-test -t "Execute: whoami"
plagentic run tool-test -t "Browser: Navigate to https://httpbin.org/get"
```

## Working Tools

- **terminal**: Execute system commands safely
- **browser**: Web automation (navigate, extract content, interact)
- **saveFile**: Save results to workspace files
- **googleSearch**: Web search (requires API key setup)

## Creating Teams

Teams are defined in YAML files in the `teams/` directory. See `teams/tool-test.yaml` for a simple example.

```yaml
name: "my-team"
description: "Team description"
version: "1.0"
max_steps: 10

model:
  provider: "claude"
  name: "claude-3-5-sonnet-20241022"
  temperature: 0.3

config:
  enable_logging: true

agents:
  - name: "Agent-Name"
    role: "Agent Role"
    description: "What this agent does"
    system_prompt: |
      Your agent's instructions and behavior.
      
      AVAILABLE TOOLS:
      - terminal: Execute commands
      - browser: Web automation
      - saveFile: Save results
    tools:
      - terminal
      - browser
      - saveFile
```

## Docker

### Option 1: Docker Compose (Recommended)

The easiest way to run Plagentic in Docker with persistent workspace and team configurations:

```bash
docker compose up -d

# list teams
docker compose exec plagentic plagentic list

# run the template team with a task (API keys from config.yaml)
docker compose exec plagentic plagentic run team-template -t "Execute: whoami"

# get interactive bash shell
docker compose exec plagentic bash

# view logs
docker compose logs plagentic

# clean up
docker compose down
```

### Option 2: Direct Docker Commands

```bash
docker build -t plagentic .

# Run with mounted volumes
docker run --rm -it \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/workspace:/workspace \
  -v $(pwd)/teams:/app/teams \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  plagentic bash

# Or run a specific command
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/teams:/app/teams \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  plagentic plagentic list
```

### Development with Docker

For development with live code reloading:

```bash
docker compose up plagentic-dev -d
docker compose exec plagentic-dev bash
```

### Configuration

**Option 1: Environment Variables (.env file)**

Create a `.env` file in the project root for your API keys:

```bash
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_google_search_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

**Option 2: Direct Configuration (config.yaml)**

Alternatively, set API keys directly in `config.yaml`:

```yaml
models:
  claude:
    api_key: "your_claude_api_key_here"
    api_base: "https://api.anthropic.com/v1"
  openai:
    api_key: "your_openai_api_key_here" 
    api_base: "https://api.openai.com/v1"
```

Both methods work seamlessly in Docker containers. The docker-compose setup will automatically load environment variables if using Option 1.

## Development

The SDK is currently in development and not yet published to PyPI. Use the local installation method above.

Check [TODO.md](TODO.md) for a list of planned features and tasks.

# License

This project is licensed under the General Public License v3.0, see the [LICENSE](LICENSE) file for details.
