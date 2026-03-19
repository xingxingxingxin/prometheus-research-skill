"""
日志分析工具
============

分析项目日志，统计错误频率、识别模式、生成报告。
支持文本日志和 JSON 结构化日志。
"""

import json
import logging
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Pattern

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: Optional[datetime] = None
    level: str = "UNKNOWN"
    logger: str = ""
    message: str = ""
    module: str = ""
    function: str = ""
    line: int = 0
    raw: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "logger": self.logger,
            "message": self.message,
            "module": self.module,
            "function": self.function,
            "line": self.line,
            "extra": self.extra
        }


@dataclass
class ErrorPattern:
    """错误模式"""
    pattern: str
    count: int
    examples: List[str]
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    affected_modules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pattern": self.pattern,
            "count": self.count,
            "examples": self.examples[:5],  # 最多5个示例
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "affected_modules": self.affected_modules
        }


@dataclass
class AnalysisResult:
    """分析结果"""
    total_entries: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    debug_count: int = 0
    level_distribution: Dict[str, int] = field(default_factory=dict)
    error_patterns: List[ErrorPattern] = field(default_factory=list)
    top_errors: List[Tuple[str, int]] = field(default_factory=list)
    top_warnings: List[Tuple[str, int]] = field(default_factory=list)
    hourly_distribution: Dict[int, int] = field(default_factory=dict)
    module_distribution: Dict[str, int] = field(default_factory=dict)
    time_range: Tuple[Optional[datetime], Optional[datetime]] = (None, None)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_entries": self.total_entries,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "debug_count": self.debug_count,
            "level_distribution": self.level_distribution,
            "error_patterns": [p.to_dict() for p in self.error_patterns],
            "top_errors": self.top_errors,
            "top_warnings": self.top_warnings,
            "hourly_distribution": self.hourly_distribution,
            "module_distribution": self.module_distribution,
            "time_range": (
                self.time_range[0].isoformat() if self.time_range[0] else None,
                self.time_range[1].isoformat() if self.time_range[1] else None
            )
        }


class LogParser:
    """日志解析器"""

    # 常见日志格式的正则表达式
    PATTERNS = {
        # 标准格式: [2024-01-15 10:30:00] [ERROR  ] [module] message
        "standard": re.compile(
            r'\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*'
            r'\[(?P<level>\w+)\s*\]\s*'
            r'\[(?P<logger>[^\]]*)\]\s*'
            r'(?P<message>.*)'
        ),
        # 详细格式: 2024-01-15 10:30:00,123 - module - ERROR - message
        "detailed": re.compile(
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:[,.]\d+)?)\s*[-:]\s*'
            r'(?P<logger>[\w.]+)\s*[-:]\s*'
            r'(?P<level>\w+)\s*[-:]\s*'
            r'(?P<message>.*)'
        ),
        # 简单格式: ERROR: message
        "simple": re.compile(
            r'^(?P<level>\w+):\s*(?P<message>.*)$'
        ),
    }

    @classmethod
    def parse_line(cls, line: str) -> Optional[LogEntry]:
        """
        解析单行日志

        Args:
            line: 日志行

        Returns:
            LogEntry 对象，解析失败返回 None
        """
        line = line.strip()
        if not line:
            return None

        # 尝试 JSON 格式
        if line.startswith('{'):
            return cls._parse_json(line)

        # 尝试各种文本格式
        for pattern_name, pattern in cls.PATTERNS.items():
            match = pattern.match(line)
            if match:
                return cls._create_entry(match.groupdict(), line)

        # 无法解析，返回原始条目
        return LogEntry(
            level="UNKNOWN",
            message=line,
            raw=line
        )

    @classmethod
    def _parse_json(cls, line: str) -> Optional[LogEntry]:
        """解析 JSON 格式日志"""
        try:
            data = json.loads(line)
            timestamp = None
            if 'timestamp' in data:
                try:
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    pass

            return LogEntry(
                timestamp=timestamp,
                level=data.get('level', 'UNKNOWN').upper(),
                logger=data.get('logger', ''),
                message=data.get('message', ''),
                module=data.get('module', ''),
                function=data.get('function', ''),
                line=data.get('line', 0),
                raw=line,
                extra={k: v for k, v in data.items()
                       if k not in {'timestamp', 'level', 'logger', 'message', 'module', 'function', 'line'}}
            )
        except json.JSONDecodeError:
            return None

    @classmethod
    def _create_entry(cls, groups: Dict[str, str], raw: str) -> LogEntry:
        """从正则匹配组创建日志条目"""
        timestamp = None
        if 'timestamp' in groups:
            try:
                ts_str = groups['timestamp'].replace(',', '.')
                # 尝试不同格式
                for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
                    try:
                        timestamp = datetime.strptime(ts_str, fmt)
                        break
                    except ValueError:
                        continue
            except (ValueError, TypeError):
                pass

        return LogEntry(
            timestamp=timestamp,
            level=groups.get('level', 'UNKNOWN').upper(),
            logger=groups.get('logger', ''),
            message=groups.get('message', ''),
            raw=raw
        )


class PatternDetector:
    """错误模式检测器"""

    # 常见错误模式
    COMMON_PATTERNS = [
        (r'ConnectionError:.*', 'Connection Error'),
        (r'TimeoutError:.*', 'Timeout Error'),
        (r'FileNotFoundError:.*', 'File Not Found'),
        (r'PermissionError:.*', 'Permission Error'),
        (r'ValueError:.*', 'Value Error'),
        (r'TypeError:.*', 'Type Error'),
        (r'KeyError:.*', 'Key Error'),
        (r'IndexError:.*', 'Index Error'),
        (r'AttributeError:.*', 'Attribute Error'),
        (r'ImportError:.*', 'Import Error'),
        (r'MemoryError:.*', 'Memory Error'),
        (r'RecursionError:.*', 'Recursion Error'),
        (r'HTTP \d{3}.*', 'HTTP Error'),
        (r'rate limit.*', 'Rate Limit'),
        (r'unauthorized.*', 'Unauthorized'),
        (r'forbidden.*', 'Forbidden'),
        (r'not found.*', 'Not Found'),
        (r'timeout.*', 'Timeout'),
        (r'failed to.*', 'Operation Failed'),
        (r'error:.*', 'Generic Error'),
    ]

    def __init__(self, custom_patterns: Optional[List[Tuple[str, str]]] = None):
        """
        初始化模式检测器

        Args:
            custom_patterns: 自定义模式列表 [(pattern_regex, pattern_name), ...]
        """
        self.patterns = self.COMMON_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)

        # 编译正则表达式
        self._compiled = [
            (re.compile(p, re.IGNORECASE), name)
            for p, name in self.patterns
        ]

    def detect(self, entries: List[LogEntry]) -> List[ErrorPattern]:
        """
        检测错误模式

        Args:
            entries: 日志条目列表

        Returns:
            检测到的错误模式列表
        """
        pattern_data: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "examples": [],
                "first_seen": None,
                "last_seen": None,
                "modules": set()
            }
        )

        for entry in entries:
            if entry.level not in ('ERROR', 'CRITICAL', 'WARNING'):
                continue

            message = entry.message

            for compiled, name in self._compiled:
                if compiled.search(message):
                    data = pattern_data[name]
                    data["count"] += 1

                    if len(data["examples"]) < 10:
                        data["examples"].append(message[:200])

                    # 更新时间范围
                    if entry.timestamp:
                        if data["first_seen"] is None or entry.timestamp < data["first_seen"]:
                            data["first_seen"] = entry.timestamp
                        if data["last_seen"] is None or entry.timestamp > data["last_seen"]:
                            data["last_seen"] = entry.timestamp

                    # 记录模块
                    if entry.module:
                        data["modules"].add(entry.module)
                    elif entry.logger:
                        data["modules"].add(entry.logger)

                    break

        # 转换为 ErrorPattern 对象
        result = []
        for name, data in pattern_data.items():
            if data["count"] > 0:
                result.append(ErrorPattern(
                    pattern=name,
                    count=data["count"],
                    examples=data["examples"],
                    first_seen=data["first_seen"],
                    last_seen=data["last_seen"],
                    affected_modules=list(data["modules"])
                ))

        # 按出现次数排序
        result.sort(key=lambda x: x.count, reverse=True)
        return result

    def detect_message_clusters(
        self,
        entries: List[LogEntry],
        similarity_threshold: float = 0.7
    ) -> List[ErrorPattern]:
        """
        基于消息相似度检测错误聚类

        使用简化的相似度检测，找出相似的错误消息。

        Args:
            entries: 日志条目列表
            similarity_threshold: 相似度阈值

        Returns:
            检测到的错误模式列表
        """
        # 只处理错误和警告
        error_entries = [
            e for e in entries
            if e.level in ('ERROR', 'CRITICAL', 'WARNING')
        ]

        if not error_entries:
            return []

        # 提取消息模板（移除变量部分）
        def extract_template(message: str) -> str:
            # 移除数字
            template = re.sub(r'\b\d+\b', '<NUM>', message)
            # 移除文件路径
            template = re.sub(r'[/\\][\w/\\.-]+', '<PATH>', template)
            # 移除 URL
            template = re.sub(r'https?://\S+', '<URL>', template)
            # 移除 UUID
            template = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '<UUID>', template, flags=re.IGNORECASE)
            return template

        # 按模板分组
        clusters: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "examples": [],
                "first_seen": None,
                "last_seen": None,
                "modules": set()
            }
        )

        for entry in error_entries:
            template = extract_template(entry.message)
            data = clusters[template]
            data["count"] += 1

            if len(data["examples"]) < 5:
                data["examples"].append(entry.message[:200])

            if entry.timestamp:
                if data["first_seen"] is None or entry.timestamp < data["first_seen"]:
                    data["first_seen"] = entry.timestamp
                if data["last_seen"] is None or entry.timestamp > data["last_seen"]:
                    data["last_seen"] = entry.timestamp

            if entry.module:
                data["modules"].add(entry.module)
            elif entry.logger:
                data["modules"].add(entry.logger)

        # 转换为 ErrorPattern 对象（只保留出现多次的）
        result = []
        for template, data in clusters.items():
            if data["count"] >= 2:  # 至少出现2次
                result.append(ErrorPattern(
                    pattern=template[:100],  # 限制模式长度
                    count=data["count"],
                    examples=data["examples"],
                    first_seen=data["first_seen"],
                    last_seen=data["last_seen"],
                    affected_modules=list(data["modules"])
                ))

        result.sort(key=lambda x: x.count, reverse=True)
        return result[:20]  # 最多返回20个聚类


class LogAnalyzer:
    """日志分析器"""

    def __init__(
        self,
        log_dir: str = "Logs",
        custom_patterns: Optional[List[Tuple[str, str]]] = None
    ):
        """
        初始化日志分析器

        Args:
            log_dir: 日志目录路径
            custom_patterns: 自定义错误模式
        """
        self.log_dir = Path(log_dir)
        self.parser = LogParser()
        self.pattern_detector = PatternDetector(custom_patterns)

    def analyze_file(
        self,
        file_path: str,
        max_entries: int = 100000
    ) -> AnalysisResult:
        """
        分析单个日志文件

        Args:
            file_path: 日志文件路径
            max_entries: 最大解析条目数

        Returns:
            分析结果
        """
        entries = self._load_entries(file_path, max_entries)
        return self._analyze_entries(entries)

    def analyze_directory(
        self,
        pattern: str = "*.log",
        max_entries_per_file: int = 50000,
        max_total_entries: int = 500000
    ) -> AnalysisResult:
        """
        分析日志目录中的所有文件

        Args:
            pattern: 文件匹配模式
            max_entries_per_file: 每个文件最大条目数
            max_total_entries: 总最大条目数

        Returns:
            合并的分析结果
        """
        all_entries: List[LogEntry] = []

        # 查找所有日志文件
        if self.log_dir.exists():
            log_files = list(self.log_dir.glob(pattern))
            log_files.extend(self.log_dir.glob("**/*.json"))
        else:
            logger.warning(f"日志目录不存在: {self.log_dir}")
            log_files = []

        # 加载所有条目
        for log_file in log_files:
            if len(all_entries) >= max_total_entries:
                break

            remaining = max_total_entries - len(all_entries)
            entries = self._load_entries(
                str(log_file),
                min(max_entries_per_file, remaining)
            )
            all_entries.extend(entries)

        return self._analyze_entries(all_entries)

    def analyze_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        pattern: str = "*.log"
    ) -> AnalysisResult:
        """
        分析指定时间范围内的日志

        Args:
            start_time: 开始时间
            end_time: 结束时间
            pattern: 文件匹配模式

        Returns:
            分析结果
        """
        # 加载所有条目
        all_entries: List[LogEntry] = []

        if self.log_dir.exists():
            for log_file in self.log_dir.glob(pattern):
                entries = self._load_entries(str(log_file))
                # 过滤时间范围
                filtered = [
                    e for e in entries
                    if e.timestamp and start_time <= e.timestamp <= end_time
                ]
                all_entries.extend(filtered)

        return self._analyze_entries(all_entries)

    def _load_entries(
        self,
        file_path: str,
        max_entries: int = 100000
    ) -> List[LogEntry]:
        """加载日志条目"""
        entries: List[LogEntry] = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= max_entries:
                        break

                    entry = self.parser.parse_line(line)
                    if entry:
                        entries.append(entry)

        except FileNotFoundError:
            logger.warning(f"日志文件不存在: {file_path}")
        except Exception as e:
            logger.error(f"读取日志文件失败: {file_path}, 错误: {e}")

        return entries

    def _analyze_entries(self, entries: List[LogEntry]) -> AnalysisResult:
        """分析日志条目"""
        result = AnalysisResult()
        result.total_entries = len(entries)

        if not entries:
            return result

        # 级别分布
        level_counter = Counter(e.level for e in entries)
        result.level_distribution = dict(level_counter)
        result.error_count = level_counter.get('ERROR', 0) + level_counter.get('CRITICAL', 0)
        result.warning_count = level_counter.get('WARNING', 0)
        result.info_count = level_counter.get('INFO', 0)
        result.debug_count = level_counter.get('DEBUG', 0)

        # 时间范围
        timestamps = [e.timestamp for e in entries if e.timestamp]
        if timestamps:
            result.time_range = (min(timestamps), max(timestamps))

        # 每小时分布
        for entry in entries:
            if entry.timestamp:
                hour = entry.timestamp.hour
                result.hourly_distribution[hour] = result.hourly_distribution.get(hour, 0) + 1

        # 模块分布
        module_counter = Counter(e.logger or e.module or 'unknown' for e in entries)
        result.module_distribution = dict(module_counter.most_common(20))

        # 错误模式检测
        result.error_patterns = self.pattern_detector.detect(entries)

        # 如果预定义模式检测到的不多，尝试消息聚类
        if len(result.error_patterns) < 5:
            clusters = self.pattern_detector.detect_message_clusters(entries)
            # 合并结果，去重
            existing_patterns = {p.pattern for p in result.error_patterns}
            for cluster in clusters:
                if cluster.pattern not in existing_patterns:
                    result.error_patterns.append(cluster)
                    existing_patterns.add(cluster.pattern)

        # Top 错误和警告
        errors = [e.message for e in entries if e.level in ('ERROR', 'CRITICAL')]
        warnings = [e.message for e in entries if e.level == 'WARNING']

        error_counter = Counter(errors)
        warning_counter = Counter(warnings)

        result.top_errors = error_counter.most_common(10)
        result.top_warnings = warning_counter.most_common(10)

        return result

    def generate_report(
        self,
        result: AnalysisResult,
        format: str = "markdown"
    ) -> str:
        """
        生成分析报告

        Args:
            result: 分析结果
            format: 报告格式 (markdown, text)

        Returns:
            报告文本
        """
        if format == "markdown":
            return self._generate_markdown_report(result)
        else:
            return self._generate_text_report(result)

    def _generate_markdown_report(self, result: AnalysisResult) -> str:
        """生成 Markdown 格式报告"""
        lines = [
            "# 日志分析报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 概览",
            "",
            f"- **总条目数**: {result.total_entries:,}",
            f"- **错误数**: {result.error_count:,}",
            f"- **警告数**: {result.warning_count:,}",
            f"- **信息数**: {result.info_count:,}",
            f"- **调试数**: {result.debug_count:,}",
            "",
        ]

        # 时间范围
        if result.time_range[0] and result.time_range[1]:
            lines.extend([
                "## 时间范围",
                "",
                f"- **开始**: {result.time_range[0].strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **结束**: {result.time_range[1].strftime('%Y-%m-%d %H:%M:%S')}",
                "",
            ])

        # 级别分布
        if result.level_distribution:
            lines.extend([
                "## 日志级别分布",
                "",
                "| 级别 | 数量 |",
                "|------|------|",
            ])
            for level, count in sorted(result.level_distribution.items(), key=lambda x: -x[1]):
                lines.append(f"| {level} | {count:,} |")
            lines.append("")

        # 错误模式
        if result.error_patterns:
            lines.extend([
                "## 检测到的错误模式",
                "",
            ])
            for i, pattern in enumerate(result.error_patterns[:10], 1):
                lines.append(f"### {i}. {pattern.pattern}")
                lines.append("")
                lines.append(f"- **出现次数**: {pattern.count}")
                if pattern.first_seen:
                    lines.append(f"- **首次出现**: {pattern.first_seen.strftime('%Y-%m-%d %H:%M:%S')}")
                if pattern.last_seen:
                    lines.append(f"- **最后出现**: {pattern.last_seen.strftime('%Y-%m-%d %H:%M:%S')}")
                if pattern.affected_modules:
                    lines.append(f"- **影响模块**: {', '.join(pattern.affected_modules[:5])}")
                if pattern.examples:
                    lines.append("- **示例:**")
                    lines.append("  ```")
                    lines.append(f"  {pattern.examples[0][:200]}")
                    lines.append("  ```")
                lines.append("")

        # Top 错误
        if result.top_errors:
            lines.extend([
                "## 最常见的错误",
                "",
                "| 排名 | 出现次数 | 错误信息 |",
                "|------|----------|----------|",
            ])
            for i, (msg, count) in enumerate(result.top_errors, 1):
                truncated = msg[:80] + "..." if len(msg) > 80 else msg
                lines.append(f"| {i} | {count} | {truncated} |")
            lines.append("")

        # Top 警告
        if result.top_warnings:
            lines.extend([
                "## 最常见的警告",
                "",
                "| 排名 | 出现次数 | 警告信息 |",
                "|------|----------|----------|",
            ])
            for i, (msg, count) in enumerate(result.top_warnings, 1):
                truncated = msg[:80] + "..." if len(msg) > 80 else msg
                lines.append(f"| {i} | {count} | {truncated} |")
            lines.append("")

        # 模块分布
        if result.module_distribution:
            lines.extend([
                "## 活跃模块 Top 10",
                "",
                "| 模块 | 日志数量 |",
                "|------|----------|",
            ])
            for module, count in list(result.module_distribution.items())[:10]:
                lines.append(f"| {module} | {count:,} |")
            lines.append("")

        # 每小时分布
        if result.hourly_distribution:
            lines.extend([
                "## 每小时活动分布",
                "",
                "```",
            ])
            max_count = max(result.hourly_distribution.values())
            for hour in range(24):
                count = result.hourly_distribution.get(hour, 0)
                bar_len = int(count / max_count * 40) if max_count > 0 else 0
                bar = '*' * bar_len
                lines.append(f"{hour:02d}:00 | {bar} ({count})")
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def _generate_text_report(self, result: AnalysisResult) -> str:
        """生成纯文本格式报告"""
        lines = [
            "=" * 60,
            "日志分析报告",
            "=" * 60,
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "概览",
            "-" * 40,
            f"总条目数: {result.total_entries:,}",
            f"错误数: {result.error_count:,}",
            f"警告数: {result.warning_count:,}",
            f"信息数: {result.info_count:,}",
            "",
        ]

        # 错误模式
        if result.error_patterns:
            lines.extend([
                "检测到的错误模式",
                "-" * 40,
            ])
            for pattern in result.error_patterns[:5]:
                lines.append(f"  [{pattern.count}次] {pattern.pattern}")
            lines.append("")

        # Top 错误
        if result.top_errors:
            lines.extend([
                "最常见的错误",
                "-" * 40,
            ])
            for i, (msg, count) in enumerate(result.top_errors[:5], 1):
                lines.append(f"  {i}. [{count}次] {msg[:60]}")
            lines.append("")

        return "\n".join(lines)


def analyze_logs(
    log_path: str = "Logs",
    output_format: str = "markdown",
    output_file: Optional[str] = None
) -> str:
    """
    便捷函数：分析日志并生成报告

    Args:
        log_path: 日志文件或目录路径
        output_format: 输出格式 (markdown, text, json)
        output_file: 输出文件路径（可选）

    Returns:
        分析报告
    """
    path = Path(log_path)

    analyzer = LogAnalyzer(log_dir=str(path) if path.is_dir() else str(path.parent))

    if path.is_file():
        result = analyzer.analyze_file(str(path))
    else:
        result = analyzer.analyze_directory()

    if output_format == "json":
        report = json.dumps(result.to_dict(), indent=2, ensure_ascii=False, default=str)
    else:
        report = analyzer.generate_report(result, format=output_format)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"报告已保存到: {output_file}")

    return report


if __name__ == "__main__":
    import argparse

    # 配置命令行日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="日志分析工具")
    parser.add_argument(
        "path",
        nargs="?",
        default="Logs",
        help="日志文件或目录路径 (默认: Logs)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["markdown", "text", "json"],
        default="markdown",
        help="输出格式 (默认: markdown)"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出文件路径"
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=100000,
        help="最大解析条目数 (默认: 100000)"
    )

    args = parser.parse_args()

    # 运行分析
    report = analyze_logs(
        log_path=args.path,
        output_format=args.format,
        output_file=args.output
    )

    if not args.output:
        print(report)
