"""
报告生成工具
============

生成各类报告（审批请求、进度报告、错误报告等），使用 Jinja2 模板引擎。
输出格式为 Markdown，支持自定义模板。

功能:
- 审批请求报告 (approval)
- 进度报告 (progress)
- 错误报告 (error)
- 实验结果报告 (experiment)
- 文献调研报告 (literature)
- 自定义报告 (custom)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field, asdict
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 检查 Jinja2 依赖
try:
    from jinja2 import Template, Environment, FileSystemLoader, DictLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logger.warning("Jinja2 未安装，请使用: pip install jinja2")


@dataclass
class ReportMetadata:
    """报告元数据"""
    title: str
    report_type: str
    author: str = "Prometheus System"
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    version: str = "1.0"


class ReportGenerator:
    """报告生成器"""

    # 内置模板
    BUILTIN_TEMPLATES = {
        # 审批请求报告模板
        'approval': """# 审批请求报告

**报告类型**: 审批请求
**生成时间**: {{ metadata.created_at }}
**请求人**: {{ metadata.author }}

---

## 请求概述

**标题**: {{ data.title }}
**请求类型**: {{ data.request_type | default('待审批') }}
**优先级**: {{ data.priority | default('普通') }}

## 请求详情

{{ data.description | default('无详细描述') }}

{% if data.changes %}
## 变更内容

{% for change in data.changes %}
### {{ loop.index }}. {{ change.title | default('变更项') }}

- **类型**: {{ change.type | default('未知') }}
- **描述**: {{ change.description | default('无描述') }}
{% if change.details %}
- **详细信息**:
  {{ change.details | indent(4) }}
{% endif %}
{% endfor %}
{% endif %}

{% if data.resources %}
## 所需资源

| 资源类型 | 数量/规格 | 备注 |
|---------|----------|------|
{% for resource in data.resources %}
| {{ resource.type }} | {{ resource.amount }} | {{ resource.note | default('-') }} |
{% endfor %}
{% endif %}

{% if data.risks %}
## 风险评估

{% for risk in data.risks %}
- **{{ risk.name }}**: {{ risk.description }} (风险等级: {{ risk.level }})
{% endfor %}
{% endif %}

---

## 审批选项

- [ ] **批准** - 同意执行此请求
- [ ] **拒绝** - 拒绝此请求
- [ ] **需要更多信息** - 需要补充信息后再审批
- [ ] **延期** - 推迟到指定时间再审批

{% if data.approval_deadline %}
**审批截止时间**: {{ data.approval_deadline }}
{% endif %}

---

*此报告由 Prometheus 自动生成*
""",

        # 进度报告模板
        'progress': """# 进度报告

**报告类型**: 项目进度
**生成时间**: {{ metadata.created_at }}
**报告人**: {{ metadata.author }}

---

## 项目信息

- **项目名称**: {{ data.project_name | default('未命名项目') }}
- **当前阶段**: {{ data.current_phase | default('未知') }}
- **总体进度**: {{ data.progress_percentage | default(0) }}%

## 进度概览

```
{% if data.progress_bar %}{{ data.progress_bar }}{% else %}[进度条未生成]{% endif %}
```

{% if data.phases %}
## 阶段详情

| 阶段 | 状态 | 开始时间 | 完成时间 | 备注 |
|------|------|---------|---------|------|
{% for phase in data.phases %}
| {{ phase.name }} | {{ phase.status }} | {{ phase.start_time | default('-') }} | {{ phase.end_time | default('-') }} | {{ phase.note | default('-') }} |
{% endfor %}
{% endif %}

{% if data.completed_tasks %}
## 已完成任务

{% for task in data.completed_tasks %}
- [x] {{ task.name }} {% if task.completed_at %}({{ task.completed_at }}){% endif %}
{% endfor %}
{% endif %}

{% if data.pending_tasks %}
## 待完成任务

{% for task in data.pending_tasks %}
- [ ] {{ task.name }} {% if task.priority %}[优先级: {{ task.priority }}]{% endif %}
{% endfor %}
{% endif %}

{% if data.blockers %}
## 阻塞问题

{% for blocker in data.blockers %}
### {{ blocker.title }}

- **严重程度**: {{ blocker.severity | default('中') }}
- **描述**: {{ blocker.description }}
- **建议解决方案**: {{ blocker.solution | default('待定') }}
{% endfor %}
{% endif %}

{% if data.next_steps %}
## 下一步计划

{% for step in data.next_steps %}
{{ loop.index }}. {{ step.description }} {% if step.deadline %}(截止: {{ step.deadline }}){% endif %}
{% endfor %}
{% endif %}

{% if data.metrics %}
## 关键指标

| 指标 | 当前值 | 目标值 | 状态 |
|------|-------|-------|------|
{% for metric in data.metrics %}
| {{ metric.name }} | {{ metric.current }} | {{ metric.target }} | {{ metric.status }} |
{% endfor %}
{% endif %}

---

*此报告由 Prometheus 自动生成*
""",

        # 错误报告模板
        'error': """# 错误报告

**报告类型**: 错误/异常
**生成时间**: {{ metadata.created_at }}
**报告人**: {{ metadata.author }}

---

## 错误概要

- **错误类型**: {{ data.error_type | default('未知错误') }}
- **严重程度**: {{ data.severity | default('中') }}
- **状态**: {{ data.status | default('未解决') }}

## 错误详情

### 错误信息

```
{{ data.error_message | default('无错误信息') }}
```

{% if data.stack_trace %}
### 堆栈跟踪

```
{{ data.stack_trace }}
```
{% endif %}

### 发生环境

| 项目 | 值 |
|------|-----|
| 操作系统 | {{ data.environment.os | default('未知') }} |
| Python 版本 | {{ data.environment.python_version | default('未知') }} |
| 相关文件 | {{ data.environment.file | default('未知') }} |
| 行号 | {{ data.environment.line | default('未知') }} |

{% if data.context %}
### 上下文信息

```json
{{ data.context | tojson(indent=2) }}
```
{% endif %}

{% if data.reproduction_steps %}
### 复现步骤

{% for step in data.reproduction_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}
{% endif %}

{% if data.possible_causes %}
## 可能原因

{% for cause in data.possible_causes %}
- {{ cause }}
{% endfor %}
{% endif %}

{% if data.suggested_fixes %}
## 建议解决方案

{% for fix in data.suggested_fixes %}
### 方案 {{ loop.index }}: {{ fix.title | default('') }}

{{ fix.description | default('无描述') }}

{% if fix.code %}
```{{ fix.language | default('python') }}
{{ fix.code }}
```
{% endif %}
{% endfor %}
{% endif %}

{% if data.related_errors %}
## 相关错误

{% for related in data.related_errors %}
- **{{ related.type }}**: {{ related.message }} ({{ related.timestamp | default('时间未知') }})
{% endfor %}
{% endif %}

---

*此报告由 Prometheus 自动生成*
""",

        # 实验结果报告模板
        'experiment': """# 实验结果报告

**报告类型**: 实验结果
**生成时间**: {{ metadata.created_at }}
**报告人**: {{ metadata.author }}

---

## 实验概述

- **实验名称**: {{ data.experiment_name | default('未命名实验') }}
- **实验目的**: {{ data.purpose | default('无') }}
- **实验日期**: {{ data.date | default(metadata.created_at) }}

## 实验设置

{% if data.hypothesis %}
### 假设

{{ data.hypothesis }}
{% endif %}

{% if data.methodology %}
### 方法

{{ data.methodology }}
{% endif %}

{% if data.parameters %}
### 参数配置

| 参数 | 值 |
|------|-----|
{% for param in data.parameters %}
| {{ param.name }} | {{ param.value }} |
{% endfor %}
{% endif %}

## 实验结果

{% if data.main_results %}
### 主要结果

| 指标 | 值 | 基准 | 差异 |
|------|-----|------|------|
{% for result in data.main_results %}
| {{ result.metric }} | {{ result.value }} | {{ result.baseline | default('-') }} | {{ result.difference | default('-') }} |
{% endfor %}
{% endif %}

{% if data.comparison %}
### 方法对比

| 方法 | {% for metric in data.comparison.metrics %}{{ metric }} | {% endfor %}
|------|{% for _ in data.comparison.metrics %}------|{% endfor %}
{% for method in data.comparison.methods %}
| {{ method.name }} | {% for value in method.values %}{{ value }} | {% endfor %}
{% endfor %}
{% endif %}

{% if data.statistical_tests %}
### 统计检验

{% for test in data.statistical_tests %}
- **{{ test.name }}**: p-value = {{ test.p_value | default('N/A') }}, {{ '显著' if test.significant else '不显著' }}
{% endfor %}
{% endif %}

{% if data.figures %}
### 图表

{% for figure in data.figures %}
- **{{ figure.title }}**: {{ figure.path }}{% if figure.description %} - {{ figure.description }}{% endif %}
{% endfor %}
{% endif %}

## 结论

{% if data.conclusions %}
### 主要发现

{% for conclusion in data.conclusions %}
{{ loop.index }}. {{ conclusion }}
{% endfor %}
{% endif %}

{% if data.limitations %}
### 局限性

{% for limitation in data.limitations %}
- {{ limitation }}
{% endfor %}
{% endif %}

{% if data.future_work %}
### 未来工作

{% for item in data.future_work %}
- {{ item }}
{% endfor %}
{% endif %}

---

*此报告由 Prometheus 自动生成*
""",

        # 文献调研报告模板
        'literature': """# 文献调研报告

**报告类型**: 文献调研
**生成时间**: {{ metadata.created_at }}
**报告人**: {{ metadata.author }}

---

## 调研概述

- **调研主题**: {{ data.topic | default('未指定主题') }}
- **调研范围**: {{ data.scope | default('未指定范围') }}
- **检索时间范围**: {{ data.time_range | default('不限') }}

## 检索策略

{% if data.search_strategy %}
{{ data.search_strategy }}
{% endif %}

{% if data.databases %}
### 检索数据库

{% for db in data.databases %}
- {{ db.name }}: {{ db.query | default('默认查询') }}
{% endfor %}
{% endif %}

## 文献统计

- **检索结果总数**: {{ data.total_papers | default(0) }}
- **筛选后数量**: {{ data.filtered_papers | default(0) }}
- **详细分析数量**: {{ data.analyzed_papers | default(0) }}

{% if data.papers %}
## 主要文献

{% for paper in data.papers %}
### {{ loop.index }}. {{ paper.title }}

- **作者**: {{ paper.authors | join(', ') | default('未知') }}
- **发表年份**: {{ paper.year | default('未知') }}
- **来源**: {{ paper.source | default('未知') }}
- **引用数**: {{ paper.citations | default(0) }}
{% if paper.abstract %}
- **摘要**: {{ paper.abstract[:200] }}{% if paper.abstract|length > 200 %}...{% endif %}
{% endif %}
{% if paper.key_findings %}
- **关键发现**:
{% for finding in paper.key_findings %}
  - {{ finding }}
{% endfor %}
{% endif %}
{% if paper.url %}
- **链接**: [查看原文]({{ paper.url }})
{% endif %}
{% endfor %}
{% endif %}

{% if data.research_gaps %}
## 研究空白 (Research Gaps)

{% for gap in data.research_gaps %}
### {{ gap.title | default('空白 ' + loop.index|string) }}

- **描述**: {{ gap.description }}
- **重要性**: {{ gap.importance | default('中') }}
- **相关文献**: {{ gap.related_papers | join(', ') | default('无') }}
{% endfor %}
{% endif %}

{% if data.trends %}
## 研究趋势

{% for trend in data.trends %}
- **{{ trend.name }}**: {{ trend.description }} {% if trend.papers_count %}({{ trend.papers_count }} 篇相关文献){% endif %}
{% endfor %}
{% endif %}

{% if data.recommendations %}
## 建议

{% for rec in data.recommendations %}
{{ loop.index }}. {{ rec }}
{% endfor %}
{% endif %}

---

## 参考文献

{% if data.bibliography %}
{% for ref in data.bibliography %}
[{{ loop.index }}] {{ ref }}
{% endfor %}
{% endif %}

---

*此报告由 Prometheus 自动生成*
""",

        # 通用报告模板
        'custom': """# {{ metadata.title }}

**报告类型**: {{ metadata.report_type | default('通用报告') }}
**生成时间**: {{ metadata.created_at }}
**报告人**: {{ metadata.author }}

---

{% if data.summary %}
## 摘要

{{ data.summary }}
{% endif %}

{% if data.sections %}
{% for section in data.sections %}
## {{ section.title }}

{{ section.content | default('无内容') }}

{% if section.subsections %}
{% for subsection in section.subsections %}
### {{ subsection.title }}

{{ subsection.content | default('无内容') }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

{% if data.tables %}
{% for table in data.tables %}
## {{ table.title | default('表格 ' + loop.index|string) }}

| {% for col in table.columns %}{{ col }} | {% endfor %}
|{% for _ in table.columns %}------|{% endfor %}
{% for row in table.rows %}
| {% for cell in row %}{{ cell }} | {% endfor %}
{% endfor %}

{% endfor %}
{% endif %}

{% if data.notes %}
## 备注

{{ data.notes }}
{% endif %}

---

*此报告由 Prometheus 自动生成*
"""
    }

    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化报告生成器

        Args:
            template_dir: 自定义模板目录路径
        """
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 是必需的依赖，请先安装: pip install jinja2")

        self.template_dir = Path(template_dir) if template_dir else None
        self.env = self._create_environment()

    def _create_environment(self) -> Environment:
        """创建 Jinja2 环境"""
        if self.template_dir and self.template_dir.exists():
            # 使用文件系统加载器
            env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            # 使用内置模板
            env = Environment(
                loader=DictLoader(self.BUILTIN_TEMPLATES),
                trim_blocks=True,
                lstrip_blocks=True
            )

        # 添加自定义过滤器
        env.filters['tojson'] = lambda obj, **kwargs: json.dumps(obj, **kwargs, ensure_ascii=False)
        env.filters['indent'] = lambda text, spaces=4: text.replace('\n', '\n' + ' ' * spaces) if text else ''

        return env

    def generate(
        self,
        report_type: str,
        data: Dict[str, Any],
        title: str = None,
        author: str = "Prometheus System",
        output_path: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> str:
        """
        生成报告

        Args:
            report_type: 报告类型 ('approval', 'progress', 'error', 'experiment', 'literature', 'custom')
            data: 报告数据
            title: 报告标题
            author: 作者
            output_path: 输出文件路径（可选）
            template_name: 自定义模板名称（可选）

        Returns:
            生成的报告内容（Markdown 格式）
        """
        # 创建元数据
        metadata = ReportMetadata(
            title=title or f"{report_type.capitalize()} Report",
            report_type=report_type,
            author=author
        )

        # 获取模板
        template_key = template_name or report_type
        try:
            template = self.env.get_template(template_key)
        except Exception:
            # 如果找不到模板，使用通用模板
            logger.warning(f"模板 '{template_key}' 未找到，使用通用模板")
            template = self.env.get_template('custom')

        # 渲染模板
        context = {
            'metadata': asdict(metadata),
            'data': data
        }

        try:
            report_content = template.render(**context)
        except Exception as e:
            logger.error(f"模板渲染失败: {e}")
            raise ValueError(f"报告生成失败: {e}")

        # 保存到文件
        if output_path:
            self._save_report(report_content, output_path)

        return report_content

    def generate_from_file(
        self,
        data_file: str,
        report_type: str = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        从数据文件生成报告

        Args:
            data_file: 数据文件路径 (JSON 格式)
            report_type: 报告类型（可选，从数据中读取）
            output_path: 输出文件路径（可选）

        Returns:
            生成的报告内容
        """
        file_path = Path(data_file)

        if file_path.suffix != '.json':
            raise ValueError("数据文件必须是 JSON 格式")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 从数据中获取报告类型
        actual_report_type = report_type or data.get('report_type', 'custom')
        title = data.get('title')
        author = data.get('author', 'Prometheus System')

        # 移除元数据字段
        report_data = {k: v for k, v in data.items()
                      if k not in ['report_type', 'title', 'author']}

        return self.generate(
            report_type=actual_report_type,
            data=report_data,
            title=title,
            author=author,
            output_path=output_path
        )

    def _save_report(self, content: str, output_path: str):
        """保存报告到文件"""
        output_file = Path(output_path)

        # 确保目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 如果没有扩展名，添加 .md
        if not output_file.suffix:
            output_file = output_file.with_suffix('.md')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"报告已保存到: {output_file}")

    def list_templates(self) -> List[str]:
        """列出可用的模板"""
        templates = list(self.BUILTIN_TEMPLATES.keys())

        if self.template_dir and self.template_dir.exists():
            # 添加自定义模板
            for file in self.template_dir.glob('*.md'):
                templates.append(file.stem)
            for file in self.template_dir.glob('*.jinja2'):
                templates.append(file.stem)

        return templates

    def add_custom_template(self, name: str, template_content: str):
        """
        添加自定义模板

        Args:
            name: 模板名称
            template_content: 模板内容
        """
        self.BUILTIN_TEMPLATES[name] = template_content
        # 重新创建环境以包含新模板
        self.env = self._create_environment()
        logger.info(f"已添加自定义模板: {name}")


def create_sample_data(report_type: str) -> Dict[str, Any]:
    """创建示例数据"""
    samples = {
        'approval': {
            'title': '新增实验功能审批请求',
            'request_type': '功能新增',
            'priority': '高',
            'description': '请求批准新增自动化实验功能，该功能将自动执行实验并生成报告。',
            'changes': [
                {
                    'title': '新增实验执行模块',
                    'type': '功能新增',
                    'description': '实现自动化实验执行流程',
                    'details': '包含实验配置、执行监控、结果收集'
                },
                {
                    'title': '新增报告生成模块',
                    'type': '功能新增',
                    'description': '自动生成实验结果报告'
                }
            ],
            'resources': [
                {'type': '计算资源', 'amount': '4 GPU', 'note': '用于模型训练'},
                {'type': '存储空间', 'amount': '100GB', 'note': '用于数据存储'}
            ],
            'risks': [
                {'name': '资源超支', 'description': '可能超出预算', 'level': '中'},
                {'name': '时间延误', 'description': '开发时间可能延长', 'level': '低'}
            ],
            'approval_deadline': '2026-02-20'
        },
        'progress': {
            'project_name': 'Project Prometheus',
            'current_phase': 'Phase 2: 假设设计',
            'progress_percentage': 35,
            'progress_bar': '████████░░░░░░░░░░░░ 35%',
            'phases': [
                {'name': 'Phase 1', 'status': '已完成', 'start_time': '2026-02-01', 'end_time': '2026-02-05', 'note': '文献调研'},
                {'name': 'Phase 2', 'status': '进行中', 'start_time': '2026-02-06', 'end_time': '-', 'note': '假设设计'},
                {'name': 'Phase 3', 'status': '未开始', 'start_time': '-', 'end_time': '-', 'note': '编码实现'}
            ],
            'completed_tasks': [
                {'name': '完成文献综述', 'completed_at': '2026-02-05'},
                {'name': '确定研究问题', 'completed_at': '2026-02-06'}
            ],
            'pending_tasks': [
                {'name': '设计实验方案', 'priority': '高'},
                {'name': '准备数据集', 'priority': '中'}
            ],
            'blockers': [
                {
                    'title': 'API 限流问题',
                    'severity': '中',
                    'description': '第三方 API 请求频率受限',
                    'solution': '实现请求队列和重试机制'
                }
            ],
            'next_steps': [
                {'description': '完成假设形式化', 'deadline': '2026-02-18'},
                {'description': '设计对比实验', 'deadline': '2026-02-20'}
            ],
            'metrics': [
                {'name': '代码覆盖率', 'current': '75%', 'target': '80%', 'status': '接近目标'},
                {'name': '文档完成度', 'current': '60%', 'target': '100%', 'status': '需加速'}
            ]
        },
        'error': {
            'error_type': 'ConnectionError',
            'severity': '高',
            'status': '未解决',
            'error_message': 'Failed to connect to API endpoint: Connection refused',
            'stack_trace': '''Traceback (most recent call last):
  File "api_client.py", line 45, in request
    response = session.get(url)
  File "requests/sessions.py", line 542, in get
    return self.request('GET', url, **kwargs)
ConnectionError: Connection refused''',
            'environment': {
                'os': 'Windows 10',
                'python_version': '3.10.0',
                'file': 'api_client.py',
                'line': '45'
            },
            'context': {'url': 'https://api.example.com/v1/data', 'timeout': 30},
            'reproduction_steps': [
                '配置 API 凭证',
                '运行 python api_client.py',
                '观察错误输出'
            ],
            'possible_causes': [
                '网络连接问题',
                'API 服务未启动',
                '防火墙阻止连接'
            ],
            'suggested_fixes': [
                {
                    'title': '检查网络连接',
                    'description': '确保网络正常，可以访问目标地址',
                    'code': 'ping api.example.com'
                },
                {
                    'title': '添加重试机制',
                    'description': '在代码中添加重试逻辑',
                    'language': 'python',
                    'code': '''from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def make_request(url):
    return session.get(url)'''
                }
            ],
            'related_errors': [
                {'type': 'TimeoutError', 'message': 'Request timed out', 'timestamp': '2026-02-15'}
            ]
        },
        'experiment': {
            'experiment_name': '模型对比实验',
            'purpose': '比较不同模型在文本分类任务上的性能',
            'date': '2026-02-16',
            'hypothesis': '新提出的 Attention 机制能提升分类准确率',
            'methodology': '使用相同数据集训练三个模型，对比准确率、F1分数和推理速度',
            'parameters': [
                {'name': '学习率', 'value': '1e-4'},
                {'name': '批次大小', 'value': '32'},
                {'name': '训练轮数', 'value': '10'}
            ],
            'main_results': [
                {'metric': '准确率', 'value': '92.5%', 'baseline': '88.3%', 'difference': '+4.2%'},
                {'metric': 'F1分数', 'value': '91.8%', 'baseline': '87.1%', 'difference': '+4.7%'}
            ],
            'comparison': {
                'metrics': ['准确率', 'F1', '推理时间(ms)'],
                'methods': [
                    {'name': 'Our Method', 'values': ['92.5%', '91.8%', '15']},
                    {'name': 'Baseline', 'values': ['88.3%', '87.1%', '12']},
                    {'name': 'Method A', 'values': ['89.1%', '88.0%', '18']}
                ]
            },
            'statistical_tests': [
                {'name': 't-test', 'p_value': 0.003, 'significant': True}
            ],
            'figures': [
                {'title': '准确率对比图', 'path': 'figures/accuracy.png', 'description': '三种方法的准确率对比'},
                {'title': '训练曲线', 'path': 'figures/training_curve.png', 'description': '训练损失变化'}
            ],
            'conclusions': [
                '新方法在准确率上显著优于基线',
                '推理速度略有下降，但可接受'
            ],
            'limitations': [
                '仅在一个数据集上测试',
                '未考虑模型大小的影响'
            ],
            'future_work': [
                '在更多数据集上验证',
                '探索模型压缩方法'
            ]
        },
        'literature': {
            'topic': '大型语言模型的高效推理方法',
            'scope': '2020-2026年的相关研究',
            'time_range': '2020-2026',
            'search_strategy': '使用关键词 "efficient inference", "LLM optimization" 在主要学术数据库中检索',
            'databases': [
                {'name': 'Semantic Scholar', 'query': 'efficient inference large language model'},
                {'name': 'arXiv', 'query': 'LLM optimization inference'}
            ],
            'total_papers': 156,
            'filtered_papers': 45,
            'analyzed_papers': 12,
            'papers': [
                {
                    'title': 'Efficient Inference for Large Language Models',
                    'authors': ['Smith, J.', 'Johnson, A.'],
                    'year': 2024,
                    'source': 'NeurIPS 2024',
                    'citations': 245,
                    'abstract': '本文提出了一种新的推理加速方法...',
                    'key_findings': [
                        '实现了2-3倍的推理加速',
                        '几乎不损失模型质量'
                    ],
                    'url': 'https://arxiv.org/abs/xxx'
                }
            ],
            'research_gaps': [
                {
                    'title': '边缘设备部署',
                    'description': '现有方法主要针对服务器环境，边缘设备的研究较少',
                    'importance': '高',
                    'related_papers': ['Smith 2024', 'Lee 2023']
                }
            ],
            'trends': [
                {'name': '量化技术', 'description': 'INT8/INT4 量化成为主流', 'papers_count': 28},
                {'name': '知识蒸馏', 'description': '从大模型蒸馏到小模型', 'papers_count': 15}
            ],
            'recommendations': [
                '关注量化技术的最新进展',
                '研究边缘设备部署的优化方法'
            ],
            'bibliography': [
                'Smith, J. et al. (2024). Efficient Inference for LLMs. NeurIPS.',
                'Lee, K. et al. (2023). Model Compression Techniques. ICML.'
            ]
        }
    }

    return samples.get(report_type, {})


def main():
    parser = argparse.ArgumentParser(
        description='报告生成工具 - 生成各类 Markdown 报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 生成进度报告
  python report_generator.py progress --data progress_data.json -o progress.md

  # 生成错误报告
  python report_generator.py error --data error_data.json -o error.md

  # 生成示例报告
  python report_generator.py --example approval -o example_approval.md

  # 列出可用模板
  python report_generator.py --list-templates
        '''
    )

    parser.add_argument(
        'report_type',
        nargs='?',
        choices=['approval', 'progress', 'error', 'experiment', 'literature', 'custom'],
        help='报告类型'
    )
    parser.add_argument('--data', '-d', help='数据文件路径 (JSON 格式)')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--title', '-t', help='报告标题')
    parser.add_argument('--author', '-a', default='Prometheus System', help='作者')
    parser.add_argument('--template-dir', help='自定义模板目录')
    parser.add_argument('--template', help='指定模板名称')
    parser.add_argument('--example', action='store_true', help='使用示例数据生成报告')
    parser.add_argument('--list-templates', action='store_true', help='列出可用模板')
    parser.add_argument('--save-example-data', metavar='DIR', help='保存示例数据文件到指定目录')

    args = parser.parse_args()

    # 列出模板
    if args.list_templates:
        generator = ReportGenerator()
        templates = generator.list_templates()
        print("可用模板:")
        for t in templates:
            print(f"  - {t}")
        return

    # 保存示例数据
    if args.save_example_data:
        output_dir = Path(args.save_example_data)
        output_dir.mkdir(parents=True, exist_ok=True)

        for report_type in ['approval', 'progress', 'error', 'experiment', 'literature']:
            sample_data = create_sample_data(report_type)
            sample_data['report_type'] = report_type
            sample_data['title'] = f'{report_type.capitalize()} Report Example'

            output_file = output_dir / f'{report_type}_data.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=2, ensure_ascii=False)
            print(f"已保存: {output_file}")
        return

    # 检查必需参数
    if not args.report_type:
        parser.print_help()
        return

    # 创建报告生成器
    generator = ReportGenerator(template_dir=args.template_dir)

    # 获取数据
    if args.example:
        data = create_sample_data(args.report_type)
    elif args.data:
        with open(args.data, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print("错误: 请使用 --data 指定数据文件，或使用 --example 生成示例报告")
        return

    # 生成报告
    try:
        report = generator.generate(
            report_type=args.report_type,
            data=data,
            title=args.title,
            author=args.author,
            output_path=args.output,
            template_name=args.template
        )

        if not args.output:
            print(report)
        else:
            print(f"报告已生成: {args.output}")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
