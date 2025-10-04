"""
Configuration Loader for Composer Engine

This module handles loading and parsing of YAML configuration files
including use_cases.yaml and prompts.yaml.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Loads and manages YAML configurations for the Composer Engine.
    
    This class is responsible for:
    1. Loading use_cases.yaml and prompts.yaml
    2. Validating configuration structure
    3. Providing easy access to configuration data
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the config loader.
        
        Args:
            config_dir: Path to the configs directory. If None, uses default location.
        """
        if config_dir is None:
            # Default to configs directory relative to this file
            self.config_dir = Path(__file__).parent.parent.parent / "configs"
        else:
            self.config_dir = config_dir
            
        self.use_cases_config = self._load_use_cases()
        self.prompts_config = self._load_prompts()
        
        logger.info(f"✅ ConfigLoader initialized with {len(self.use_cases_config.get('use_cases', {}))} use cases")
    
    def _load_use_cases(self) -> Dict[str, Any]:
        """Load the use_cases.yaml configuration."""
        use_cases_path = self.config_dir / "use_cases.yaml"
        
        if not use_cases_path.exists():
            raise FileNotFoundError(f"use_cases.yaml not found at {use_cases_path}")
        
        try:
            with open(use_cases_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"📁 Loaded use cases configuration from {use_cases_path}")
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in use_cases.yaml: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load use_cases.yaml: {e}")
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load the prompts.yaml configuration."""
        prompts_path = self.config_dir / "prompts.yaml"
        
        if not prompts_path.exists():
            raise FileNotFoundError(f"prompts.yaml not found at {prompts_path}")
        
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"📁 Loaded prompts configuration from {prompts_path}")
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in prompts.yaml: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load prompts.yaml: {e}")
    
    def get_use_case_config(self, use_case_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific use case.
        
        Args:
            use_case_name: Name of the use case
            
        Returns:
            Configuration dictionary for the use case
            
        Raises:
            ValueError: If use case is not found or not enabled
        """
        use_cases = self.use_cases_config.get("use_cases", {})
        
        if use_case_name not in use_cases:
            available = list(use_cases.keys())
            raise ValueError(f"Use case '{use_case_name}' not found. Available: {available}")
        
        use_case_config = use_cases[use_case_name]
        
        if not use_case_config.get("enabled", False):
            raise ValueError(f"Use case '{use_case_name}' is disabled")
        
        return use_case_config
    
    def get_agent_prompt(self, agent_name: str, prompt_type: str = "system_prompt") -> str:
        """
        Get prompt for a specific agent.
        
        Args:
            agent_name: Name of the agent
            prompt_type: Type of prompt (system_prompt, user_prompt, etc.)
            
        Returns:
            Prompt string
            
        Raises:
            ValueError: If agent or prompt type not found
        """
        if agent_name not in self.prompts_config:
            available = list(self.prompts_config.keys())
            raise ValueError(f"Agent '{agent_name}' not found in prompts. Available: {available}")
        
        agent_prompts = self.prompts_config[agent_name]
        
        if prompt_type not in agent_prompts:
            available = list(agent_prompts.keys())
            raise ValueError(f"Prompt type '{prompt_type}' not found for agent '{agent_name}'. Available: {available}")
        
        return agent_prompts[prompt_type]
    
    def get_enabled_agents(self, use_case_name: str) -> List[Dict[str, Any]]:
        """
        Get list of enabled agents for a use case.
        
        Args:
            use_case_name: Name of the use case
            
        Returns:
            List of enabled agent configurations
        """
        use_case_config = self.get_use_case_config(use_case_name)
        agents = use_case_config.get("agents", [])
        
        return [agent for agent in agents if agent.get("enabled", False)]
    
    def list_available_use_cases(self) -> List[str]:
        """
        Get list of all available use case names.
        
        Returns:
            List of use case names
        """
        return list(self.use_cases_config.get("use_cases", {}).keys())
    
    def list_enabled_use_cases(self) -> List[str]:
        """
        Get list of enabled use case names.
        
        Returns:
            List of enabled use case names
        """
        use_cases = self.use_cases_config.get("use_cases", {})
        return [name for name, config in use_cases.items() if config.get("enabled", False)]
    
    def get_story_length_config(self, use_case_name: str, story_length: str) -> Dict[str, Any]:
        """
        Get story length configuration for a specific use case and length.
        
        Args:
            use_case_name: Name of the use case
            story_length: Story length ('short', 'medium', 'long')
            
        Returns:
            Dictionary containing word_count, words_per_chapter, etc.
            
        Raises:
            ValueError: If use case or story length not found
        """
        use_case_config = self.get_use_case_config(use_case_name)
        length_constraints = use_case_config.get("settings", {}).get("story_length_constraints", {})
        
        if story_length not in length_constraints:
            available = list(length_constraints.keys())
            raise ValueError(f"Story length '{story_length}' not found for use case '{use_case_name}'. Available: {available}")
        
        return length_constraints[story_length]
    
    def get_word_count(self, use_case_name: str, story_length: str) -> int:
        """
        Get the target word count for a specific use case and story length.
        
        Args:
            use_case_name: Name of the use case  
            story_length: Story length ('short', 'medium', 'long')
            
        Returns:
            Target word count as integer
        """
        length_config = self.get_story_length_config(use_case_name, story_length)
        return length_config.get("word_count", 400)
    
    def validate_use_case_config(self, use_case_name: str) -> bool:
        """
        Validate that a use case configuration is properly structured.
        
        Args:
            use_case_name: Name of the use case to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            use_case_config = self.get_use_case_config(use_case_name)
            
            # Check required fields
            required_fields = ["display_name", "description", "enabled", "agents"]
            for field in required_fields:
                if field not in use_case_config:
                    logger.error(f"Missing required field '{field}' in use case '{use_case_name}'")
                    return False
            
            # Validate agents
            agents = use_case_config.get("agents", [])
            if not agents:
                logger.error(f"No agents defined for use case '{use_case_name}'")
                return False
            
            for agent in agents:
                if "name" not in agent:
                    logger.error(f"Agent missing 'name' field in use case '{use_case_name}'")
                    return False
                
                # Check if agent has prompts defined
                agent_name = agent["name"]
                try:
                    self.get_agent_prompt(agent_name)
                except ValueError as e:
                    logger.warning(f"Prompt validation warning for agent '{agent_name}': {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Validation failed for use case '{use_case_name}': {e}")
            return False
