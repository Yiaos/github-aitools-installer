# GitHub AI Tools Installer

**The universal package manager for AI Agents.**
Installs Skills, Agents, Plugins, Commands, Hooks, and Prompts from any GitHub repository into your AI environment (OpenCode, Codex, Gemini).

[中文文档 (Chinese README)](README_CN.md)

## 🚀 Features

*   **Universal Compatibility**: Converts any GitHub repository into an installed extension.
*   **Multi-Agent Support**: Installs to OpenCode, Codex, and Gemini simultaneously.
*   **Smart Detection**: Automatically finds and links:
    *   `skills/`
    *   `agents/`
    *   `plugins/`
    *   `commands/`
    *   `hooks/` (New!)
    *   `mcp/` (Model Context Protocol)
    *   `prompts/`
*   **Update All**: Update all installed tools with one command (`update_all_tools`).
*   **Post-Install Summary**: Shows tool capabilities and verification steps after installation.
*   **Non-Destructive**: Backs up existing local directories before linking.

## 📦 Installation

This tool can install itself!

```bash
# Clone to your tools directory
mkdir -p ~/.config/opencode/tools
git clone https://github.com/Yiaos/github-aitools-installer.git ~/.config/opencode/tools/github-aitools-installer

# Link it to OpenCode manually (first time only)
mkdir -p ~/.config/opencode/skills
ln -s ~/.config/opencode/tools/github-aitools-installer/skills/github-aitools-installer ~/.config/opencode/skills/github-aitools-installer
```

## 🛠 Usage

### 1. Install a new tool
Just asking your Agent:
> "Install https://github.com/obra/superpowers"

### 2. Update ALL tools
> "Update all AI tools"

Or runs as a python script:
```bash
python3 ~/.config/opencode/tools/github-aitools-installer/skills/github-aitools-installer/scripts/install.py --all
```

## 📂 Repository Structure

```text
├── README.md
├── README_CN.md
└── skills/
    └── github-aitools-installer/
        ├── SKILL.md
        └── scripts/
            └── install.py
```
