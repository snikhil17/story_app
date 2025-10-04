"""
Main API for the Composer Engine

This module provides a simple interface to run the one-graph-workflow
for any configured use case.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .composer.graph import DynamicGraph
from .composer.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class ComposerAPI:
    """
    Main API interface for the Composer Engine.
    
    This class provides a simple interface to:
    1. List available use cases
    2. Run workflows for specific use cases
    3. Get information about configured workflows
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the Composer API.
        
        Args:
            config_dir: Path to the configs directory
        """
        self.config_loader = ConfigLoader(config_dir)
        logger.info("✅ ComposerAPI initialized")
    
    def list_use_cases(self) -> Dict[str, Any]:
        """
        List all available use cases.
        
        Returns:
            Dictionary with use case information
        """
        enabled_cases = self.config_loader.list_enabled_use_cases()
        all_cases = self.config_loader.list_available_use_cases()
        
        use_case_info = {}
        for case_name in all_cases:
            try:
                config = self.config_loader.get_use_case_config(case_name)
                use_case_info[case_name] = {
                    "display_name": config.get("display_name", case_name),
                    "description": config.get("description", ""),
                    "enabled": case_name in enabled_cases,
                    "agents": [agent["name"] for agent in config.get("agents", [])]
                }
            except ValueError:
                # Use case is disabled or invalid
                continue
        
        return {
            "total_use_cases": len(all_cases),
            "enabled_use_cases": len(enabled_cases),
            "use_cases": use_case_info
        }
    
    def run_workflow(self, 
                    use_case: str,
                    user_input: str,
                    **kwargs) -> Dict[str, Any]:
        """
        Run a workflow for the specified use case with personalization support.
        
        Args:
            use_case: Name of the use case to run
            user_input: User's request or prompt
            **kwargs: Additional parameters including personalization data
            
        Returns:
            Final state as dictionary
            
        Raises:
            ValueError: If use case is not found or invalid
        """
        logger.info(f"🚀 Running workflow for use case: {use_case}")
        logger.info(f"📝 User input: {user_input}")
        
        # Log all received parameters for debugging
        logger.info(f"🔍 All received parameters: {list(kwargs.keys())}")
        for key, value in kwargs.items():
            if key == 'image_style':
                logger.info(f"🎨 IMAGE_STYLE: {key} = {value}")
            elif key in ['child_name', 'child_age', 'age', 'interests']:
                logger.info(f"👤 PERSONALIZATION: {key} = {value}")
            else:
                logger.info(f"⚙️ PARAMETER: {key} = {value}")
        
        # Log personalization parameters if present
        personalization_keys = [
            'child_name', 'age', 'child_gender', 'story_language', 'interests', 
            'reading_level', 'companions', 'location', 'region', 'mother_tongue',
            'theme', 'moral_lesson', 'image_style', 'include_images', 'story_length',
            'child_age', 'language_of_story', 'target_audience'
        ]
        
        personalization_data = {k: v for k, v in kwargs.items() if k in personalization_keys and v}
        if personalization_data:
            logger.info(f"🎯 Personalization data: {personalization_data}")
        
        # Validate use case
        if not self.config_loader.validate_use_case_config(use_case):
            raise ValueError(f"Invalid or disabled use case: {use_case}")
        
        # Create dynamic graph for this use case
        graph = DynamicGraph(use_case, self.config_loader.config_dir)
        
        # Run the workflow with all parameters
        result = graph.run(user_input, **kwargs)
        
        logger.info(f"✅ Workflow completed for use case: {use_case}")
        return result
    
    def get_workflow_info(self, use_case: str) -> Dict[str, Any]:
        """
        Get information about a specific workflow.
        
        Args:
            use_case: Name of the use case
            
        Returns:
            Workflow information dictionary
        """
        graph = DynamicGraph(use_case, self.config_loader.config_dir)
        return graph.get_workflow_info()


# Convenience function for quick access
def run_story_generation(user_input: str, **kwargs) -> Dict[str, Any]:
    """
    Quick function to run story generation.
    
    Args:
        user_input: User's story request
        **kwargs: Additional parameters
        
    Returns:
        Generated story result
    """
    api = ComposerAPI()
    return api.run_workflow("story_generator", user_input, **kwargs)


def run_poetry_and_song(user_input: str, **kwargs) -> Dict[str, Any]:
    """
    Quick function to run poetry and song generation.
    
    Args:
        user_input: User's poetry/song request
        **kwargs: Additional parameters
        
    Returns:
        Generated poetry/song result
    """
    api = ComposerAPI()
    return api.run_workflow("poetry_and_song", user_input, **kwargs)
