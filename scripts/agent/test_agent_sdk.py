#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent SDK 集成测试

验证 PrometheusAgent 是否正确使用 Anthropic SDK。
"""

import sys
import os
from pathlib import Path

# 设置输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Core"))
sys.path.insert(0, str(PROJECT_ROOT / "agent"))

def test_sdk_availability():
    """测试 SDK 可用性"""
    print("=" * 60)
    print("  Agent SDK 集成测试")
    print("=" * 60)
    print()
    
    # 1. 检查 Anthropic SDK
    print("[1] 检查 Anthropic SDK...")
    try:
        import anthropic
        print(f"    [OK] anthropic 版本: {anthropic.__version__}")
        anthropic_available = True
    except ImportError:
        print("    [X] anthropic 未安装")
        print("       安装: pip install anthropic")
        anthropic_available = False
    
    print()
    
    # 2. 检查环境变量
    print("[2] 检查 API Key...")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        print(f"    [OK] ANTHROPIC_API_KEY 已设置 ({len(api_key)} 字符)")
    else:
        print("    [!] ANTHROPIC_API_KEY 未设置")
        print("       设置: set ANTHROPIC_API_KEY=sk-xxx")
    
    print()
    
    # 3. 检查 PrometheusAgent
    print("[3] 检查 PrometheusAgent...")
    try:
        from prometheus_agent import (
            PrometheusAgent, AgentConfig, Phase, AgentContext,
            ANTHROPIC_SDK_AVAILABLE
        )
        print(f"    [OK] PrometheusAgent 导入成功")
        print(f"    [OK] ANTHROPIC_SDK_AVAILABLE = {ANTHROPIC_SDK_AVAILABLE}")
        
        # 检查关键方法
        agent = PrometheusAgent(config=AgentConfig())
        print(f"    [OK] _execute_with_claude 方法: {hasattr(agent, '_execute_with_claude')}")
        print(f"    [OK] _execute_with_cli_fallback 方法: {hasattr(agent, '_execute_with_cli_fallback')}")
        
    except ImportError as e:
        print(f"    [X] 导入失败: {e}")
        return False
    
    print()
    
    # 4. 总结
    print("=" * 60)
    print("  测试总结")
    print("=" * 60)
    print()
    
    if anthropic_available and api_key:
        print("[OK] Agent SDK 完全可用")
        print("   可以直接调用 Claude API")
        return True
    elif anthropic_available:
        print("[!] Agent SDK 已安装但未配置 API Key")
        print("   将使用 CLI 回退模式")
        return True
    else:
        print("[X] Agent SDK 不可用")
        print("   请安装: pip install anthropic")
        return False


def test_simple_call():
    """测试简单的 API 调用"""
    print()
    print("=" * 60)
    print("  API 调用测试")
    print("=" * 60)
    print()
    
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    
    if not api_key:
        print("[!] 跳过: 未设置 ANTHROPIC_API_KEY")
        return False
    
    try:
        import anthropic
        
        print("[1] 初始化客户端...")
        client = anthropic.Anthropic(api_key=api_key)
        print("    [OK] 客户端初始化成功")
        
        print()
        print("[2] 发送测试请求...")
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": "Say 'Hello, Prometheus!'"}]
        )
        
        print("    [OK] 请求成功")
        print(f"    响应: {response.content[0].text}")
        
        return True
        
    except Exception as e:
        print(f"[X] API 调用失败: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent SDK 集成测试")
    parser.add_argument("--call", action="store_true", help="测试 API 调用")
    args = parser.parse_args()
    
    success = test_sdk_availability()
    
    if args.call and success:
        test_simple_call()
