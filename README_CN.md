# GitHub AI Tools Installer (AI 工具通用安装器)

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
    *   `hooks/` (钩子)
    *   `mcp/` (MCP 协议服务)
    *   `prompts/` (提示词模板)
*   **全量更新**: 支持一键更新所有已安装的工具 (`update_all_tools`)。
*   **安装摘要**: 安装后自动显示工具描述和验证方法。
*   **非破坏性**: 链接前自动备份冲突的本地目录。

## 📦 安装方法

本工具也是一个 Skill，可以自己安装自己！

```bash
# 1. 克隆到您的 tools 目录
mkdir -p ~/.config/opencode/tools
git clone https://github.com/Yiaos/github-aitools-installer.git ~/.config/opencode/tools/github-aitools-installer

# 2. 手动链接到 OpenCode (仅第一次需要)
mkdir -p ~/.config/opencode/skills
ln -s ~/.config/opencode/tools/github-aitools-installer/skills/github-aitools-installer ~/.config/opencode/skills/github-aitools-installer
```

## 🛠 使用指南

### 1. 安装新工具
直接在对话中命令：
> "帮我安装 https://github.com/obra/superpowers"

### 2. 检查更新全部
> "帮我更新所有 AI 工具"

或者运行脚本：
```bash
python3 ~/.config/opencode/tools/github-aitools-installer/skills/github-aitools-installer/scripts/install.py --all
```

## 📂 仓库结构

```text
├── README.md       # 英文文档
├── README_CN.md    # 中文文档
└── skills/
    └── github-aitools-installer/
        ├── SKILL.md
        └── scripts/
            └── install.py
```
