#!/usr/bin/env python3
"""
AI Tools Installer - Logging System

Provides structured logging for all installation operations and maintains
a manifest of installed tools.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict

@dataclass
class ToolManifestEntry:
    """Represents an installed tool in the manifest"""
    name: str
    url: str
    installed_at: str
    last_updated: str
    version: Optional[str] = None  # Git commit hash
    status: str = 'active'  # 'active', 'failed', 'uninstalled'
    validation_passed: bool = True
    environments: List[str] = None  # ['opencode', 'codex', 'gemini']
    components: Dict[str, List[str]] = None  # {'skills': ['skill1'], 'agents': ['agent1']}
    
    def __post_init__(self):
        if self.environments is None:
            self.environments = []
        if self.components is None:
            self.components = {}


class InstallLogger:
    """Manages installation logs and manifest"""
    
    def __init__(self, logs_dir: Path = None):
        if logs_dir is None:
            logs_dir = Path.home() / '.config' / 'opencode' / 'tools' / '.install-logs'
        
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(exist_ok=True)
        
        self.manifest_file = self.logs_dir / 'manifest.json'
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Load the manifest file"""
        if self.manifest_file.exists():
            try:
                return json.loads(self.manifest_file.read_text())
            except json.JSONDecodeError:
                print(f"⚠️  Corrupt manifest file, creating new one")
                return {'installed_tools': [], 'last_updated': datetime.now().isoformat()}
        else:
            return {'installed_tools': [], 'last_updated': datetime.now().isoformat()}
    
    def _save_manifest(self):
        """Save the manifest file"""
        self.manifest['last_updated'] = datetime.now().isoformat()
        self.manifest_file.write_text(json.dumps(self.manifest, indent=2))
    
    def log_installation(self, tool_name: str, url: str, version: Optional[str] = None,
                        validation_passed: bool = True, environments: List[str] = None,
                        components: Dict[str, List[str]] = None) -> str:
        """
        Log a tool installation.
        
        Returns:
            Path to the log file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.logs_dir / f"{timestamp}_{tool_name}.log"
        
        # Create detailed log
        log_content = [
            f"=== Installation Log: {tool_name} ===",
            f"Time: {datetime.now().isoformat()}",
            f"URL: {url}",
            f"Version: {version or 'unknown'}",
            f"Validation: {'PASSED' if validation_passed else 'FAILED'}",
            f"Environments: {', '.join(environments or [])}",
            "",
            "Components:",
        ]
        
        if components:
            for comp_type, items in components.items():
                log_content.append(f"  {comp_type}: {', '.join(items)}")
        else:
            log_content.append("  (No components detected)")
        
        log_content.append("\n" + "=" * 50)
        
        log_file.write_text('\n'.join(log_content))
        
        # Update manifest
        self._update_manifest_entry(tool_name, url, version, validation_passed, environments, components)
        
        return str(log_file)
    
    def _update_manifest_entry(self, tool_name: str, url: str, version: Optional[str],
                               validation_passed: bool, environments: List[str],
                               components: Dict[str, List[str]]):
        """Update or create manifest entry for a tool"""
        now = datetime.now().isoformat()
        
        # Find existing entry
        existing = None
        for i, tool in enumerate(self.manifest['installed_tools']):
            if tool['name'] == tool_name:
                existing = i
                break
        
        if existing is not None:
            # Update existing
            entry = self.manifest['installed_tools'][existing]
            entry['last_updated'] = now
            if version:
                entry['version'] = version
            entry['validation_passed'] = validation_passed
            if environments:
                entry['environments'] = environments
            if components:
                entry['components'] = components
            entry['status'] = 'active' if validation_passed else 'failed'
        else:
            # Create new
            entry = ToolManifestEntry(
                name=tool_name,
                url=url,
                installed_at=now,
                last_updated=now,
                version=version,
                status='active' if validation_passed else 'failed',
                validation_passed=validation_passed,
                environments=environments or [],
                components=components or {}
            )
            self.manifest['installed_tools'].append(asdict(entry))
        
        self._save_manifest()
    
    def log_failure(self, tool_name: str, url: str, error_message: str):
        """Log a failed installation"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.logs_dir / f"{timestamp}_{tool_name}_FAILED.log"
        
        log_content = [
            f"=== Installation FAILED: {tool_name} ===",
            f"Time: {datetime.now().isoformat()}",
            f"URL: {url}",
            "",
            "Error:",
            error_message,
            "\n" + "=" * 50
        ]
        
        log_file.write_text('\n'.join(log_content))
        
        # Update manifest as failed
        self._update_manifest_entry(tool_name, url, None, False, [], {})
        
        return str(log_file)
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict]:
        """Get manifest entry for a tool"""
        for tool in self.manifest['installed_tools']:
            if tool['name'] == tool_name:
                return tool
        return None
    
    def get_all_tools(self) -> List[Dict]:
        """Get all installed tools"""
        return self.manifest['installed_tools']
    
    def get_failed_installations(self) -> List[Dict]:
        """Get all failed installations"""
        return [t for t in self.manifest['installed_tools'] if not t.get('validation_passed', True)]
    
    def mark_uninstalled(self, tool_name: str):
        """Mark a tool as uninstalled"""
        for tool in self.manifest['installed_tools']:
            if tool['name'] == tool_name:
                tool['status'] = 'uninstalled'
                tool['last_updated'] = datetime.now().isoformat()
                self._save_manifest()
                return True
        return False


def format_history_output(tools: List[Dict], show_all: bool = False) -> str:
    """Format tool list for display"""
    if not tools:
        return "No tools found."
    
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"{'Tool':<25} {'Status':<12} {'Last Updated':<20}")
    lines.append(f"{'-'*60}")
    
    for tool in tools:
        if not show_all and tool.get('status') == 'uninstalled':
            continue
        
        name = tool['name'][:24]
        status = tool.get('status', 'unknown')
        
        # Color code status
        if status == 'active':
            status_str = f"\033[32m{status}\033[0m"
        elif status == 'failed':
            status_str = f"\033[31m{status}\033[0m"
        else:
            status_str = status
        
        last_updated = tool.get('last_updated', 'unknown')[:19]
        
        lines.append(f"{name:<25} {status_str:<12} {last_updated:<20}")
    
    lines.append(f"{'='*60}\n")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    import sys
    
    logger = InstallLogger()
    
    if len(sys.argv) < 2:
        # Show all tools
        tools = logger.get_all_tools()
        print(format_history_output(tools))
    else:
        command = sys.argv[1]
        
        if command == 'list':
            tools = logger.get_all_tools()
            print(format_history_output(tools))
        
        elif command == 'failures':
            tools = logger.get_failed_installations()
            if tools:
                print(f"\n🔴 Failed Installations:\n")
                print(format_history_output(tools))
            else:
                print("\n✅ No failed installations")
        
        elif command == 'info':
            if len(sys.argv) < 3:
                print("Usage: install_logger.py info <tool_name>")
                sys.exit(1)
            
            tool_name = sys.argv[2]
            info = logger.get_tool_info(tool_name)
            
            if info:
                print(f"\n📦 Tool: {info['name']}")
                print(f"   URL: {info['url']}")
                print(f"   Installed: {info['installed_at']}")
                print(f"   Last Updated: {info['last_updated']}")
                print(f"   Status: {info['status']}")
                print(f"   Validation: {'✅ Passed' if info.get('validation_passed') else '❌ Failed'}")
                print(f"   Environments: {', '.join(info.get('environments', []))}")
                
                if info.get('components'):
                    print(f"\n   Components:")
                    for comp_type, items in info['components'].items():
                        print(f"     {comp_type}: {', '.join(items[:5])}")
            else:
                print(f"❌ Tool '{tool_name}' not found in manifest")
        
        else:
            print(f"Unknown command: {command}")
            print("Usage:")
            print("  install_logger.py list")
            print("  install_logger.py failures")
            print("  install_logger.py info <tool_name>")
