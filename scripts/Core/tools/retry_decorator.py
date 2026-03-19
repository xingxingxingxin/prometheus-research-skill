"""
重试装饰器
==========

为网络请求和外部调用添加自动重试功能。
支持指数退避、自定义异常处理和日志记录。
"""

import functools
import logging
import random
import time
from typing import Callable, Type, Tuple, Optional, Any, Union

# 配置日志
logger = logging.getLogger(__name__)


class RetryError(Exception):
    """重试次数耗尽后抛出的异常"""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, int], None]] = None,
    jitter: bool = True,
    reraise: bool = True
):
    """
    重试装饰器

    为函数添加自动重试功能，支持指数退避和自定义异常处理。

    Args:
        max_attempts: 最大尝试次数（包括首次调用）
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子，每次重试延迟乘以此因子
        max_delay: 最大延迟时间（秒）
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数，参数为 (exception, attempt, max_attempts)
        jitter: 是否添加随机抖动以避免同步重试
        reraise: 重试耗尽后是否重新抛出最后一个异常

    Returns:
        装饰后的函数

    Examples:
        # 基本用法
        @retry(max_attempts=3)
        def fetch_data():
            return requests.get("https://api.example.com/data")

        # 自定义异常和延迟
        @retry(
            max_attempts=5,
            delay=2.0,
            backoff_factor=1.5,
            exceptions=(requests.RequestException, ConnectionError)
        )
        def download_file(url):
            return requests.get(url)

        # 带回调函数
        def on_retry_callback(exc, attempt, max_attempts):
            print(f"重试 {attempt}/{max_attempts}: {exc}")

        @retry(max_attempts=3, on_retry=on_retry_callback)
        def unstable_operation():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt >= max_attempts:
                        # 重试次数耗尽
                        logger.error(
                            f"函数 {func.__name__} 重试 {max_attempts} 次后仍失败: {e}"
                        )

                        if reraise:
                            raise RetryError(
                                f"重试 {max_attempts} 次后失败: {func.__name__}",
                                last_exception
                            ) from e
                        raise

                    # 计算延迟时间
                    sleep_delay = current_delay

                    # 添加随机抖动 (±25%)
                    if jitter:
                        sleep_delay *= (0.75 + random.random() * 0.5)

                    # 限制最大延迟
                    sleep_delay = min(sleep_delay, max_delay)

                    # 日志记录
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt}/{max_attempts} 次调用失败: {e}, "
                        f"{sleep_delay:.2f} 秒后重试"
                    )

                    # 调用回调函数
                    if on_retry:
                        try:
                            on_retry(e, attempt, max_attempts)
                        except Exception as callback_error:
                            logger.error(f"重试回调函数执行失败: {callback_error}")

                    # 等待
                    time.sleep(sleep_delay)

                    # 指数退避
                    current_delay *= backoff_factor

            # 理论上不应该执行到这里
            return None

        return wrapper
    return decorator


def retry_with_result_check(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    result_checker: Optional[Callable[[Any], bool]] = None,
    on_retry: Optional[Callable[[Any, int, int], None]] = None,
    jitter: bool = True
):
    """
    基于结果检查的重试装饰器

    当函数返回结果不符合预期时进行重试，而不是基于异常。

    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        max_delay: 最大延迟时间（秒）
        result_checker: 结果检查函数，返回 False 表示需要重试
        on_retry: 重试回调函数，参数为 (result, attempt, max_attempts)
        jitter: 是否添加随机抖动

    Returns:
        装饰后的函数

    Examples:
        @retry_with_result_check(
            max_attempts=5,
            result_checker=lambda r: r is not None and r.get('status') == 'ok'
        )
        def poll_api():
            return requests.get("https://api.example.com/status").json()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                result = func(*args, **kwargs)

                # 检查结果
                if result_checker is None or result_checker(result):
                    return result

                # 结果不符合预期，需要重试
                if attempt >= max_attempts:
                    logger.warning(
                        f"函数 {func.__name__} 重试 {max_attempts} 次后结果仍不符合预期"
                    )
                    return result

                # 计算延迟
                sleep_delay = current_delay
                if jitter:
                    sleep_delay *= (0.75 + random.random() * 0.5)
                sleep_delay = min(sleep_delay, max_delay)

                logger.info(
                    f"函数 {func.__name__} 第 {attempt}/{max_attempts} 次结果不符合预期, "
                    f"{sleep_delay:.2f} 秒后重试"
                )

                # 回调
                if on_retry:
                    try:
                        on_retry(result, attempt, max_attempts)
                    except Exception as callback_error:
                        logger.error(f"重试回调函数执行失败: {callback_error}")

                time.sleep(sleep_delay)
                current_delay *= backoff_factor

            return None

        return wrapper
    return decorator


class RetryContext:
    """
    重试上下文管理器

    用于需要手动控制重试逻辑的场景。

    Examples:
        with RetryContext(max_attempts=3, delay=1.0) as retry_ctx:
            while retry_ctx.should_retry():
                try:
                    result = some_operation()
                    retry_ctx.success(result)
                except SomeException as e:
                    retry_ctx.failure(e)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter = jitter

        self.attempt = 0
        self.current_delay = delay
        self._success = False
        self._result = None
        self._last_exception = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val and not self._success:
            self._last_exception = exc_val
        return False  # 不抑制异常

    def should_retry(self) -> bool:
        """是否应该继续尝试"""
        return self.attempt < self.max_attempts and not self._success

    def success(self, result: Any = None):
        """标记成功"""
        self._success = True
        self._result = result

    def failure(self, exception: Exception = None):
        """标记失败并准备下一次尝试"""
        self.attempt += 1
        self._last_exception = exception

        if self.should_retry():
            sleep_delay = self.current_delay
            if self.jitter:
                sleep_delay *= (0.75 + random.random() * 0.5)
            sleep_delay = min(sleep_delay, self.max_delay)

            logger.info(
                f"第 {self.attempt}/{self.max_attempts} 次尝试失败, "
                f"{sleep_delay:.2f} 秒后重试"
            )

            time.sleep(sleep_delay)
            self.current_delay *= self.backoff_factor

    @property
    def result(self):
        """获取结果"""
        return self._result

    @property
    def last_exception(self):
        """获取最后一次异常"""
        return self._last_exception


# 预配置的重试装饰器，用于常见场景

# 网络请求重试（适合 HTTP 请求）
retry_network = retry(
    max_attempts=3,
    delay=1.0,
    backoff_factor=2.0,
    exceptions=(
        ConnectionError,
        TimeoutError,
        OSError,
    )
)

# API 调用重试（更长延迟，更多重试）
retry_api = retry(
    max_attempts=5,
    delay=2.0,
    backoff_factor=1.5,
    max_delay=30.0,
    exceptions=(
        ConnectionError,
        TimeoutError,
        OSError,
    )
)

# 文件操作重试
retry_file = retry(
    max_attempts=3,
    delay=0.5,
    backoff_factor=2.0,
    exceptions=(
        IOError,
        OSError,
        PermissionError,
    )
)


def setup_retry_logging(level: int = logging.INFO, log_file: str = None):
    """
    配置重试模块的日志

    Args:
        level: 日志级别
        log_file: 日志文件路径（可选）
    """
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


if __name__ == "__main__":
    # 演示用法
    import requests

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 示例 1: 基本重试
    @retry(max_attempts=3, delay=1.0)
    def fetch_example():
        print("尝试获取数据...")
        # 模拟可能失败的操作
        if random.random() < 0.5:
            raise ConnectionError("连接失败")
        return "成功!"

    # 示例 2: 网络请求重试
    @retry_network
    def get_data(url):
        return requests.get(url, timeout=10)

    # 示例 3: 带回调的重试
    def retry_callback(exc, attempt, max_attempts):
        print(f"回调: 第 {attempt}/{max_attempts} 次重试, 错误: {exc}")

    @retry(max_attempts=3, on_retry=retry_callback)
    def unstable_function():
        if random.random() < 0.7:
            raise ValueError("随机失败")
        return "成功!"

    # 示例 4: 结果检查重试
    @retry_with_result_check(
        max_attempts=5,
        result_checker=lambda r: r is not None and r.get('ready', False)
    )
    def poll_status():
        print("检查状态...")
        return {'ready': random.random() > 0.6}

    # 运行示例
    print("=" * 50)
    print("示例 1: 基本重试")
    try:
        result = fetch_example()
        print(f"结果: {result}")
    except RetryError as e:
        print(f"重试失败: {e}")

    print("\n" + "=" * 50)
    print("示例 3: 带回调的重试")
    try:
        result = unstable_function()
        print(f"结果: {result}")
    except RetryError as e:
        print(f"重试失败: {e}")

    print("\n" + "=" * 50)
    print("示例 4: 结果检查重试")
    result = poll_status()
    print(f"最终结果: {result}")
