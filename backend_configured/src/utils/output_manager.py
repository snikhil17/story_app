"""
Output Management for Composer System

This module handles structured output saving for stories, images, and other            logger.info(f"📖 Saved story content: {story_path}")
        
        # Save poetry (standardized as content.txt)
        if "poetry_content" in state and state["poetry_content"]:
            poetry_path = run_dir / "content.txt"rated content.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OutputManager:
    """
    Manages structured output saving for Composer-generated content.
    """
    
    def __init__(self, base_output_dir: Optional[Path] = None):
        """
        Initialize the output manager.
        
        Args:
            base_output_dir: Base directory for outputs. If None, uses default.
        """
        if base_output_dir is None:
            # Default to outputs directory relative to this file
            self.base_output_dir = Path(__file__).parent.parent.parent / "outputs"
        else:
            self.base_output_dir = base_output_dir
            
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
    def create_run_directory(self, run_id: Optional[str] = None) -> Path:
        """
        Create a new run directory with timestamp.
        
        Args:
            run_id: Optional custom run ID. If None, uses timestamp.
            
        Returns:
            Path to the created run directory
        """
        if run_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_id = f"composer_run_{timestamp}"
        
        run_dir = self.base_output_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Created run directory: {run_dir}")
        return run_dir
    
    def save_state_snapshot(self, state: Dict[str, Any], run_dir: Path, filename: str = "final_state.json") -> Path:
        """
        Save a complete state snapshot to JSON.
        
        Args:
            state: The state dictionary to save
            run_dir: Directory to save the file in
            filename: Name of the JSON file
            
        Returns:
            Path to the saved file
        """
        # Create a clean copy of state for saving (remove non-serializable items)
        clean_state = self._clean_state_for_json(state)
        
        file_path = run_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(clean_state, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Saved state snapshot: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving state snapshot: {e}")
            raise
    
    def save_story_artifacts(self, state: Dict[str, Any], run_dir: Path) -> Dict[str, Path]:
        """
        Save individual story artifacts (plan, story, critique, etc.).
        
        Args:
            state: The state dictionary containing story data
            run_dir: Directory to save files in
            
        Returns:
            Dictionary mapping artifact names to file paths
        """
        saved_files = {}
        
        # Save story plan
        if "plan" in state and state["plan"]:
            plan_path = run_dir / "story_plan.json"
            with open(plan_path, 'w', encoding='utf-8') as f:
                json.dump(state["plan"], f, indent=2, ensure_ascii=False)
            saved_files["plan"] = plan_path
            logger.info(f"📝 Saved story plan: {plan_path}")
        
        # Save story content (standardized as content.txt)
        if "content" in state and state["content"]:
            story_path = run_dir / "content.txt"
            with open(story_path, 'w', encoding='utf-8') as f:
                f.write(state["content"])
            saved_files["story"] = story_path
            logger.info(f"📖 Saved story content: {story_path}")
        
        # Save critique
        if "critique_feedback" in state and state["critique_feedback"]:
            critique_path = run_dir / "story_critique.json"
            with open(critique_path, 'w', encoding='utf-8') as f:
                json.dump(state["critique_feedback"], f, indent=2, ensure_ascii=False)
            saved_files["critique"] = critique_path
            logger.info(f"📋 Saved story critique: {critique_path}")
        
        # Save poetry
        if "poetry_content" in state and state["poetry_content"]:
            poetry_path = run_dir / "poetry.txt"
            with open(poetry_path, 'w', encoding='utf-8') as f:
                f.write(state["poetry_content"])
            saved_files["content"] = poetry_path
            logger.info(f"🎭 Saved poetry: {poetry_path}")
        
        # Save music
        if "music_content" in state and state["music_content"]:
            music_path = run_dir / "music_lyrics.txt"
            with open(music_path, 'w', encoding='utf-8') as f:
                f.write(state["music_content"])
            saved_files["music"] = music_path
            logger.info(f"🎵 Saved music content: {music_path}")
        
        # Save image metadata
        if "image_metadata" in state and state["image_metadata"]:
            image_meta_path = run_dir / "image_metadata.json"
            with open(image_meta_path, 'w', encoding='utf-8') as f:
                json.dump(state["image_metadata"], f, indent=2, ensure_ascii=False)
            saved_files["image_metadata"] = image_meta_path
            logger.info(f"🖼️ Saved image metadata: {image_meta_path}")
        
        return saved_files
    
    def create_summary_report(self, state: Dict[str, Any], run_dir: Path, saved_files: Dict[str, Path]) -> Path:
        """
        Create a summary report for the run.
        
        Args:
            state: The final state dictionary
            run_dir: Directory containing the run files
            saved_files: Dictionary of saved file paths
            
        Returns:
            Path to the summary report
        """
        summary_data = {
            "run_info": {
                "run_id": run_dir.name,
                "created_at": datetime.now().isoformat(),
                "user_input": state.get("user_input", ""),
                "target_age_group": state.get("target_age_group", ""),
                "educational_themes": state.get("educational_themes", []),
                "workflow_step": state.get("workflow_step", ""),
                "use_case": state.get("use_case", "")
            },
            "artifacts_generated": {
                "files_created": len(saved_files),
                "file_list": [str(path.name) for path in saved_files.values()],
                "total_size_bytes": sum(path.stat().st_size for path in saved_files.values() if path.exists())
            },
            "quality_metrics": {
                "quality_score": state.get("quality_score", 0),
                "has_errors": bool(state.get("errors", [])),
                "error_count": len(state.get("errors", []))
            },
            "agent_performance": {
                "final_agent": state.get("current_agent", ""),
                "execution_time": self._calculate_execution_time(state),
                "agents_executed": self._get_executed_agents(state)
            }
        }
        
        summary_path = run_dir / "run_summary.json"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📊 Created summary report: {summary_path}")
        return summary_path
    
    def _clean_state_for_json(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Remove non-JSON-serializable items from state."""
        clean_state = {}
        
        for key, value in state.items():
            try:
                # Test if the value is JSON serializable
                json.dumps(value, default=str)
                clean_state[key] = value
            except (TypeError, ValueError):
                # Skip non-serializable values
                logger.debug(f"Skipping non-serializable key: {key}")
                continue
        
        return clean_state
    
    def _calculate_execution_time(self, state: Dict[str, Any]) -> Optional[float]:
        """Calculate total execution time if timestamps are available."""
        try:
            if "created_at" in state and "updated_at" in state:
                start = state["created_at"]
                end = state["updated_at"]
                
                if hasattr(start, 'timestamp') and hasattr(end, 'timestamp'):
                    return end.timestamp() - start.timestamp()
        except Exception:
            pass
        
        return None
    
    def _get_executed_agents(self, state: Dict[str, Any]) -> list:
        """Extract list of agents that were executed."""
        executed = []
        
        # Check for evidence of each agent's execution
        if state.get("plan"):
            executed.append("planner")
        if state.get("content") or state.get("poetry_content"):
            executed.append("writer")
        if state.get("critique_feedback"):
            executed.append("critique")
        if state.get("poetry_content"):
            executed.append("poetry_agent")
        if state.get("music_content"):
            executed.append("music_agent")
        if state.get("image_metadata"):
            executed.append("image_generator")
        
        return executed


def save_run_output(state: Dict[str, Any], run_id: Optional[str] = None) -> Path:
    """
    Convenience function to save a complete run output.
    
    Args:
        state: The final state dictionary
        run_id: Optional custom run ID
        
    Returns:
        Path to the run directory
    """
    output_manager = OutputManager()
    run_dir = output_manager.create_run_directory(run_id)
    
    # Save all artifacts
    saved_files = output_manager.save_story_artifacts(state, run_dir)
    output_manager.save_state_snapshot(state, run_dir)
    output_manager.create_summary_report(state, run_dir, saved_files)
    
    logger.info(f"✅ Complete run output saved to: {run_dir}")
    return run_dir
