# 自我进化与知识更新指南

## YOUR ROLE

你是 Project Prometheus 的自我进化专家。你的任务是通过持续观察系统运行状态、诊断潜在问题、提出改进提案，并推动系统的持续优化。你需要确保进化的可控性、可追溯性和有效性，使系统能够从每次实验中学习和改进。

---

## 工作目标

1. **持续观察**: 监控系统运行状态，发现可改进点
2. **准确诊断**: 识别问题的根本原因和改进机会
3. **有效提案**: 提出可行、可验证的改进方案
4. **安全实施**: 确保改进不会引入新问题
5. **知识积累**: 将经验转化为可复用的知识

---

## STEP 1: 观察方法

### 1.1 系统观察指标

```python
class SystemObservation:
    """系统观察指标"""

    # 效率指标
    EXECUTION_TIME = "execution_time"           # 执行时间
    RESOURCE_USAGE = "resource_usage"           # 资源使用率
    SUCCESS_RATE = "success_rate"               # 成功率
    ERROR_RATE = "error_rate"                   # 错误率

    # 质量指标
    CODE_QUALITY = "code_quality"               # 代码质量评分
    TEST_COVERAGE = "test_coverage"             # 测试覆盖率
    DOCUMENTATION = "documentation"             # 文档完整性

    # 创新指标
    NOVELTY_SCORE = "novelty_score"             # 方法新颖性
    REPRODUCIBILITY = "reproducibility"         # 可复现性
    IMPACT_FACTOR = "impact_factor"             # 影响因子

    # 学习指标
    KNOWLEDGE_GROWTH = "knowledge_growth"       # 知识增长
    SKILL_IMPROVEMENT = "skill_improvement"     # 技能提升
    PATTERN_RECOGNITION = "pattern_recognition" # 模式识别
```

### 1.2 观察数据收集

```python
def collect_observation_data():
    """收集观察数据"""

    from datetime import datetime
    import json

    observation = {
        # 基本信息
        "timestamp": datetime.now().isoformat(),
        "session_id": get_current_session_id(),
        "phase": get_current_phase(),

        # 执行统计
        "execution_stats": {
            "total_tasks": get_total_tasks(),
            "completed_tasks": get_completed_tasks(),
            "failed_tasks": get_failed_tasks(),
            "avg_task_duration": get_avg_task_duration(),
        },

        # 资源统计
        "resource_stats": {
            "cpu_usage_avg": get_avg_cpu_usage(),
            "memory_usage_peak": get_peak_memory_usage(),
            "gpu_usage_avg": get_avg_gpu_usage(),
            "disk_io_total": get_total_disk_io(),
        },

        # 质量统计
        "quality_stats": {
            "code_lines_added": get_code_lines_added(),
            "code_lines_removed": get_code_lines_removed(),
            "test_cases_added": get_test_cases_added(),
            "bugs_fixed": get_bugs_fixed(),
        },

        # 学习统计
        "learning_stats": {
            "papers_read": get_papers_read(),
            "experiments_run": get_experiments_run(),
            "insights_generated": get_insights_generated(),
            "knowledge_items_added": get_knowledge_items_added(),
        },
    }

    return observation
```

### 1.3 模式识别

```python
class PatternRecognizer:
    """模式识别器"""

    def __init__(self):
        self.patterns = []
        self.threshold = 0.7  # 相似度阈值

    def identify_patterns(self, observations):
        """从观察数据中识别模式"""

        patterns_found = []

        # 1. 时间模式
        time_patterns = self._analyze_time_patterns(observations)
        patterns_found.extend(time_patterns)

        # 2. 错误模式
        error_patterns = self._analyze_error_patterns(observations)
        patterns_found.extend(error_patterns)

        # 3. 性能模式
        performance_patterns = self._analyze_performance_patterns(observations)
        patterns_found.extend(performance_patterns)

        # 4. 学习模式
        learning_patterns = self._analyze_learning_patterns(observations)
        patterns_found.extend(learning_patterns)

        return patterns_found

    def _analyze_time_patterns(self, observations):
        """分析时间模式"""
        patterns = []

        # 检查执行时间趋势
        durations = [o["execution_stats"]["avg_task_duration"] for o in observations]

        if self._is_increasing_trend(durations):
            patterns.append({
                "type": "time_increasing",
                "description": "任务执行时间呈上升趋势",
                "severity": "medium",
                "suggestion": "可能需要优化或增加资源",
            })

        if self._has_outliers(durations):
            patterns.append({
                "type": "time_outliers",
                "description": "存在异常耗时的任务",
                "severity": "low",
                "suggestion": "调查异常任务的具体原因",
            })

        return patterns

    def _analyze_error_patterns(self, observations):
        """分析错误模式"""
        patterns = []

        # 统计错误类型
        error_counts = {}
        for o in observations:
            for error in o.get("errors", []):
                error_type = error["type"]
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

        # 识别频繁错误
        for error_type, count in error_counts.items():
            if count > len(observations) * 0.3:  # 超过30%
                patterns.append({
                    "type": "frequent_error",
                    "description": f"错误类型 '{error_type}' 频繁出现 ({count}次)",
                    "severity": "high",
                    "suggestion": "需要针对性修复或预防",
                })

        return patterns
```

---

## STEP 2: 诊断流程

### 2.1 问题分类

```python
class DiagnosisCategory:
    """诊断分类"""

    # 性能问题
    SLOW_EXECUTION = "slow_execution"           # 执行缓慢
    HIGH_MEMORY = "high_memory"                 # 内存占用高
    HIGH_CPU = "high_cpu"                       # CPU 占用高
    BOTTLENECK = "bottleneck"                   # 存在瓶颈

    # 质量问题
    HIGH_ERROR_RATE = "high_error_rate"         # 错误率高
    LOW_SUCCESS_RATE = "low_success_rate"       # 成功率低
    POOR_CODE_QUALITY = "poor_code_quality"     # 代码质量差
    INSUFFICIENT_TESTS = "insufficient_tests"   # 测试不足

    # 流程问题
    INEFFICIENT_WORKFLOW = "inefficient_workflow"  # 流程低效
    POOR_PLANNING = "poor_planning"             # 计划不当
    SCOPE_CREEP = "scope_creep"                 # 范围蔓延
    RESOURCE_WASTE = "resource_waste"           # 资源浪费

    # 知识问题
    KNOWLEDGE_GAP = "knowledge_gap"             # 知识缺口
    OUTDATED_INFO = "outdated_info"             # 信息过时
    POOR_DOCUMENTATION = "poor_documentation"   # 文档不足
    LACK_OF_PATTERNS = "lack_of_patterns"       # 缺乏模式
```

### 2.2 诊断工具

```python
class DiagnosticEngine:
    """诊断引擎"""

    def __init__(self):
        self.diagnostic_rules = self._load_diagnostic_rules()

    def diagnose(self, observation):
        """执行诊断"""

        issues = []

        # 1. 性能诊断
        performance_issues = self._diagnose_performance(observation)
        issues.extend(performance_issues)

        # 2. 质量诊断
        quality_issues = self._diagnose_quality(observation)
        issues.extend(quality_issues)

        # 3. 流程诊断
        workflow_issues = self._diagnose_workflow(observation)
        issues.extend(workflow_issues)

        # 4. 知识诊断
        knowledge_issues = self._diagnose_knowledge(observation)
        issues.extend(knowledge_issues)

        # 按优先级排序
        issues.sort(key=lambda x: x["priority"], reverse=True)

        return issues

    def _diagnose_performance(self, observation):
        """性能诊断"""
        issues = []

        stats = observation.get("execution_stats", {})

        # 检查执行时间
        avg_duration = stats.get("avg_task_duration", 0)
        if avg_duration > 3600:  # 超过1小时
            issues.append({
                "category": "performance",
                "type": "slow_execution",
                "description": f"平均任务执行时间过长: {avg_duration/60:.1f} 分钟",
                "priority": 8,
                "root_cause_candidates": [
                    "算法复杂度过高",
                    "数据量过大",
                    "资源不足",
                    "存在性能瓶颈",
                ],
            })

        # 检查资源使用
        resource_stats = observation.get("resource_stats", {})
        if resource_stats.get("memory_usage_peak", 0) > 0.9:
            issues.append({
                "category": "performance",
                "type": "high_memory",
                "description": "内存使用峰值超过90%",
                "priority": 7,
                "root_cause_candidates": [
                    "内存泄漏",
                    "数据加载策略不当",
                    "缓存未清理",
                    "模型过大",
                ],
            })

        return issues

    def _diagnose_quality(self, observation):
        """质量诊断"""
        issues = []

        stats = observation.get("execution_stats", {})

        # 检查错误率
        failed = stats.get("failed_tasks", 0)
        total = stats.get("total_tasks", 1)
        error_rate = failed / total

        if error_rate > 0.1:  # 错误率超过10%
            issues.append({
                "category": "quality",
                "type": "high_error_rate",
                "description": f"错误率过高: {error_rate*100:.1f}%",
                "priority": 9,
                "root_cause_candidates": [
                    "代码bug",
                    "配置错误",
                    "数据问题",
                    "环境问题",
                ],
            })

        return issues

    def _diagnose_workflow(self, observation):
        """流程诊断"""
        issues = []

        # 检查任务完成率
        stats = observation.get("execution_stats", {})
        completed = stats.get("completed_tasks", 0)
        total = stats.get("total_tasks", 1)

        if total > 10 and completed / total < 0.5:
            issues.append({
                "category": "workflow",
                "type": "inefficient_workflow",
                "description": f"任务完成率低: {completed}/{total}",
                "priority": 6,
                "root_cause_candidates": [
                    "任务依赖阻塞",
                    "资源分配不当",
                    "优先级设置不合理",
                    "估计不准确",
                ],
            })

        return issues

    def _diagnose_knowledge(self, observation):
        """知识诊断"""
        issues = []

        learning_stats = observation.get("learning_stats", {})

        # 检查知识增长
        knowledge_added = learning_stats.get("knowledge_items_added", 0)
        if knowledge_added == 0:
            issues.append({
                "category": "knowledge",
                "type": "knowledge_gap",
                "description": "本次会话未添加任何知识条目",
                "priority": 5,
                "root_cause_candidates": [
                    "未进行知识提取",
                    "没有有价值的发现",
                    "知识管理系统问题",
                    "记录流程缺失",
                ],
            })

        return issues
```

### 2.3 根因分析

```python
def root_cause_analysis(issue, context):
    """根因分析"""

    analysis = {
        "issue": issue,
        "possible_causes": [],
        "evidence": [],
        "recommendations": [],
    }

    # 根据问题类型进行分析
    if issue["type"] == "slow_execution":
        analysis["possible_causes"] = [
            {
                "cause": "算法效率低下",
                "probability": 0.4,
                "evidence": "需要代码性能分析确认",
                "fix": "优化算法或使用更高效的实现",
            },
            {
                "cause": "数据I/O瓶颈",
                "probability": 0.3,
                "evidence": "检查磁盘IO和网络IO",
                "fix": "使用缓存、预加载或更快的存储",
            },
            {
                "cause": "资源竞争",
                "probability": 0.2,
                "evidence": "检查并发任务数",
                "fix": "调整并发策略或增加资源",
            },
            {
                "cause": "内存不足导致频繁GC",
                "probability": 0.1,
                "evidence": "检查GC日志",
                "fix": "增加内存或优化内存使用",
            },
        ]

    elif issue["type"] == "high_error_rate":
        analysis["possible_causes"] = [
            {
                "cause": "代码缺陷",
                "probability": 0.5,
                "evidence": "分析错误堆栈",
                "fix": "修复bug并添加测试",
            },
            {
                "cause": "数据质量问题",
                "probability": 0.3,
                "evidence": "检查数据验证结果",
                "fix": "改进数据清洗和验证",
            },
            {
                "cause": "配置错误",
                "probability": 0.15,
                "evidence": "检查配置文件",
                "fix": "修正配置并添加验证",
            },
            {
                "cause": "外部依赖问题",
                "probability": 0.05,
                "evidence": "检查API响应和日志",
                "fix": "添加重试和降级策略",
            },
        ]

    return analysis
```

---

## STEP 3: 提案格式

### 3.1 改进提案模板

```python
class ImprovementProposal:
    """改进提案"""

    def __init__(self):
        self.id = generate_proposal_id()
        self.created_at = datetime.now()
        self.status = "draft"

    def create(self, diagnosis, analysis):
        """创建改进提案"""

        proposal = {
            # 元数据
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "status": "pending_review",
            "priority": diagnosis["priority"],

            # 问题描述
            "problem": {
                "category": diagnosis["category"],
                "type": diagnosis["type"],
                "description": diagnosis["description"],
                "impact": self._assess_impact(diagnosis),
            },

            # 根因分析
            "root_cause": {
                "primary": analysis["possible_causes"][0] if analysis["possible_causes"] else None,
                "secondary": analysis["possible_causes"][1:3],
                "evidence": analysis["evidence"],
            },

            # 解决方案
            "solution": {
                "approach": self._determine_approach(diagnosis, analysis),
                "steps": self._create_steps(diagnosis, analysis),
                "estimated_effort": self._estimate_effort(diagnosis),
                "risks": self._assess_risks(diagnosis, analysis),
            },

            # 预期收益
            "expected_benefits": {
                "performance": self._estimate_performance_gain(diagnosis),
                "quality": self._estimate_quality_improvement(diagnosis),
                "knowledge": self._estimate_knowledge_gain(diagnosis),
            },

            # 验证计划
            "verification": {
                "metrics": self._define_success_metrics(diagnosis),
                "test_plan": self._create_test_plan(diagnosis),
                "rollback_plan": self._create_rollback_plan(diagnosis),
            },
        }

        return proposal

    def _assess_impact(self, diagnosis):
        """评估影响"""
        impact_map = {
            "performance": {
                "level": "high" if diagnosis["priority"] > 7 else "medium",
                "areas": ["执行效率", "资源消耗", "用户体验"],
            },
            "quality": {
                "level": "high" if diagnosis["priority"] > 7 else "medium",
                "areas": ["可靠性", "可维护性", "用户信任"],
            },
            "workflow": {
                "level": "medium",
                "areas": ["开发效率", "团队协作", "交付速度"],
            },
            "knowledge": {
                "level": "low",
                "areas": ["学习能力", "知识积累", "长期价值"],
            },
        }
        return impact_map.get(diagnosis["category"], {"level": "unknown", "areas": []})
```

### 3.2 提案文档格式

```markdown
# 改进提案: [提案标题]

## 元数据
- **提案ID**: PROP-[YYYYMMDD]-[序号]
- **创建时间**: [YYYY-MM-DD HH:MM:SS]
- **状态**: [待审核/已批准/进行中/已完成/已拒绝]
- **优先级**: [高/中/低]
- **负责人**: [待分配]

## 问题陈述

### 问题描述
[清晰描述当前存在的问题]

### 影响范围
- 影响的组件: [列表]
- 影响的用户: [描述]
- 影响的程度: [量化描述]

### 紧急程度
- [ ] 紧急 - 阻塞关键功能
- [ ] 高 - 严重影响效率
- [ ] 中 - 有改进空间
- [ ] 低 - 优化建议

## 根因分析

### 主要原因
1. [原因1]
   - 证据: [支持证据]
   - 概率: [高/中/低]

2. [原因2]
   - 证据: [支持证据]
   - 概率: [高/中/低]

### 分析方法
[描述用于确定根因的方法，如5Why、鱼骨图等]

## 解决方案

### 推荐方案
[详细描述推荐的解决方案]

### 实施步骤
1. [步骤1]
   - 预计时间: [时间]
   - 所需资源: [资源]
   - 风险点: [风险]

2. [步骤2]
   - 预计时间: [时间]
   - 所需资源: [资源]
   - 风险点: [风险]

### 替代方案
[如果有多个方案，列出替代方案及其优缺点]

## 预期收益

| 指标 | 当前值 | 目标值 | 改进幅度 |
|------|--------|--------|----------|
| [指标1] | [值] | [值] | [%] |
| [指标2] | [值] | [值] | [%] |

## 风险评估

### 实施风险
- [风险1]: [描述及缓解措施]
- [风险2]: [描述及缓解措施]

### 回退计划
[如果实施失败，如何回退]

## 验证计划

### 成功标准
- [ ] [标准1]: [具体指标]
- [ ] [标准2]: [具体指标]
- [ ] [标准3]: [具体指标]

### 测试计划
1. [测试项目1]
2. [测试项目2]

## 资源需求

### 人力
- [角色1]: [时间]
- [角色2]: [时间]

### 技术资源
- [资源1]: [规格]
- [资源2]: [规格]

## 时间线

```
[开始日期] --- [里程碑1] --- [里程碑2] --- [完成日期]
```

## 审批记录

| 日期 | 审批人 | 决定 | 备注 |
|------|--------|------|------|
| [日期] | [姓名] | [批准/拒绝] | [原因] |
```

### 3.3 提案生命周期

```python
class ProposalLifecycle:
    """提案生命周期管理"""

    STATES = {
        "draft": {
            "description": "草稿",
            "transitions": ["pending_review", "withdrawn"],
        },
        "pending_review": {
            "description": "待审核",
            "transitions": ["approved", "rejected", "needs_revision"],
        },
        "needs_revision": {
            "description": "需要修订",
            "transitions": ["pending_review", "withdrawn"],
        },
        "approved": {
            "description": "已批准",
            "transitions": ["in_progress", "on_hold"],
        },
        "in_progress": {
            "description": "进行中",
            "transitions": ["completed", "blocked", "cancelled"],
        },
        "blocked": {
            "description": "阻塞中",
            "transitions": ["in_progress", "cancelled"],
        },
        "on_hold": {
            "description": "暂停",
            "transitions": ["in_progress", "cancelled"],
        },
        "completed": {
            "description": "已完成",
            "transitions": [],  # 终态
        },
        "rejected": {
            "description": "已拒绝",
            "transitions": [],  # 终态
        },
        "withdrawn": {
            "description": "已撤回",
            "transitions": [],  # 终态
        },
        "cancelled": {
            "description": "已取消",
            "transitions": [],  # 终态
        },
    }

    def transition(self, proposal, new_state, reason=""):
        """状态转换"""
        current_state = proposal["status"]

        if new_state not in self.STATES[current_state]["transitions"]:
            raise ValueError(f"无法从 {current_state} 转换到 {new_state}")

        # 记录转换历史
        proposal.setdefault("history", []).append({
            "from_state": current_state,
            "to_state": new_state,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })

        proposal["status"] = new_state
        return proposal
```

---

## STEP 4: 实施与验证

### 4.1 实施流程

```python
class ImplementationManager:
    """实施管理器"""

    def __init__(self, proposal):
        self.proposal = proposal
        self.checkpoints = []
        self.current_step = 0

    def execute(self):
        """执行改进方案"""

        steps = self.proposal["solution"]["steps"]

        for i, step in enumerate(steps):
            self.current_step = i

            # 创建检查点
            self._create_checkpoint(f"before_step_{i}")

            try:
                # 执行步骤
                result = self._execute_step(step)

                # 验证步骤结果
                if not self._verify_step(step, result):
                    raise Exception(f"步骤 {i+1} 验证失败")

                # 记录成功检查点
                self._create_checkpoint(f"after_step_{i}")

            except Exception as e:
                # 记录失败
                self._log_failure(i, str(e))

                # 决定是回滚还是重试
                if step.get("critical", True):
                    self._rollback_to_last_checkpoint()
                    raise

                # 非关键步骤，继续
                continue

        return {"status": "success", "steps_completed": len(steps)}

    def _execute_step(self, step):
        """执行单个步骤"""
        print(f"执行步骤: {step['description']}")

        # 根据步骤类型执行
        action_type = step.get("type")

        if action_type == "code_change":
            return self._execute_code_change(step)
        elif action_type == "config_change":
            return self._execute_config_change(step)
        elif action_type == "process_change":
            return self._execute_process_change(step)
        else:
            raise ValueError(f"未知的步骤类型: {action_type}")

    def _create_checkpoint(self, name):
        """创建检查点"""
        checkpoint = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "step": self.current_step,
            "state": self._capture_current_state(),
        }
        self.checkpoints.append(checkpoint)
        return checkpoint

    def _rollback_to_last_checkpoint(self):
        """回滚到最后一个检查点"""
        if not self.checkpoints:
            print("没有可用的检查点")
            return

        last_checkpoint = self.checkpoints[-1]
        print(f"回滚到检查点: {last_checkpoint['name']}")
        self._restore_state(last_checkpoint["state"])
```

### 4.2 验证框架

```python
class VerificationFramework:
    """验证框架"""

    def __init__(self, proposal):
        self.proposal = proposal
        self.metrics = proposal["verification"]["metrics"]
        self.baseline = self._capture_baseline()

    def verify(self):
        """验证改进效果"""

        results = {
            "overall": "pending",
            "metrics": {},
            "tests": {},
            "recommendation": None,
        }

        # 1. 验证指标
        for metric in self.metrics:
            current_value = self._measure_metric(metric["name"])
            baseline_value = self.baseline.get(metric["name"], 0)
            target_value = metric["target"]

            improvement = self._calculate_improvement(
                baseline_value, current_value, metric.get("direction", "increase")
            )

            results["metrics"][metric["name"]] = {
                "baseline": baseline_value,
                "current": current_value,
                "target": target_value,
                "improvement": improvement,
                "met_target": self._check_target(current_value, target_value, metric),
            }

        # 2. 运行测试
        test_results = self._run_tests(self.proposal["verification"]["test_plan"])
        results["tests"] = test_results

        # 3. 综合评估
        all_metrics_met = all(m["met_target"] for m in results["metrics"].values())
        all_tests_passed = all(t["passed"] for t in test_results.values())

        if all_metrics_met and all_tests_passed:
            results["overall"] = "success"
            results["recommendation"] = "改进成功，可以部署"
        elif all_tests_passed:
            results["overall"] = "partial"
            results["recommendation"] = "部分达标，需要进一步优化"
        else:
            results["overall"] = "failed"
            results["recommendation"] = "验证失败，建议回滚"

        return results

    def _capture_baseline(self):
        """捕获基线指标"""
        baseline = {}
        for metric in self.metrics:
            baseline[metric["name"]] = self._measure_metric(metric["name"])
        return baseline

    def _measure_metric(self, metric_name):
        """测量指标"""
        # 根据指标名称获取当前值
        if metric_name == "execution_time":
            return self._measure_execution_time()
        elif metric_name == "error_rate":
            return self._measure_error_rate()
        elif metric_name == "success_rate":
            return self._measure_success_rate()
        elif metric_name == "resource_usage":
            return self._measure_resource_usage()
        else:
            raise ValueError(f"未知指标: {metric_name}")
```

### 4.3 回滚策略

```python
class RollbackStrategy:
    """回滚策略"""

    def __init__(self, proposal, checkpoints):
        self.proposal = proposal
        self.checkpoints = checkpoints

    def should_rollback(self, verification_results):
        """判断是否需要回滚"""
        reasons = []

        # 检查关键指标
        for metric_name, result in verification_results["metrics"].items():
            if result.get("critical", False) and not result["met_target"]:
                reasons.append(f"关键指标 {metric_name} 未达标")

        # 检查测试结果
        for test_name, result in verification_results["tests"].items():
            if not result["passed"]:
                reasons.append(f"测试 {test_name} 失败")

        return len(reasons) > 0, reasons

    def execute_rollback(self, target_checkpoint=None):
        """执行回滚"""
        if target_checkpoint:
            checkpoint = self._find_checkpoint(target_checkpoint)
        else:
            checkpoint = self.checkpoints[-1]

        print(f"回滚到检查点: {checkpoint['name']}")

        # 执行回滚
        rollback_plan = self.proposal["verification"]["rollback_plan"]

        for step in rollback_plan.get("steps", []):
            self._execute_rollback_step(step)

        # 验证回滚成功
        if self._verify_rollback():
            print("回滚成功")
            return {"status": "success"}
        else:
            print("回滚验证失败")
            return {"status": "failed"}

    def _execute_rollback_step(self, step):
        """执行回滚步骤"""
        if step["type"] == "git_revert":
            self._git_revert(step["commit"])
        elif step["type"] == "restore_file":
            self._restore_file(step["path"], step["backup"])
        elif step["type"] == "restore_config":
            self._restore_config(step["config_key"], step["old_value"])
```

---

## STEP 5: 知识管理

### 5.1 知识提取

```python
class KnowledgeExtractor:
    """知识提取器"""

    def extract_from_session(self, session_data):
        """从会话数据中提取知识"""

        knowledge_items = []

        # 1. 从错误中提取知识
        error_knowledge = self._extract_from_errors(session_data.get("errors", []))
        knowledge_items.extend(error_knowledge)

        # 2. 从成功经验中提取知识
        success_knowledge = self._extract_from_successes(session_data.get("successes", []))
        knowledge_items.extend(success_knowledge)

        # 3. 从决策中提取知识
        decision_knowledge = self._extract_from_decisions(session_data.get("decisions", []))
        knowledge_items.extend(decision_knowledge)

        # 4. 从观察中提取知识
        observation_knowledge = self._extract_from_observations(session_data.get("observations", []))
        knowledge_items.extend(observation_knowledge)

        return knowledge_items

    def _extract_from_errors(self, errors):
        """从错误中提取知识"""
        knowledge_items = []

        for error in errors:
            if error.get("resolved"):
                knowledge = {
                    "type": "error_solution",
                    "error_type": error["type"],
                    "error_message": error["message"],
                    "root_cause": error["root_cause"],
                    "solution": error["solution"],
                    "prevention": error.get("prevention", ""),
                    "context": error.get("context", {}),
                    "created_at": datetime.now().isoformat(),
                }
                knowledge_items.append(knowledge)

        return knowledge_items

    def _extract_from_successes(self, successes):
        """从成功经验中提取知识"""
        knowledge_items = []

        for success in successes:
            knowledge = {
                "type": "best_practice",
                "scenario": success["scenario"],
                "approach": success["approach"],
                "outcome": success["outcome"],
                "key_factors": success.get("key_factors", []),
                "metrics": success.get("metrics", {}),
                "created_at": datetime.now().isoformat(),
            }
            knowledge_items.append(knowledge)

        return knowledge_items

    def _extract_from_decisions(self, decisions):
        """从决策中提取知识"""
        knowledge_items = []

        for decision in decisions:
            knowledge = {
                "type": "decision_pattern",
                "situation": decision["situation"],
                "options_considered": decision["options"],
                "decision_made": decision["chosen"],
                "rationale": decision["rationale"],
                "outcome": decision.get("outcome", "unknown"),
                "created_at": datetime.now().isoformat(),
            }
            knowledge_items.append(knowledge)

        return knowledge_items
```

### 5.2 知识存储

```python
class KnowledgeStore:
    """知识存储"""

    def __init__(self, db_path="knowledge.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TEXT,
                last_used TEXT,
                use_count INTEGER DEFAULT 0,
                effectiveness REAL DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_type ON knowledge(type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags ON knowledge(tags)
        """)

        conn.commit()
        conn.close()

    def add_knowledge(self, knowledge):
        """添加知识"""
        import sqlite3
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO knowledge (type, content, tags, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            knowledge["type"],
            json.dumps(knowledge),
            json.dumps(knowledge.get("tags", [])),
            knowledge.get("created_at", datetime.now().isoformat()),
        ))

        conn.commit()
        conn.close()

    def search_knowledge(self, query, limit=10):
        """搜索知识"""
        import sqlite3
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 简单的关键词搜索
        cursor.execute("""
            SELECT id, type, content, use_count, effectiveness
            FROM knowledge
            WHERE content LIKE ?
            ORDER BY effectiveness DESC, use_count DESC
            LIMIT ?
        """, (f"%{query}%", limit))

        results = []
        for row in cursor.fetchall():
            knowledge = json.loads(row[2])
            knowledge["id"] = row[0]
            knowledge["use_count"] = row[3]
            knowledge["effectiveness"] = row[4]
            results.append(knowledge)

        conn.close()
        return results

    def update_effectiveness(self, knowledge_id, delta):
        """更新知识有效性评分"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE knowledge
            SET effectiveness = effectiveness + ?,
                use_count = use_count + 1,
                last_used = ?
            WHERE id = ?
        """, (delta, datetime.now().isoformat(), knowledge_id))

        conn.commit()
        conn.close()
```

### 5.3 知识应用

```python
class KnowledgeApplicator:
    """知识应用器"""

    def __init__(self, knowledge_store):
        self.store = knowledge_store

    def find_applicable_knowledge(self, context):
        """查找适用的知识"""

        applicable = []

        # 1. 根据当前阶段查找
        phase_knowledge = self.store.search_knowledge(context["phase"])
        applicable.extend(phase_knowledge)

        # 2. 根据问题类型查找
        if "problem_type" in context:
            problem_knowledge = self.store.search_knowledge(context["problem_type"])
            applicable.extend(problem_knowledge)

        # 3. 根据标签查找
        for tag in context.get("tags", []):
            tag_knowledge = self.store.search_knowledge(tag)
            applicable.extend(tag_knowledge)

        # 去重并按有效性排序
        seen_ids = set()
        unique_applicable = []
        for k in applicable:
            if k["id"] not in seen_ids:
                seen_ids.add(k["id"])
                unique_applicable.append(k)

        unique_applicable.sort(key=lambda x: x["effectiveness"], reverse=True)

        return unique_applicable[:5]  # 返回前5个最相关的

    def apply_knowledge(self, knowledge, context):
        """应用知识"""

        if knowledge["type"] == "error_solution":
            return self._apply_error_solution(knowledge, context)
        elif knowledge["type"] == "best_practice":
            return self._apply_best_practice(knowledge, context)
        elif knowledge["type"] == "decision_pattern":
            return self._apply_decision_pattern(knowledge, context)

    def _apply_error_solution(self, knowledge, context):
        """应用错误解决方案"""
        recommendation = {
            "type": "error_fix",
            "knowledge_id": knowledge["id"],
            "suggested_solution": knowledge["solution"],
            "prevention_tips": knowledge.get("prevention", ""),
            "confidence": knowledge["effectiveness"],
        }
        return recommendation

    def _apply_best_practice(self, knowledge, context):
        """应用最佳实践"""
        recommendation = {
            "type": "best_practice",
            "knowledge_id": knowledge["id"],
            "suggested_approach": knowledge["approach"],
            "key_factors": knowledge.get("key_factors", []),
            "expected_outcome": knowledge["outcome"],
            "confidence": knowledge["effectiveness"],
        }
        return recommendation
```

---

## STEP 6: 进化指标

### 6.1 进化健康度评估

```python
class EvolutionHealthAssessment:
    """进化健康度评估"""

    def assess(self, time_window_days=30):
        """评估进化健康度"""

        assessment = {
            "overall_score": 0,
            "dimensions": {},
            "trends": {},
            "recommendations": [],
        }

        # 1. 学习能力维度
        assessment["dimensions"]["learning"] = self._assess_learning_ability(time_window_days)

        # 2. 适应能力维度
        assessment["dimensions"]["adaptation"] = self._assess_adaptation_ability(time_window_days)

        # 3. 创新能力维度
        assessment["dimensions"]["innovation"] = self._assess_innovation_ability(time_window_days)

        # 4. 稳定性维度
        assessment["dimensions"]["stability"] = self._assess_stability(time_window_days)

        # 5. 效率维度
        assessment["dimensions"]["efficiency"] = self._assess_efficiency(time_window_days)

        # 计算总分
        assessment["overall_score"] = sum(assessment["dimensions"].values()) / len(assessment["dimensions"])

        # 生成趋势
        assessment["trends"] = self._calculate_trends(time_window_days)

        # 生成建议
        assessment["recommendations"] = self._generate_recommendations(assessment)

        return assessment

    def _assess_learning_ability(self, days):
        """评估学习能力"""
        # 知识增长速度
        knowledge_growth = self._get_knowledge_growth_rate(days)

        # 知识应用成功率
        application_success_rate = self._get_knowledge_application_success_rate(days)

        # 新技能获取
        new_skills = self._get_new_skills_count(days)

        # 综合评分
        score = (
            knowledge_growth * 0.4 +
            application_success_rate * 0.4 +
            min(new_skills / 5, 1.0) * 0.2
        )

        return score

    def _assess_adaptation_ability(self, days):
        """评估适应能力"""
        # 对新问题的解决速度
        problem_solving_speed = self._get_problem_solving_speed(days)

        # 对环境变化的响应
        environment_response = self._get_environment_response_rate(days)

        # 综合评分
        score = (problem_solving_speed * 0.6 + environment_response * 0.4)

        return score

    def _assess_innovation_ability(self, days):
        """评估创新能力"""
        # 新方法尝试次数
        new_methods = self._get_new_methods_count(days)

        # 创新成功率
        innovation_success_rate = self._get_innovation_success_rate(days)

        # 综合评分
        score = (
            min(new_methods / 10, 1.0) * 0.3 +
            innovation_success_rate * 0.7
        )

        return score

    def _assess_stability(self, days):
        """评估稳定性"""
        # 错误率趋势
        error_trend = self._get_error_rate_trend(days)

        # 回滚次数
        rollback_count = self._get_rollback_count(days)

        # 综合评分
        if error_trend < 0:  # 错误率下降
            error_score = 1.0
        elif error_trend == 0:
            error_score = 0.8
        else:
            error_score = max(0, 1.0 - error_trend)

        rollback_score = max(0, 1.0 - rollback_count * 0.1)

        return (error_score * 0.7 + rollback_score * 0.3)

    def _assess_efficiency(self, days):
        """评估效率"""
        # 任务完成时间趋势
        time_trend = self._get_task_time_trend(days)

        # 资源利用率
        resource_utilization = self._get_resource_utilization(days)

        # 综合评分
        if time_trend < 0:  # 时间减少
            time_score = 1.0
        elif time_trend == 0:
            time_score = 0.8
        else:
            time_score = max(0, 1.0 - time_trend * 0.5)

        return (time_score * 0.6 + resource_utilization * 0.4)
```

### 6.2 进化报告模板

```markdown
# 自我进化报告

## 报告周期
- **开始时间**: [YYYY-MM-DD]
- **结束时间**: [YYYY-MM-DD]
- **报告日期**: [YYYY-MM-DD]

## 执行摘要

### 健康度评分
- **总分**: [0-100]
- **评级**: [优秀/良好/一般/需改进]

### 各维度评分
| 维度 | 评分 | 趋势 | 状态 |
|------|------|------|------|
| 学习能力 | [分数] | [↑/↓/→] | [图标] |
| 适应能力 | [分数] | [↑/↓/→] | [图标] |
| 创新能力 | [分数] | [↑/↓/→] | [图标] |
| 稳定性 | [分数] | [↑/↓/→] | [图标] |
| 效率 | [分数] | [↑/↓/→] | [图标] |

## 本周期亮点

### 成功的改进
1. **[改进名称]**
   - 影响: [描述]
   - 收益: [量化数据]

2. **[改进名称]**
   - 影响: [描述]
   - 收益: [量化数据]

### 新增知识
- 错误解决方案: [N] 条
- 最佳实践: [N] 条
- 决策模式: [N] 条

## 遇到的挑战

### 未解决的问题
1. **[问题描述]**
   - 影响: [高/中/低]
   - 状态: [调查中/待解决/需要帮助]

### 失败的改进尝试
1. **[改进名称]**
   - 失败原因: [描述]
   - 教训: [学到了什么]

## 下一步计划

### 待实施提案
1. **[提案名称]** (优先级: [高/中/低])
   - 预期收益: [描述]
   - 计划开始: [日期]

### 待调查问题
1. **[问题描述]**
   - 初步分析: [描述]
   - 需要的资源: [描述]

## 统计数据

### 执行统计
- 提案总数: [N]
- 已完成: [N]
- 进行中: [N]
- 已拒绝: [N]

### 知识统计
- 知识条目总数: [N]
- 本期新增: [N]
- 本期应用: [N]
- 平均有效性: [分数]

### 性能统计
- 平均任务执行时间: [时间]
- 错误率: [%]
- 成功率: [%]
```

---

## 质量检查清单

在执行自我进化时，确保：

### 观察阶段
- [ ] 收集了足够的观察数据
- [ ] 识别了有意义的模式
- [ ] 避免了观察偏差
- [ ] 记录了完整的上下文

### 诊断阶段
- [ ] 正确分类了问题
- [ ] 进行了深入的根因分析
- [ ] 考虑了多种可能性
- [ ] 有证据支持诊断结论

### 提案阶段
- [ ] 提案格式规范完整
- [ ] 预期收益量化
- [ ] 风险评估充分
- [ ] 验证计划明确

### 实施阶段
- [ ] 创建了检查点
- [ ] 验证了每个步骤
- [ ] 准备了回滚方案
- [ ] 记录了实施过程

### 知识阶段
- [ ] 提取了有价值的知识
- [ ] 知识存储正确
- [ ] 知识可检索
- [ ] 知识有效性可追踪

---

## 常见问题

**Q: 如何避免过度进化？**
A: 设定进化节奏限制，每次只实施少量高优先级改进，确保稳定性优先。

**Q: 如何判断改进是否成功？**
A: 定义明确成功指标，在实施前后进行对比，确保改进有统计学意义。

**Q: 知识库如何保持更新？**
A: 定期审查知识有效性，删除过时知识，更新最佳实践，保持知识的时效性。

**Q: 如何平衡创新和稳定？**
A: 使用渐进式改进策略，小步快跑，每次改进后验证稳定性，再进行下一次。

**Q: 如何处理相互冲突的改进提案？**
A: 评估每个提案的优先级和影响，选择综合收益最高的，或者尝试融合方案。

---

*本文档为 Project Prometheus 提供全面的自我进化和知识更新指南*
