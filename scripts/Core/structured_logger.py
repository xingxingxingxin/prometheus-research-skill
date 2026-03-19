"""
Project Prometheus - 结构化日志模块
=====================================

提供 JSON 格式的结构化日志功能，便于日志解析和分析。

功能：
1. JSON 格式日志输出
2. 支持日志字段扩展
3. 日志轮转和压缩
4. 同时支持文件和控制台输出
5. 日志查询和分析工具

使用方法：
    from Core.structured_logger import StructuredLogger, get_structured_logger

    # 获取日志器
    logger = get_structured_logger("my_module")

    # 基本日志
    logger.info("Task started", task_id="TASK-001", phase="literature")

    # 带额外上下文
    logger.error("API call failed",
                 api="semantic_scholar",
                 status_code=429,
                 retry_count=3)

    # 使用日志上下文管理器
    with logger.context(task_id="TASK-002", phase="coding"):
        logger.info("Processing file", file="test.py")
        logger.debug("Variable value", var_name="x", value=42)
"""

import json
import logging
import os
import gzip
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from functools import wraps
import threading
import re


# 默认路径
DEFAULT_BASE_DIR = Path(__file__).parent.parent
DEFAULT_LOG_DIR = DEFAULT_BASE_DIR / "Logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "structured.jsonl"


class StructuredLogRecord:
    """结构化日志记录"""

    def __init__(self, level: str, message: str, **kwargs):
        self.timestamp = datetime.now().isoformat()
        self.level = level.upper()
        self.message = message
        self.extra = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message
        }
        if self.extra:
            result["extra"] = self.extra
        return result

    def to_json(self, indent: Optional[int] = None) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __str__(self) -> str:
        return self.to_json()


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""

    def __init__(self, include_extra: bool = True, pretty: bool = False):
        super().__init__()
        self.include_extra = include_extra
        self.pretty = pretty

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # 添加位置信息
        if record.pathname:
            log_data["location"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName
            }

        # 添加额外字段
        if self.include_extra and hasattr(record, 'structured_extra'):
            extra = record.structured_extra
            if extra:
                log_data["extra"] = extra

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }

        indent = 2 if self.pretty else None
        return json.dumps(log_data, indent=indent, ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """人类可读的格式化器（带颜色支持）"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and self._supports_color()

    def _supports_color(self) -> bool:
        """检查终端是否支持颜色"""
        # 检查是否在终端环境中
        if not hasattr(sys.stdout, 'isatty'):
            return False
        if not sys.stdout.isatty():
            return False
        # 检查环境变量
        if os.environ.get('NO_COLOR'):
            return False
        if os.environ.get('TERM') == 'dumb':
            return False
        return True

    def format(self, record: logging.LogRecord) -> str:
        """格式化为人类可读的格式"""
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname

        if self.use_colors:
            color = self.COLORS.get(level, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            level_str = f"{color}[{level:^8}]{reset}"
        else:
            level_str = f"[{level:^8}]"

        # 基本消息
        parts = [f"[{timestamp}] {level_str} [{record.name}] {record.getMessage()}"]

        # 添加额外字段
        if hasattr(record, 'structured_extra') and record.structured_extra:
            extra_str = " | ".join(f"{k}={v}" for k, v in record.structured_extra.items())
            parts.append(f"  >> {extra_str}")

        # 添加异常信息
        if record.exc_info:
            parts.append(self.formatException(record.exc_info))

        return "\n".join(parts)


class StructuredHandler(logging.Handler):
    """结构化日志处理器"""

    def __init__(self, file_path: Optional[Path] = None,
                 mode: str = 'a',
                 encoding: str = 'utf-8'):
        super().__init__()
        self.file_path = Path(file_path) if file_path else DEFAULT_LOG_FILE
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.encoding = encoding
        self._lock = threading.Lock()
        self._file = None
        self.formatter = StructuredFormatter()

    def emit(self, record: logging.LogRecord) -> None:
        """写入日志记录"""
        try:
            msg = self.format(record)
            with self._lock:
                with open(self.file_path, self.mode, encoding=self.encoding) as f:
                    f.write(msg + "\n")
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """关闭处理器"""
        if self._file:
            self._file.close()
        super().close()


class RotatingStructuredHandler(StructuredHandler):
    """带轮转的结构化日志处理器"""

    def __init__(self, file_path: Optional[Path] = None,
                 max_size_mb: float = 10,
                 backup_count: int = 5,
                 compress: bool = True):
        super().__init__(file_path)
        self.max_bytes = int(max_size_mb * 1024 * 1024)
        self.backup_count = backup_count
        self.compress = compress

    def emit(self, record: logging.LogRecord) -> None:
        """写入日志记录（带轮转检查）"""
        try:
            # 检查是否需要轮转
            if self._should_rotate():
                self._do_rotate()

            # 写入日志
            msg = self.format(record)
            with self._lock:
                with open(self.file_path, 'a', encoding=self.encoding) as f:
                    f.write(msg + "\n")
        except Exception:
            self.handleError(record)

    def _should_rotate(self) -> bool:
        """检查是否需要轮转"""
        if not self.file_path.exists():
            return False
        return self.file_path.stat().st_size >= self.max_bytes

    def _do_rotate(self) -> None:
        """执行日志轮转"""
        with self._lock:
            # 删除最旧的备份
            oldest = self.file_path.with_suffix(f'.{self.backup_count}.jsonl')
            if oldest.exists():
                if self.compress and oldest.suffix == '.gz':
                    oldest.unlink()
                else:
                    gz_oldest = oldest.with_suffix(oldest.suffix + '.gz')
                    if gz_oldest.exists():
                        gz_oldest.unlink()

            # 轮转现有备份
            for i in range(self.backup_count - 1, 0, -1):
                src = self.file_path.with_suffix(f'.{i}.jsonl')
                if self.compress:
                    src_gz = src.with_suffix(src.suffix + '.gz')
                    if src_gz.exists():
                        dst_gz = self.file_path.with_suffix(f'.{i+1}.jsonl.gz')
                        src_gz.rename(dst_gz)
                if src.exists():
                    dst = self.file_path.with_suffix(f'.{i+1}.jsonl')
                    if self.compress:
                        self._compress_file(src, dst.with_suffix(dst.suffix + '.gz'))
                        src.unlink()
                    else:
                        src.rename(dst)

            # 轮转当前日志文件
            if self.file_path.exists():
                backup = self.file_path.with_suffix('.1.jsonl')
                if self.compress:
                    self._compress_file(self.file_path, backup.with_suffix(backup.suffix + '.gz'))
                    self.file_path.unlink()
                else:
                    self.file_path.rename(backup)

    def _compress_file(self, src: Path, dst: Path) -> None:
        """压缩文件"""
        with open(src, 'rb') as f_in:
            with gzip.open(dst, 'wb') as f_out:
                f_out.writelines(f_in)


class StructuredLogger:
    """结构化日志器

    提供便捷的结构化日志记录功能。

    使用方法：
        logger = StructuredLogger("my_module")
        logger.info("Task started", task_id="TASK-001")
        logger.error("Failed", error_code=500, details="Connection timeout")

        # 使用上下文
        with logger.context(request_id="req-123"):
            logger.info("Processing")
    """

    def __init__(self, name: str,
                 log_file: Optional[Path] = None,
                 level: str = "INFO",
                 console_output: bool = True,
                 console_colors: bool = True,
                 structured_output: bool = True,
                 max_file_size_mb: float = 10,
                 backup_count: int = 5,
                 compress_rotated: bool = True):
        """
        初始化结构化日志器

        Args:
            name: 日志器名称
            log_file: 日志文件路径
            level: 日志级别
            console_output: 是否输出到控制台
            console_colors: 控制台是否使用颜色
            structured_output: 是否输出结构化日志（JSON）
            max_file_size_mb: 单个日志文件最大大小（MB）
            backup_count: 保留的备份数量
            compress_rotated: 是否压缩轮转的日志
        """
        self.name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper()))
        self._logger.handlers = []  # 清除现有处理器

        self._context: Dict[str, Any] = {}
        self._context_stack: List[Dict[str, Any]] = []

        # 添加结构化文件处理器
        if structured_output and log_file:
            file_handler = RotatingStructuredHandler(
                file_path=log_file,
                max_size_mb=max_file_size_mb,
                backup_count=backup_count,
                compress=compress_rotated
            )
            self._logger.addHandler(file_handler)

        # 添加控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_handler.setFormatter(HumanReadableFormatter(use_colors=console_colors))
            self._logger.addHandler(console_handler)

    def _log(self, level: str, message: str, **kwargs) -> None:
        """内部日志方法"""
        # 合并上下文和额外字段
        extra = {**self._context, **kwargs}

        # 创建日志记录
        record = self._logger.makeRecord(
            self.name,
            getattr(logging, level.upper()),
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.structured_extra = extra if extra else None

        # 处理记录
        self._logger.handle(record)

    def debug(self, message: str, **kwargs) -> None:
        """记录 DEBUG 级别日志"""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """记录 INFO 级别日志"""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """记录 WARNING 级别日志"""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """记录 ERROR 级别日志"""
        if exc_info:
            self._logger.error(message, exc_info=True, extra={'structured_extra': {**self._context, **kwargs} if self._context or kwargs else None})
        else:
            self._log("ERROR", message, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """记录 CRITICAL 级别日志"""
        if exc_info:
            self._logger.critical(message, exc_info=True, extra={'structured_extra': {**self._context, **kwargs} if self._context or kwargs else None})
        else:
            self._log("CRITICAL", message, **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """记录异常日志（自动包含堆栈跟踪）"""
        self._logger.exception(message, extra={'structured_extra': {**self._context, **kwargs} if self._context or kwargs else None})

    def context(self, **kwargs) -> 'LogContext':
        """
        创建日志上下文管理器

        使用方法：
            with logger.context(task_id="TASK-001", phase="coding"):
                logger.info("Processing")  # 自动包含 task_id 和 phase
        """
        return LogContext(self, kwargs)

    def bind(self, **kwargs) -> 'StructuredLogger':
        """
        绑定持久的上下文字段

        使用方法：
            logger = logger.bind(task_id="TASK-001")
            logger.info("Processing")  # 自动包含 task_id
        """
        new_logger = StructuredLogger.__new__(StructuredLogger)
        new_logger.name = self.name
        new_logger._logger = self._logger
        new_logger._context = {**self._context, **kwargs}
        new_logger._context_stack = self._context_stack.copy()
        return new_logger

    def unbind(self, *keys) -> 'StructuredLogger':
        """
        解绑上下文字段

        Args:
            *keys: 要解绑的键名
        """
        new_context = {k: v for k, v in self._context.items() if k not in keys}
        new_logger = StructuredLogger.__new__(StructuredLogger)
        new_logger.name = self.name
        new_logger._logger = self._logger
        new_logger._context = new_context
        new_logger._context_stack = self._context_stack.copy()
        return new_logger

    def push_context(self, **kwargs) -> None:
        """推入上下文"""
        self._context_stack.append(self._context.copy())
        self._context.update(kwargs)

    def pop_context(self) -> Dict[str, Any]:
        """弹出上下文"""
        if self._context_stack:
            self._context = self._context_stack.pop()
        return self._context.copy()


class LogContext:
    """日志上下文管理器"""

    def __init__(self, logger: StructuredLogger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context

    def __enter__(self) -> 'LogContext':
        self.logger.push_context(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.logger.pop_context()


# 日志器缓存
_loggers: Dict[str, StructuredLogger] = {}
_config: Dict[str, Any] = {}


def configure_structured_logging(
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    log_file: Optional[Path] = None,
    console_output: bool = True,
    console_colors: bool = True,
    max_file_size_mb: float = 10,
    backup_count: int = 5,
    compress_rotated: bool = True
) -> None:
    """
    配置全局结构化日志

    Args:
        level: 日志级别
        log_dir: 日志目录
        log_file: 日志文件路径
        console_output: 是否输出到控制台
        console_colors: 控制台是否使用颜色
        max_file_size_mb: 单个日志文件最大大小（MB）
        backup_count: 保留的备份数量
        compress_rotated: 是否压缩轮转的日志
    """
    global _config

    _config = {
        "level": level,
        "log_dir": log_dir or DEFAULT_LOG_DIR,
        "log_file": log_file,
        "console_output": console_output,
        "console_colors": console_colors,
        "max_file_size_mb": max_file_size_mb,
        "backup_count": backup_count,
        "compress_rotated": compress_rotated
    }

    # 确保日志目录存在
    _config["log_dir"].mkdir(parents=True, exist_ok=True)


def get_structured_logger(name: str, **kwargs) -> StructuredLogger:
    """
    获取结构化日志器

    Args:
        name: 日志器名称
        **kwargs: 额外配置参数（覆盖全局配置）

    Returns:
        StructuredLogger 实例
    """
    if name in _loggers and not kwargs:
        return _loggers[name]

    # 合并配置
    config = {**_config, **kwargs}

    # 设置默认日志文件
    if 'log_file' not in config or config['log_file'] is None:
        config['log_file'] = config.get('log_dir', DEFAULT_LOG_DIR) / "structured.jsonl"

    logger = StructuredLogger(
        name=name,
        log_file=config.get('log_file'),
        level=config.get('level', 'INFO'),
        console_output=config.get('console_output', True),
        console_colors=config.get('console_colors', True),
        max_file_size_mb=config.get('max_file_size_mb', 10),
        backup_count=config.get('backup_count', 5),
        compress_rotated=config.get('compress_rotated', True)
    )

    _loggers[name] = logger
    return logger


class StructuredLogAnalyzer:
    """结构化日志分析器

    提供日志查询、统计和分析功能。
    """

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = Path(log_file) if log_file else DEFAULT_LOG_FILE

    def read_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        读取日志记录

        Args:
            limit: 最大读取数量

        Returns:
            日志记录列表
        """
        logs = []

        if not self.log_file.exists():
            return logs

        with open(self.log_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return logs

    def filter_logs(self,
                    level: Optional[str] = None,
                    logger_name: Optional[str] = None,
                    message_pattern: Optional[str] = None,
                    start_time: Optional[str] = None,
                    end_time: Optional[str] = None,
                    extra_filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        筛选日志

        Args:
            level: 日志级别
            logger_name: 日志器名称
            message_pattern: 消息匹配模式（正则）
            start_time: 开始时间（ISO 格式）
            end_time: 结束时间（ISO 格式）
            extra_filters: 额外字段筛选条件

        Returns:
            匹配的日志记录列表
        """
        logs = self.read_logs()
        filtered = []

        for log in logs:
            # 级别筛选
            if level and log.get('level') != level.upper():
                continue

            # 日志器名称筛选
            if logger_name and log.get('logger') != logger_name:
                continue

            # 消息模式筛选
            if message_pattern:
                if not re.search(message_pattern, log.get('message', '')):
                    continue

            # 时间范围筛选
            timestamp = log.get('timestamp', '')
            if start_time and timestamp < start_time:
                continue
            if end_time and timestamp > end_time:
                continue

            # 额外字段筛选
            if extra_filters:
                extra = log.get('extra', {})
                match = True
                for key, value in extra_filters.items():
                    if extra.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            filtered.append(log)

        return filtered

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取日志统计信息

        Returns:
            统计信息字典
        """
        logs = self.read_logs()

        if not logs:
            return {
                "total_logs": 0,
                "by_level": {},
                "by_logger": {},
                "first_timestamp": None,
                "last_timestamp": None
            }

        # 按级别统计
        by_level: Dict[str, int] = {}
        for log in logs:
            level = log.get('level', 'UNKNOWN')
            by_level[level] = by_level.get(level, 0) + 1

        # 按日志器统计
        by_logger: Dict[str, int] = {}
        for log in logs:
            logger = log.get('logger', 'unknown')
            by_logger[logger] = by_logger.get(logger, 0) + 1

        # 时间范围
        timestamps = [log.get('timestamp') for log in logs if log.get('timestamp')]
        first_timestamp = min(timestamps) if timestamps else None
        last_timestamp = max(timestamps) if timestamps else None

        return {
            "total_logs": len(logs),
            "by_level": by_level,
            "by_logger": by_logger,
            "first_timestamp": first_timestamp,
            "last_timestamp": last_timestamp
        }

    def get_error_summary(self, limit: int = 100) -> Dict[str, Any]:
        """
        获取错误摘要

        Args:
            limit: 最大分析数量

        Returns:
            错误摘要字典
        """
        error_logs = self.filter_logs(level='ERROR')[:limit]
        critical_logs = self.filter_logs(level='CRITICAL')[:limit]

        # 统计错误类型
        error_types: Dict[str, int] = {}
        for log in error_logs + critical_logs:
            msg = log.get('message', '')
            # 简单提取错误类型（取第一个词）
            error_type = msg.split()[0] if msg else 'Unknown'
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_errors": len(error_logs),
            "total_critical": len(critical_logs),
            "error_types": error_types,
            "recent_errors": error_logs[:10]
        }

    def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        搜索日志

        Args:
            query: 搜索关键词
            case_sensitive: 是否区分大小写

        Returns:
            匹配的日志记录列表
        """
        logs = self.read_logs()
        results = []

        if not case_sensitive:
            query = query.lower()

        for log in logs:
            # 在消息中搜索
            message = log.get('message', '')
            if not case_sensitive:
                message = message.lower()

            if query in message:
                results.append(log)
                continue

            # 在额外字段中搜索
            extra = log.get('extra', {})
            for value in extra.values():
                value_str = str(value)
                if not case_sensitive:
                    value_str = value_str.lower()
                if query in value_str:
                    results.append(log)
                    break

        return results

    def export(self, output_file: Path, format: str = 'json',
               level: Optional[str] = None,
               start_time: Optional[str] = None,
               end_time: Optional[str] = None) -> int:
        """
        导出日志

        Args:
            output_file: 输出文件路径
            format: 导出格式（json, jsonl, text）
            level: 日志级别筛选
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            导出的日志数量
        """
        logs = self.filter_logs(level=level, start_time=start_time, end_time=end_time)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            if format == 'json':
                json.dump(logs, f, indent=2, ensure_ascii=False)
            elif format == 'jsonl':
                for log in logs:
                    f.write(json.dumps(log, ensure_ascii=False) + '\n')
            else:  # text
                for log in logs:
                    timestamp = log.get('timestamp', '')
                    level_str = log.get('level', '')
                    logger = log.get('logger', '')
                    message = log.get('message', '')
                    f.write(f"[{timestamp}] [{level_str}] [{logger}] {message}\n")

        return len(logs)


def log_function_call(logger: Optional[StructuredLogger] = None):
    """
    函数调用日志装饰器

    使用方法：
        @log_function_call()
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_structured_logger(func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Calling {func.__name__}",
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"Completed {func.__name__}",
                    function=func.__name__,
                    status="success"
                )
                return result
            except Exception as e:
                logger.error(
                    f"Failed {func.__name__}",
                    function=func.__name__,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise

        return wrapper
    return decorator


# 初始化默认配置
configure_structured_logging()


if __name__ == "__main__":
    # 测试
    print("Testing StructuredLogger...")

    # 配置日志
    test_log_file = Path(__file__).parent.parent / "Logs" / "test_structured.jsonl"
    configure_structured_logging(
        level="DEBUG",
        log_file=test_log_file,
        console_output=True,
        console_colors=True
    )

    # 获取日志器
    logger = get_structured_logger("test_module")

    # 测试基本日志
    print("\n1. Basic logging:")
    logger.debug("Debug message", debug_var="value")
    logger.info("Info message", count=42, status="active")
    logger.warning("Warning message", threshold=100)
    logger.error("Error message", error_code=500)

    # 测试上下文
    print("\n2. Context logging:")
    with logger.context(task_id="TASK-001", phase="testing"):
        logger.info("Processing started")
        logger.info("Processing step 1", step=1)
        logger.info("Processing step 2", step=2)
        logger.info("Processing completed")

    # 测试绑定
    print("\n3. Bind logging:")
    bound_logger = logger.bind(session_id="sess_123", user="test_user")
    bound_logger.info("User action", action="login")
    bound_logger.info("User action", action="view_page")

    # 测试异常日志
    print("\n4. Exception logging:")
    try:
        raise ValueError("Test exception for logging")
    except Exception:
        logger.exception("Caught an exception", context="testing")

    # 测试函数装饰器
    print("\n5. Function decorator:")

    @log_function_call(logger)
    def test_function(x, y):
        return x / y

    test_function(10, 2)
    try:
        test_function(10, 0)
    except ZeroDivisionError:
        pass

    # 测试日志分析器
    print("\n6. Log analyzer:")
    analyzer = StructuredLogAnalyzer(test_log_file)

    # 统计
    stats = analyzer.get_statistics()
    print(f"Total logs: {stats['total_logs']}")
    print(f"By level: {stats['by_level']}")

    # 搜索
    results = analyzer.search("Processing")
    print(f"Search 'Processing': {len(results)} results")

    # 筛选
    errors = analyzer.filter_logs(level="ERROR")
    print(f"Error logs: {len(errors)}")

    # 错误摘要
    error_summary = analyzer.get_error_summary()
    print(f"Error summary: {error_summary['total_errors']} errors")

    # 导出
    export_file = Path(__file__).parent.parent / "Logs" / "test_export.json"
    count = analyzer.export(export_file, format='json')
    print(f"Exported {count} logs to {export_file}")

    print("\nAll tests passed!")
