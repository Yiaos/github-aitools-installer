#!/usr/bin/env python3
"""
AI Tools Installer - Security Scanner

Performs basic security checks on tools before installation.
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

@dataclass
class SecurityIssue:
    """Represents a security concern"""
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'code_pattern', 'permission', 'network'
    file_path: str
    line_number: int
    description: str
    pattern: str


class SecurityScanner:
    """Scans tools for security issues"""
    
    # Suspicious patterns to detect
    SUSPICIOUS_PATTERNS = {
        'critical': [
            (r'rm\s+-rf\s+/', 'Dangerous: Recursive force delete from root'),
            (r'eval\s*\([^)]*\$', 'Code injection risk: eval with variable'),
            (r'curl\s+[^\|]*\|\s*bash', 'Remote code execution: curl | bash'),
            (r'wget\s+[^\|]*\|\s*sh', 'Remote code execution: wget | sh'),
        ],
        'high': [
            (r'chmod\s+777', 'Insecure permissions: chmod 777'),
            (r'sudo\s+', 'Privilege escalation attempt'),
            (r'exec\s*\([^)]*\$', 'Code execution with variable'),
            (r'\\$\\{[^}]*exec', 'Command substitution with exec'),
        ],
        'medium': [
            (r'rm\s+-rf\s+\$', 'Force delete with variable'),
            (r'\\>\\s*/dev/null\\s+2>&1', 'Output suppression (hiding errors)'),
            (r'nc\s+-[lep]', 'Netcat listening/execution'),
        ]
    }
    
    def __init__(self, tool_dir: Path):
        self.tool_dir = tool_dir
        self.issues: List[SecurityIssue] = []
        self.permissions: Set[str] = set()
    
    def scan(self) -> List[SecurityIssue]:
        """Run security scan on the tool"""
        # Scan executable files
        self._scan_scripts()
        
        # Check for hooks (startup scripts)
        self._check_hooks()
        
        # Analyze permissions requested
        self._analyze_permissions()
        
        return self.issues
    
    def _scan_scripts(self):
        """Scan shell scripts and Python files for suspicious patterns"""
        script_patterns = ['**/*.sh', '**/*.bash', '**/*.py', '**/*.js']
        
        for pattern in script_patterns:
            for script_file in self.tool_dir.glob(pattern):
                if script_file.is_file():
                    try:
                        content = script_file.read_text()
                        self._scan_content(script_file, content)
                    except:
                        pass  # Skip binary or unreadable files
    
    def _scan_content(self, file_path: Path, content: str):
        """Scan file content for suspicious patterns"""
        lines = content.split('\n')
        
        for severity, patterns in self.SUSPICIOUS_PATTERNS.items():
            for pattern, description in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        self.issues.append(SecurityIssue(
                            severity=severity,
                            category='code_pattern',
                            file_path=str(file_path.relative_to(self.tool_dir)),
                            line_number=i,
                            description=description,
                            pattern=line.strip()
                        ))
    
    def _check_hooks(self):
        """Check for hook scripts that run on startup"""
        hooks_dir = self.tool_dir / 'hooks'
        
        if hooks_dir.exists():
            self.permissions.add('execute_on_startup')
            
            # List hook files
            for hook_file in hooks_dir.iterdir():
                if hook_file.is_file():
                    self.issues.append(SecurityIssue(
                        severity='medium',
                        category='permission',
                        file_path=str(hook_file.relative_to(self.tool_dir)),
                        line_number=0,
                        description='Hook script runs on session start',
                        pattern=f'Hook: {hook_file.name}'
                    ))
    
    def _analyze_permissions(self):
        """Analyze what permissions the tool might need"""
        # Check for network access patterns
        for script_file in self.tool_dir.glob('**/*.{sh,py,js}'):
            if script_file.is_file():
                try:
                    content = script_file.read_text()
                    
                    if re.search(r'(curl|wget|http|fetch|requests|axios)', content, re.IGNORECASE):
                        self.permissions.add('network_access')
                    
                    if re.search(r'(rm|delete|unlink|shutil\\.rmtree)', content, re.IGNORECASE):
                        self.permissions.add('file_deletion')
                    
                    if re.search(r'(write|create|mkdir|touch)', content, re.IGNORECASE):
                        self.permissions.add('file_write')
                except:
                    pass
    
    def get_permissions_report(self) -> List[str]:
        """Get list of permissions this tool requests"""
        return sorted(list(self.permissions))


def scan_tool_security(tool_dir: Path) -> Tuple[List[SecurityIssue], List[str]]:
    """
    Scan a tool for security issues.
    
    Returns:
        (issues, permissions)
    """
    scanner = SecurityScanner(tool_dir)
    issues = scanner.scan()
    permissions = scanner.get_permissions_report()
    
    return issues, permissions


def format_security_report(issues: List[SecurityIssue], permissions: List[str], tool_name: str) -> str:
    """Format security scan results"""
    lines = []
    
    lines.append(f"\n🔒 Security Scan: {tool_name}\n")
    
    # Permissions
    if permissions:
        lines.append("Requested Permissions:")
        emoji_map = {
            'execute_on_startup': '🔴',
            'network_access': '🟡',
            'file_deletion': '🟡',
            'file_write': '🟢'
        }
        for perm in permissions:
            emoji = emoji_map.get(perm, '  ')
            perm_display = perm.replace('_', ' ').title()
            lines.append(f"  {emoji} {perm_display}")
    else:
        lines.append("Requested Permissions: None detected")
    
    # Issues
    if issues:
        lines.append(f"\n⚠️  Detected {len(issues)} Issue(s):\n")
        
        by_severity = {}
        for issue in issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)
        
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in by_severity:
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
                lines.append(f"{severity_emoji[severity]} {severity.upper()}:")
                
                for issue in by_severity[severity]:
                    lines.append(f"  File: {issue.file_path}:{issue.line_number}")
                    lines.append(f"  {issue.description}")
                    lines.append(f"  Pattern: {issue.pattern[:80]}")
                    lines.append("")
    else:
        lines.append("\n✅ No security issues detected")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python security_scanner.py <tool_directory>")
        sys.exit(1)
    
    tool_dir = Path(sys.argv[1])
    
    if not tool_dir.exists():
        print(f"Error: Directory not found: {tool_dir}")
        sys.exit(1)
    
    issues, permissions = scan_tool_security(tool_dir)
    
    print(format_security_report(issues, permissions, tool_dir.name))
