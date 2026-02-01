---
name: github-tools-installer
description: A universal installer for OpenCode/Codex/Gemini. Automatically installs Agents, Skills, Plugins, Hooks, and Prompts from any GitHub repository.
---

# GitHub Tools Installer

Use this skill to install **ANY** GitHub repository as an extension for your AI environment.

It intelligently detects the repository structure and links components to:
- `~/.config/opencode/` (Skills, Agents, Plugins, Commands, Hooks, Prompts)
- `~/.codex/` (Skills)
- `~/.gemini/` (Skills)

## Usage

```python
# Install a repository
install_tool("https://github.com/obra/superpowers")

# Update an existing tool
install_tool("https://github.com/obra/superpowers")
```

## Implementation

The installation logic is handled by `scripts/install.py`. It performs the following:
1. Parses the repo URL.
2. Clones to `~/.config/opencode/tools/`.
3. Scans the cloned directory for standard folders (`skills`, `agents`, `commands`, `plugins`).
4. Creates symbolic links in:
   - `~/.config/opencode/{skills,agents,commands,plugins}`
   - `~/.codex/skills`
   - `~/.gemini/skills` (if applicable)
