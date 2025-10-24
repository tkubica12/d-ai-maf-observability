#!/usr/bin/env python3
"""
Build and push Docker images to Azure Container Registry using ACR remote build tasks.

This script builds Docker images for the API and MCP tools using ACR remote build tasks,
tags them with sequential versioning (v1, v2, etc.), and updates the Terraform variables file.
"""

import os
import re
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Tuple

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv package is required. Install with: pip install python-dotenv")
    sys.exit(1)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_colored(message: str, color: str = Colors.RESET) -> None:
    """Print a colored message to the terminal."""
    print(f"{color}{message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print an error message and exit."""
    print_colored(f"❌ {message}", Colors.RED)
    sys.exit(1)


def print_success(message: str) -> None:
    """Print a success message."""
    print_colored(f"✅ {message}", Colors.GREEN)


def print_info(message: str) -> None:
    """Print an info message."""
    print_colored(f"🚀 {message}", Colors.GREEN)


def print_warning(message: str) -> None:
    """Print a warning message."""
    print_colored(f"📄 {message}", Colors.YELLOW)


def run_command(command: list, capture_output: bool = True) -> Tuple[bool, str]:
    """
    Run a shell command and return success status and output.
    
    Args:
        command: Command and arguments as a list
        capture_output: Whether to capture the output
        
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        if capture_output:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                shell=True  # Required on Windows for az command
            )
            return result.returncode == 0, result.stdout.strip()
        else:
            result = subprocess.run(command, check=False, shell=True)
            return result.returncode == 0, ""
    except Exception as e:
        return False, str(e)


def get_next_version(current_version: str) -> str:
    """
    Get the next version number in sequence.
    
    Args:
        current_version: Current version string (e.g., "v1", "v2")
        
    Returns:
        Next version string
    """
    match = re.match(r'^v(\d+)$', current_version)
    if match:
        number = int(match.group(1))
        return f"v{number + 1}"
    return "v1"


def read_current_versions(tfvars_file: Path) -> Dict[str, str]:
    """
    Read current image versions from the Terraform variables file.
    
    Args:
        tfvars_file: Path to the images.auto.tfvars file
        
    Returns:
        Dictionary with current versions
    """
    versions = {
        "api_tool_image_tag": "v1",
        "mcp_tool_image_tag": "v1"
    }
    
    if tfvars_file.exists():
        print_warning(f"Reading current versions from {tfvars_file}")
        
        try:
            content = tfvars_file.read_text(encoding='utf-8')
            
            # Extract API tool version
            api_match = re.search(r'api_tool_image_tag\s*=\s*"([^"]+)"', content)
            if api_match:
                versions["api_tool_image_tag"] = api_match.group(1)
            
            # Extract MCP tool version
            mcp_match = re.search(r'mcp_tool_image_tag\s*=\s*"([^"]+)"', content)
            if mcp_match:
                versions["mcp_tool_image_tag"] = mcp_match.group(1)
            
            print_colored(f"Current API tool version: {versions['api_tool_image_tag']}", Colors.CYAN)
            print_colored(f"Current MCP tool version: {versions['mcp_tool_image_tag']}", Colors.CYAN)
            
        except Exception as e:
            print_error(f"Failed to read versions file: {e}")
    else:
        print_warning("No existing versions file found, starting with v1")
    
    return versions


def write_new_versions(tfvars_file: Path, api_version: str, mcp_version: str) -> None:
    """
    Write new image versions to the Terraform variables file.
    
    Args:
        tfvars_file: Path to the images.auto.tfvars file
        api_version: New API tool version
        mcp_version: New MCP tool version
    """
    content = f'''api_tool_image_tag = "{api_version}"
mcp_tool_image_tag = "{mcp_version}"
'''
    
    print_warning(f"Writing new versions to {tfvars_file}")
    print_colored(f"  API tool version: {api_version}", Colors.CYAN)
    print_colored(f"  MCP tool version: {mcp_version}", Colors.CYAN)
    
    try:
        tfvars_file.write_text(content, encoding='utf-8')
    except Exception as e:
        print_error(f"Failed to write versions file: {e}")


def build_acr_image(image_name: str, tag: str, source_path: Path, 
                   resource_group: str, registry: str) -> bool:
    """
    Build an image using ACR remote build task.
    
    Args:
        image_name: Name of the Docker image
        tag: Image tag
        source_path: Path to the source code
        resource_group: Azure resource group name
        registry: ACR registry name
        
    Returns:
        True if build was successful, False otherwise
    """
    print_info(f"Building {image_name}:{tag} using ACR remote build...")
    print_colored(f"Source path: {source_path}", Colors.GRAY)
    
    command = [
        "az", "acr", "build",
        "--registry", registry,
        "--resource-group", resource_group,
        "--image", f"{image_name}:{tag}",
        str(source_path),
        "--no-logs"
    ]
    
    success, output = run_command(command)
    
    if success:
        print_success(f"Successfully built {image_name}:{tag}")
        return True
    else:
        print_error(f"Failed to build {image_name}:{tag}. Error: {output}")
        return False


def check_azure_cli() -> None:
    """Check if Azure CLI is installed and user is logged in."""
    # Check if Azure CLI is installed
    success, output = run_command(["az", "version", "--output", "json"])
    if not success:
        print_error("Azure CLI is not installed or not working properly. Please install Azure CLI and login.")
    
    try:
        version_info = json.loads(output)
        print_success(f"Azure CLI version: {version_info.get('azure-cli', 'unknown')}")
    except Exception:
        print_error("Failed to parse Azure CLI version information.")
    
    # Check if user is logged in
    success, output = run_command(["az", "account", "show", "--output", "json"])
    if not success:
        print_error("Not logged in to Azure. Please run 'az login' first.")
    
    try:
        account_info = json.loads(output)
        user_name = account_info.get('user', {}).get('name', 'unknown')
        print_success(f"Logged in as: {user_name}")
    except Exception:
        print_error("Failed to parse Azure account information.")


def verify_acr(acr_name: str, resource_group: str) -> str:
    """
    Verify that the ACR exists and return its login server.
    
    Args:
        acr_name: Name of the ACR
        resource_group: Resource group name
        
    Returns:
        ACR login server URL
    """
    success, output = run_command([
        "az", "acr", "show",
        "--name", acr_name,
        "--resource-group", resource_group,
        "--output", "json"
    ])
    
    if not success:
        print_error(f"Could not find ACR '{acr_name}' in resource group '{resource_group}'")
    
    try:
        acr_info = json.loads(output)
        login_server = acr_info.get('loginServer')
        print_success(f"Found ACR: {login_server}")
        return login_server
    except Exception:
        print_error("Failed to parse ACR information.")


def main():
    """Main function."""
    # Load environment variables
    script_dir = Path(__file__).parent
    env_file = script_dir / ".env"
    
    if not env_file.exists():
        print_error(f"Environment file not found: {env_file}")
    
    load_dotenv(env_file)
    
    # Get configuration from environment
    resource_group = os.getenv("AZURE_RESOURCE_GROUP_NAME")
    acr_name = os.getenv("AZURE_ACR_NAME")
    
    if not resource_group:
        print_error("AZURE_RESOURCE_GROUP_NAME not found in .env file")
    
    if not acr_name:
        print_error("AZURE_ACR_NAME not found in .env file")
    
    # Define paths
    root_dir = script_dir.parent
    terraform_dir = root_dir / "infra"
    images_vars_file = terraform_dir / "images.auto.tfvars"
    api_source_dir = root_dir / "src" / "api_server"
    mcp_source_dir = root_dir / "src" / "mcp_server"
    
    print_info("Starting build and push process...")
    print_colored(f"Resource Group: {resource_group}", Colors.CYAN)
    print_colored(f"ACR Name: {acr_name}", Colors.CYAN)
    
    # Verify prerequisites
    check_azure_cli()
    verify_acr(acr_name, resource_group)
    
    # Get current versions and calculate next versions
    current_versions = read_current_versions(images_vars_file)
    new_api_version = get_next_version(current_versions["api_tool_image_tag"])
    new_mcp_version = get_next_version(current_versions["mcp_tool_image_tag"])
    
    print()
    print_colored("🏷️  Version Update Plan:", Colors.MAGENTA)
    print_colored(f"  API tool: {current_versions['api_tool_image_tag']} → {new_api_version}", Colors.CYAN)
    print_colored(f"  MCP tool: {current_versions['mcp_tool_image_tag']} → {new_mcp_version}", Colors.CYAN)
    print()
    
    # Build API tool image
    api_success = build_acr_image(
        "api-tool", new_api_version, api_source_dir, 
        resource_group, acr_name
    )
    
    if not api_success:
        print_error("Failed to build API tool image")
    
    # Build MCP tool image
    mcp_success = build_acr_image(
        "mcp-tool", new_mcp_version, mcp_source_dir,
        resource_group, acr_name
    )
    
    if not mcp_success:
        print_error("Failed to build MCP tool image")
    
    # Update the tfvars file with new versions
    write_new_versions(images_vars_file, new_api_version, new_mcp_version)
    
    print()
    print_success("Build and push completed successfully!")
    print_success(f"Updated {images_vars_file} with new image tags")
    print_colored("💡 Next steps:", Colors.YELLOW)
    print_colored("   1. Run 'terraform plan' to see the deployment changes", Colors.GRAY)
    print_colored("   2. Run 'terraform apply' to deploy the new images", Colors.GRAY)
    print()


if __name__ == "__main__":
    main()