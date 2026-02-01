#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

# Configuration
TOOLS_DIR = Path("~/.config/opencode/tools").expanduser()
OPENCODE_DIR = Path("~/.config/opencode").expanduser()
CODEX_DIR = Path("~/.codex").expanduser()
GEMINI_DIR = Path("~/.gemini").expanduser()

FOLDERS_TO_LINK = {
    "skills": [OPENCODE_DIR / "skills", CODEX_DIR / "skills", GEMINI_DIR / "skills"],
    "agents": [OPENCODE_DIR / "agents"],
    "commands": [OPENCODE_DIR / "commands"],
    "plugins": [OPENCODE_DIR / "plugins"],
    "hooks": [OPENCODE_DIR / "hooks"],
    "mcp": [OPENCODE_DIR / "mcp"],
    "prompts": [OPENCODE_DIR / "prompts"]
}

def run_command(cmd, cwd=None, quiet=False):
    try:
        kwargs = {}
        if quiet:
            kwargs['stdout'] = subprocess.DEVNULL
            kwargs['stderr'] = subprocess.DEVNULL
        subprocess.check_call(cmd, shell=True, cwd=cwd, **kwargs)
    except subprocess.CalledProcessError as e:
        if not quiet:
            print(f"Error running command: {cmd}\n{e}")
        return False
    return True

def get_tool_description(dir_path):
    """Attempt to read description from README.md or SKILL.md"""
    desc = "No description available."
    for readme in ["README.md", "README_CN.md", "SKILL.md", "README.txt"]:
        readme_path = dir_path / readme
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Determine start
                    content_start = 0
                    if lines and lines[0].strip() == "---": # Skip frontmatter
                        for i in range(1, len(lines)):
                            if lines[i].strip() == "---":
                                content_start = i + 1
                                break
                    
                    # Get first non-empty paragraph
                    paragraph = []
                    for line in lines[content_start:]:
                        line = line.strip()
                        if line:
                            paragraph.append(line)
                        elif paragraph: # End of paragraph
                            break
                    
                    if paragraph:
                        # Limit to ~200 chars
                        full_text = " ".join(paragraph)
                        return full_text[:200] + "..." if len(full_text) > 200 else full_text
            except Exception:
                pass
    return desc

def link_directory(target_dir, name):
    linked_components = []
    
    for folder, dest_parents in FOLDERS_TO_LINK.items():
        source_path = target_dir / folder
        if not source_path.exists():
            continue
            
        for parent in dest_parents:
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
            
            link_name = parent / name
            
            if link_name.is_symlink() or link_name.is_file():
                link_name.unlink()
            elif link_name.is_dir():
                timestamp = int(os.path.getmtime(link_name))
                backup_name = link_name.with_suffix(f".bak.{timestamp}")
                print(f"    ⚠️  Target {link_name} is a real directory.")
                print(f"    🔄 Moving it to backup: {backup_name}")
                shutil.move(str(link_name), str(backup_name))
            
            os.symlink(source_path, link_name)
        
        linked_components.append(folder)
    
    return linked_components

def install_tool(repo_url, name=None):
    # Handle short GitHub format "user/repo"
    if not repo_url.startswith("http") and not repo_url.startswith("git@") and "/" in repo_url:
        repo_url = f"https://github.com/{repo_url}.git"
        
    if not name:
        name = repo_url.split("/")[-1].replace(".git", "")
    
    target_dir = TOOLS_DIR / name
    print(f"🔧 Processing {name}...")
    
    is_new = False
    if not TOOLS_DIR.exists():
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    
    if target_dir.exists():
        print(f"  ⬇️  Updating (git pull)...")
        if not run_command("git pull", cwd=target_dir):
            return
    else:
        print(f"  ⬇️  Cloning from {repo_url}...")
        is_new = True
        if not run_command(f"git clone {repo_url} {target_dir}"):
            return

    components = link_directory(target_dir, name)
    description = get_tool_description(target_dir)

    print(f"\n🎉 {'Installed' if is_new else 'Updated'} {name} Successfully!")
    print(f"📝 Description: {description}")
    print(f"🧩 Components: {', '.join(components) if components else 'None found'}")
    
    if "skills" in components:
        print(f"✅ Verify: Ask 'Help me use {name}' or run '/skill list'")
    if "commands" in components:
        print(f"✅ Verify: Type '/' to see new commands")
    if "agents" in components:
        print(f"✅ Verify: Type '@{name}' to activate agent")
    print("-" * 40)

def update_all_tools():
    print(f"🚀 Updating ALL tools in {TOOLS_DIR}...")
    count = 0
    if TOOLS_DIR.exists():
        for item in TOOLS_DIR.iterdir():
            if item.is_dir() and (item / ".git").exists():
                install_tool("dummy_url", name=item.name) # install_tool handles update if dir exists
                count += 1
    print(f"🏁 Update checks completed for {count} tools.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub AI Tools Installer")
    parser.add_argument("url", nargs="?", help="GitHub Repository URL")
    parser.add_argument("--all", action="store_true", help="Update all installed tools")
    args = parser.parse_args()

    if args.all:
        update_all_tools()
    elif args.url:
        install_tool(args.url)
    else:
        parser.print_help()
