#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

# Import validation and transaction systems
try:
    from install_validator import run_validation
    from install_transaction import InstallTransaction
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    print("⚠️  Validation system not available (missing dependencies)")

# Configuration
TOOLS_DIR = Path("~/.config/opencode/tools").expanduser()
OPENCODE_DIR = Path("~/.config/opencode").expanduser()
CODEX_DIR = Path("~/.codex").expanduser()
GEMINI_DIR = Path("~/.gemini").expanduser()

# Mapping component names to their potential destination directories in all environments
DESTINATION_MAP = {
    "skills":   [OPENCODE_DIR / "skills",   CODEX_DIR / "skills",   GEMINI_DIR / "skills"],
    "agents":   [OPENCODE_DIR / "agents",   CODEX_DIR / "agents",   GEMINI_DIR / "agents"],
    "commands": [OPENCODE_DIR / "commands", CODEX_DIR / "commands", GEMINI_DIR / "commands"],
    "plugins":  [OPENCODE_DIR / "plugins",  CODEX_DIR / "plugins",  GEMINI_DIR / "plugins"],
    "hooks":    [OPENCODE_DIR / "hooks",    CODEX_DIR / "hooks",    GEMINI_DIR / "hooks"],
    "mcp":      [OPENCODE_DIR / "mcp",      CODEX_DIR / "mcp",      GEMINI_DIR / "mcp"],
    "prompts":  [OPENCODE_DIR / "prompts",  CODEX_DIR / "prompts",  GEMINI_DIR / "prompts"]
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

def find_components(root_dir):
    """Recursively find component directories (up to depth 3) to handle varying structures."""
    components = {}
    root_path = Path(root_dir)
    
    # Priority folders to look for at root first
    for key in DESTINATION_MAP.keys():
        direct_path = root_path / key
        if direct_path.is_dir():
            components[key] = direct_path

    # Deep search if not found at root (or to find additional ones, though usually one per repo)
    # We limit depth to avoid deep 'node_modules' scanning
    for root, dirs, files in os.walk(root_dir):
        # Skip hidden and annoying dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'dist', 'build', 'vendor']]
        
        rel_level = str(Path(root).relative_to(root_dir)).count(os.sep)
        if rel_level > 2: # Max depth 2
            continue
            
        for d in dirs:
            if d in DESTINATION_MAP and d not in components:
                 components[d] = Path(root) / d
    
    return components

def get_tool_description(dir_path):
    desc = "No description available."
    for readme in ["README.md", "README_CN.md", "SKILL.md", "README.txt"]:
        readme_path = dir_path / readme
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    paragraph = []
                    # Simple heuristic to find first paragraph
                    start = False
                    for line in lines:
                        if line.strip().startswith('---'): continue # Skip frontmatter
                        if line.strip().startswith('#'): 
                            start = True
                            continue
                        if start and line.strip():
                            paragraph.append(line.strip())
                        if start and paragraph and not line.strip():
                            break
                    if paragraph:
                        return " ".join(paragraph)[:200] + "..."
            except Exception:
                pass
    return desc

def link_component(source_path, component_type, tool_name):
    targets = DESTINATION_MAP.get(component_type, [])
    linked_to = []
    
    for dest_parent in targets:
        # Only link if the destination parent directory actually exists (is supported by the env)
        # OR force create for OpenCode as primary. 
        # For Codex/Gemini, we only installed if user has them set up.
        if "opencode" in str(dest_parent) or dest_parent.parent.exists():
            if not dest_parent.exists():
                dest_parent.mkdir(parents=True, exist_ok=True)
            
            link_name = dest_parent / tool_name
            
            # Smart Backup & Overwrite
            if link_name.is_symlink() or link_name.is_file():
                link_name.unlink()
            elif link_name.is_dir():
                timestamp = int(os.path.getmtime(link_name))
                backup_name = link_name.with_suffix(f".bak.{timestamp}")
                print(f"    ⚠️  [Backup] Moving existing {link_name} -> {backup_name}")
                shutil.move(str(link_name), str(backup_name))
            
            os.symlink(source_path, link_name)
            linked_to.append(str(dest_parent))
            
    return linked_to

def get_component_items(path, c_type):
    """List specific items (skills/agents names) within a component directory."""
    items = []
    if not path.is_dir(): return items
    
    for item in path.iterdir():
        if item.name.startswith('.'): continue
        if c_type in ['commands']:
            # For commands, any file that is executable or script is a command
            if item.is_file():
                items.append(item.name)
        elif c_type in ['skills', 'agents', 'plugins', 'mcp']:
            # Usually directories
            if item.is_dir():
                items.append(item.name)
            # Agents/Skills can sometimes be single files
            elif item.is_file() and item.suffix in ['.md', '.json', '.py', '.js']:
                 items.append(item.stem)
    return sorted(items)

def get_remote_url(repo_dir):
    try:
        url = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=repo_dir, stderr=subprocess.DEVNULL).decode().strip()
        return url
    except:
        return None

def install_tool(repo_url, name=None, only_clone=False, only_link=False, validate=True, backup=True):
    # Handle short GitHub format "user/repo"
    if not repo_url.startswith("http") and not repo_url.startswith("git@") and "/" in repo_url:
        repo_url = f"https://github.com/{repo_url}.git"

    # Extraction
    parts = repo_url.rstrip('/').split('/')
    repo_name_raw = parts[-1].replace(".git", "")
    
    # Try to extract author for fallback
    author = "unknown"
    if len(parts) >= 2:
        author = parts[-2]
        if ":" in author: # git@github.com:User/Repo
            author = author.split(":")[-1]

    target_dir = None
    target_name = name

    if name:
        # Explicit name provided (e.g. from update_all), trust it
        target_dir = TOOLS_DIR / name
    else:
        # Smart detection logic
        default_name = repo_name_raw
        default_dir = TOOLS_DIR / default_name
        
        if default_dir.exists():
            # Check if it's the same repo
            existing_url = get_remote_url(default_dir)
            
            # Loose comparison (ignore .git, protocol) across both
            clean_new = repo_url.replace(".git", "").lower()
            clean_existing = (existing_url or "").replace(".git", "").lower()
            
            # Does existing url end with author/repo? or match completely?
            match_suffix = f"/{author.lower()}/{repo_name_raw.lower()}"
            
            if clean_existing == clean_new or clean_existing.endswith(match_suffix):
                # It's the same repo, verify existing link
                print(f"  🔍 Found existing repository at {default_name}")
                target_name = default_name
                target_dir = default_dir
            else:
                # Conflict! Different repo with same name.
                print(f"  ⚠️  Conflict: {default_name} occupied by {existing_url}")
                alt_name = f"{author}-{repo_name_raw}"
                print(f"  🔄 Switching to namespaced: {alt_name}")
                target_name = alt_name
                target_dir = TOOLS_DIR / alt_name
        else:
            # Free slot
            target_name = default_name
            target_dir = default_dir

    print(f"🔧 \033[1mProcessing {target_name}\033[0m ({repo_url})...")
    name = target_name
    
    # Clone or Pull
    if not TOOLS_DIR.exists(): TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    
    if not only_link:
        if target_dir.exists():
            print(f"  ⬇️  Updating git repository...")
            if not run_command("git pull", cwd=target_dir, quiet=True):
                print("  ⚠️  Git pull failed (dirty state?), skipping update.")
        else:
            print(f"  ⬇️  Cloning repository...")
            if not run_command(f"git clone {repo_url} {target_dir}", quiet=True):
                print("  ❌ Clone failed.")
                return
    
    if only_clone:
        print(f"  ⏹️  Clone complete. Skipping install/linking (--only-clone).")
        print(f"     Path: {target_dir}")
        return

    # Discovery & Linking
    found_components = find_components(target_dir)
    installed_summary = {} # {type: {locations: [], items: []}}

    print("  🔗 Linking components...")
    if not found_components:
        print("     ⚠️  No standard components (skills, agents, etc.) found in root or subdirs.")
    
    for c_type, c_path in found_components.items():
        links = link_component(c_path, c_type, name)
        if links:
            items = get_component_items(c_path, c_type)
            installed_summary[c_type] = {'locations': links, 'items': items}
            print(f"     ✅ Linked \033[36m{c_type}\033[0m from {c_path.relative_to(target_dir)}")

    # Summary Output
    desc = get_tool_description(target_dir)
    print(f"\n✨ \033[32mSuccessfully Installed {name}\033[0m")
    print(f"📖 \033[3m{desc}\033[0m\n")
    
    print("🔎 \033[1mCapabilities Installed:\033[0m")
    if not installed_summary:
        print("   (No active components found. Is this a raw library?)")
    else:
        for c_type, data in installed_summary.items():
            item_list = ", ".join(data['items'][:5]) # Show first 5
            if len(data['items']) > 5: item_list += f", +{len(data['items'])-5} more"
            print(f"   • \033[1m{c_type.capitalize()}\033[0m: {item_list if item_list else '(Standard link)'}")
            
    print("\n🚀 \033[1mHow to Validate:\033[0m")
    
    if "skills" in installed_summary and installed_summary["skills"]['items']:
        ex_skill = installed_summary["skills"]['items'][0]
        print(f"   ▶ Skill: Ask \033[33m'Help me using {ex_skill}'\033[0m or run \033[33m/skill run {ex_skill}\033[0m")
    
    if "agents" in installed_summary and installed_summary["agents"]['items']:
        ex_agent = installed_summary["agents"]['items'][0]
        print(f"   ▶ Agent: Type \033[33m@{ex_agent}\033[0m to switch to this agent.")

    if "commands" in installed_summary and installed_summary["commands"]['items']:
        ex_cmd = installed_summary["commands"]['items'][0]
        print(f"   ▶ Command: Type \033[33m/{ex_cmd} --help\033[0m")
        
    if "plugins" in installed_summary:
        print(f"   ▶ Check plugins: \033[33m/plugin list\033[0m")

    print("-" * 50)
    
    # Phase 4: Validation (NEW)
    if validate and VALIDATION_AVAILABLE and not only_clone:
        print(f"\n🔍 \033[1mPhase 4: Validation\033[0m")
        validation_passed = run_validation(name)
        
        if not validation_passed:
            print(f"\n❌ \033[31mValidation failed!\033[0m")
            print(f"   Installation completed but has issues.")
            print(f"   Review errors above and fix manually, or run:")
            print(f"   \033[33mpython install_transaction.py rollback {name}\033[0m")
            return False
        
        print(f"\n✅ \033[32mValidation passed!\033[0m")
    
    return True

def update_all_tools():
    print(f"🚀 Batch Updating ALL tools in {TOOLS_DIR}...")
    count = 0
    if TOOLS_DIR.exists():
        for item in TOOLS_DIR.iterdir():
            if item.is_dir() and (item / ".git").exists():
                # Re-install triggers update+link
                # We construct a dummy URL since it exists
                install_tool(f"local/{item.name}", name=item.name)
                count += 1
    print(f"🏁 Update checks completed for {count} tools.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub AI Tools Installer")
    parser.add_argument("url", nargs="?", help="GitHub Repository URL or user/repo")
    parser.add_argument("--all", action="store_true", help="Update all installed tools")
    parser.add_argument("--only-clone", action="store_true", help="Only clone/pull, do not link")
    parser.add_argument("--only-link", action="store_true", help="Only link existing repo, do not pull")
    parser.add_argument("--no-validate", action="store_true", help="Skip post-installation validation")
    parser.add_argument("--backup", action="store_true", default=True, help="Create backup before installation")
    parser.add_argument("--no-backup", dest='backup', action="store_false", help="Skip backup creation")
    args = parser.parse_args()

    if args.all:
        update_all_tools()
    elif args.url:
        # Use transaction wrapper if available and not in clone-only mode
        if VALIDATION_AVAILABLE and not args.only_clone and args.backup:
            with InstallTransaction(args.url.split('/')[-1].replace('.git', ''), backup=args.backup) as tx:
                success = install_tool(
                    args.url, 
                    only_clone=args.only_clone, 
                    only_link=args.only_link,
                    validate=not args.no_validate,
                    backup=False  # Transaction handles backup
                )
                if success:
                    tx.commit()
                # Rollback handled automatically by transaction on failure
        else:
            install_tool(
                args.url, 
                only_clone=args.only_clone, 
                only_link=args.only_link,
                validate=not args.no_validate,
                backup=args.backup
            )
    else:
        parser.print_help()
