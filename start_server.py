#!/usr/bin/env python3
"""
Startup script for Quest & Rewards MCP Server
This script starts the server from the project root directory
"""

import os
import sys
import subprocess

def main():
    """Start the quest server"""
    print("🎮 Starting Quest & Rewards MCP Server...")
    
    # Change to the mcp-bearer-token directory
    server_dir = os.path.join(os.path.dirname(__file__), "mcp-bearer-token")
    
    if not os.path.exists(server_dir):
        print("❌ Error: mcp-bearer-token directory not found!")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check if quest_rewards_mcp.py exists
    server_file = os.path.join(server_dir, "quest_rewards_mcp.py")
    if not os.path.exists(server_file):
        print("❌ Error: quest_rewards_mcp.py not found!")
        print("Please ensure the quest server file exists.")
        sys.exit(1)
    
    # Change to server directory and start the server
    os.chdir(server_dir)
    
    print(f"📁 Working directory: {os.getcwd()}")
    print("🚀 Starting server...")
    print("💡 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the server
        subprocess.run([sys.executable, "quest_rewards_mcp.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Python executable not found!")
        print("Please ensure Python 3.11+ is installed and in your PATH.")
        sys.exit(1)

if __name__ == "__main__":
    main()
