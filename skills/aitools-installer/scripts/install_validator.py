#!/usr/bin/env python3
"""
AI Tools Installer - Post-Installation Validator

Validates installations to prevent broken configurations that could crash OpenCode/Codex/Gemini.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re
import yaml

@dataclass
class ValidationIssue:
    """Represents a validation problem"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'yaml', 'symlink', 'compatibility'
    file_path: str
    line_number: Optional[int]
    message: str
    suggested_fix: Optional[str] = None

@dataclass
class ValidationResult:
    """Validation result for a tool"""
    tool_name: str
    passed: bool
    issues: List[ValidationIssue]
    
    def get_errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == 'error']
    
    def get_warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == 'warning']


class InstallValidator:
    """Validates tool installations"""
    
    def __init__(self, tools_dir: Path, config_dirs: Dict[str, Path]):
        self.tools_dir = tools_dir
        self.config_dirs = config_dirs  # {'opencode': Path(...), 'codex': ...}
        
    def validate_tool(self, tool_name: str) -> ValidationResult:
        """Run all validation checks on a tool"""
        tool_path = self.tools_dir / tool_name
        issues = []
        
        # Check 1: YAML syntax validation
        issues.extend(self._validate_yaml_configs(tool_path))
        
        # Check 2: Symlink integrity
        issues.extend(self._validate_symlinks(tool_name))
        
        # Check 3: Compatibility issues
        issues.extend(self._detect_compatibility_issues(tool_path))
        
        # Passed if no errors (warnings are OK)
        passed = all(issue.severity != 'error' for issue in issues)
        
        return ValidationResult(tool_name, passed, issues)
    
    def _validate_yaml_configs(self, tool_path: Path) -> List[ValidationIssue]:
        """Validate YAML frontmatter in agent/skill config files"""
        issues = []
        
        # Find all .md files in agents/, skills/, etc.
        config_patterns = ['agents/**/*.md', 'skills/**/*.md', 'commands/**/*.md']
        
        for pattern in config_patterns:
            for config_file in tool_path.glob(pattern):
                try:
                    content = config_file.read_text(encoding='utf-8')
                    
                    # Extract YAML frontmatter (between --- markers)
                    yaml_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
                    
                    if not yaml_match:
                        continue  # No frontmatter, skip
                    
                    yaml_content = yaml_match.group(1)
                    
                    # Parse YAML
                    try:
                        data = yaml.safe_load(yaml_content)
                        
                        # Check for incompatible 'tools' array format
                        if 'tools' in data:
                            if isinstance(data['tools'], list):
                                issues.append(ValidationIssue(
                                    severity='error',
                                    category='compatibility',
                                    file_path=str(config_file),
                                    line_number=self._find_line_number(content, 'tools:'),
                                    message='Incompatible tools format: Array found, expected Map/Dictionary',
                                    suggested_fix='Convert tools: [A, B] to tools:\\n  A: {}\\n  B: {}'
                                ))
                    
                    except yaml.YAMLError as e:
                        issues.append(ValidationIssue(
                            severity='error',
                            category='yaml',
                            file_path=str(config_file),
                            line_number=getattr(e, 'problem_mark', None),
                            message=f'YAML syntax error: {str(e)}',
                            suggested_fix='Fix YAML syntax using a validator'
                        ))
                
                except Exception as e:
                    issues.append(ValidationIssue(
                        severity='warning',
                        category='yaml',
                        file_path=str(config_file),
                        line_number=None,
                        message=f'Could not read file: {str(e)}'
                    ))
        
        return issues
    
    def _validate_symlinks(self, tool_name: str) -> List[ValidationIssue]:
        """Validate that created symlinks are valid"""
        issues = []
        
        for env_name, config_dir in self.config_dirs.items():
            # Check common symlink locations
            link_types = ['skills', 'agents', 'commands', 'hooks', 'plugins']
            
            for link_type in link_types:
                link_dir = config_dir / link_type
                if not link_dir.exists():
                    continue
                
                # Find symlinks for this tool
                for item in link_dir.iterdir():
                    if item.is_symlink():
                        # Check if it's for our tool
                        target = item.resolve()
                        if tool_name in str(target):
                            # Validate symlink
                            if not target.exists():
                                issues.append(ValidationIssue(
                                    severity='error',
                                    category='symlink',
                                    file_path=str(item),
                                    line_number=None,
                                    message=f'Broken symlink: {item.name} → {target} (target does not exist)',
                                    suggested_fix=f'Remove broken link: rm {item}'
                                ))
        
        return issues
    
    def _detect_compatibility_issues(self, tool_path: Path) -> List[ValidationIssue]:
        """Detect other compatibility issues"""
        issues = []
        
        # Check for missing dependencies (if INSTALL.md exists)
        install_doc = tool_path / 'INSTALL.md'
        if install_doc.exists():
            content = install_doc.read_text()
            
            # Look for common dependency patterns
            if 'npm install' in content.lower() or 'yarn install' in content.lower():
                node_modules = tool_path / 'node_modules'
                if not node_modules.exists():
                    issues.append(ValidationIssue(
                        severity='warning',
                        category='compatibility',
                        file_path=str(install_doc),
                        line_number=None,
                        message='Tool requires npm dependencies, but node_modules not found',
                        suggested_fix=f'Run: npm install in {tool_path}'
                    ))
            
            if 'pip install' in content.lower():
                # Check for requirements.txt
                requirements = tool_path / 'requirements.txt'
                if requirements.exists():
                    issues.append(ValidationIssue(
                        severity='warning',
                        category='compatibility',
                        file_path=str(requirements),
                        line_number=None,
                        message='Tool has Python dependencies, ensure they are installed',
                        suggested_fix=f'Run: pip install -r {requirements}'
                    ))
        
        return issues
    
    def _find_line_number(self, content: str, search_string: str) -> Optional[int]:
        """Find line number of a string in content"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_string in line:
                return i
        return None


def run_validation(tool_name: str, tools_dir: Path = None, config_dirs: Dict[str, Path] = None) -> bool:
    """
    Run validation on a tool and print results.
    
    Returns:
        bool: True if validation passed (no errors), False otherwise
    """
    if tools_dir is None:
        tools_dir = Path.home() / '.config' / 'opencode' / 'tools'
    
    if config_dirs is None:
        config_dirs = {
            'opencode': Path.home() / '.config' / 'opencode',
            'codex': Path.home() / '.codex',
            'gemini': Path.home() / '.gemini',
        }
    
    validator = InstallValidator(tools_dir, config_dirs)
    result = validator.validate_tool(tool_name)
    
    # Print results
    print(f"\n🔍 \033[1mValidation Results: {tool_name}\033[0m")
    
    if result.passed:
        print(f"✅ \033[32mPASSED\033[0m - No critical issues found")
    else:
        print(f"❌ \033[31mFAILED\033[0m - Critical issues detected")
    
    # Print errors
    errors = result.get_errors()
    if errors:
        print(f"\n🔴 \033[1m{len(errors)} Error(s):\033[0m")
        for issue in errors:
            print(f"\n  File: {issue.file_path}")
            if issue.line_number:
                print(f"  Line: {issue.line_number}")
            print(f"  {issue.message}")
            if issue.suggested_fix:
                print(f"  💡 Fix: {issue.suggested_fix}")
    
    # Print warnings
    warnings = result.get_warnings()
    if warnings:
        print(f"\n🟡 \033[1m{len(warnings)} Warning(s):\033[0m")
        for issue in warnings:
            print(f"\n  File: {issue.file_path}")
            print(f"  {issue.message}")
            if issue.suggested_fix:
                print(f"  💡 Suggestion: {issue.suggested_fix}")
    
    if not errors and not warnings:
        print("  No issues detected.")
    
    print("-" * 50)
    
    return result.passed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python install_validator.py <tool_name>")
        sys.exit(1)
    
    tool_name = sys.argv[1]
    passed = run_validation(tool_name)
    
    sys.exit(0 if passed else 1)
