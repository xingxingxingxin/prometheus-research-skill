#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Prometheus - 系统启动验证器
=====================================

执行系统启动时的强制检查流程，确保所有组件就绪。

用法:
    python system_validator.py [--fix]
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Windows 编码修复
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class SystemValidator:
    """系统启动验证器"""
    
    def __init__(self, project_root: Path = None, auto_fix: bool = False):
        self.project_root = project_root or PROJECT_ROOT
        self.auto_fix = auto_fix
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.fixes_applied: List[str] = []
        
    def validate_all(self) -> bool:
        """执行所有验证检查"""
        print("=" * 70)
        print("  Project Prometheus - 系统启动验证")
        print("=" * 70)
        print(f"  项目目录: {self.project_root}")
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        
        # 执行检查
        checks = [
            ("1. 目录结构", self._check_directories),
            ("2. 状态文件", self._check_state_files),
            ("3. 任务清单", self._check_task_list),
            ("4. Git 状态", self._check_git),
            ("5. Python 依赖", self._check_dependencies),
            ("6. GEP 模块", self._check_gep),
            ("7. Ralph Loop", self._check_ralph),
            ("8. Claude Code Hooks", self._check_hooks),
            ("9. 权限配置", self._check_permissions),
        ]
        
        all_passed = True
        for name, check_func in checks:
            print(f"检查 {name}...", end=" ")
            try:
                result = check_func()
                if result:
                    print("[OK] 通过")
                else:
                    print("[X] 失败")
                    all_passed = False
            except Exception as e:
                print(f"[X] 错误: {e}")
                self.errors.append(f"{name}: {e}")
                all_passed = False
        
        print()
        print("=" * 70)
        
        # 显示摘要
        if self.warnings:
            print("\n[!] 警告:")
            for w in self.warnings:
                print(f"  - {w}")
        
        if self.fixes_applied:
            print("\n[FIX] 已自动修复:")
            for f in self.fixes_applied:
                print(f"  - {f}")
        
        if self.errors:
            print("\n[X] 错误:")
            for e in self.errors:
                print(f"  - {e}")
        
        print()
        if all_passed:
            print("[OK] 所有检查通过，系统就绪！")
        else:
            print("[X] 部分检查未通过，请修复后重试")
            if self.auto_fix:
                print("   提示: 部分问题已自动修复，请重新运行验证")
        
        return all_passed
    
    def _check_directories(self) -> bool:
        """检查目录结构"""
        required_dirs = [
            "Core",
            "Core/prompts",
            "Core/tools",
            "Core/gep",
            "Projects",
            "Logs",
            "Communication/inbox",
            "Communication/outbox",
            "Checkpoints",
            ".claude",
            ".claude/hooks",
            ".claude/skills",
        ]
        
        all_exist = True
        for d in required_dirs:
            dir_path = self.project_root / d
            if not dir_path.exists():
                if self.auto_fix:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.fixes_applied.append(f"创建目录: {d}")
                else:
                    self.errors.append(f"目录不存在: {d}")
                    all_exist = False
        
        return all_exist
    
    def _check_state_files(self) -> bool:
        """检查项目状态文件"""
        # 检查是否有项目目录
        projects_dir = self.project_root / "Projects"
        if not projects_dir.exists():
            self.warnings.append("Projects 目录不存在，运行 start_research.py 创建新项目")
            return True

        # 检查各个项目的状态文件
        project_dirs = [d for d in projects_dir.iterdir() if d.is_dir() and d.name != "current"]
        if not project_dirs:
            self.warnings.append("未找到任何项目，运行 start_research.py 创建新项目")
            return True

        for proj_dir in project_dirs[:3]:  # 只检查前3个项目
            state_file = proj_dir / "state.json"
            if state_file.exists():
                try:
                    with open(state_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    self.errors.append(f"{proj_dir.name}/state.json 格式错误")

        return True

    def _check_task_list(self) -> bool:
        """检查任务清单"""
        # 检查各项目的任务清单
        projects_dir = self.project_root / "Projects"
        if projects_dir.exists():
            project_dirs = [d for d in projects_dir.iterdir() if d.is_dir() and d.name != "current"]
            for proj_dir in project_dirs[:3]:
                tasks_file = proj_dir / "research_tasks.json"
                if not tasks_file.exists():
                    self.warnings.append(f"{proj_dir.name}/research_tasks.json 不存在")

        return True
    
    def _check_git(self) -> bool:
        """检查 Git 状态"""
        git_dir = self.project_root / ".git"
        
        if not git_dir.exists():
            if self.auto_fix:
                try:
                    subprocess.run(
                        ['git', 'init'],
                        cwd=self.project_root,
                        check=True,
                        capture_output=True
                    )
                    self.fixes_applied.append("初始化 Git 仓库")
                    return True
                except Exception as e:
                    self.errors.append(f"无法初始化 Git: {e}")
                    return False
            else:
                self.warnings.append("Git 仓库未初始化")
                return True
        
        # 检查是否有未提交的更改
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                self.warnings.append("有未提交的更改")
        except Exception:
            pass
        
        return True
    
    def _check_dependencies(self) -> bool:
        """检查 Python 依赖"""
        req_file = self.project_root / "requirements.txt"
        
        if not req_file.exists():
            self.warnings.append("requirements.txt 不存在")
            return True
        
        # 检查关键依赖
        critical_deps = ['anthropic', 'rich', 'requests']
        missing = []
        
        for dep in critical_deps:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        
        if missing:
            self.warnings.append(f"缺少依赖: {', '.join(missing)}")
            if self.auto_fix:
                self.warnings.append("请手动运行: pip install -r requirements.txt")
        
        return len(missing) == 0

    def _check_gep(self) -> bool:
        """检查 GEP 模块"""
        gep_dir = self.project_root / "Core" / "gep"
        
        if not gep_dir.exists():
            self.warnings.append("GEP 模块目录不存在")
            return False
        
        # 检查 Gene 库
        gene_file = gep_dir / "defaults" / "genes.json"
        if not gene_file.exists():
            self.warnings.append("Gene 库文件不存在")
            return False
        
        # 验证 Gene 库格式
        try:
            with open(gene_file, 'r', encoding='utf-8') as f:
                gene_data = json.load(f)
            
            if 'genes' not in gene_data:
                self.errors.append("Gene 库格式错误: 缺少 'genes' 字段")
                return False
            
            if len(gene_data['genes']) == 0:
                self.warnings.append("Gene 库为空")
            
            return True
        except json.JSONDecodeError:
            self.errors.append("Gene 库 JSON 格式错误")
            return False
    
    def _check_ralph(self) -> bool:
        """检查 Ralph Loop 配置"""
        hooks_dir = self.project_root / ".claude" / "hooks"
        
        # 检查 Stop Hook
        stop_hook = hooks_dir / "ralph-stop.sh"
        stop_hook_cmd = hooks_dir / "ralph-stop.cmd"
        
        if not stop_hook.exists() and not stop_hook_cmd.exists():
            self.warnings.append("Ralph Stop Hook 不存在")
            return False
        
        # 检查 settings.local.json
        settings_file = self.project_root / ".claude" / "settings.local.json"
        if not settings_file.exists():
            self.warnings.append("Claude Code 设置文件不存在")
            return False
        
        # 验证 settings.local.json 格式
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            if 'hooks' not in settings:
                self.warnings.append("settings.local.json 缺少 hooks 配置")
                return False
            
            return True
        except json.JSONDecodeError:
            self.errors.append("settings.local.json JSON 格式错误")
            return False
    
    def _check_permissions(self) -> bool:
        """检查权限配置"""
        # 检查关键目录的写入权限
        writable_dirs = [
            "Logs",
            "Communication/inbox",
            "Communication/outbox",
            "Projects",
        ]
        
        for d in writable_dirs:
            dir_path = self.project_root / d
            if dir_path.exists():
                # 尝试创建测试文件
                test_file = dir_path / ".write_test"
                try:
                    test_file.write_text("test", encoding='utf-8')
                    test_file.unlink()
                except PermissionError:
                    self.errors.append(f"无写入权限: {d}")
                    return False
        
        return True
    
    def _check_hooks(self) -> bool:
        """检查 Claude Code Hooks 配置"""
        hooks_dir = self.project_root / ".claude" / "hooks"
        settings_file = self.project_root / ".claude" / "settings.local.json"
        
        # 检查 hooks 目录
        if not hooks_dir.exists():
            if self.auto_fix:
                hooks_dir.mkdir(parents=True, exist_ok=True)
                self.fixes_applied.append("创建 .claude/hooks 目录")
            else:
                self.warnings.append(".claude/hooks 目录不存在")
        
        # 检查 settings.local.json
        if not settings_file.exists():
            self.warnings.append("settings.local.json 不存在，Ralph Loop 可能无法工作")
        else:
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                if 'hooks' not in settings:
                    self.warnings.append("settings.local.json 缺少 hooks 配置")
            except json.JSONDecodeError:
                self.errors.append("settings.local.json 格式错误")
                return False
        
        # 检查 Stop Hook 脚本
        stop_hook_sh = hooks_dir / "ralph-stop.sh"
        stop_hook_cmd = hooks_dir / "ralph-stop.cmd"
        
        if not stop_hook_sh.exists() and not stop_hook_cmd.exists():
            self.warnings.append("Ralph Stop Hook 脚本不存在")
        else:
            # 检查文件是否可执行（Linux/macOS）
            if stop_hook_sh.exists() and sys.platform != 'win32':
                import stat
                mode = stop_hook_sh.stat().st_mode
                if not mode & stat.S_IXUSR:
                    self.warnings.append("ralph-stop.sh 不可执行，运行: chmod +x .claude/hooks/ralph-stop.sh")
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='系统启动验证器')
    parser.add_argument('--fix', action='store_true', help='自动修复发现的问题')
    args = parser.parse_args()
    
    validator = SystemValidator(auto_fix=args.fix)
    success = validator.validate_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
