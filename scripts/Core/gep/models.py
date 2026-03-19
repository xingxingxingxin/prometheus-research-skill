#!/usr/bin/env python3
"""
Project Prometheus - GEP Data Models
=====================================

Core data models for the GEP (Genome Evolution Protocol).

Based on EvoMap/evolver GEP protocol v1.10.3

Usage:
    from Core.gep.models import Gene, Capsule, EvolutionEvent, GeneCategory

    gene = Gene(
        id="gene_syntax_fix",
        name="Syntax Error Fix",
        category=GeneCategory.REPAIR,
        signals_match=["error_type:SyntaxError"],
        strategy=[{"step": 1, "action": "parse_error_line"}]
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import json
import hashlib
import re


class GeneCategory(Enum):
    """Gene 演化意图类别"""
    REPAIR = "repair"       # 修复模式：修复错误
    OPTIMIZE = "optimize"   # 优化模式：改进性能/结构
    INNOVATE = "innovate"   # 创新模式：引入新功能


class SignalType(Enum):
    """信号类型"""
    ERROR = "error"
    WARNING = "warning"
    PERFORMANCE = "performance"
    OPPORTUNITY = "opportunity"
    PATTERN = "pattern"


@dataclass
class Signal:
    """
    从错误或观察中提取的信号。

    信号用于匹配 Gene 的 signals_match 模式。
    """
    error_type: str = ""
    error_message: str = ""
    phase: str = ""
    task_id: str = ""
    file_path: str = ""
    line_number: int = 0
    traceback: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_match_patterns(self) -> List[str]:
        """转换为匹配模式列表"""
        patterns = []
        if self.error_type:
            patterns.append(f"error_type:{self.error_type}")
        if self.phase:
            patterns.append(f"phase:{self.phase}")
        if self.file_path:
            patterns.append(f"file_ext:{self._get_file_ext()}")
        # 从错误消息中提取关键词
        keywords = self._extract_keywords()
        patterns.extend([f"keyword:{kw}" for kw in keywords])
        return patterns

    def _get_file_ext(self) -> str:
        """获取文件扩展名"""
        if self.file_path:
            return self.file_path.rsplit('.', 1)[-1] if '.' in self.file_path else ""
        return ""

    def _extract_keywords(self) -> List[str]:
        """从错误消息中提取关键词"""
        keywords = []
        # 提取常见的错误关键词
        patterns = [
            r'undefined',
            r'not found',
            r'missing',
            r'invalid',
            r'unexpected',
            r'failed',
            r'error',
            r'warning',
        ]
        msg_lower = self.error_message.lower()
        for p in patterns:
            if re.search(p, msg_lower):
                keywords.append(p.replace(' ', '_'))
        return keywords[:5]  # 最多5个关键词

    def to_dict(self) -> Dict:
        return {
            'error_type': self.error_type,
            'error_message': self.error_message,
            'phase': self.phase,
            'task_id': self.task_id,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'traceback': self.traceback,
            'context': self.context,
            'timestamp': self.timestamp
        }


@dataclass
class Gene:
    """
    Gene - 可复用的演化策略模板。

    Gene 定义了如何响应特定类型的信号（错误、警告、机会），
    包含执行策略、约束条件和验证命令。

    Attributes:
        id: 唯一标识符
        name: 人类可读的名称
        category: 演化类别 (repair/optimize/innovate)
        signals_match: 触发此 Gene 的信号模式列表
        strategy: 执行策略步骤列表
        constraints: 执行约束
        validation_cmd: 验证命令模板
        description: 详细描述
        priority: 优先级 (越高越优先)
        success_rate: 历史成功率 (0-1)
        use_count: 使用次数
    """
    id: str
    name: str
    category: GeneCategory
    signals_match: List[str] = field(default_factory=list)
    strategy: List[Dict[str, Any]] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    validation_cmd: str = ""
    description: str = ""
    priority: int = 50
    success_rate: float = 0.5
    use_count: int = 0
    created_at: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def matches_signal(self, signal: Signal) -> float:
        """
        计算与信号的匹配分数。

        Args:
            signal: 输入信号

        Returns:
            匹配分数 (0-1)，越高越匹配
        """
        signal_patterns = signal.to_match_patterns()
        if not signal_patterns:
            return 0.0

        matched = 0
        for gene_pattern in self.signals_match:
            for signal_pattern in signal_patterns:
                if self._pattern_matches(gene_pattern, signal_pattern):
                    matched += 1
                    break

        # 计算覆盖率
        coverage = matched / len(self.signals_match) if self.signals_match else 0

        # 考虑优先级和成功率
        score = coverage * 0.7 + (self.priority / 100) * 0.1 + self.success_rate * 0.2

        return min(1.0, score)

    def _pattern_matches(self, gene_pattern: str, signal_pattern: str) -> bool:
        """检查基因模式是否匹配信号模式"""
        # 支持通配符
        if gene_pattern.endswith('*'):
            prefix = gene_pattern[:-1]
            return signal_pattern.startswith(prefix)

        # 支持正则表达式
        if gene_pattern.startswith('/') and gene_pattern.endswith('/'):
            regex = gene_pattern[1:-1]
            try:
                return bool(re.search(regex, signal_pattern, re.IGNORECASE))
            except re.error:
                return False

        # 精确匹配（忽略大小写）
        return gene_pattern.lower() == signal_pattern.lower()

    def get_strategy_prompt(self, context: Dict[str, Any]) -> str:
        """
        将策略转换为可执行的 Prompt。

        Args:
            context: 执行上下文

        Returns:
            生成的 Prompt 字符串
        """
        lines = [f"# Gene Strategy: {self.name}", ""]
        lines.append(f"Category: {self.category.value}")
        lines.append(f"Description: {self.description}")
        lines.append("")

        if self.constraints:
            lines.append("## Constraints")
            for key, value in self.constraints.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        lines.append("## Execution Steps")
        for step in self.strategy:
            step_num = step.get('step', '?')
            action = step.get('action', 'unknown')
            desc = step.get('description', '')
            lines.append(f"{step_num}. **{action}**: {desc}")

        if self.validation_cmd:
            lines.append("")
            lines.append("## Validation")
            cmd = self.validation_cmd.format(**context)
            lines.append(f"```bash\n{cmd}\n```")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'signals_match': self.signals_match,
            'strategy': self.strategy,
            'constraints': self.constraints,
            'validation_cmd': self.validation_cmd,
            'description': self.description,
            'priority': self.priority,
            'success_rate': self.success_rate,
            'use_count': self.use_count,
            'created_at': self.created_at,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Gene':
        return cls(
            id=data['id'],
            name=data['name'],
            category=GeneCategory(data['category']),
            signals_match=data.get('signals_match', []),
            strategy=data.get('strategy', []),
            constraints=data.get('constraints', {}),
            validation_cmd=data.get('validation_cmd', ''),
            description=data.get('description', ''),
            priority=data.get('priority', 50),
            success_rate=data.get('success_rate', 0.5),
            use_count=data.get('use_count', 0),
            created_at=data.get('created_at', ''),
            tags=data.get('tags', [])
        )


@dataclass
class Capsule:
    """
    Capsule - 成功修复胶囊。

    Capsule 记录一次成功的演化/修复，包含触发条件、使用的 Gene、
    置信度、影响范围等信息。可被语义检索复用。

    Attributes:
        id: 唯一标识符
        trigger: 触发信号描述
        gene_id: 使用的 Gene ID
        confidence: 置信度 (0-1)，基于历史成功率计算
        blast_radius: 影响范围（修改的文件列表）
        outcome: 结果状态 (success/partial/failed)
        context: 执行上下文
        summary: 修复摘要
        env_fingerprint: 环境指纹
        use_count: 被复用次数
    """
    id: str
    trigger: str
    gene_id: str
    confidence: float = 0.5
    blast_radius: List[str] = field(default_factory=list)
    outcome: str = "success"
    context: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    env_fingerprint: Dict[str, str] = field(default_factory=dict)
    use_count: int = 0
    created_at: str = ""
    asset_id: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.asset_id:
            self.asset_id = self._compute_asset_id()

    def _compute_asset_id(self) -> str:
        """计算内容哈希作为 asset_id"""
        content = json.dumps({
            'trigger': self.trigger,
            'gene_id': self.gene_id,
            'summary': self.summary
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_searchable_text(self) -> str:
        """转换为可搜索的文本（用于 RAG 索引）"""
        parts = [
            f"Trigger: {self.trigger}",
            f"Gene: {self.gene_id}",
            f"Summary: {self.summary}",
            f"Outcome: {self.outcome}",
            f"Confidence: {self.confidence:.2f}",
        ]
        if self.context:
            parts.append(f"Context: {json.dumps(self.context)}")
        return "\n".join(parts)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'trigger': self.trigger,
            'gene_id': self.gene_id,
            'confidence': self.confidence,
            'blast_radius': self.blast_radius,
            'outcome': self.outcome,
            'context': self.context,
            'summary': self.summary,
            'env_fingerprint': self.env_fingerprint,
            'use_count': self.use_count,
            'created_at': self.created_at,
            'asset_id': self.asset_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Capsule':
        return cls(
            id=data['id'],
            trigger=data['trigger'],
            gene_id=data['gene_id'],
            confidence=data.get('confidence', 0.5),
            blast_radius=data.get('blast_radius', []),
            outcome=data.get('outcome', 'success'),
            context=data.get('context', {}),
            summary=data.get('summary', ''),
            env_fingerprint=data.get('env_fingerprint', {}),
            use_count=data.get('use_count', 0),
            created_at=data.get('created_at', ''),
            asset_id=data.get('asset_id', '')
        )


@dataclass
class EvolutionEvent:
    """
    EvolutionEvent - 演化事件。

    记录演化过程中发生的每个事件，形成可追溯的事件链。

    Attributes:
        id: 唯一标识符
        type: 事件类型 (attempt/success/failure/validation)
        gene_id: 使用的 Gene ID
        capsule_id: 创建/使用的 Capsule ID
        signal: 触发信号
        action_taken: 采取的行动描述
        result: 结果描述
        parent_event_id: 父事件 ID（形成链）
        metadata: 额外元数据
    """
    id: str
    type: str  # attempt, success, failure, validation
    gene_id: Optional[str] = None
    capsule_id: Optional[str] = None
    signal: Dict[str, Any] = field(default_factory=dict)
    action_taken: str = ""
    result: str = ""
    parent_event_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type,
            'gene_id': self.gene_id,
            'capsule_id': self.capsule_id,
            'signal': self.signal,
            'action_taken': self.action_taken,
            'result': self.result,
            'parent_event_id': self.parent_event_id,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EvolutionEvent':
        return cls(
            id=data['id'],
            type=data['type'],
            gene_id=data.get('gene_id'),
            capsule_id=data.get('capsule_id'),
            signal=data.get('signal', {}),
            action_taken=data.get('action_taken', ''),
            result=data.get('result', ''),
            parent_event_id=data.get('parent_event_id'),
            metadata=data.get('metadata', {}),
            timestamp=data.get('timestamp', '')
        )


@dataclass
class ValidationReport:
    """
    ValidationReport - 验证报告。

    记录演化后的验证结果。

    Attributes:
        event_id: 关联的事件 ID
        passed: 是否通过验证
        metrics: 验证指标
        errors: 错误列表
        test_results: 测试结果
    """
    event_id: str
    passed: bool = False
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    test_results: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'passed': self.passed,
            'metrics': self.metrics,
            'errors': self.errors,
            'test_results': self.test_results,
            'timestamp': self.timestamp
        }


@dataclass
class SelectorDecision:
    """
    SelectorDecision - 选择器决策。

    记录 GEP Selector 的决策过程和结果。

    Attributes:
        signal: 输入信号
        matched_genes: 匹配的 Gene 列表（带分数）
        selected_gene: 最终选择的 Gene
        related_capsules: 相关的 Capsule 列表
        decision_reason: 决策原因
        confidence: 决策置信度
    """
    signal: Signal
    matched_genes: List[Tuple[str, float]] = field(default_factory=list)
    selected_gene: Optional[str] = None
    related_capsules: List[str] = field(default_factory=list)
    decision_reason: str = ""
    confidence: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            'signal': self.signal.to_dict(),
            'matched_genes': self.matched_genes,
            'selected_gene': self.selected_gene,
            'related_capsules': self.related_capsules,
            'decision_reason': self.decision_reason,
            'confidence': self.confidence,
            'timestamp': self.timestamp
        }
