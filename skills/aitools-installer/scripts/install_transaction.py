#!/usr/bin/env python3
"""
AI Tools Installer - Transaction Management

Provides atomic installations with automatic rollback on failure.
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
import tempfile

@dataclass
class TransactionLog:
    """Log of a transaction"""
    tool_name: str
    started_at: str
    snapshot_path: Optional[str] = None
    operations: List[Dict] = None
    status: str = 'in_progress'  # 'in_progress', 'committed', 'rolled_back'
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.operations is None:
            self.operations = []


class InstallTransaction:
    """
    Context manager for atomic tool installation.
    
    Usage:
        with InstallTransaction(tool_name) as tx:
            tx.clone()
            tx.link()
            tx.validate()
            tx.commit()  # Only commits if no exceptions
    """
    
    def __init__(self, tool_name: str, tools_dir: Path = None, config_dirs: Dict[str, Path] = None, backup: bool = True):
        self.tool_name = tool_name
        self.backup_enabled = backup
        
        # Paths
        if tools_dir is None:
            tools_dir = Path.home() / '.config' / 'opencode' / 'tools'
        self.tools_dir = tools_dir
        
        if config_dirs is None:
            config_dirs = {
                'opencode': Path.home() / '.config' / 'opencode',
                'codex': Path.home() / '.codex',
                'gemini': Path.home() / '.gemini',
            }
        self.config_dirs = config_dirs
        
        # Transaction state
        self.tool_path = tools_dir / tool_name
        self.snapshot_dir: Optional[Path] = None
        self.log = TransactionLog(
            tool_name=tool_name,
            started_at=datetime.now().isoformat()
        )
        self.committed = False
        self.rolled_back = False
        
    def __enter__(self):
        """Start transaction"""
        print(f"🔄 Starting transaction: {self.tool_name}")
        
        # Create snapshot if tool exists and backup enabled
        if self.backup_enabled and self.tool_path.exists():
            self._create_snapshot()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End transaction - auto-rollback on exception"""
        if exc_type is not None:
            # Exception occurred
            print(f"\n❌ Transaction failed: {exc_val}")
            if not self.rolled_back:
                self.rollback()
            return False  # Re-raise exception
        
        if not self.committed and not self.rolled_back:
            # Transaction not explicitly committed
            print(f"\n⚠️  Transaction not committed, rolling back...")
            self.rollback()
        
        # Clean up snapshot if committed
        if self.committed and self.snapshot_dir:
            self._cleanup_snapshot()
        
        return False
    
    def _create_snapshot(self):
        """Create backup snapshot of current installation"""
        print(f"  📸 Creating snapshot...")
        
        # Create temp directory for snapshot
        snapshot_base = self.tools_dir.parent / '.install-snapshots'
        snapshot_base.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.snapshot_dir = snapshot_base / f"{self.tool_name}_{timestamp}"
        
        # Backup tool directory
        if self.tool_path.exists():
            shutil.copytree(self.tool_path, self.snapshot_dir / 'tool')
        
        # Backup symlinks
        symlinks_backup = {}
        for env_name, config_dir in self.config_dirs.items():
            env_links = []
            for link_type in ['skills', 'agents', 'commands', 'hooks', 'plugins', 'mcp']:
                link_dir = config_dir / link_type
                if not link_dir.exists():
                    continue
                
                for item in link_dir.iterdir():
                    if item.is_symlink() and self.tool_name in str(item.resolve()):
                        env_links.append({
                            'link': str(item),
                            'target': str(item.resolve())
                        })
            
            if env_links:
                symlinks_backup[env_name] = env_links
        
        # Save symlinks info
        if symlinks_backup:
            (self.snapshot_dir / 'symlinks.json').write_text(
                json.dumps(symlinks_backup, indent=2)
            )
        
        self.log.snapshot_path = str(self.snapshot_dir)
        self._log_operation('snapshot_created', {'path': str(self.snapshot_dir)})
        
        print(f"     Snapshot: {self.snapshot_dir}")
    
    def _log_operation(self, operation: str, details: Dict = None):
        """Log an operation"""
        self.log.operations.append({
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        })
    
    def commit(self):
        """Commit the transaction"""
        if self.rolled_back:
            raise RuntimeError("Cannot commit: transaction already rolled back")
        
        print(f"\n✅ Committing transaction: {self.tool_name}")
        
        self.log.status = 'committed'
        self.log.completed_at = datetime.now().isoformat()
        self.committed = True
        
        # Save transaction log
        self._save_transaction_log()
    
    def rollback(self):
        """Rollback the transaction"""
        if self.committed:
            raise RuntimeError("Cannot rollback: transaction already committed")
        
        print(f"\n🔙 Rolling back transaction: {self.tool_name}")
        
        if self.snapshot_dir and self.snapshot_dir.exists():
            # Restore from snapshot
            print(f"  📦 Restoring from snapshot...")
            
            # Restore tool directory
            tool_backup = self.snapshot_dir / 'tool'
            if tool_backup.exists():
                if self.tool_path.exists():
                    shutil.rmtree(self.tool_path)
                shutil.copytree(tool_backup, self.tool_path)
                print(f"     Restored: {self.tool_path}")
            
            # Restore symlinks
            symlinks_file = self.snapshot_dir / 'symlinks.json'
            if symlinks_file.exists():
                symlinks_data = json.loads(symlinks_file.read_text())
                
                for env_name, links in symlinks_data.items():
                    for link_info in links:
                        link_path = Path(link_info['link'])
                        target_path = Path(link_info['target'])
                        
                        # Remove current link if exists
                        if link_path.exists() or link_path.is_symlink():
                            link_path.unlink()
                        
                        # Recreate original link
                        link_path.symlink_to(target_path)
                
                print(f"     Restored {len(symlinks_data)} symlink(s)")
        else:
            # No snapshot, just remove new files
            print(f"  🗑️  Removing newly installed files...")
            if self.tool_path.exists():
                shutil.rmtree(self.tool_path)
                print(f"     Removed: {self.tool_path}")
            
            # Remove symlinks
            for env_name, config_dir in self.config_dirs.items():
                for link_type in ['skills', 'agents', 'commands', 'hooks', 'plugins', 'mcp']:
                    link_dir = config_dir / link_type
                    if not link_dir.exists():
                        continue
                    
                    for item in link_dir.iterdir():
                        if item.is_symlink():
                            target = item.resolve()
                            if self.tool_name in str(target):
                                item.unlink()
                                print(f"     Removed link: {item}")
        
        self.log.status = 'rolled_back'
        self.log.completed_at = datetime.now().isoformat()
        self.rolled_back = True
        
        # Save transaction log
        self._save_transaction_log()
        
        print(f"  ✅ Rollback complete")
    
    def _cleanup_snapshot(self):
        """Clean up snapshot after successful commit"""
        if self.snapshot_dir and self.snapshot_dir.exists():
            shutil.rmtree(self.snapshot_dir)
            print(f"  🧹 Cleaned up snapshot")
    
    def _save_transaction_log(self):
        """Save transaction log for audit trail"""
        logs_dir = self.tools_dir.parent / '.install-logs'
        logs_dir.mkdir(exist_ok=True)
        
        log_file = logs_dir / f"{self.tool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_file.write_text(json.dumps(asdict(self.log), indent=2))


# Convenience function for manual rollback
def rollback_tool(tool_name: str, snapshot_path: str = None):
    """
    Manually rollback a tool to a previous snapshot.
    
    Args:
        tool_name: Name of the tool
        snapshot_path: Optional specific snapshot to restore from
    """
    tools_dir = Path.home() / '.config' / 'opencode' / 'tools'
    snapshot_base = tools_dir.parent / '.install-snapshots'
    
    if snapshot_path:
        snapshot_dir = Path(snapshot_path)
    else:
        # Find latest snapshot for this tool
        snapshots = sorted(snapshot_base.glob(f"{tool_name}_*"), reverse=True)
        if not snapshots:
            print(f"❌ No snapshots found for {tool_name}")
            return False
        snapshot_dir = snapshots[0]
    
    if not snapshot_dir.exists():
        print(f"❌ Snapshot not found: {snapshot_dir}")
        return False
    
    print(f"🔙 Rolling back {tool_name} to snapshot: {snapshot_dir.name}")
    
    # Create transaction to handle rollback
    tx = InstallTransaction(tool_name, backup=False)
    tx.snapshot_dir = snapshot_dir
    tx.rollback()
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python install_transaction.py rollback <tool_name> [snapshot_path]")
        sys.exit(1)
    
    if sys.argv[1] == 'rollback':
        tool_name = sys.argv[2] if len(sys.argv) > 2 else None
        snapshot_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        if not tool_name:
            print("Error: tool_name required")
            sys.exit(1)
        
        success = rollback_tool(tool_name, snapshot_path)
        sys.exit(0 if success else 1)
