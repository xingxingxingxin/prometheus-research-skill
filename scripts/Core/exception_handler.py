"""
Project Prometheus - 全局异常处理模块
======================================

提供全局异常捕获、记录日志、优雅退出的功能。

功能：
1. 捕获未处理异常
2. 记录详细的错误日志
3. 生成错误报告
4. 优雅退出（保存状态、清理资源）
"""

import sys
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List
from functools import wraps

# 默认路径
DEFAULT_BASE_DIR = Path(__file__).parent.parent
ERROR_LOG_DIR = DEFAULT_BASE_DIR / "Logs"
CRASH_REPORT_DIR = DEFAULT_BASE_DIR / "Logs" / "crashes"


class PrometheusError(Exception):
    """Project Prometheus 基础异常类"""

    def __init__(self, message: str, error_code: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp
        }


class StateError(PrometheusError):
    """状态管理相关错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "STATE_ERROR", context)


class TaskError(PrometheusError):
    """任务执行相关错误"""

    def __init__(self, message: str, task_id: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        if task_id:
            ctx["task_id"] = task_id
        super().__init__(message, "TASK_ERROR", ctx)


class ConfigurationError(PrometheusError):
    """配置相关错误"""

    def __init__(self, message: str, config_key: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        if config_key:
            ctx["config_key"] = config_key
        super().__init__(message, "CONFIG_ERROR", ctx)


class ExternalAPIError(PrometheusError):
    """外部 API 调用相关错误"""

    def __init__(self, message: str, api_name: Optional[str] = None,
                 status_code: Optional[int] = None,
                 context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        if api_name:
            ctx["api_name"] = api_name
        if status_code:
            ctx["status_code"] = status_code
        super().__init__(message, "API_ERROR", ctx)


class ResourceError(PrometheusError):
    """资源相关错误（文件、网络等）"""

    def __init__(self, message: str, resource_type: Optional[str] = None,
                 resource_path: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        if resource_type:
            ctx["resource_type"] = resource_type
        if resource_path:
            ctx["resource_path"] = resource_path
        super().__init__(message, "RESOURCE_ERROR", ctx)


class SecurityError(PrometheusError):
    """安全相关错误"""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SECURITY_ERROR", context)


class ExceptionHandler:
    """全局异常处理器

    捕获未处理的异常，记录日志，生成崩溃报告，并执行清理操作。
    """

    def __init__(self, log_dir: Optional[Path] = None,
                 crash_dir: Optional[Path] = None,
                 state_manager: Any = None):
        """
        初始化异常处理器

        Args:
            log_dir: 日志目录
            crash_dir: 崩溃报告目录
            state_manager: 状态管理器实例（用于保存状态）
        """
        self.log_dir = Path(log_dir) if log_dir else ERROR_LOG_DIR
        self.crash_dir = Path(crash_dir) if crash_dir else CRASH_REPORT_DIR
        self.state_manager = state_manager
        self._cleanup_handlers: List[Callable[[], None]] = []
        self._error_handlers: Dict[str, Callable[[Exception], None]] = {}
        self._installed = False
        self._original_excepthook = None

    def register_cleanup_handler(self, handler: Callable[[], None]) -> None:
        """
        注册清理处理函数

        Args:
            handler: 清理函数（无参数）
        """
        self._cleanup_handlers.append(handler)

    def register_error_handler(self, error_type: str,
                               handler: Callable[[Exception], None]) -> None:
        """
        注册特定类型错误的处理函数

        Args:
            error_type: 错误类型名称
            handler: 处理函数
        """
        self._error_handlers[error_type] = handler

    def _run_cleanup(self) -> None:
        """执行所有清理处理函数"""
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                # 清理过程中出错也要记录
                self._write_error_log("CleanupError", str(e), None)

    def _save_state(self) -> None:
        """保存当前状态"""
        if self.state_manager:
            try:
                # 更新状态为错误状态
                if hasattr(self.state_manager, 'set_status'):
                    self.state_manager.set_status("error", "System crashed")
            except Exception:
                pass  # 忽略状态保存失败

    def _write_error_log(self, error_type: str, error_message: str,
                         trace: Optional[str]) -> None:
        """
        写入错误日志

        Args:
            error_type: 错误类型
            error_message: 错误消息
            trace: 堆栈跟踪
        """
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / "error_trace.log"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{timestamp}] UNHANDLED EXCEPTION\n")
            f.write(f"Type: {error_type}\n")
            f.write(f"Message: {error_message}\n")
            if trace:
                f.write(f"Trace:\n{trace}\n")
            f.write(f"{'='*60}\n")

    def _generate_crash_report(self, exc_type: type, exc_value: Exception,
                               exc_traceback) -> Path:
        """
        生成崩溃报告

        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 堆栈跟踪

        Returns:
            崩溃报告文件路径
        """
        self.crash_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.crash_dir / f"crash_{timestamp}.json"

        # 获取完整的堆栈跟踪
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_str = ''.join(tb_lines)

        report = {
            "timestamp": datetime.now().isoformat(),
            "exception": {
                "type": exc_type.__name__,
                "module": exc_type.__module__,
                "message": str(exc_value)
            },
            "traceback": tb_str,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "executable": sys.executable
            }
        }

        # 如果是 PrometheusError，添加额外信息
        if isinstance(exc_value, PrometheusError):
            report["prometheus_error"] = exc_value.to_dict()

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report_file

    def _print_error_message(self, exc_type: type, exc_value: Exception,
                            report_file: Optional[Path] = None) -> None:
        """
        打印用户友好的错误消息

        Args:
            exc_type: 异常类型
            exc_value: 异常值
            report_file: 崩溃报告文件路径
        """
        print("\n" + "=" * 60, file=sys.stderr)
        print("  Project Prometheus - 发生未处理的异常", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(file=sys.stderr)
        print(f"  错误类型: {exc_type.__name__}", file=sys.stderr)
        print(f"  错误消息: {exc_value}", file=sys.stderr)
        print(file=sys.stderr)

        if report_file:
            print(f"  崩溃报告已保存到: {report_file}", file=sys.stderr)

        print(file=sys.stderr)
        print("  建议操作:", file=sys.stderr)
        print("  1. 查看崩溃报告了解详细错误信息", file=sys.stderr)
        print("  2. 尝试运行 'python prometheus.py --validate' 检查系统状态", file=sys.stderr)
        print("  3. 如果问题持续，请在 GitHub 上报告此问题", file=sys.stderr)
        print(file=sys.stderr)
        print("=" * 60, file=sys.stderr)

    def handle_exception(self, exc_type: type, exc_value: Exception,
                        exc_traceback) -> None:
        """
        处理未捕获的异常

        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 堆栈跟踪
        """
        # 忽略 KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            print("\n\n操作被用户中断。")
            self._run_cleanup()
            sys.exit(0)

        # 获取堆栈跟踪字符串
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_str = ''.join(tb_lines)

        # 检查是否有特定的错误处理器
        error_type_name = exc_type.__name__
        if error_type_name in self._error_handlers:
            try:
                self._error_handlers[error_type_name](exc_value)
            except Exception:
                pass  # 忽略处理器中的错误

        # 写入错误日志
        self._write_error_log(error_type_name, str(exc_value), tb_str)

        # 生成崩溃报告
        report_file = None
        try:
            report_file = self._generate_crash_report(
                exc_type, exc_value, exc_traceback
            )
        except Exception:
            pass  # 忽略报告生成失败

        # 保存状态
        self._save_state()

        # 打印错误消息
        self._print_error_message(exc_type, exc_value, report_file)

        # 执行清理
        self._run_cleanup()

        # 调用原始的异常钩子（如果有）
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)

        # 退出
        sys.exit(1)

    def install(self) -> None:
        """安装全局异常处理器"""
        if self._installed:
            return

        self._original_excepthook = sys.excepthook
        sys.excepthook = self.handle_exception
        self._installed = True

    def uninstall(self) -> None:
        """卸载全局异常处理器"""
        if not self._installed:
            return

        if self._original_excepthook:
            sys.excepthook = self._original_excepthook
        self._installed = False

    def __enter__(self):
        """上下文管理器入口"""
        self.install()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type is not None:
            self.handle_exception(exc_type, exc_val, exc_tb)
            return True  # 抑制异常
        self.uninstall()
        return False


def safe_execute(func: Callable) -> Callable:
    """
    安全执行装饰器

    捕获函数中的所有异常，记录日志并返回 None。

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PrometheusError as e:
            # 记录 Prometheus 错误
            _log_prometheus_error(e)
            return None
        except Exception as e:
            # 记录其他错误
            _log_unexpected_error(e)
            return None
    return wrapper


def safe_execute_with_default(default: Any = None) -> Callable:
    """
    带默认返回值的安全执行装饰器

    Args:
        default: 发生异常时返回的默认值

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _log_unexpected_error(e)
                return default
        return wrapper
    return decorator


def _log_prometheus_error(error: PrometheusError) -> None:
    """记录 Prometheus 错误"""
    ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = ERROR_LOG_DIR / "error_trace.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{timestamp}] PROMETHEUS ERROR\n")
        f.write(f"Code: {error.error_code}\n")
        f.write(f"Message: {error.message}\n")
        if error.context:
            f.write(f"Context: {json.dumps(error.context, ensure_ascii=False)}\n")
        f.write(f"{'='*60}\n")


def _log_unexpected_error(error: Exception) -> None:
    """记录意外错误"""
    ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = ERROR_LOG_DIR / "error_trace.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{timestamp}] UNEXPECTED ERROR\n")
        f.write(f"Type: {type(error).__name__}\n")
        f.write(f"Message: {str(error)}\n")
        f.write(f"{'='*60}\n")


class ErrorContext:
    """错误上下文管理器

    用于捕获代码块中的异常并执行特定操作。
    """

    def __init__(self, error_message: str = "An error occurred",
                 reraise: bool = False,
                 default: Any = None,
                 on_error: Optional[Callable[[Exception], None]] = None):
        """
        初始化错误上下文

        Args:
            error_message: 错误消息前缀
            reraise: 是否重新抛出异常
            default: 发生异常时的默认返回值
            on_error: 错误处理回调
        """
        self.error_message = error_message
        self.reraise = reraise
        self.default = default
        self.on_error = on_error
        self.error = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val

            # 记录错误
            _log_unexpected_error(exc_val)

            # 调用错误回调
            if self.on_error:
                try:
                    self.on_error(exc_val)
                except Exception:
                    pass

            # 是否重新抛出
            if self.reraise:
                return False

            return True  # 抑制异常


# 全局异常处理器实例
_global_handler: Optional[ExceptionHandler] = None


def get_exception_handler(state_manager: Any = None) -> ExceptionHandler:
    """
    获取全局异常处理器实例

    Args:
        state_manager: 状态管理器实例

    Returns:
        ExceptionHandler 实例
    """
    global _global_handler

    if _global_handler is None:
        _global_handler = ExceptionHandler(state_manager=state_manager)

    return _global_handler


def install_global_exception_handler(state_manager: Any = None) -> ExceptionHandler:
    """
    安装全局异常处理器

    Args:
        state_manager: 状态管理器实例

    Returns:
        ExceptionHandler 实例
    """
    handler = get_exception_handler(state_manager)
    handler.install()
    return handler


def uninstall_global_exception_handler() -> None:
    """卸载全局异常处理器"""
    global _global_handler

    if _global_handler is not None:
        _global_handler.uninstall()


if __name__ == "__main__":
    # 测试
    print("Testing ExceptionHandler...")

    # 创建测试目录
    test_dir = Path(__file__).parent.parent / "Logs" / "test"
    test_dir.mkdir(parents=True, exist_ok=True)

    # 创建处理器
    handler = ExceptionHandler(log_dir=test_dir, crash_dir=test_dir / "crashes")

    # 测试自定义异常
    try:
        raise TaskError("Test task failed", task_id="TEST-001")
    except TaskError as e:
        print(f"Caught TaskError: {e.to_dict()}")

    # 测试错误上下文
    with ErrorContext("Testing error context", reraise=False, default="fallback") as ctx:
        raise ValueError("Test error")

    print(f"Context error: {ctx.error}")
    print(f"Context returned: {ctx.default}")

    # 测试安全执行装饰器
    @safe_execute
    def risky_function():
        raise RuntimeError("Something went wrong")

    result = risky_function()
    print(f"Safe execute result: {result}")

    # 测试带默认值的安全执行
    @safe_execute_with_default(default="default_value")
    def another_risky_function():
        raise ValueError("Another error")

    result = another_risky_function()
    print(f"Safe execute with default result: {result}")

    print("\nAll tests passed!")
