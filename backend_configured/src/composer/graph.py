"""
Dynamic Graph Builder - The heart of the Composer Engine

This module implements the one-graph-workflow architecture where a single
LangGraph workflow can handle multiple use cases by dynamically enabling/disabling
agents and configuring their routing based on YAML configuration.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional, Union

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from .state import ComposerState, should_continue_workflow
from .config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class DynamicGraph:
    """
    Core engine for building dynamic LangGraph workflows from YAML configuration.
    
    This class implements the one-graph-workflow architecture:
    1. Single graph that handles all use cases
    2. Agents are enabled/disabled based on configuration
    3. Routing is dynamic based on use case requirements
    4. Prompts are loaded from YAML and injected at runtime
    """
    
    def __init__(self, use_case_name: str, config_dir: Optional[Path] = None):
        """
        Initialize the DynamicGraph for a specific use case.
        
        Args:
            use_case_name: Name of the use case to build (e.g., 'story_generator')
            config_dir: Path to the configs directory
        """
        self.use_case_name = use_case_name
        self.config_loader = ConfigLoader(config_dir)
        
        # Load and validate configuration
        self.use_case_config = self.config_loader.get_use_case_config(use_case_name)
        
        if not self.config_loader.validate_use_case_config(use_case_name):
            raise ValueError(f"Invalid configuration for use case '{use_case_name}'")
        
        # Get enabled agents for this use case
        self.enabled_agents = self.config_loader.get_enabled_agents(use_case_name)
        
        # Build the workflow
        self.workflow = self._build_workflow()
        
        logger.info(f"✅ DynamicGraph initialized for use case: {use_case_name}")
        logger.info(f"📋 Enabled agents: {[agent['name'] for agent in self.enabled_agents]}")
    
    def _build_workflow(self):
        """
        Build the LangGraph workflow based on the use case configuration.
        
        Returns:
            Compiled LangGraph workflow
        """
        # Create the state graph
        graph = StateGraph(ComposerState)
        
        # Add all enabled agent nodes
        agent_nodes_added = []
        for agent_config in self.enabled_agents:
            agent_name = agent_config["name"]
            
            # Get the agent function
            agent_function = self._get_agent_function(agent_name)
            if agent_function:
                # Wrap the agent function to inject prompts
                wrapped_function = self._wrap_agent_function(agent_function, agent_config)
                graph.add_node(agent_name, wrapped_function)
                agent_nodes_added.append(agent_name)
                logger.info(f"➕ Added agent node: {agent_name}")
        
        if not agent_nodes_added:
            raise ValueError(f"No valid agent nodes found for use case '{self.use_case_name}'")
        
        # Set the entry point (first enabled agent)
        first_agent = agent_nodes_added[0]
        graph.set_entry_point(first_agent)
        logger.info(f"🚀 Entry point set to: {first_agent}")
        
        # Add edges based on agent configuration
        self._add_edges(graph, agent_nodes_added)
        
        # Compile the graph
        compiled_graph = graph.compile()
        logger.info(f"🔧 Graph compiled successfully for use case: {self.use_case_name}")
        
        # Generate and save workflow diagram
        self._generate_workflow_diagram(compiled_graph)
        
        return compiled_graph
    
    def _get_agent_function(self, agent_name: str) -> Optional[Callable]:
        """
        Get the agent function by name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent function or None if not found
        """
        # Import agents dynamically to avoid circular imports
        from ..agents.agent_nodes import (
            planner_node, writer_node, formatter_node, critique_node,
            poetry_agent_node, music_agent_node, image_generator_node,
            content_generator_node
        )
        
        # Map agent names to functions
        agent_function_map = {
            "planner": planner_node,
            "writer": writer_node,
            "formatter": formatter_node,
            "content_generator": content_generator_node,  # New unified node
            "story_formatter": formatter_node,  # Backward compatibility alias
            "poetry_formatter": formatter_node,  # Use same formatter for poetry
            "critique": critique_node,
            "poetry_agent": poetry_agent_node,
            "poetry_writer": poetry_agent_node,  # Alias
            "music_agent": music_agent_node,
            "image_generator": image_generator_node,
            # Add more agents as needed
        }
        
        function = agent_function_map.get(agent_name)
        if not function:
            logger.warning(f"⚠️ Agent function not found for: {agent_name}")
            return None
        
        return function
    
    def _wrap_agent_function(self, agent_function: Callable, agent_config: Dict[str, Any]) -> Callable:
        """
        Wrap an agent function to inject configuration and prompts.
        
        Args:
            agent_function: Original agent function
            agent_config: Configuration for this agent
            
        Returns:
            Wrapped agent function
        """
        def wrapped_agent(state: ComposerState) -> ComposerState:
            # Inject agent-specific configuration
            agent_name = agent_config["name"]
            
            # Get prompts for this agent
            try:
                system_prompt = self.config_loader.get_agent_prompt(agent_name, "system_prompt")
                state["agent_config"] = {
                    **state.get("agent_config", {}),
                    f"{agent_name}_system_prompt": system_prompt
                }
            except ValueError as e:
                logger.warning(f"Could not load system prompt for {agent_name}: {e}")
            
            # Add use case context
            state["use_case"] = self.use_case_name
            
            logger.info(f"🎯 Executing agent: {agent_name}")
            
            # Execute the original agent function
            result_state = agent_function(state)
            
            # Update workflow step tracking
            if agent_name not in result_state.get("completed_steps", []):
                result_state["completed_steps"] = result_state.get("completed_steps", []) + [agent_name]
            
            return result_state
        
        return wrapped_agent
    
    def _add_edges(self, graph: StateGraph, agent_nodes: List[str]) -> None:
        """
        Add edges between nodes based on the configuration.
        
        Args:
            graph: The state graph to add edges to
            agent_nodes: List of agent node names that were added
        """
        for i, agent_config in enumerate(self.enabled_agents):
            agent_name = agent_config["name"]
            
            if agent_name not in agent_nodes:
                continue
            
            # Check if this agent has conditional routing
            edge_type = agent_config.get("edge_type", "linear")
            
            if edge_type == "conditional":
                # Add conditional edge
                routing_map = agent_config.get("routing_map", {})
                
                def route_function(state: ComposerState) -> str:
                    return self._route_conditional_agent(state, routing_map)
                
                graph.add_conditional_edges(
                    agent_name,
                    route_function,
                    routing_map
                )
                logger.info(f"🔀 Added conditional edge for {agent_name} with routes: {list(routing_map.keys())}")
                
            else:
                # Linear routing to next agent or END
                if i + 1 < len(self.enabled_agents):
                    next_agent_config = self.enabled_agents[i + 1]
                    next_agent_name = next_agent_config["name"]
                    
                    if next_agent_name in agent_nodes:
                        graph.add_edge(agent_name, next_agent_name)
                        logger.info(f"➡️ Added linear edge: {agent_name} -> {next_agent_name}")
                    else:
                        graph.add_edge(agent_name, END)
                        logger.info(f"🏁 Added end edge: {agent_name} -> END")
                else:
                    graph.add_edge(agent_name, END)
                    logger.info(f"🏁 Added end edge: {agent_name} -> END")
    
    def _route_conditional_agent(self, state: ComposerState, routing_map: Dict[str, str]) -> str:
        """
        Determine routing for a conditional agent based on state.
        
        Args:
            state: Current state
            routing_map: Map of conditions to next nodes
            
        Returns:
            Name of next node to route to
        """
        # Check if workflow should end
        if not should_continue_workflow(state):
            return "end"
        
        # For critique agent, check if revision is needed
        if state.get("current_agent") == "critique":
            quality_score = state.get("quality_score", 7.0)
            revision_count = state.get("revision_count", 0)
            max_revisions = state.get("max_revisions", 3)
            
            # Debug logging
            logger.info(f"🔍 DEBUG: Critique routing - quality_score: {quality_score}, revision_count: {revision_count}")
            
            if quality_score and quality_score < 7 and revision_count < max_revisions:
                logger.info(f"🔄 Routing to revision (quality score {quality_score} < 7)")
                return "revise"
            else:
                logger.info(f"✅ Routing to end (quality score {quality_score} >= 7 or max revisions reached)")
                
                # Check the actual routing map
                route_target = routing_map.get("end", "END")
                logger.info(f"🎯 DEBUG: routing_map['end'] = {route_target}")
                return "end"
        
        # Default routing
        return routing_map.get("default", "end")
    
    def run(self, 
            user_input: str,
            target_audience: str = "children",
            theme: str = "adventure",
            style_preferences: Optional[Dict[str, Any]] = None,
            **kwargs) -> Dict[str, Any]:
        """
        Run the workflow for the configured use case.
        
        Args:
            user_input: User's request or prompt
            target_audience: Target audience for the content
            theme: Theme or genre for the content
            style_preferences: Style preferences for content generation
            **kwargs: Additional parameters
            
        Returns:
            Final state as dictionary
        """
        from .state import create_initial_state
        
        # Create initial state
        initial_state = create_initial_state(
            use_case=self.use_case_name,
            user_input=user_input,
            target_audience=target_audience,
            theme=theme,
            style_preferences=style_preferences or {},
            **kwargs
        )
        
        logger.info(f"🚀 Starting workflow for use case: {self.use_case_name}")
        logger.info(f"📝 User input: {user_input}")

        # Run the workflow
        try:
            final_state = self.workflow.invoke(initial_state)
            logger.info(f"✅ Workflow completed successfully")
            return dict(final_state)
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {str(e)}")
            raise
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Get information about the configured workflow.
        
        Returns:
            Dictionary with workflow information
        """
        return {
            "use_case": self.use_case_name,
            "display_name": self.use_case_config.get("display_name"),
            "description": self.use_case_config.get("description"),
            "enabled_agents": [agent["name"] for agent in self.enabled_agents],
            "agent_count": len(self.enabled_agents)
        }

    def _generate_workflow_diagram(self, compiled_graph) -> None:
        """
        Generate and save a mermaid workflow diagram for the current use case.
        
        Args:
            compiled_graph: The compiled LangGraph workflow
        """
        try:
            import os
            
            # Create output directory
            base_path = Path(__file__).parent.parent.parent
            diagram_folder = base_path / "outputs" / "diagrams"
            diagram_folder.mkdir(parents=True, exist_ok=True)
            
            # Generate diagram filename based on use case
            diagram_filename = f"{self.use_case_name}_workflow.png"
            diagram_path = diagram_folder / diagram_filename
            
            # Generate the mermaid diagram
            compiled_graph.get_graph().draw_mermaid_png(output_file_path=str(diagram_path))
            
            logger.info(f"✅ Workflow diagram saved to: {diagram_path}")
            
        except ImportError:
            logger.warning(
                "⚠️ Could not generate workflow diagram. "
                "Make sure you have installed mermaid-cli: "
                "`npm install -g @mermaid-js/mermaid-cli`"
            )
        except Exception as e:
            logger.error(f"❌ Error generating workflow diagram: {e}")
            logger.warning(
                "💡 To fix this, ensure mermaid-cli is installed: "
                "`npm install -g @mermaid-js/mermaid-cli`"
            )
