#!/usr/bin/env python3
"""
Breathsmith MCP Server
Personal collection of useful tools and utilities
"""
import asyncio
import json
import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Create the main server instance
mcp = FastMCP("Breathsmith")

@mcp.tool()
def get_timestamp(format_type: str = "iso") -> str:
    """Get current timestamp in various formats.
    
    Args:
        format_type: Type of format - 'iso', 'unix', 'readable'
    
    Returns:
        Formatted timestamp string
    """
    now = datetime.now()
    
    if format_type == "unix":
        return str(int(now.timestamp()))
    elif format_type == "readable":
        return now.strftime("%Y-%m-%d %H:%M:%S")
    else:  # iso
        return now.isoformat()

@mcp.tool()
def test_tool(message: str = "Hello") -> str:
    """A simple test tool to verify the server is working.
    
    Args:
        message: A message to echo back
        
    Returns:
        The message with a timestamp
    """
    return f"Echo: {message} at {datetime.now().strftime('%H:%M:%S')}"

@mcp.tool()
def openai_chat(prompt: str, model: str = "gpt-4.1-mini", max_tokens: int = 500) -> str:
    """Send a prompt to OpenAI using the modern Responses API.
    
    Args:
        prompt: The message/question to send to OpenAI
        model: The OpenAI model to use (default: gpt-4.1-mini) 
        max_tokens: Maximum tokens in response (default: 500)
        
    Returns:
        The AI response as a string
    """
    try:
        # Import here to avoid issues if not installed
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if not client.api_key:
            return "Error: OPENAI_API_KEY not found in environment variables"
        
        # Try the modern Responses API first
        try:
            response = client.responses.create(
                model=model,
                input=prompt
            )
            
            # Extract text from the response output
            if response.output and len(response.output) > 0:
                # Find the last message in the output
                for item in reversed(response.output):
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                return content_item.text
            
            return "No response received from Responses API"
            
        except Exception as responses_error:
            # Fallback to Chat Completions API
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content or "No response received"
        
    except ImportError:
        return "Error: OpenAI library not installed. Run 'uv add openai' to install."
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"

@mcp.tool()
def claude_chat(prompt: str, model: str = "claude-sonnet-4-20250514", max_tokens: int = 1000) -> str:
    """Send a prompt to Claude (Anthropic) and get a response.
    
    Args:
        prompt: The message/question to send to Claude
        model: The Claude model to use (default: claude-sonnet-4-20250514)
        max_tokens: Maximum tokens in response (default: 1000)
        
    Returns:
        Claude's response as a string
    """
    try:
        # Import here to avoid issues if not installed
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        if not os.getenv("ANTHROPIC_API_KEY"):
            return "Error: ANTHROPIC_API_KEY not found in environment variables"
        
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text if response.content else "No response received"
        
    except ImportError:
        return "Error: Anthropic library not installed. Run 'uv add anthropic' to install."
    except Exception as e:
        return f"Error calling Claude API: {str(e)}"

@mcp.tool()
def claude_vs_openai(prompt: str, claude_model: str = "claude-sonnet-4-20250514", openai_model: str = "gpt-4.1-mini") -> str:
    """Compare responses from both Claude and OpenAI for the same prompt.
    
    Args:
        prompt: The question/prompt to send to both models
        claude_model: Claude model to use (default: claude-3-5-sonnet-20241022)
        openai_model: OpenAI model to use (default: gpt-4.1-mini)
        
    Returns:
        Comparison of both responses
    """
    # Get Claude response
    claude_response = claude_chat(prompt, claude_model, 800)
    
    # Get OpenAI response
    openai_response = openai_chat(prompt, openai_model, 800)
    
    return f"**Claude ({claude_model}):**\n{claude_response}\n\n**OpenAI ({openai_model}):**\n{openai_response}"

@mcp.tool()
def claude_opus_4(prompt: str, max_tokens: int = 2000) -> str:
    """Send a prompt to Claude Opus 4 - the most powerful Claude model for complex tasks.
    
    Args:
        prompt: The message/question to send to Claude Opus 4
        max_tokens: Maximum tokens in response (default: 2000)
        
    Returns:
        Claude Opus 4's response as a string
    """
    return claude_chat(prompt, "claude-opus-4-20250514", max_tokens)

@mcp.tool()
def openai_web_search(query: str, model: str = "gpt-4.1-mini", max_tokens: int = 1000) -> str:
    """Ask OpenAI to search the web and provide an answer with sources.
    
    Args:
        query: The search query or question
        model: The OpenAI model to use (default: gpt-4.1-mini)
        max_tokens: Maximum tokens in response (default: 1000)
        
    Returns:
        AI response with web search results and citations
    """
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if not client.api_key:
            return "Error: OPENAI_API_KEY not found in environment variables"
        
        try:
            response = client.responses.create(
                model=model,
                input=query,
                tools=[{"type": "web_search"}]
            )
            
            # Extract text from the response output
            if response.output and len(response.output) > 0:
                # Find the last message in the output
                for item in reversed(response.output):
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                return content_item.text
            
            return "No response received from web search"
            
        except Exception as e:
            return f"Error using web search tool: {str(e)}. This feature requires the Responses API."
        
    except ImportError:
        return "Error: OpenAI library not installed. Run 'uv add openai' to install."
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"

@mcp.tool()
def openai_with_tools(prompt: str, enable_web_search: bool = False, enable_file_search: bool = False, model: str = "gpt-4.1-mini", max_tokens: int = 1000) -> str:
    """Send a prompt to OpenAI with optional built-in tools enabled.
    
    Args:
        prompt: The message/question to send to OpenAI
        enable_web_search: Enable real-time web search capability
        enable_file_search: Enable file search capability (for uploaded documents)
        model: The OpenAI model to use (default: gpt-4.1-mini)
        max_tokens: Maximum tokens in response (default: 1000)
        
    Returns:
        AI response potentially enhanced with web search or file search
    """
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if not client.api_key:
            return "Error: OPENAI_API_KEY not found in environment variables"
        
        # Build tools list based on parameters
        tools = []
        if enable_web_search:
            tools.append({"type": "web_search"})
        if enable_file_search:
            tools.append({"type": "file_search"})
        
        try:
            response = client.responses.create(
                model=model,
                input=prompt,
                tools=tools if tools else None
            )
            
            # Extract text from the response output
            if response.output and len(response.output) > 0:
                # Find the last message in the output
                for item in reversed(response.output):
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                return content_item.text
            
            return "No response received"
            
        except Exception as e:
            return f"Error using enhanced tools: {str(e)}. Falling back to basic chat."
        
    except ImportError:
        return "Error: OpenAI library not installed. Run 'uv add openai' to install."
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"

@mcp.tool()
def read_claude_logs(log_type: str = "mcp", lines: int = 20) -> str:
    """Read Claude Desktop log files to help with debugging.
    
    Args:
        log_type: Type of log to read - 'mcp', 'breathsmith', 'all'
        lines: Number of recent lines to read (default: 20)
        
    Returns:
        Recent log entries
    """
    try:
        import subprocess
        from pathlib import Path
        
        log_dir = Path.home() / "Library" / "Logs" / "Claude"
        
        if not log_dir.exists():
            return "Claude log directory not found. Are you on macOS?"
        
        if log_type == "breathsmith":
            log_files = list(log_dir.glob("mcp-server-breathsmith.log"))
        elif log_type == "mcp":
            log_files = [log_dir / "mcp.log"]
        elif log_type == "all":
            log_files = list(log_dir.glob("mcp*.log"))
        else:
            return f"Unknown log type: {log_type}. Use 'mcp', 'breathsmith', or 'all'"
        
        if not log_files:
            return f"No log files found for type: {log_type}"
        
        result = []
        for log_file in log_files:
            if log_file.exists():
                try:
                    # Use tail to get recent lines
                    tail_result = subprocess.run(
                        ["tail", "-n", str(lines), str(log_file)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if tail_result.stdout:
                        result.append(f"=== {log_file.name} ===")
                        result.append(tail_result.stdout.strip())
                    else:
                        result.append(f"=== {log_file.name} === (empty or no recent entries)")
                except subprocess.TimeoutExpired:
                    result.append(f"=== {log_file.name} === (timeout reading file)")
                except Exception as e:
                    result.append(f"=== {log_file.name} === (error: {str(e)})")
        
        return "\n\n".join(result) if result else "No log entries found"
        
    except Exception as e:
        return f"Error reading logs: {str(e)}"

@mcp.tool()
def list_claude_logs() -> str:
    """List all available Claude Desktop log files.
    
    Returns:
        List of log files with their sizes and modification times
    """
    try:
        from pathlib import Path
        
        log_dir = Path.home() / "Library" / "Logs" / "Claude"
        
        if not log_dir.exists():
            return "Claude log directory not found. Are you on macOS?"
        
        log_files = list(log_dir.glob("*.log"))
        
        if not log_files:
            return "No log files found in Claude directory"
        
        result = ["Claude Desktop Log Files:"]
        for log_file in sorted(log_files):
            try:
                stat = log_file.stat()
                size_mb = stat.st_size / (1024 * 1024)
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                result.append(f"  {log_file.name} - {size_mb:.2f}MB - Modified: {modified}")
            except Exception as e:
                result.append(f"  {log_file.name} - Error reading: {str(e)}")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error listing logs: {str(e)}"

@mcp.tool()
def watch_breathsmith_changes(enable: bool = True) -> str:
    """Enable or disable file watching for hot reloading (experimental).
    
    Args:
        enable: Whether to enable file watching
        
    Returns:
        Status message about file watching
    """
    # For now, just return info about manual restart
    # Hot reloading would require more complex implementation
    if enable:
        return (
            "File watching not yet implemented. For now, restart Claude Desktop manually after changes.\n"
            "To implement hot reloading, you would need to:\n"
            "1. Use watchdog library to monitor breathsmith.py\n"
            "2. Signal Claude Desktop to restart the MCP server\n"
            "3. Handle graceful shutdown/restart without breaking connections\n\n"
            "Current workflow: Edit code -> Save -> Restart Claude Desktop"
        )
    else:
        return "File watching disabled (was not active anyway)"

@mcp.tool()
def uv_command(command: str, directory: Optional[str] = None, timeout: int = 60) -> str:
    """Run UV commands like sync, add, run, etc.
    
    Args:
        command: The uv command to run (without 'uv' prefix)
        directory: Optional directory to run the command in (defaults to current directory)
        timeout: Timeout in seconds (default: 60)
        
    Returns:
        Command output and exit status
        
    Examples:
        - uv_command("--version") - Check UV version
        - uv_command("sync") - Install/sync dependencies  
        - uv_command("add requests") - Add a package
        - uv_command("remove requests") - Remove a package
        - uv_command("pip list") - List installed packages
        - uv_command("run script.py") - Run a Python script
        - uv_command("run -m json.tool --help") - Run a Python module
        
    Notes:
        - Don't include 'uv' in the command - it's added automatically
        - For 'uv run python -c', complex quoting may not work - use scripts instead
        - Long-running commands (like servers) will timeout after specified seconds
        - Both stdout and stderr are captured and returned
    """
    try:
        # Basic safety check - only allow uv commands
        if not command.strip():
            return "Error: Empty command provided"
            
        # Split command into parts
        cmd_parts = ["uv"] + command.split()
        
        # Set working directory
        cwd = directory if directory else os.getcwd()
        if directory and not os.path.exists(directory):
            return f"Error: Directory '{directory}' does not exist"
            
        # Run the command
        result = subprocess.run(
            cmd_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output_parts = []
        output_parts.append(f"Command: uv {command}")
        output_parts.append(f"Directory: {cwd}")
        output_parts.append(f"Exit code: {result.returncode}")
        
        if result.stdout:
            output_parts.append(f"\nSTDOUT:\n{result.stdout.strip()}")
            
        if result.stderr:
            output_parts.append(f"\nSTDERR:\n{result.stderr.strip()}")
            
        return "\n".join(output_parts)
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return "Error: 'uv' command not found. Is UV installed?"
    except Exception as e:
        return f"Error running uv command: {str(e)}"

@mcp.tool()
def npm_command(command: str, directory: Optional[str] = None, timeout: int = 60) -> str:
    """Run npm commands like install, run, test, etc.
    
    Args:
        command: The npm command to run (without 'npm' prefix)
        directory: Optional directory to run the command in (defaults to current directory)
        timeout: Timeout in seconds (default: 60)
        
    Returns:
        Command output and exit status
        
    Examples:
        - npm_command("--version") - Check npm version
        - npm_command("install") - Install dependencies from package.json
        - npm_command("install express") - Install a specific package
        - npm_command("install --save-dev jest") - Install dev dependency
        - npm_command("uninstall lodash") - Remove a package
        - npm_command("run build") - Run build script
        - npm_command("run test") - Run test script
        - npm_command("list --depth=0") - List installed packages
        - npm_command("outdated") - Check for outdated packages
        - npm_command("audit") - Run security audit
        - npm_command("init -y") - Initialize new package.json
        
    Notes:
        - Don't include 'npm' in the command - it's added automatically
        - Commands are run in the specified directory or current working directory
        - Will automatically detect and use package.json in the target directory
        - Long-running commands (like dev servers) will timeout after specified seconds
        - Both stdout and stderr are captured and returned
        - For global installs, use "install -g package-name"
    """
    try:
        # Basic safety check - only allow npm commands
        if not command.strip():
            return "Error: Empty command provided"
            
        # Split command into parts
        cmd_parts = ["npm"] + command.split()
        
        # Set working directory
        cwd = directory if directory else os.getcwd()
        if directory and not os.path.exists(directory):
            return f"Error: Directory '{directory}' does not exist"
            
        # Check if package.json exists in target directory (helpful info)
        package_json_path = Path(cwd) / "package.json"
        has_package_json = package_json_path.exists()
        
        # Run the command
        result = subprocess.run(
            cmd_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output_parts = []
        output_parts.append(f"Command: npm {command}")
        output_parts.append(f"Directory: {cwd}")
        output_parts.append(f"Package.json present: {has_package_json}")
        output_parts.append(f"Exit code: {result.returncode}")
        
        if result.stdout:
            output_parts.append(f"\nSTDOUT:\n{result.stdout.strip()}")
            
        if result.stderr:
            output_parts.append(f"\nSTDERR:\n{result.stderr.strip()}")
            
        return "\n".join(output_parts)
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return "Error: 'npm' command not found. Is Node.js/npm installed?"
    except Exception as e:
        return f"Error running npm command: {str(e)}"

@mcp.tool()
def npx_command(command: str, directory: Optional[str] = None, timeout: int = 60) -> str:
    """Run npx commands to execute packages without installing them globally.
    
    Args:
        command: The npx command to run (without 'npx' prefix)
        directory: Optional directory to run the command in (defaults to current directory)
        timeout: Timeout in seconds (default: 60)
        
    Returns:
        Command output and exit status
        
    Examples:
        - npx_command("--version") - Check npx version
        - npx_command("create-react-app my-app") - Create React app
        - npx_command("typescript --init") - Initialize TypeScript config
        - npx_command("eslint --init") - Initialize ESLint config
        - npx_command("prettier --write .") - Format files with Prettier
        - npx_command("json-server --watch db.json") - Run JSON server
        - npx_command("serve build") - Serve a build directory
        - npx_command("cowsay hello world") - Run any npm package temporarily
        - npx_command("@angular/cli new my-app") - Use scoped packages
        - npx_command("degit user/repo my-project") - Clone git repos
        
    Notes:
        - Don't include 'npx' in the command - it's added automatically
        - Commands are run in the specified directory or current working directory
        - npx automatically downloads and runs packages if not locally installed
        - Long-running commands (like dev servers) will timeout after specified seconds
        - Both stdout and stderr are captured and returned
        - Use for one-time package execution or scaffolding tools
    """
    try:
        # Basic safety check - only allow npx commands
        if not command.strip():
            return "Error: Empty command provided"
            
        # Split command into parts
        cmd_parts = ["npx"] + command.split()
        
        # Set working directory
        cwd = directory if directory else os.getcwd()
        if directory and not os.path.exists(directory):
            return f"Error: Directory '{directory}' does not exist"
            
        # Check if package.json exists in target directory (helpful info)
        package_json_path = Path(cwd) / "package.json"
        has_package_json = package_json_path.exists()
        
        # Check if node_modules exists (indicates local packages available)
        node_modules_path = Path(cwd) / "node_modules"
        has_node_modules = node_modules_path.exists()
        
        # Run the command
        result = subprocess.run(
            cmd_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output_parts = []
        output_parts.append(f"Command: npx {command}")
        output_parts.append(f"Directory: {cwd}")
        output_parts.append(f"Package.json present: {has_package_json}")
        output_parts.append(f"Node_modules present: {has_node_modules}")
        output_parts.append(f"Exit code: {result.returncode}")
        
        if result.stdout:
            output_parts.append(f"\nSTDOUT:\n{result.stdout.strip()}")
            
        if result.stderr:
            output_parts.append(f"\nSTDERR:\n{result.stderr.strip()}")
            
        return "\n".join(output_parts)
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return "Error: 'npx' command not found. Is Node.js/npm installed?"
    except Exception as e:
        return f"Error running npx command: {str(e)}"

@mcp.tool()
def yarn_command(command: str, directory: Optional[str] = None, timeout: int = 60) -> str:
    """Run Yarn commands for package management and script execution.
    
    Args:
        command: The yarn command to run (without 'yarn' prefix)
        directory: Optional directory to run the command in (defaults to current directory)
        timeout: Timeout in seconds (default: 60)
        
    Returns:
        Command output and exit status
        
    Examples:
        - yarn_command("--version") - Check Yarn version
        - yarn_command("install") or yarn_command("") - Install dependencies
        - yarn_command("add express") - Add a package
        - yarn_command("add --dev jest") - Add dev dependency
        - yarn_command("remove lodash") - Remove a package
        - yarn_command("run build") - Run build script
        - yarn_command("test") - Run test script (shorthand)
        - yarn_command("list --depth=0") - List installed packages
        - yarn_command("outdated") - Check for outdated packages
        - yarn_command("audit") - Run security audit
        - yarn_command("init -y") - Initialize new package.json
        - yarn_command("upgrade") - Upgrade all packages
        - yarn_command("global add create-react-app") - Global package install
        
    Notes:
        - Don't include 'yarn' in the command - it's added automatically
        - Empty command defaults to 'yarn install'
        - Commands are run in the specified directory or current working directory
        - Will automatically detect yarn.lock and package.json files
        - Long-running commands (like dev servers) will timeout after specified seconds
        - Both stdout and stderr are captured and returned
        - Supports both Yarn 1.x and Yarn 2+ (Berry) commands
    """
    try:
        # Basic safety check
        if command is None:
            command = ""
        command = command.strip()
        
        # Empty command defaults to install
        if not command:
            cmd_parts = ["yarn"]
        else:
            cmd_parts = ["yarn"] + command.split()
        
        # Set working directory
        cwd = directory if directory else os.getcwd()
        if directory and not os.path.exists(directory):
            return f"Error: Directory '{directory}' does not exist"
            
        # Check project files
        package_json_path = Path(cwd) / "package.json"
        has_package_json = package_json_path.exists()
        
        yarn_lock_path = Path(cwd) / "yarn.lock"
        has_yarn_lock = yarn_lock_path.exists()
        
        node_modules_path = Path(cwd) / "node_modules"
        has_node_modules = node_modules_path.exists()
        
        # Check for Yarn version (helps identify Yarn 1 vs 2+)
        yarn_version = "unknown"
        try:
            version_result = subprocess.run(
                ["yarn", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if version_result.returncode == 0:
                yarn_version = version_result.stdout.strip()
        except:
            pass
        
        # Run the command
        result = subprocess.run(
            cmd_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output_parts = []
        display_command = "yarn" if not command else f"yarn {command}"
        output_parts.append(f"Command: {display_command}")
        output_parts.append(f"Directory: {cwd}")
        output_parts.append(f"Yarn version: {yarn_version}")
        output_parts.append(f"Package.json present: {has_package_json}")
        output_parts.append(f"Yarn.lock present: {has_yarn_lock}")
        output_parts.append(f"Node_modules present: {has_node_modules}")
        output_parts.append(f"Exit code: {result.returncode}")
        
        if result.stdout:
            output_parts.append(f"\nSTDOUT:\n{result.stdout.strip()}")
            
        if result.stderr:
            output_parts.append(f"\nSTDERR:\n{result.stderr.strip()}")
            
        return "\n".join(output_parts)
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return "Error: 'yarn' command not found. Is Yarn installed? Install with: npm install -g yarn"
    except Exception as e:
        return f"Error running yarn command: {str(e)}"

@mcp.tool()
def bun_command(command: str, directory: Optional[str] = None, timeout: int = 60) -> str:
    """Run Bun commands for ultra-fast package management and JavaScript execution.
    
    Args:
        command: The bun command to run (without 'bun' prefix)
        directory: Optional directory to run the command in (defaults to current directory)
        timeout: Timeout in seconds (default: 60)
        
    Returns:
        Command output and exit status
        
    Examples:
        - bun_command("--version") - Check Bun version
        - bun_command("install") or bun_command("i") - Install dependencies
        - bun_command("add express") - Add a package
        - bun_command("add --dev jest") - Add dev dependency
        - bun_command("remove lodash") - Remove a package
        - bun_command("run build") - Run build script
        - bun_command("test") - Run tests with Bun's built-in test runner
        - bun_command("dev") - Run development script
        - bun_command("create react-app my-app") - Scaffold new projects
        - bun_command("outdated") - Check for outdated packages
        - bun_command("init") - Initialize new project
        - bun_command("upgrade") - Upgrade all packages
        - bun_command("link") - Link package for development
        - bun_command("run --watch script.js") - Run with file watching
        - bun_command("build ./index.ts") - Build/bundle files
        
    Notes:
        - Don't include 'bun' in the command - it's added automatically
        - Commands are run in the specified directory or current working directory
        - Will automatically detect bun.lockb, package.json, and node_modules
        - Bun is much faster than npm/yarn for package operations
        - Supports running TypeScript files directly without compilation
        - Long-running commands (like dev servers) will timeout after specified seconds
        - Both stdout and stderr are captured and returned
    """
    try:
        # Basic safety check
        if not command.strip():
            return "Error: Empty command provided"
            
        # Split command into parts - but first try to find bun in common locations
        bun_executable = "bun"
        
        # Check common bun installation paths if bun is not in PATH
        try:
            subprocess.run(["bun"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Try common bun installation locations
            common_bun_paths = [
                os.path.expanduser("~/.bun/bin/bun"),
                "/usr/local/bin/bun",
                "/opt/homebrew/bin/bun",
            ]
            
            for bun_path in common_bun_paths:
                if os.path.exists(bun_path):
                    bun_executable = bun_path
                    break
        
        cmd_parts = [bun_executable] + command.split()
        
        # Set working directory
        cwd = directory if directory else os.getcwd()
        if directory and not os.path.exists(directory):
            return f"Error: Directory '{directory}' does not exist"
            
        # Check project files
        package_json_path = Path(cwd) / "package.json"
        has_package_json = package_json_path.exists()
        
        bun_lockb_path = Path(cwd) / "bun.lockb"
        has_bun_lockb = bun_lockb_path.exists()
        
        node_modules_path = Path(cwd) / "node_modules"
        has_node_modules = node_modules_path.exists()
        
        # Check for other lock files that might conflict
        yarn_lock_path = Path(cwd) / "yarn.lock"
        package_lock_path = Path(cwd) / "package-lock.json"
        has_other_locks = yarn_lock_path.exists() or package_lock_path.exists()
        
        # Check Bun version
        bun_version = "unknown"
        try:
            version_result = subprocess.run(
                [bun_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if version_result.returncode == 0:
                bun_version = version_result.stdout.strip()
        except:
            pass
        
        # Run the command
        result = subprocess.run(
            cmd_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output_parts = []
        output_parts.append(f"Command: bun {command}")
        output_parts.append(f"Directory: {cwd}")
        output_parts.append(f"Bun version: {bun_version}")
        output_parts.append(f"Package.json present: {has_package_json}")
        output_parts.append(f"Bun.lockb present: {has_bun_lockb}")
        output_parts.append(f"Node_modules present: {has_node_modules}")
        if has_other_locks:
            output_parts.append(f"⚠️ Other lock files detected (yarn.lock/package-lock.json)")
        output_parts.append(f"Exit code: {result.returncode}")
        
        if result.stdout:
            output_parts.append(f"\nSTDOUT:\n{result.stdout.strip()}")
            
        if result.stderr:
            output_parts.append(f"\nSTDERR:\n{result.stderr.strip()}")
            
        return "\n".join(output_parts)
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return "Error: 'bun' command not found. Is Bun installed? Install from: https://bun.sh"
    except Exception as e:
        return f"Error running bun command: {str(e)}"

@mcp.tool()
def sqlite_execute(database_path: str, query: str, params: Optional[List] = None, fetch_results: bool = True) -> str:
    """Execute SQLite queries and return results.
    
    Args:
        database_path: Path to the SQLite database file
        query: SQL query to execute
        params: Optional list of parameters for parameterized queries
        fetch_results: Whether to fetch and return results (default: True)
        
    Returns:
        Query results as formatted text or execution status
        
    Examples:
        - sqlite_execute("data.db", "SELECT * FROM users LIMIT 5") - Query data
        - sqlite_execute("data.db", "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)") - Create table
        - sqlite_execute("data.db", "INSERT INTO users (name) VALUES (?)", ["Alice"]) - Insert with params
        - sqlite_execute("data.db", "SELECT COUNT(*) FROM users") - Count rows
        - sqlite_execute("data.db", ".schema users", fetch_results=False) - Get table schema
        
    Notes:
        - Database file will be created if it doesn't exist
        - Use parameterized queries (?) for safe data insertion
        - Set fetch_results=False for CREATE, INSERT, UPDATE, DELETE operations
        - Results are limited to 1000 rows for performance
        - Use PRAGMA statements to configure database settings
    """
    try:
        # Validate database path
        db_path = Path(database_path)
        if not db_path.is_absolute():
            # Make relative paths relative to current working directory
            db_path = Path.cwd() / db_path
            
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Execute query with optional parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Handle different types of queries
            if fetch_results and query.strip().upper().startswith(('SELECT', 'PRAGMA', 'EXPLAIN')):
                # Fetch results for queries that return data
                rows = cursor.fetchmany(1000)  # Limit to 1000 rows
                
                if not rows:
                    return f"Query executed successfully. No rows returned.\nDatabase: {db_path}"
                
                # Format results as a table
                columns = [description[0] for description in cursor.description]
                result_lines = []
                result_lines.append(f"Database: {db_path}")
                result_lines.append(f"Rows returned: {len(rows)}")
                result_lines.append("")
                
                # Add column headers
                header = " | ".join(columns)
                result_lines.append(header)
                result_lines.append("-" * len(header))
                
                # Add data rows
                for row in rows:
                    row_data = [str(row[col]) if row[col] is not None else 'NULL' for col in columns]
                    result_lines.append(" | ".join(row_data))
                
                # Check if there might be more rows
                if len(rows) == 1000:
                    result_lines.append("")
                    result_lines.append("Note: Results limited to 1000 rows. Use LIMIT/OFFSET for pagination.")
                
                return "\n".join(result_lines)
            
            else:
                # For INSERT, UPDATE, DELETE, CREATE, etc.
                conn.commit()
                affected_rows = cursor.rowcount
                
                result_lines = []
                result_lines.append(f"Query executed successfully.")
                result_lines.append(f"Database: {db_path}")
                
                if affected_rows >= 0:
                    result_lines.append(f"Rows affected: {affected_rows}")
                
                # For INSERT operations, show the last inserted row ID
                if query.strip().upper().startswith('INSERT') and cursor.lastrowid:
                    result_lines.append(f"Last inserted row ID: {cursor.lastrowid}")
                
                return "\n".join(result_lines)
                
    except sqlite3.Error as e:
        return f"SQLite error: {str(e)}\nDatabase: {database_path}\nQuery: {query}"
    except Exception as e:
        return f"Error executing SQLite query: {str(e)}\nDatabase: {database_path}"

@mcp.tool()
def sqlite_info(database_path: str) -> str:
    """Get information about a SQLite database structure.
    
    Args:
        database_path: Path to the SQLite database file
        
    Returns:
        Database schema information and table details
        
    Examples:
        - sqlite_info("data.db") - Get complete database structure
        
    Notes:
        - Shows all tables, their schemas, and row counts
        - Useful for exploring unknown databases
        - Returns empty result if database doesn't exist
    """
    try:
        db_path = Path(database_path)
        if not db_path.is_absolute():
            db_path = Path.cwd() / db_path
            
        if not db_path.exists():
            return f"Database does not exist: {db_path}"
            
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            result_lines = []
            result_lines.append(f"Database: {db_path}")
            result_lines.append(f"File size: {db_path.stat().st_size / 1024:.2f} KB")
            result_lines.append("")
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            
            if not tables:
                result_lines.append("No tables found in database.")
                return "\n".join(result_lines)
                
            result_lines.append(f"Tables ({len(tables)}):")
            result_lines.append("="*50)
            
            for (table_name,) in tables:
                result_lines.append(f"\nTable: {table_name}")
                result_lines.append("-" * (7 + len(table_name)))
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                result_lines.append("Columns:")
                for col in columns:
                    cid, name, col_type, notnull, default, pk = col
                    pk_marker = " (PK)" if pk else ""
                    null_marker = " NOT NULL" if notnull else ""
                    default_marker = f" DEFAULT {default}" if default else ""
                    result_lines.append(f"  {name}: {col_type}{pk_marker}{null_marker}{default_marker}")
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                result_lines.append(f"Rows: {row_count}")
                
                # Get indexes
                cursor.execute(f"PRAGMA index_list({table_name})")
                indexes = cursor.fetchall()
                if indexes:
                    result_lines.append("Indexes:")
                    for idx in indexes:
                        result_lines.append(f"  {idx[1]} ({'UNIQUE' if idx[2] else 'NON-UNIQUE'})")
            
            return "\n".join(result_lines)
            
    except sqlite3.Error as e:
        return f"SQLite error: {str(e)}\nDatabase: {database_path}"
    except Exception as e:
        return f"Error getting database info: {str(e)}\nDatabase: {database_path}"

@mcp.tool() 
def debug_mcp_connection() -> str:
    """Get information about the current MCP server connection.
    
    Returns:
        Debug information about the server state
    """
    try:
        import sys
        import os
        from pathlib import Path
        
        info = []
        info.append(f"Python version: {sys.version}")
        info.append(f"Current working directory: {os.getcwd()}")
        info.append(f"Server file: {__file__ if '__file__' in globals() else 'Unknown'}")
        info.append(f"Process ID: {os.getpid()}")
        
        # Check if we're in the right directory
        breathsmith_dir = Path(os.getenv('BREATHSMITH_DIR'))
        info.append(f"Breathsmith directory exists: {breathsmith_dir.exists()}")
        
        if breathsmith_dir.exists():
            files = list(breathsmith_dir.glob("*"))
            info.append(f"Files in breathsmith directory: {[f.name for f in files]}")
        
        # Check environment
        has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
        info.append(f"OpenAI API key present: {has_openai_key}")
        
        return "\n".join(info)
        
    except Exception as e:
        return f"Error getting debug info: {str(e)}"

if __name__ == "__main__":
    mcp.run()
