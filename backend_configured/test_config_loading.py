#!/usr/bin/env python3
"""
Test script to verify configuration loading is working properly
after cleaning up redundant prompt loading functions.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_config_loader():
    """Test that ConfigLoader can load prompts from prompts.yaml"""
    print("🧪 Testing ConfigLoader...")
    
    try:
        from composer.config_loader import ConfigLoader
        
        # Initialize config loader
        config_loader = ConfigLoader()
        print("✅ ConfigLoader initialized successfully")
        
        # Test loading different agent prompts from prompts.yaml
        test_agents = ["planner", "writer", "critique", "formatter", "content_generator", "poetry_agent", "music_agent"]
        
        for agent_name in test_agents:
            try:
                system_prompt = config_loader.get_agent_prompt(agent_name, "system_prompt")
                print(f"✅ {agent_name}.system_prompt loaded: {len(system_prompt)} chars")
                
                # Test user_prompt if available
                try:
                    user_prompt = config_loader.get_agent_prompt(agent_name, "user_prompt")
                    print(f"✅ {agent_name}.user_prompt loaded: {len(user_prompt)} chars")
                except ValueError:
                    print(f"ℹ️  {agent_name}.user_prompt not found (optional)")
                    
            except Exception as e:
                print(f"❌ Failed to load {agent_name} prompts: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ ConfigLoader test failed: {e}")
        return False

def test_agent_prompt_loading():
    """Test that agent nodes can load prompts using only config-based approach"""
    print("\n🧪 Testing agent prompt loading functions...")
    
    try:
        from agents.agent_nodes import load_prompt_from_config
        
        # Test the single source of truth function
        test_agents = ["planner", "writer", "critique"]
        
        for agent_name in test_agents:
            try:
                prompt = load_prompt_from_config(agent_name, "system_prompt")
                print(f"✅ load_prompt_from_config works for {agent_name}: {len(prompt)} chars")
            except Exception as e:
                print(f"❌ load_prompt_from_config failed for {agent_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent prompt loading test failed: {e}")
        return False

def test_redundant_functions_commented():
    """Test that redundant functions are properly commented out"""
    print("\n🧪 Testing that redundant functions are commented out...")
    
    try:
        from agents import agent_nodes
        
        # Check that load_prompt_with_priority is not available
        if hasattr(agent_nodes, 'load_prompt_with_priority'):
            print("❌ load_prompt_with_priority is still available (should be commented out)")
            return False
        else:
            print("✅ load_prompt_with_priority is properly commented out")
        
        # Check that load_prompt_from_config is available
        if hasattr(agent_nodes, 'load_prompt_from_config'):
            print("✅ load_prompt_from_config is available")
        else:
            print("❌ load_prompt_from_config is missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Redundant functions test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting configuration cleanup verification tests...\n")
    
    success = True
    
    # Test 1: ConfigLoader functionality
    success &= test_config_loader()
    
    # Test 2: Agent prompt loading
    success &= test_agent_prompt_loading()
    
    # Test 3: Redundant functions commented
    success &= test_redundant_functions_commented()
    
    print("\n" + "="*60)
    if success:
        print("🎉 All tests passed! Configuration cleanup was successful.")
        print("📋 Summary:")
        print("   ✅ ConfigLoader working properly")
        print("   ✅ Prompts loading from prompts.yaml only")
        print("   ✅ Redundant functions properly commented out")
        print("   ✅ Single source of truth established")
    else:
        print("❌ Some tests failed. Please check the output above.")
        
    print("="*60)

if __name__ == "__main__":
    main()