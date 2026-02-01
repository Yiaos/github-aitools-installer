# GitHub Tools Installer

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
*   **Idempotent Updates**: Run it again to update (git pull) and refresh links.
*   **Non-Destructive**: Backs up existing local directories before linking.

## 📦 Installation

This tool can install itself!

```bash
# Clone to your tools directory
mkdir -p ~/.config/opencode/tools
git clone https://github.com/Yiaos/github-tools-installer.git ~/.config/opencode/tools/github-tools-installer

# Link it to OpenCode manually (first time only)
mkdir -p ~/.config/opencode/skills
ln -s ~/.config/opencode/tools/github-tools-installer/skills/github-tools-installer ~/.config/opencode/skills/github-tools-installer
```

## 🛠 Usage

Once installed, just ask your AI Agent:

> "Install https://github.com/obra/superpowers"

> "Install https://github.com/wshobson/agents"

Or runs as a python script:

```bash
python3 ~/.config/opencode/tools/github-tools-installer/skills/github-tools-installer/scripts/install.py <repo_url>
```

## 📂 Repository Structure

```text
├── README.md
├── README_CN.md
└── skills/
    └── github-tools-installer/
        ├── SKILL.md
        └── scripts/
            └── install.py
```
