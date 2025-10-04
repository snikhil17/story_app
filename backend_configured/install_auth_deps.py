#!/usr/bin/env python3
"""
Install authentication dependencies for FastAPI app
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install the required authentication dependencies"""
    dependencies = [
        "firebase-admin==6.5.0",
        "email-validator==2.1.1", 
        "bcrypt==4.1.2"
    ]
    
    print("🔧 Installing authentication dependencies...")
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    print("\n✅ All authentication dependencies installed successfully!")
    print("\n📋 Summary of installed packages:")
    for dep in dependencies:
        print(f"  - {dep}")
    
    print("\n🔧 Dependencies are ready for FastAPI authentication features:")
    print("  - Firebase Admin SDK for Google Authentication")
    print("  - Email validation for user registration")
    print("  - Password hashing for email/password authentication")
    
    return True

def test_imports():
    """Test if the installed dependencies can be imported"""
    print("\n🧪 Testing imports...")
    
    try:
        import firebase_admin
        print("✅ firebase_admin imported successfully")
    except ImportError as e:
        print(f"❌ firebase_admin import failed: {e}")
        return False
    
    try:
        import email_validator
        print("✅ email_validator imported successfully")
    except ImportError as e:
        print(f"❌ email_validator import failed: {e}")
        return False
    
    try:
        import bcrypt
        print("✅ bcrypt imported successfully")
    except ImportError as e:
        print(f"❌ bcrypt import failed: {e}")
        return False
    
    print("✅ All imports successful!")
    return True

if __name__ == "__main__":
    print("🚀 Setting up authentication dependencies for FastAPI app")
    print("=" * 60)
    
    if install_dependencies():
        if test_imports():
            print("\n🎉 Setup completed successfully!")
            print("\n📚 Next steps:")
            print("1. Start the FastAPI server: python fastapi_app.py")
            print("2. The API will be available at http://localhost:8000")
            print("3. Authentication endpoints will be available at:")
            print("   - POST /auth/register (email/password)")
            print("   - POST /auth/login (email/password)")  
            print("   - POST /auth/firebase (Firebase token)")
            print("   - GET /auth/me (get current user)")
            print("   - POST /user/form (user form management)")
            print("4. Simple UI will be served at http://localhost:8000")
            print("5. API docs available at http://localhost:8000/docs")
        else:
            print("\n❌ Import tests failed. Please check the installation.")
            sys.exit(1)
    else:
        print("\n❌ Dependency installation failed.")
        sys.exit(1)