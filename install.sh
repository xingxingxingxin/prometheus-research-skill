#!/bin/bash
# Prometheus Research Skill 安装脚本

set -e

echo "🚀 安装 Prometheus Research Skill..."

# 检测操作系统
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    SKILL_DIR="$USERPROFILE\\.claude\\skills\\prometheus-research"
else
    SKILL_DIR="$HOME/.claude/skills/prometheus-research"
fi

# 创建目录
mkdir -p "$SKILL_DIR"

# 复制文件
echo "📁 复制文件..."
cp -r . "$SKILL_DIR/"

# 安装 Python 依赖
if [ -f "scripts/requirements.txt" ]; then
    echo "📦 安装 Python 依赖..."
    pip install -r "$SKILL_DIR/scripts/requirements.txt"
fi

# 设置权限
chmod +x "$SKILL_DIR/scripts/prometheus.py" 2>/dev/null || true
chmod +x "$SKILL_DIR/scripts/start_research.py" 2>/dev/null || true

echo "✅ 安装完成!"
echo ""
echo "使用方法："
echo "  在 Claude Code 中说："
echo "    启动研究 [研究主题]"
echo "    继续研究"
echo ""
echo "安装位置: $SKILL_DIR"
