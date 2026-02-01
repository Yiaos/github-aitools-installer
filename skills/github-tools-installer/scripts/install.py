#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from pathlib import Path

# Configuration
TOOLS_DIR = Path("~/.config/opencode/tools").expanduser()
OPENCODE_DIR = Path("~/.config/opencode").expanduser()
CODEX_DIR = Path("~/.codex").expanduser()
GEMINI_DIR = Path("~/.gemini").expanduser()

# Mapping: Source Folder Name -> [List of Target Destination Paths]
# Only creating links if the source folder exists in the cloned repo
FOLDERS_TO_LINK = {
    "skills": [
        OPENCODE_DIR / "skills",
        CODEX_DIR / "skills",
        GEMINI_DIR / "skills"
    ],
    "agents": [
        OPENCODE_DIR / "agents",
        # Assuming Codex/Gemini might support agents in the future or standard paths
        # CODEX_DIR / "agents", 
    ],
    "commands": [
        OPENCODE_DIR / "commands"
    ],
    "plugins": [
        OPENCODE_DIR / "plugins"
    ],
    "hooks": [
        OPENCODE_DIR / "hooks"
    ],
    "mcp": [
        OPENCODE_DIR / "mcp"
    ],
    "prompts": [
        OPENCODE_DIR / "prompts"
    ]
}

def run_command(cmd, cwd=None):
    try:
        subprocess.check_call(cmd, shell=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}\n{e}")
        return False
    return True

def install_tool(repo_url, name=None):
    if not name:
        name = repo_url.split("/")[-1].replace(".git", "")
    
    target_dir = TOOLS_DIR / name
    
    print(f"🔧 Installing {name} from {repo_url}...")
    
    # 1. Prepare Tools Directory
    if not TOOLS_DIR.exists():
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Clone or Update
    if target_dir.exists():
        print(f"  - Directory {target_dir} exists. Updating...")
        if not run_command("git pull", cwd=target_dir):
            return
    else:
        print(f"  - Cloning to {target_dir}...")
        if not run_command(f"git clone {repo_url} {target_dir}"):
            return

    # 3. Create Symlinks
    print("  - Linking components...")
    for folder, dest_parents in FOLDERS_TO_LINK.items():
        source_path = target_dir / folder
        
        # Check if the repo actually has this folder (e.g. does it have a 'skills' folder?)
        if not source_path.exists():
            continue
            
        print(f"    found '{folder}', linking...")
        
        for parent in dest_parents:
            # Create config dir if not exists (e.g. ~/.codex/skills)
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
            
            link_name = parent / name
            
            # Remove existing link/file if it exists to ensure freshness
            if link_name.is_symlink() or link_name.is_file():
                link_name.unlink()
            elif link_name.is_dir():
                # If it's a real directory, back it up and replace with link
                timestamp = int(os.path.getmtime(link_name))
                backup_name = link_name.with_suffix(f".bak.{timestamp}")
                print(f"    ⚠️  Target {link_name} is a real directory.")
                print(f"    🔄 Moving it to backup: {backup_name}")
                shutil.move(str(link_name), str(backup_name))
            
            # Create Symlink
            # source_path is absolute? Yes.
            os.symlink(source_path, link_name)
            print(f"      -> Linked to {link_name}")

    print(f"✅ Successfully installed {name}!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: install.py <repo_url> [name]")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    
    install_tool(repo_url, name)
