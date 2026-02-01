#!/usr/bin/env python3
"""
AI Tools Installer - Dependency Resolver

Parses and resolves tool dependencies from INSTALL.md or manifest files.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Dependency:
    """Represents a dependency"""
    name: str
    type: str  # 'tool', 'system', 'npm', 'pip'
    version_spec: Optional[str] = None  # e.g., ">=2.0", "1.x"
    url: Optional[str] = None  # For tool dependencies


class DependencyResolver:
    """Resolves dependencies for tool installations"""
    
    def __init__(self, tool_dir: Path):
        self.tool_dir = tool_dir
        self.dependencies: List[Dependency] = []
        self.conflicts: List[str] = []
    
    def parse_dependencies(self) -> Tuple[List[Dependency], List[str]]:
        """
        Parse dependencies from INSTALL.md or package files.
        
        Returns:
            (dependencies, conflicts)
        """
        # Check for INSTALL.md with YAML frontmatter
        install_md = self.tool_dir / 'INSTALL.md'
        if install_md.exists():
            self._parse_install_md(install_md)
        
        # Check for package.json
        package_json = self.tool_dir / 'package.json'
        if package_json.exists():
            self._parse_package_json(package_json)
        
        # Check for requirements.txt
        requirements_txt = self.tool_dir / 'requirements.txt'
        if requirements_txt.exists():
            self._parse_requirements_txt(requirements_txt)
        
        # Check README for dependency hints
        readme = self.tool_dir / 'README.md'
        if readme.exists():
            self._parse_readme(readme)
        
        return self.dependencies, self.conflicts
    
    def _parse_install_md(self, install_md: Path):
        """Parse INSTALL.md with YAML frontmatter"""
        content = install_md.read_text()
        
        # Extract YAML frontmatter
        yaml_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1)
            
            # Parse dependencies section
            deps_match = re.search(r'dependencies:\s*\n((?:  - .+\n?)+)', yaml_content)
            if deps_match:
                deps_text = deps_match.group(1)
                for line in deps_text.strip().split('\n'):
                    line = line.strip('- ').strip()
                    if ':' in line:
                        dep_spec, version = line.split(':', 1)
                        dep_spec = dep_spec.strip()
                        version = version.strip().strip('"\'')
                        
                        # Determine type
                        if '/' in dep_spec and ('github' in dep_spec or 'http' in dep_spec):
                            dep_type = 'tool'
                            url = dep_spec if dep_spec.startswith('http') else f"https://github.com/{dep_spec}"
                            name = dep_spec.split('/')[-1]
                        else:
                            dep_type = 'system'
                            url = None
                            name = dep_spec
                        
                        self.dependencies.append(Dependency(
                            name=name,
                            type=dep_type,
                            version_spec=version,
                            url=url
                        ))
            
            # Parse conflicts
            conflicts_match = re.search(r'conflicts:\s*\n((?:  - .+\n?)+)', yaml_content)
            if conflicts_match:
                conflicts_text = conflicts_match.group(1)
                for line in conflicts_text.strip().split('\n'):
                    conflict = line.strip('- ').strip()
                    self.conflicts.append(conflict)
    
    def _parse_package_json(self, package_json: Path):
        """Parse package.json for npm dependencies"""
        try:
            import json
            data = json.loads(package_json.read_text())
            
            # Check dependencies
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in data:
                    for name, version in data[dep_type].items():
                        self.dependencies.append(Dependency(
                            name=name,
                            type='npm',
                            version_spec=version
                        ))
        except:
            pass
    
    def _parse_requirements_txt(self, requirements_txt: Path):
        """Parse requirements.txt for pip dependencies"""
        content = requirements_txt.read_text()
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Parse requirement spec (e.g., "package>=1.0.0")
                match = re.match(r'([a-zA-Z0-9\-_]+)(.*)', line)
                if match:
                    name = match.group(1)
                    version = match.group(2).strip()
                    
                    self.dependencies.append(Dependency(
                        name=name,
                        type='pip',
                        version_spec=version if version else None
                    ))
    
    def _parse_readme(self, readme: Path):
        """Parse README for dependency hints"""
        content = readme.read_text().lower()
        
        # Look for common patterns
        if 'npm install' in content:
            if not any(d.type == 'npm' for d in self.dependencies):
                self.dependencies.append(Dependency(
                    name='npm-packages',
                    type='npm',
                    version_spec=None
                ))
        
        if 'pip install' in content:
            if not any(d.type == 'pip' for d in self.dependencies):
                self.dependencies.append(Dependency(
                    name='python-packages',
                    type='pip',
                    version_spec=None
                ))


def check_dependencies(tool_dir: Path) -> Tuple[List[Dependency], List[str]]:
    """
    Check dependencies for a tool.
    
    Returns:
        (dependencies, conflicts)
    """
    resolver = DependencyResolver(tool_dir)
    return resolver.parse_dependencies()


def format_dependencies_report(dependencies: List[Dependency], conflicts: List[str]) -> str:
    """Format dependencies for display"""
    lines = []
    
    if dependencies:
        lines.append("\n📦 Dependencies:")
        
        by_type = {}
        for dep in dependencies:
            if dep.type not in by_type:
                by_type[dep.type] = []
            by_type[dep.type].append(dep)
        
        for dep_type, deps in by_type.items():
            lines.append(f"\n  {dep_type.upper()}:")
            for dep in deps:
                version_str = f" ({dep.version_spec})" if dep.version_spec else ""
                lines.append(f"    - {dep.name}{version_str}")
    
    if conflicts:
        lines.append("\n⚠️  Conflicts:")
        for conflict in conflicts:
            lines.append(f"    - {conflict}")
    
    return '\n'.join(lines) if lines else "  No dependencies specified"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dependency_resolver.py <tool_directory>")
        sys.exit(1)
    
    tool_dir = Path(sys.argv[1])
    
    if not tool_dir.exists():
        print(f"Error: Directory not found: {tool_dir}")
        sys.exit(1)
    
    deps, conflicts = check_dependencies(tool_dir)
    
    print(f"\n🔍 Dependency Analysis: {tool_dir.name}")
    print(format_dependencies_report(deps, conflicts))
    print()
