# GitHub Tools Installer (GitHub 工具安装器)

**AI Agent 的通用包管理器**
能够将 **任何 GitHub 仓库** 中的 Skills, Agents, Plugins, Commands, Hooks 和 Prompts 安装到您的 AI 环境中 (OpenCode, Codex, Gemini)。

[English README](README.md)

## 🚀 功能特性

*   **通用兼容**: 将任何 GitHub 仓库转换为可安装的扩展包。
*   **多 Agent 支持**: 一次安装，同时支持 OpenCode, Codex, 和 Gemini。
*   **智能检测**: 自动发现并链接以下组件:
    *   `skills/` (技能)
    *   `agents/` (智能体)
    *   `plugins/` (插件)
    *   `commands/` (指令)
    *   `hooks/` (钩子 - 新!)
    *   `mcp/` (MCP 协议服务)
    *   `prompts/` (提示词模板)
*   **幂等更新**: 再次运行即可自动更新代码 (git pull) 并刷新链接。
*   **非破坏性**: 在链接前会自动备份已存在的本地目录，防止数据丢失。

## 📦 安装方法

本工具也是一个 Skill，可以自己安装自己！

```bash
# 1. 克隆到您的 tools 目录
mkdir -p ~/.config/opencode/tools
git clone https://github.com/Yiaos/github-tools-installer.git ~/.config/opencode/tools/github-tools-installer

# 2. 手动链接到 OpenCode (仅第一次需要)
mkdir -p ~/.config/opencode/skills
ln -s ~/.config/opencode/tools/github-tools-installer/skills/github-tools-installer ~/.config/opencode/skills/github-tools-installer
```

## 🛠 使用指南

安装完成后，直接在该 AI Agent 的对话框中下达命令：

> "帮我安装 https://github.com/obra/superpowers"

> "Install https://github.com/wshobson/agents"

或者作为 Python 脚本手动运行:

```bash
python3 ~/.config/opencode/tools/github-tools-installer/skills/github-tools-installer/scripts/install.py <仓库URL>
```

## 📂 仓库结构

```text
├── README.md       # 英文文档
├── README_CN.md    # 中文文档
└── skills/
    └── github-tools-installer/
        ├── SKILL.md
        └── scripts/
            └── install.py
```
