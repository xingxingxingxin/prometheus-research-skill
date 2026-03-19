#!/bin/bash
# Prometheus Research - 日志监控脚本

LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../Logs" && pwd)"

echo "📊 Prometheus Research 日志监控"
echo "================================"
echo ""

# 查找最新的日志文件
LATEST_LOG=$(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "❌ 没有找到日志文件"
    echo ""
    echo "启动后台任务:"
    echo "  ./scripts/run_background.sh"
    exit 1
fi

echo "📁 日志文件: $LATEST_LOG"
echo ""

# 显示选项
echo "选择操作:"
echo "  1) 实时查看日志 (tail -f)"
echo "  2) 查看最近 50 行"
echo "  3) 查看完整日志"
echo "  4) 搜索关键词"
echo "  5) 查看进度摘要"
echo ""
read -p "请选择 [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "按 Ctrl+C 退出"
        echo "─────────────────────────────────────────"
        tail -f "$LATEST_LOG"
        ;;
    2)
        echo ""
        echo "─────────────────────────────────────────"
        tail -50 "$LATEST_LOG"
        ;;
    3)
        echo ""
        echo "─────────────────────────────────────────"
        cat "$LATEST_LOG"
        ;;
    4)
        read -p "输入搜索关键词: " keyword
        echo ""
        echo "─────────────────────────────────────────"
        grep -i "$keyword" "$LATEST_LOG" | tail -20
        ;;
    5)
        echo ""
        echo "─────────────────────────────────────────"
        echo "📈 进度摘要:"
        echo ""
        grep -E "(Phase|任务|TASK_COMPLETE|ERROR|WARNING)" "$LATEST_LOG" | tail -30
        ;;
    *)
        echo "无效选择"
        ;;
esac
