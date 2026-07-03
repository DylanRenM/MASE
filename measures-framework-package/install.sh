#!/bin/bash
# ============================================================
# 麦哲思AI软件开发统一流程 — 安装脚本 v1.0
# MASE (Measures AI Software Engineering)
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEASURES_HOME="$HOME/.measures-framework"
TRAE_SKILLS="$HOME/.trae-cn/skills"

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║  麦哲思AI软件开发统一流程  v1.0         ║"
echo "  ║  MASE (Measures AI Software Engineering)        ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# ----------------------------------------------------------
# Step 1: Deploy templates
# ----------------------------------------------------------
echo "  [1/4] 部署项目模板..."
mkdir -p "$MEASURES_HOME/templates"
cp -r "$SCRIPT_DIR/templates/"* "$MEASURES_HOME/templates/"
echo "         → $MEASURES_HOME/templates/"

# ----------------------------------------------------------
# Step 2: Deploy Skills to Trae IDE
# ----------------------------------------------------------
echo "  [2/4] 部署 AI Skills..."

if [ -d "$TRAE_SKILLS" ]; then
    for skill_dir in "$SCRIPT_DIR/skills/"*/; do
        skill_name=$(basename "$skill_dir")
        target="$TRAE_SKILLS/$skill_name"
        
        if [ -d "$target" ]; then
            echo "         ⚠ $skill_name 已存在，跳过 (如需覆盖请手动删除后重试)"
        else
            cp -r "$skill_dir" "$target"
            echo "         ✓ $skill_name"
        fi
    done
else
    echo "         ⚠ 未找到 Trae IDE Skills 目录 ($TRAE_SKILLS)"
    echo "          Skills 文件已复制到 $MEASURES_HOME/skills/"
    echo "          请手动复制到 ~/.trae-cn/skills/"
    cp -r "$SCRIPT_DIR/skills/" "$MEASURES_HOME/skills/"
fi

# ----------------------------------------------------------
# Step 3: Deploy docs
# ----------------------------------------------------------
echo "  [3/4] 部署文档..."
mkdir -p "$MEASURES_HOME/docs"
cp -r "$SCRIPT_DIR/docs/"* "$MEASURES_HOME/docs/"
echo "         → $MEASURES_HOME/docs/"

# ----------------------------------------------------------
# Step 4: Deploy training slides
# ----------------------------------------------------------
echo "  [4/4] 部署培训讲义..."
mkdir -p "$MEASURES_HOME/training"
cp -r "$SCRIPT_DIR/training/"* "$MEASURES_HOME/training/"
echo "         → $MEASURES_HOME/training/"

# ----------------------------------------------------------
# Done
# ----------------------------------------------------------
echo ""
echo "  ┌──────────────────────────────────────────┐"
echo "  │  ✓ 安装完成！                            │"
echo "  │                                          │"
echo "  │  模板位置: ~/.measures-framework/templates/"
echo "  │  文档位置: ~/.measures-framework/docs/"
echo "  │  讲义位置: ~/.measures-framework/training/"
echo "  │                                          │"
echo "  │  快速开始:                                │"
echo "  │  1. cp -r ~/.measures-framework/templates/* \\"
echo "  │       openspec/changes/_template/"
echo "  │  2. 对 AI 说: '创建新项目 {项目名}'        │"
echo "  └──────────────────────────────────────────┘"
echo ""
