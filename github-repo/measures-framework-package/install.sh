#!/bin/bash
# ============================================================
# 麦哲思AI软件开发统一流程 — 安装脚本 v1.1
# MASE (Measures AI Software Engineering)
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEASURES_HOME="$HOME/.measures-framework"

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║  麦哲思AI软件开发统一流程  v1.1         ║"
echo "  ║  MASE (Measures AI Software Engineering)║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# ----------------------------------------------------------
# Step 0: Detect AI IDE skills directory
# ----------------------------------------------------------
DETECTED_SKILLS=""
for dir in "$HOME/.trae-cn/skills" "$HOME/.cursor/skills" "$HOME/.windsurf/skills"; do
    if [ -d "$dir" ]; then
        DETECTED_SKILLS="$dir"
        break
    fi
done

# ----------------------------------------------------------
# Step 1: Deploy templates
# ----------------------------------------------------------
echo "  [1/6] 部署项目模板..."
mkdir -p "$MEASURES_HOME/templates"
cp -r "$SCRIPT_DIR/templates/"* "$MEASURES_HOME/templates/"
echo "         → $MEASURES_HOME/templates/"

# ----------------------------------------------------------
# Step 2: Deploy project rules
# ----------------------------------------------------------
echo "  [2/6] 部署工程规则..."
if [ -f "$SCRIPT_DIR/project-rules.md" ]; then
    cp "$SCRIPT_DIR/project-rules.md" "$MEASURES_HOME/project-rules.md"
    echo "         → $MEASURES_HOME/project-rules.md"
fi

# ----------------------------------------------------------
# Step 3: Deploy Agent definitions
# ----------------------------------------------------------
echo "  [3/6] 部署 Agent 定义..."

if [ -n "$DETECTED_SKILLS" ]; then
    for agent_dir in "$SCRIPT_DIR/agents/"*/; do
        agent_name=$(basename "$agent_dir")
        target="$DETECTED_SKILLS/$agent_name"

        if [ -d "$target" ]; then
            echo "         ⚠ $agent_name 已存在，跳过 (如需覆盖请手动删除后重试)"
        else
            cp -r "$agent_dir" "$target"
            echo "         ✓ $agent_name"
        fi
    done
else
    echo "         ℹ 未检测到 AI IDE Skills 目录"
    echo "           Agent 文件已复制到 $MEASURES_HOME/agents/"
    echo "           请手动复制到你的 AI IDE skills 目录"
    cp -r "$SCRIPT_DIR/agents/" "$MEASURES_HOME/agents/"
fi

# ----------------------------------------------------------
# Step 4: Deploy Skills
# ----------------------------------------------------------
echo "  [4/6] 部署 Skills..."

if [ -n "$DETECTED_SKILLS" ]; then
    for skill_dir in "$SCRIPT_DIR/skills/"*/; do
        skill_name=$(basename "$skill_dir")
        target="$DETECTED_SKILLS/$skill_name"

        if [ -d "$target" ]; then
            echo "         ⚠ $skill_name 已存在，跳过 (如需覆盖请手动删除后重试)"
        else
            cp -r "$skill_dir" "$target"
            echo "         ✓ $skill_name"
        fi
    done
else
    echo "         ℹ 未检测到 AI IDE Skills 目录"
    echo "           Skills 文件已复制到 $MEASURES_HOME/skills/"
    echo "           请手动复制到你的 AI IDE skills 目录"
    cp -r "$SCRIPT_DIR/skills/" "$MEASURES_HOME/skills/"
fi

# ----------------------------------------------------------
# Step 5: Deploy docs
# ----------------------------------------------------------
echo "  [5/6] 部署文档..."
mkdir -p "$MEASURES_HOME/docs"
cp -r "$SCRIPT_DIR/docs/"* "$MEASURES_HOME/docs/"
echo "         → $MEASURES_HOME/docs/"

# ----------------------------------------------------------
# Step 6: Deploy training slides
# ----------------------------------------------------------
echo "  [6/6] 部署培训讲义及入口页面..."
mkdir -p "$MEASURES_HOME/training"
cp -r "$SCRIPT_DIR/training/"* "$MEASURES_HOME/training/"
echo "         → $MEASURES_HOME/training/"

# Deploy index.html
if [ -f "$SCRIPT_DIR/index.html" ]; then
    cp "$SCRIPT_DIR/index.html" "$MEASURES_HOME/index.html"
    echo "         → $MEASURES_HOME/index.html"
fi

# ----------------------------------------------------------
# Done
# ----------------------------------------------------------
echo ""
echo "  ┌──────────────────────────────────────────┐"
echo "  │  ✓ 安装完成！                            │"
echo "  │                                          │"
echo "  │  模板位置: ~/.measures-framework/templates/"
echo "  │  Agents:  ~/.measures-framework/agents/"
echo "  │  规则位置: ~/.measures-framework/project-rules.md"
echo "  │  文档位置: ~/.measures-framework/docs/"
echo "  │  讲义位置: ~/.measures-framework/training/"
echo "  │                                          │"
echo "  │  快速开始:                                │"
echo "  │  1. mase init my-project -p my_app        │"
echo "  │  2. cd my-project                        │"
echo "  │  3. 对 AI 说: '创建新项目' → 框架自动运转  │"
echo "  └──────────────────────────────────────────┘"
echo ""
