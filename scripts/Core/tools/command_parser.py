"""
命令解析工具
============

解析 commands.txt 中的指令，支持多种命令类型的结构化解析。

支持的命令类型:
- APPROVE: 批准请求
- REJECT: 拒绝请求
- PAUSE: 暂停项目
- RESUME: 恢复项目
- NEW_PROJECT: 创建新项目
- MODIFY: 修改项目配置

命令格式:
    COMMAND [target] [options]
    # 注释内容
    PARAM: value
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CommandType(Enum):
    """命令类型枚举"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    NEW_PROJECT = "NEW_PROJECT"
    MODIFY = "MODIFY"
    COMMENT = "COMMENT"  # 注释行
    UNKNOWN = "UNKNOWN"


@dataclass
class ParsedCommand:
    """解析后的命令对象"""
    command_type: CommandType
    raw_line: str
    line_number: int
    target: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    options: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'command_type': self.command_type.value,
            'raw_line': self.raw_line,
            'line_number': self.line_number,
            'target': self.target,
            'parameters': self.parameters,
            'options': self.options,
            'comments': self.comments,
            'timestamp': self.timestamp
        }

    def is_valid(self) -> bool:
        """检查命令是否有效"""
        return self.command_type != CommandType.UNKNOWN


@dataclass
class CommandFile:
    """命令文件对象"""
    file_path: str
    commands: List[ParsedCommand] = field(default_factory=list)
    parse_errors: List[Dict[str, Any]] = field(default_factory=list)
    parse_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def get_commands_by_type(self, cmd_type: CommandType) -> List[ParsedCommand]:
        """获取特定类型的命令"""
        return [cmd for cmd in self.commands if cmd.command_type == cmd_type]

    def get_valid_commands(self) -> List[ParsedCommand]:
        """获取所有有效命令"""
        return [cmd for cmd in self.commands if cmd.is_valid()]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'file_path': self.file_path,
            'commands': [cmd.to_dict() for cmd in self.commands],
            'parse_errors': self.parse_errors,
            'parse_time': self.parse_time,
            'total_commands': len(self.commands),
            'valid_commands': len(self.get_valid_commands())
        }


class CommandParser:
    """命令解析器"""

    # 命令正则模式
    COMMAND_PATTERN = re.compile(
        r'^(APPROVE|REJECT|PAUSE|RESUME|NEW_PROJECT|MODIFY)\s*'
        r'(.*?)$',
        re.IGNORECASE
    )

    # 参数行模式 (PARAM: value 或 PARAM=value)
    PARAM_PATTERN = re.compile(
        r'^([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(.*?)$'
    )

    # 注释模式
    COMMENT_PATTERN = re.compile(r'^#\s*(.*?)$')

    # 命令的必需参数
    REQUIRED_PARAMS = {
        CommandType.NEW_PROJECT: ['name'],
        CommandType.MODIFY: ['target']
    }

    # 命令的可选参数
    OPTIONAL_PARAMS = {
        CommandType.APPROVE: ['reason', 'priority'],
        CommandType.REJECT: ['reason', 'alternative'],
        CommandType.PAUSE: ['duration', 'reason'],
        CommandType.RESUME: ['checkpoint'],
        CommandType.NEW_PROJECT: ['description', 'template', 'priority'],
        CommandType.MODIFY: ['field', 'value', 'reason']
    }

    def __init__(self, strict_mode: bool = False):
        """
        初始化命令解析器

        Args:
            strict_mode: 严格模式，启用时会验证必需参数
        """
        self.strict_mode = strict_mode

    def parse_file(self, file_path: str) -> CommandFile:
        """
        解析命令文件

        Args:
            file_path: 命令文件路径

        Returns:
            CommandFile 对象
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"命令文件不存在: {file_path}")

        command_file = CommandFile(file_path=str(path.absolute()))

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_command = None
        pending_comments = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 检查是否为注释行
            comment_match = self.COMMENT_PATTERN.match(line)
            if comment_match:
                comment_text = comment_match.group(1)
                if current_command:
                    current_command.comments.append(comment_text)
                else:
                    pending_comments.append(comment_text)
                continue

            # 尝试解析为命令
            cmd_match = self.COMMAND_PATTERN.match(line)
            if cmd_match:
                # 保存前一个命令
                if current_command:
                    self._validate_command(current_command, command_file)
                    command_file.commands.append(current_command)

                # 解析新命令
                cmd_type_str = cmd_match.group(1).upper()
                cmd_args = cmd_match.group(2).strip()

                try:
                    cmd_type = CommandType[cmd_type_str]
                except KeyError:
                    cmd_type = CommandType.UNKNOWN

                # 分割目标和其他参数
                target, options = self._parse_arguments(cmd_args)

                current_command = ParsedCommand(
                    command_type=cmd_type,
                    raw_line=line,
                    line_number=line_num,
                    target=target,
                    options=options,
                    comments=pending_comments.copy()
                )
                pending_comments.clear()
                continue

            # 尝试解析为参数行
            param_match = self.PARAM_PATTERN.match(line)
            if param_match and current_command:
                param_name = param_match.group(1).lower()
                param_value = self._parse_param_value(param_match.group(2))
                current_command.parameters[param_name] = param_value
                continue

            # 无法识别的行
            if current_command:
                # 如果当前有命令，将无法识别的行作为额外参数或警告
                if ':' in line or '=' in line:
                    # 尝试作为参数
                    parts = re.split(r'[:=]', line, 1)
                    if len(parts) == 2:
                        current_command.parameters[parts[0].strip().lower()] = self._parse_param_value(parts[1].strip())
                else:
                    # 记录警告
                    logger.warning(f"无法识别的行 {line_num}: {line}")
            else:
                logger.warning(f"命令外的无法识别内容 (行 {line_num}): {line}")

        # 保存最后一个命令
        if current_command:
            self._validate_command(current_command, command_file)
            command_file.commands.append(current_command)

        logger.info(f"解析完成: {len(command_file.commands)} 条命令, {len(command_file.parse_errors)} 个错误")
        return command_file

    def parse_string(self, content: str) -> CommandFile:
        """
        解析命令字符串

        Args:
            content: 命令内容字符串

        Returns:
            CommandFile 对象
        """
        # 创建临时文件对象
        command_file = CommandFile(file_path="<string>")

        lines = content.strip().split('\n')
        current_command = None
        pending_comments = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            if not line:
                continue

            comment_match = self.COMMENT_PATTERN.match(line)
            if comment_match:
                comment_text = comment_match.group(1)
                if current_command:
                    current_command.comments.append(comment_text)
                else:
                    pending_comments.append(comment_text)
                continue

            cmd_match = self.COMMAND_PATTERN.match(line)
            if cmd_match:
                if current_command:
                    self._validate_command(current_command, command_file)
                    command_file.commands.append(current_command)

                cmd_type_str = cmd_match.group(1).upper()
                cmd_args = cmd_match.group(2).strip()

                try:
                    cmd_type = CommandType[cmd_type_str]
                except KeyError:
                    cmd_type = CommandType.UNKNOWN

                target, options = self._parse_arguments(cmd_args)

                current_command = ParsedCommand(
                    command_type=cmd_type,
                    raw_line=line,
                    line_number=line_num,
                    target=target,
                    options=options,
                    comments=pending_comments.copy()
                )
                pending_comments.clear()
                continue

            param_match = self.PARAM_PATTERN.match(line)
            if param_match and current_command:
                param_name = param_match.group(1).lower()
                param_value = self._parse_param_value(param_match.group(2))
                current_command.parameters[param_name] = param_value

        if current_command:
            self._validate_command(current_command, command_file)
            command_file.commands.append(current_command)

        return command_file

    def parse_single_line(self, line: str) -> ParsedCommand:
        """
        解析单行命令

        Args:
            line: 命令行

        Returns:
            ParsedCommand 对象
        """
        line = line.strip()

        # 检查注释
        comment_match = self.COMMENT_PATTERN.match(line)
        if comment_match:
            return ParsedCommand(
                command_type=CommandType.COMMENT,
                raw_line=line,
                line_number=1,
                comments=[comment_match.group(1)]
            )

        # 解析命令
        cmd_match = self.COMMAND_PATTERN.match(line)
        if cmd_match:
            cmd_type_str = cmd_match.group(1).upper()
            cmd_args = cmd_match.group(2).strip()

            try:
                cmd_type = CommandType[cmd_type_str]
            except KeyError:
                cmd_type = CommandType.UNKNOWN

            target, options = self._parse_arguments(cmd_args)

            return ParsedCommand(
                command_type=cmd_type,
                raw_line=line,
                line_number=1,
                target=target,
                options=options
            )

        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            raw_line=line,
            line_number=1
        )

    def _parse_arguments(self, args_str: str) -> tuple:
        """
        解析命令参数

        Args:
            args_str: 参数字符串

        Returns:
            (target, options) 元组
        """
        if not args_str:
            return None, []

        parts = args_str.split()
        target = parts[0] if parts else None
        options = parts[1:] if len(parts) > 1 else []

        return target, options

    def _parse_param_value(self, value_str: str) -> Any:
        """
        解析参数值

        Args:
            value_str: 参数值字符串

        Returns:
            解析后的值
        """
        value_str = value_str.strip()

        # 尝试解析为布尔值
        if value_str.lower() in ('true', 'yes', 'on'):
            return True
        if value_str.lower() in ('false', 'no', 'off'):
            return False

        # 尝试解析为数字
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # 尝试解析为 JSON
        if value_str.startswith('{') or value_str.startswith('['):
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                pass

        # 移除引号
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        return value_str

    def _validate_command(self, command: ParsedCommand, command_file: CommandFile):
        """
        验证命令

        Args:
            command: 要验证的命令
            command_file: 命令文件对象（用于记录错误）
        """
        if not self.strict_mode:
            return

        # 检查必需参数
        required = self.REQUIRED_PARAMS.get(command.command_type, [])
        missing = []

        for param in required:
            if param not in command.parameters:
                if param == 'target' and command.target:
                    continue
                missing.append(param)

        if missing:
            error = {
                'line': command.line_number,
                'command': command.command_type.value,
                'error_type': 'missing_required_params',
                'message': f"缺少必需参数: {', '.join(missing)}",
                'missing_params': missing
            }
            command_file.parse_errors.append(error)
            logger.warning(f"命令验证失败 (行 {command.line_number}): {error['message']}")


class CommandExecutor:
    """命令执行器（提供执行框架，具体逻辑由外部实现）"""

    def __init__(self):
        """初始化命令执行器"""
        self.handlers: Dict[CommandType, callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """注册默认处理器"""
        for cmd_type in CommandType:
            self.handlers[cmd_type] = self._default_handler

    def register_handler(self, cmd_type: CommandType, handler: callable):
        """
        注册命令处理器

        Args:
            cmd_type: 命令类型
            handler: 处理函数，签名为 (command: ParsedCommand) -> Dict[str, Any]
        """
        self.handlers[cmd_type] = handler
        logger.info(f"已注册命令处理器: {cmd_type.value}")

    def execute(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        执行命令

        Args:
            command: 要执行的命令

        Returns:
            执行结果
        """
        handler = self.handlers.get(command.command_type, self._default_handler)

        try:
            result = handler(command)
            result['success'] = True
            result['command'] = command.to_dict()
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'command': command.to_dict()
            }
            logger.error(f"命令执行失败: {e}")

        return result

    def execute_all(self, commands: List[ParsedCommand]) -> List[Dict[str, Any]]:
        """
        执行多个命令

        Args:
            commands: 命令列表

        Returns:
            执行结果列表
        """
        results = []
        for cmd in commands:
            if cmd.is_valid():
                results.append(self.execute(cmd))
        return results

    def _default_handler(self, command: ParsedCommand) -> Dict[str, Any]:
        """默认命令处理器"""
        return {
            'message': f"命令 {command.command_type.value} 已接收，但未配置处理器",
            'action': 'none'
        }


def create_sample_commands_file(output_path: str):
    """
    创建示例命令文件

    Args:
        output_path: 输出文件路径
    """
    sample_content = """# Project Prometheus 命令文件示例
# 此文件展示了所有支持的命令类型

# ============================================
# APPROVE 命令 - 批准请求
# ============================================
APPROVE request-001
reason: 实验方案经过充分验证
priority: high

# ============================================
# REJECT 命令 - 拒绝请求
# ============================================
REJECT request-002
reason: 资源不足，无法满足需求
alternative: 建议使用更轻量级的方案

# ============================================
# PAUSE 命令 - 暂停项目
# ============================================
# 暂停当前项目
PAUSE project-alpha
duration: 7d
reason: 等待外部资源

# ============================================
# RESUME 命令 - 恢复项目
# ============================================
# 恢复项目执行
RESUME project-alpha
checkpoint: checkpoint-2026-02-10

# ============================================
# NEW_PROJECT 命令 - 创建新项目
# ============================================
NEW_PROJECT
name: new-llm-project
description: 大型语言模型优化研究
template: ml-research
priority: medium

# ============================================
# MODIFY 命令 - 修改配置
# ============================================
MODIFY project-alpha
field: max_iterations
value: 1000
reason: 需要更长的训练时间
"""

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(sample_content)

    logger.info(f"示例命令文件已创建: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='命令解析工具 - 解析 commands.txt 中的指令',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 解析命令文件
  python command_parser.py commands.txt

  # 解析并输出 JSON 格式
  python command_parser.py commands.txt --format json

  # 解析单行命令
  python command_parser.py --line "APPROVE request-001 --force"

  # 创建示例命令文件
  python command_parser.py --create-example example_commands.txt

  # 验证命令文件（严格模式）
  python command_parser.py commands.txt --strict

命令格式:
  COMMAND [target] [options]
  # 注释内容
  PARAM: value

支持的命令:
  APPROVE      - 批准请求
  REJECT       - 拒绝请求
  PAUSE        - 暂停项目
  RESUME       - 恢复项目
  NEW_PROJECT  - 创建新项目
  MODIFY       - 修改项目配置
        '''
    )

    parser.add_argument(
        'file',
        nargs='?',
        help='要解析的命令文件路径'
    )
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                       help='输出格式 (默认: text)')
    parser.add_argument('--line', '-l', help='解析单行命令')
    parser.add_argument('--strict', '-s', action='store_true',
                       help='启用严格模式，验证必需参数')
    parser.add_argument('--create-example', metavar='FILE',
                       help='创建示例命令文件')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--summary', action='store_true',
                       help='显示命令摘要统计')

    args = parser.parse_args()

    # 创建示例文件
    if args.create_example:
        create_sample_commands_file(args.create_example)
        return

    # 解析单行命令
    if args.line:
        cmd_parser = CommandParser(strict_mode=args.strict)
        command = cmd_parser.parse_single_line(args.line)

        if args.format == 'json':
            output = json.dumps(command.to_dict(), indent=2, ensure_ascii=False)
        else:
            output = f"命令类型: {command.command_type.value}\n"
            output += f"目标: {command.target or '无'}\n"
            output += f"参数: {command.parameters or '无'}\n"
            output += f"选项: {command.options or '无'}"

        print(output)
        return

    # 解析文件
    if not args.file:
        parser.print_help()
        return

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"错误: 文件不存在 - {args.file}")
        sys.exit(1)

    cmd_parser = CommandParser(strict_mode=args.strict)

    try:
        command_file = cmd_parser.parse_file(str(file_path))
    except Exception as e:
        print(f"解析错误: {e}")
        sys.exit(1)

    # 输出结果
    if args.format == 'json':
        output = json.dumps(command_file.to_dict(), indent=2, ensure_ascii=False)
    elif args.summary:
        # 统计摘要
        cmd_counts = {}
        for cmd in command_file.commands:
            cmd_type = cmd.command_type.value
            cmd_counts[cmd_type] = cmd_counts.get(cmd_type, 0) + 1

        output = f"命令文件: {command_file.file_path}\n"
        output += f"解析时间: {command_file.parse_time}\n"
        output += f"总命令数: {len(command_file.commands)}\n"
        output += f"有效命令: {len(command_file.get_valid_commands())}\n"
        output += f"解析错误: {len(command_file.parse_errors)}\n\n"
        output += "命令统计:\n"
        for cmd_type, count in sorted(cmd_counts.items()):
            output += f"  {cmd_type}: {count}\n"
    else:
        # 文本格式
        output = f"文件: {command_file.file_path}\n"
        output += f"解析时间: {command_file.parse_time}\n"
        output += f"命令数: {len(command_file.commands)}\n"
        output += "=" * 50 + "\n\n"

        for cmd in command_file.commands:
            output += f"[行 {cmd.line_number}] {cmd.command_type.value}"
            if cmd.target:
                output += f" -> {cmd.target}"
            output += "\n"

            if cmd.parameters:
                for key, value in cmd.parameters.items():
                    output += f"  {key}: {value}\n"

            if cmd.options:
                output += f"  选项: {', '.join(cmd.options)}\n"

            output += "\n"

        if command_file.parse_errors:
            output += "\n解析错误:\n"
            for error in command_file.parse_errors:
                output += f"  行 {error['line']}: {error['message']}\n"

    # 输出到文件或控制台
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"结果已保存到: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
