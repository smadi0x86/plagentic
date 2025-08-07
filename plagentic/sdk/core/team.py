from typing import Union, Literal, Generator, Dict, Any, Optional, Tuple, List
import json
import re

from plagentic.sdk.common import LoadingIndicator
from plagentic.sdk.common.utils import stringUtil
from plagentic.sdk.common.utils.log import logger
from plagentic.sdk.models import LLMRequest, LLMModel
from plagentic.sdk.models.modelFactory import ModelFactory
from plagentic.sdk.core.agent import Agent
from plagentic.sdk.core.context import TeamContext
from plagentic.sdk.core.result import TeamResult, AgentExecutionResult
from plagentic.sdk.core.task import Task, TaskStatus
from plagentic.sdk.tools.toolManager import ToolManager


class AgentTeam:
    def __init__(self, name: str, description: str, rule: str = "", model: LLMModel = None, max_steps: int = 20):
        """
        Initialize the AgentTeam with a name, description, rules, and a list of agents.

        :param name: The name of the agent group.
        :param description: A description of the agent group.
        :param rule: The rules governing the agent group.
        :param model: An instance of LLMModel to be used by the team.
        :param max_steps: Maximum number of total steps across all agents (default: 20)
        """
        self.name = name
        self.description = description
        self.rule = rule
        self.agents = []
        self.context = TeamContext(name, description, rule, agents=self.agents, max_steps=max_steps)
        self.model: LLMModel = model  # Instance of LLMModel
        self.max_steps = max_steps  # Maximum total steps across all agents
        self.task_short_name = ""

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'AgentTeam':
        """
        Create an AgentTeam instance from a dictionary configuration.
        
        :param config: Dictionary containing team configuration
        :return: AgentTeam instance
        """
        # Extract basic team information
        name = config.get('name', 'unnamed_team')
        description = config.get('description', '')
        rule = config.get('rule', '')
        max_steps = config.get('max_steps', 20)
        
        # Create model instance if specified
        model = None
        if 'model' in config:
            model_config = config['model']
            if isinstance(model_config, dict):
                provider = model_config.get('provider', 'openai')
                model_name = model_config.get('name', 'gpt-4o-mini')
            elif isinstance(model_config, str):
                # Handle case where model is just a string
                model_name = model_config
                provider = 'claude' if 'claude' in model_name.lower() else 'openai'
            else:
                model_name = 'claude-3-5-sonnet-20241022'
                provider = 'claude'
            
            try:
                factory = ModelFactory()
                model = factory.get_model(model_name, provider)
            except Exception as e:
                logger.warning(f"Failed to create model {provider}/{model_name}: {e}")
                # Fallback to default model
                factory = ModelFactory()
                model = factory.get_model('claude-3-5-sonnet-20241022', 'claude')
        
        # Create team instance
        team = cls(name=name, description=description, rule=rule, model=model, max_steps=max_steps)
        
        # Add agents if specified
        if 'agents' in config:
            for agent_config in config['agents']:
                try:
                    # Create agent from configuration
                    agent_name = agent_config.get('name', 'unnamed_agent')
                    agent_description = agent_config.get('description', '')
                    system_prompt = agent_config.get('system_prompt', '')
                    tool_names = agent_config.get('tools', [])
                    
                    # Resolve tool names to tool objects
                    toolManager = ToolManager()
                    toolManager.load_tools()  # Ensure tools are loaded
                    tools = []
                    for tool_name in tool_names:
                        tool_instance = toolManager.create_tool(tool_name)
                        if tool_instance:
                            tools.append(tool_instance)
                        else:
                            logger.warning(f"Tool '{tool_name}' not found, skipping for agent '{agent_name}'")
                    
                    # Create agent instance using correct Agent constructor signature
                    agent = Agent(
                        name=agent_name,
                        system_prompt=system_prompt,
                        description=agent_description,
                        model=model,  # Use team's model
                        tools=tools
                    )
                    
                    team.add(agent)
                    
                except Exception as e:
                    logger.error(f"Failed to create agent from config {agent_config}: {e}")
                    continue
        
        return team

    def add(self, agent: Agent):
        """
        Add an agent to the group.

        :param agent: The agent to be added.
        """
        agent.team_context = self.context  # Pass the group context to the agent

        # If agent doesn't have a model specified, use the team's model
        if not agent.model and self.model:
            agent.model = self.model

        self.agents.append(agent)

    def run(self, task: Union[str, Task], output_mode: Literal["print", "logger"] = "logger") -> TeamResult:
        """
        Decide which agent will handle the task and execute its step method.
        
        :param task: The task to be processed, can be a string or Task object
        :param output_mode: Control how execution progress is displayed: 
                           "print" for console output or "logger" for using logger
        :return: A TeamResult object containing the execution results
        """
        # Set output mode in context for agents to use
        self.context.output_mode = output_mode

        # Create a function for output based on the mode
        def output(message, end="\n"):
            if output_mode == "print":
                print(message, end=end)
            elif message:
                logger.info(message.strip())

        # Convert string task to Task object if needed
        if isinstance(task, str):
            task = Task(content=task)

        # Update task status
        task.update_status(TaskStatus.PROCESSING)

        # Create a TeamResult to track the execution
        result = TeamResult(team_name=self.name, task=task)

        # Store task in context
        self.context.user_task = task.get_text()
        self.context.task = task
        self.context.model = self.model  # Set the model in the context

        # Print user task and team information
        output("")
        output(f"Team {self.name} received the task and started processing")
        output("")

        try:
            # Select the initial agent and prepare the context
            selected_agent, selected_agent_id, subtask = self._select_initial_agent(task, output_mode, output)
            if selected_agent is None:
                result.complete("failed")
                return result

            # Pass output mode to agent
            selected_agent.output_mode = output_mode

            # Track total steps used across all agents
            total_steps_used = 0

            # Process all agents in the chain
            agent_results = self._process_agent_chain(selected_agent, selected_agent_id, subtask,
                                                      total_steps_used, output, stream=False)

            # Add all agent results to the team result
            for agent_result in agent_results:
                result.add_agent_result(agent_result)

            # Update task status and complete the result
            task.update_status(TaskStatus.COMPLETED)

            # Set the final output to the last agent's final answer
            if result.agent_results and result.agent_results[-1].final_answer:
                result.final_output = result.agent_results[-1].final_answer

            result.complete("completed")

            # Print task completion information
            output(f"\nTeam {self.name} completed the task")

            # Clean up resources before returning
            self.cleanup()

            return result

        except Exception as e:
            # Handle any exceptions
            import traceback
            error_msg = f"Error during team execution: {str(e)}"
            detail_msg = traceback.format_exc()

            logger.error(error_msg)
            logger.debug(f"Error details: {detail_msg}")

            # Clean up resources even when exception occurs
            self.cleanup()

            result.complete("failed")
            return result

    def run_async(self, task: Union[str, Task], output_mode: Literal["print", "logger"] = "logger") -> \
            Generator[Dict[str, Any], None, TeamResult]:
        """
        Decide which agent will handle the task and execute its step method.
        Yields agent execution results as they occur.

        :param task: The task to be processed, can be a string or Task object
        :param output_mode: Control how execution progress is displayed:
                           "print" for console output or "logger" for using logger
        :return: A generator yielding agent execution results and finally the TeamResult
        """
        # Set output mode in context for agents to use
        self.context.output_mode = output_mode

        # Create a function for output based on the mode
        def output(message, end="\n"):
            if output_mode == "print":
                print(message, end=end)
            elif message:
                logger.info(message.strip())

        # Convert string task to Task object if needed
        if isinstance(task, str):
            task = Task(content=task)

        # Update task status
        task.update_status(TaskStatus.PROCESSING)

        # Create a TeamResult to track the execution
        result = TeamResult(team_name=self.name, task=task)

        # Store task in context
        self.context.user_task = task.get_text()
        self.context.task = task
        self.context.model = self.model  # Set the model in the context

        # Print user task and team information
        output("")
        output(f"Team {self.name} received the task and started processing")
        output("")

        try:
            # Select the initial agent and prepare the context
            selected_agent, selected_agent_id, subtask = self._select_initial_agent(task, output_mode, output)
            if selected_agent is None:
                result.complete("failed")
                return result

            # Pass output mode to agent
            selected_agent.output_mode = output_mode

            # Track total steps used across all agents
            total_steps_used = 0

            # Create an AgentExecutionResult to track this agent's execution
            agent_result = AgentExecutionResult(
                agent_id=str(selected_agent_id),
                agent_name=selected_agent.name,
                subtask=subtask
            )

            # Execute the selected agent's step method
            step_result = selected_agent.step()
            final_answer = step_result.final_answer
            step_count = step_result.step_count

            # Update total steps used
            total_steps_used += step_count

            # Collect the execution results of the selected agent
            agent_result.final_answer = final_answer if final_answer else ""

            # Collect the execution history of the selected agent
            if hasattr(selected_agent, 'captured_actions') and selected_agent.captured_actions:
                for action in selected_agent.captured_actions:
                    agent_result.add_action(action)

            # Mark the selected agent execution as complete
            agent_result.complete()

            # Add the selected agent result to the team result
            result.add_agent_result(agent_result)

            # Yield the agent result
            yield agent_result.to_dict()

            # Process the agent chain
            current_agent = selected_agent
            while True:
                # Check if we've exceeded the maximum total steps
                if total_steps_used >= self.max_steps:
                    output(f"\nReached maximum total steps ({self.max_steps}). Stopping execution.")
                    break

                # Get the next agent ID
                next_agent_id = current_agent.should_invoke_next_agent()

                # If no next agent or invalid ID, break the loop
                if next_agent_id == -1 or next_agent_id >= len(self.agents):
                    break

                # Get the next agent
                next_agent = self.agents[next_agent_id]

                # Pass output mode to next agent
                next_agent.output_mode = current_agent.output_mode

                # Create the execution result for the next agent
                next_agent_result = AgentExecutionResult(
                    agent_id=str(next_agent_id),
                    agent_name=next_agent.name,
                    subtask=next_agent.subtask
                )

                # Execute the next agent
                step_result = next_agent.step()
                next_final_answer = step_result.final_answer
                step_count = step_result.step_count

                # Update total steps used
                total_steps_used += step_count

                # Collect the execution results of the next agent
                next_agent_result.final_answer = next_final_answer if next_final_answer else ""

                # Collect the execution history of the next agent
                if hasattr(next_agent, 'captured_actions') and next_agent.captured_actions:
                    for action in next_agent.captured_actions:
                        next_agent_result.add_action(action)

                # Mark the next agent execution as complete
                next_agent_result.complete()

                # Add the next agent result to the team result
                result.add_agent_result(next_agent_result)

                # Yield the next agent result
                yield next_agent_result.to_dict()

                # Update current agent for the next iteration
                current_agent = next_agent

            # Update task status and complete the result
            task.update_status(TaskStatus.COMPLETED)

            # Set the final output to the last agent's final answer
            if result.agent_results and result.agent_results[-1].final_answer:
                result.final_output = result.agent_results[-1].final_answer

            result.complete("completed")

            # Print task completion information
            output(f"\nTeam {self.name} completed the task")

            # Clean up resources before returning
            self.cleanup()

            return result

        except Exception as e:
            # Handle any exceptions
            import traceback
            error_msg = f"Error during team execution: {str(e)}"
            detail_msg = traceback.format_exc()

            logger.error(error_msg)
            logger.debug(f"Error details: {detail_msg}")

            # Clean up resources even when exception occurs
            self.cleanup()

            result.complete("failed")
            return result

    def _select_initial_agent(self, task: Task, output_mode: str, output_func) -> Tuple[
        Optional[Agent], Optional[int], Optional[str]]:
        """
        Select the initial agent to handle the task.

        :param task: The task to be processed
        :param output_mode: Output mode ("print" or "logger")
        :param output_func: Function to use for output
        :return: Tuple of (selected_agent, selected_agent_id, subtask)
        """
        # Generate agents_str from the list of agents
        agents_str = ', '.join(
            f'{{"id": {i}, "name": "{agent.name}", "description": "{agent.description}", "system_prompt": "{agent.system_prompt}"}}'
            for i, agent in enumerate(self.agents)
        )

        prompt = GROUP_DECISION_PROMPT.format(group_name=self.name, group_description=self.description,
                                              group_rules=self.rule, agents_str=agents_str,
                                              user_task=task.get_text())

        # Start loading animation (only in print mode)
        loading = None
        if output_mode == "print":
            loading = LoadingIndicator(message="Select an agent in the team...", animation_type="spinner")
            loading.start()

        request = LLMRequest(
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0,
            json_format=True
        )

        # Directly call the model instance
        response = self.model.call(request)

        # Stop loading animation if in print mode
        if loading:
            loading.stop()

        # Check if the API call was successful
        if response.is_error:
            error_message = response.get_error_msg()
            # Use logger to record errors regardless of output mode
            logger.error(f"Error: {error_message}")
            return None, None, None

        reply_text = response.data["choices"][0]["message"]["content"]
        
        # Debug logging for model response
        logger.debug(f"Model response: {reply_text[:500]}..." if len(reply_text) > 500 else f"Model response: {reply_text}")

        # Parse the response to get the selected agent's id
        try:
            decision_res = stringUtil.json_loads(reply_text)
            selected_agent_id = decision_res.get("id")  # Extract the id from the response
            subtask = decision_res.get("subtask")
            task_short_name = decision_res.get("task_short_name")
            self.context.task_short_name = task_short_name

            # Find the selected agent based on the id
            selected_agent: Agent = self.agents[selected_agent_id]
            selected_agent.subtask = subtask
            return selected_agent, selected_agent_id, subtask
        except (json.JSONDecodeError, IndexError, KeyError, ValueError) as e:
            error_message = f"Failed to parse model response: {str(e)}\nResponse: {reply_text[:100]}..."
            logger.error(f"Error: {error_message}")
            return None, None, None

    def _process_agent_chain(self, initial_agent: Agent, initial_agent_id: int, subtask: str,
                             total_steps_used: int, output_func, stream: bool = False) -> List[AgentExecutionResult]:
        """
        Process the chain of agents starting with the initial agent.

        :param initial_agent: The first agent to execute
        :param initial_agent_id: ID of the initial agent
        :param subtask: The subtask for the initial agent
        :param total_steps_used: Counter for total steps used
        :param output_func: Function to use for output
        :param stream: Whether this is being called in streaming mode (not used in this method)
        :return: List of agent execution results
        """
        agent_results = []

        # Create an AgentExecutionResult to track this agent's execution
        agent_result = AgentExecutionResult(
            agent_id=str(initial_agent_id),
            agent_name=initial_agent.name,
            subtask=subtask
        )

        # Execute the selected agent's step method
        step_result = initial_agent.step()
        final_answer = step_result.final_answer
        step_count = step_result.step_count

        # Update total steps used
        total_steps_used += step_count

        # Collect the execution results of the selected agent
        agent_result.final_answer = final_answer if final_answer else ""

        # Collect the execution history of the selected agent
        if hasattr(initial_agent, 'captured_actions') and initial_agent.captured_actions:
            for action in initial_agent.captured_actions:
                agent_result.add_action(action)

        # Mark the selected agent execution as complete
        agent_result.complete()

        # Add to our list of results
        agent_results.append(agent_result)

        # Process the agent chain
        current_agent = initial_agent
        while True:
            # Check if we've exceeded the maximum total steps
            if total_steps_used >= self.max_steps:
                output_func(f"\nReached maximum total steps ({self.max_steps}). Stopping execution.")
                break

            # Get the next agent ID
            next_agent_id = current_agent.should_invoke_next_agent()

            # If no next agent or invalid ID, break the loop
            if next_agent_id == -1 or next_agent_id >= len(self.agents):
                break

            # Get the next agent
            next_agent = self.agents[next_agent_id]

            # Pass output mode to next agent
            next_agent.output_mode = current_agent.output_mode

            # Create the execution result for the next agent
            next_agent_result = AgentExecutionResult(
                agent_id=str(next_agent_id),
                agent_name=next_agent.name,
                subtask=next_agent.subtask
            )

            # Execute the next agent
            step_result = next_agent.step()
            next_final_answer = step_result.final_answer
            step_count = step_result.step_count

            # Update total steps used
            total_steps_used += step_count

            # Collect the execution results of the next agent
            next_agent_result.final_answer = next_final_answer if next_final_answer else ""

            # Collect the execution history of the next agent
            if hasattr(next_agent, 'captured_actions') and next_agent.captured_actions:
                for action in next_agent.captured_actions:
                    next_agent_result.add_action(action)

            # Mark the next agent execution as complete
            next_agent_result.complete()

            # Add to our list of results
            agent_results.append(next_agent_result)

            # Update current agent for the next iteration
            current_agent = next_agent

        return agent_results

    def cleanup(self):
        """
        Clean up resources used by the team and its agents.
        This includes closing browser connections, file handles, etc.
        """
        # Clean up resources for each agent
        for agent in self.agents:
            # Clean up tools for each agent
            if hasattr(agent, 'tools'):
                for tool in agent.tools:
                    try:
                        tool.close()
                    except Exception as e:
                        logger.warning(f"Error closing tool {tool.name}: {str(e)}")


GROUP_DECISION_PROMPT = """## Role
You are the coordinator for a team of AI agents. Your job is to analyze the user's task and decide which agent in the team should handle it first, and give the subtask that need to be answered by this member.

## Team Information
Team name: {group_name}
Team description: {group_description}
Team rules: {group_rules}

## Available Agents
{agents_str}

## User Task to Process
The user has provided the following task that needs to be handled:

**Task:** {user_task}

This task must be analyzed and assigned to the most appropriate agent from the team listed above.

## Instructions
1. Analyze the user's task: "{user_task}"
2. Select the most appropriate agent based on their expertise
3. Create a specific subtask for that agent
4. Provide a short task name

## Output Format
You MUST respond with valid JSON only. No other text.

{{"id": <agent_id_number>, "subtask": "<specific_subtask_for_selected_agent>", "task_short_name": "<short_name>"}}"""
