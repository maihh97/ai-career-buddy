#!/usr/bin/env python3
"""
Career Buddy Setup Script
This script helps set up the Career Buddy application environment.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(f"Command: {command}")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible!")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible. Please use Python 3.8 or higher.")
        return False

def install_dependencies():
    """Install Python dependencies"""
    commands = [
        ("pip install agent-framework-azure-ai --pre", "Installing Microsoft Agent Framework (preview)"),
        ("pip install -r requirements.txt", "Installing other dependencies"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True

def setup_environment_file():
    """Setup environment configuration file"""
    print("\n⚙️ Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists!")
        return True
    
    if env_example.exists():
        try:
            env_example.rename(env_file)
            print("✅ Created .env file from template!")
            print("🔧 Please edit .env file with your Azure configuration.")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("❌ .env.example file not found!")
        return False

def main():
    """Main setup function"""
    print("🚀 Career Buddy Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies. Please check the errors above.")
        sys.exit(1)
    
    # Setup environment file
    setup_environment_file()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your Azure AI configuration")
    print("2. Ensure you have Azure credentials configured (az login)")
    print("3. Run the application with: streamlit run career_buddy_app.py")
    print("\n💡 See README.md for detailed configuration instructions.")

if __name__ == "__main__":
    main()