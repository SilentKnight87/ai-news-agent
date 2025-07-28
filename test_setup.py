#!/usr/bin/env python3
"""
Test script to verify AI News Aggregator setup.

This script helps you test the application step by step.
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   Run: cp .env.example .env")
        print("   Then edit .env with your API keys")
        return False
    
    # Read .env file
    with open(env_path) as f:
        content = f.read()
    
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "GEMINI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=your_" in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or incomplete environment variables: {', '.join(missing_vars)}")
        print("   Please update your .env file with actual API keys")
        return False
    
    print("✅ .env file looks good!")
    return True

def test_imports():
    """Test if all core modules can be imported."""
    try:
        # Add src to path
        sys.path.insert(0, str(Path("src").absolute()))
        
        from src.config import get_settings
        print("✅ Configuration module imported successfully")
        
        # Test if settings can be loaded (will fail if env vars missing)
        try:
            settings = get_settings()
            print("✅ Settings loaded successfully")
            print(f"   Supabase URL: {settings.supabase_url[:20]}...")
            return True
        except Exception as e:
            print(f"❌ Failed to load settings: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_connection():
    """Test Supabase database connection."""
    try:
        from src.config import get_settings
        from supabase import create_client
        
        settings = get_settings()
        supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        
        # Test simple query
        result = supabase.table("articles").select("count").limit(1).execute()
        print("✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Check your Supabase credentials and database schema")
        return False

def test_ai_connection():
    """Test Google Gemini API connection."""
    try:
        import os
        from src.config import get_settings
        from pydantic_ai import Agent
        
        # Load settings and set environment variable
        settings = get_settings()
        os.environ['GOOGLE_API_KEY'] = settings.gemini_api_key
        
        # Simple test with minimal prompt
        agent = Agent(
            model='gemini-1.5-flash',
            output_type=str,
            system_prompt="You are a test assistant. Respond with 'OK' to confirm the connection."
        )
        
        print("✅ Gemini API connection configured!")
        print("   (Note: Not making actual API call to avoid charges)")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API configuration failed: {e}")
        print("   Check your GEMINI_API_KEY in .env file")
        return False

def main():
    """Run all setup tests."""
    print("🔍 AI News Aggregator Setup Test")
    print("=" * 40)
    
    tests = [
        ("Environment Configuration", check_env_file),
        ("Module Imports", test_imports),
        ("Database Connection", test_database_connection),
        ("AI API Connection", test_ai_connection),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! You can start the server with:")
        print("   source venv_linux/bin/activate")
        print("   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")
        print("\n📖 Then visit: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please fix the issues above before running the server.")

if __name__ == "__main__":
    main()