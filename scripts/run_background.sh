#!/bin/bash
# Prometheus Research - 后台执行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../Logs"
PROJECTS_DIR="$SCRIPT_DIR/../Projects"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 生成日志文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/executor_$TIMESTAMP.log"

echo "🚀 启动 Prometheus Research 后台任务..."
echo "📁 日志文件: $LOG_FILE"
echo ""

# 检查是否有项目
if [ -z "$1" ]; then
    # 查找最新的项目
    LATEST_PROJECT=$(ls -td "$PROJECTS_DIR"/*/ 2>/dev/null | head -1)
    if [ -z "$LATEST_PROJECT" ]; then
        echo "❌ 没有找到项目。请先启动一个研究："
        echo "   python scripts/start_research.py --topic \"研究主题\""
        exit 1
    fi
    PROJECT="$LATEST_PROJECT"
    echo "📌 使用最新项目: $(basename "$PROJECT")"
else
    PROJECT="$PROJECTS_DIR/$1"
    if [ ! -d "$PROJECT" ]; then
        echo "❌ 项目不存在: $1"
        exit 1
    fi
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo "  后台执行中... 使用以下命令查看进度："
echo ""
echo "  # 查看实时日志"
echo "  tail -f $LOG_FILE"
echo ""
echo "  # 或使用 less 浏览"
echo "  less $LOG_FILE"
echo "─────────────────────────────────────────────────────────────"
echo ""

# 后台执行
nohup python "$SCRIPT_DIR/automation/task_executor.py" \
    --project "$PROJECT" \
    --loop \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo "✅ 已启动后台任务 (PID: $PID)"
echo ""
echo "监控命令："
echo "  查看日志: tail -f $LOG_FILE"
echo "  查看状态: python scripts/prometheus.py --status"
echo "  停止任务: kill $PID"
