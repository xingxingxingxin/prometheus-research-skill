"""
Statistical Analysis Skill - 统计分析技能

执行统计显著性检验，纯代码实现
"""

from typing import Dict, Any, List
from pathlib import Path

from Core.skills.base import DeterministicSkill, SkillContext, SkillResult


class StatisticalAnalysisSkill(DeterministicSkill):
    """
    统计分析技能

    执行各种统计检验：
    - t检验
    - Wilcoxon检验
    - ANOVA
    - 效应量计算
    """

    name = "statistical_analysis"
    description = "Perform statistical significance tests on experimental results"
    inputs = ["baseline_scores", "method_scores"]
    outputs = ["test_results", "summary", "is_significant"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        执行统计分析

        Args:
            context: 执行上下文

        Returns:
            SkillResult: 分析结果
        """
        import time
        start_time = time.time()

        # 获取数据
        baseline = context.inputs.get("baseline_scores", [])
        method = context.inputs.get("method_scores", [])

        if not baseline or not method:
            # 尝试从文件加载
            baseline, method = self._load_results(context)

        if not baseline or not method:
            return SkillResult(
                success=False,
                error="No data provided for statistical analysis",
            )

        # 执行统计检验
        results = {}

        # 1. t检验
        results["t_test"] = self._t_test(baseline, method)

        # 2. Wilcoxon检验（配对）
        if len(baseline) == len(method):
            results["wilcoxon"] = self._wilcoxon_test(baseline, method)

        # 3. 效应量
        results["effect_size"] = self._cohens_d(baseline, method)

        # 4. 置信区间
        results["confidence_interval"] = self._confidence_interval(method)

        # 5. 描述性统计
        results["descriptive"] = {
            "baseline": self._descriptive_stats(baseline),
            "method": self._descriptive_stats(method),
        }

        # 生成摘要
        summary = self._generate_summary(results)

        # 判断显著性
        is_significant = (
            results["t_test"].get("significant_at_0.05", False) and
            abs(results["effect_size"].get("cohens_d", 0)) >= 0.5
        )

        # 保存结果
        output_file = self._save_results(context, results)

        execution_time = time.time() - start_time

        return SkillResult(
            success=True,
            outputs={
                "test_results": results,
                "summary": summary,
                "is_significant": is_significant,
                "output_file": str(output_file),
            },
            artifacts=[str(output_file)],
            execution_time=execution_time,
        )

    def _load_results(self, context: SkillContext) -> tuple:
        """从文件加载结果"""
        import json

        project_dir = context.working_dir or Path.cwd()
        results_file = project_dir / "results" / "experiment_results.json"

        if not results_file.exists():
            return [], []

        try:
            with open(results_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            baseline = data.get("baseline", [])
            method = data.get("method", [])
            return baseline, method
        except Exception:
            return [], []

    def _t_test(self, group1: List[float], group2: List[float]) -> Dict:
        """独立样本t检验"""
        import math

        n1, n2 = len(group1), len(group2)
        if n1 < 2 or n2 < 2:
            return {"error": "Insufficient samples"}

        mean1 = sum(group1) / n1
        mean2 = sum(group2) / n2

        var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1)
        var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1)

        se = math.sqrt(var1 / n1 + var2 / n2)
        if se == 0:
            return {"error": "Zero standard error"}

        t_stat = (mean2 - mean1) / se

        # 近似p值
        df = n1 + n2 - 2
        p_value = self._approx_t_pvalue(abs(t_stat), df)

        return {
            "t_statistic": round(t_stat, 4),
            "p_value": round(p_value, 6),
            "significant_at_0.05": p_value < 0.05,
            "significant_at_0.01": p_value < 0.01,
            "mean_difference": round(mean2 - mean1, 4),
        }

    def _wilcoxon_test(self, group1: List[float], group2: List[float]) -> Dict:
        """Wilcoxon符号秩检验"""
        if len(group1) != len(group2):
            return {"error": "Groups must have equal size"}

        differences = [g2 - g1 for g1, g2 in zip(group1, group2)]
        non_zero = [(abs(d), i) for i, d in enumerate(differences) if d != 0]

        if len(non_zero) < 10:
            return {"error": "Too few non-zero differences"}

        # 计算秩
        non_zero.sort(key=lambda x: x[0])
        ranks = {i: rank for rank, (_, i) in enumerate(non_zero, 1)}

        w_plus = sum(ranks[i] for i, d in enumerate(differences) if d > 0 and i in ranks)
        w_minus = sum(ranks[i] for i, d in enumerate(differences) if d < 0 and i in ranks)

        w_stat = min(w_plus, w_minus)

        # 正态近似p值
        n = len(non_zero)
        mean_w = n * (n + 1) / 4
        std_w = math.sqrt(n * (n + 1) * (2 * n + 1) / 24) if n > 0 else 0

        if std_w > 0:
            z = (w_stat - mean_w) / std_w
            p_value = 2 * (1 - self._normal_cdf(abs(z)))
        else:
            p_value = 1.0

        return {
            "w_statistic": w_stat,
            "p_value": round(p_value, 6),
            "significant_at_0.05": p_value < 0.05,
        }

    def _cohens_d(self, group1: List[float], group2: List[float]) -> Dict:
        """Cohen's d效应量"""
        import math

        n1, n2 = len(group1), len(group2)
        if n1 < 2 or n2 < 2:
            return {"error": "Insufficient samples"}

        mean1 = sum(group1) / n1
        mean2 = sum(group2) / n2

        var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1)
        var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1)

        pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return {"error": "Zero pooled standard deviation"}

        d = (mean2 - mean1) / pooled_std
        abs_d = abs(d)

        if abs_d < 0.2:
            interpretation = "negligible"
        elif abs_d < 0.5:
            interpretation = "small"
        elif abs_d < 0.8:
            interpretation = "medium"
        else:
            interpretation = "large"

        return {
            "cohens_d": round(d, 4),
            "interpretation": interpretation,
        }

    def _confidence_interval(self, data: List[float], confidence: float = 0.95) -> Dict:
        """置信区间"""
        import math

        n = len(data)
        if n < 2:
            return {"error": "Insufficient samples"}

        mean = sum(data) / n
        std = math.sqrt(sum((x - mean) ** 2 for x in data) / (n - 1))
        se = std / math.sqrt(n)

        # t临界值近似
        t_crit = 2.0 if n >= 30 else 2.5 if n >= 10 else 3.0
        margin = t_crit * se

        return {
            "mean": round(mean, 4),
            "ci_lower": round(mean - margin, 4),
            "ci_upper": round(mean + margin, 4),
            "confidence_level": confidence,
        }

    def _descriptive_stats(self, data: List[float]) -> Dict:
        """描述性统计"""
        import math

        n = len(data)
        if n == 0:
            return {}

        mean = sum(data) / n
        std = math.sqrt(sum((x - mean) ** 2 for x in data) / max(n - 1, 1))

        sorted_data = sorted(data)
        median = sorted_data[n // 2] if n % 2 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2

        return {
            "n": n,
            "mean": round(mean, 4),
            "std": round(std, 4),
            "median": round(median, 4),
            "min": round(min(data), 4),
            "max": round(max(data), 4),
        }

    def _approx_t_pvalue(self, t: float, df: int) -> float:
        """近似t分布p值"""
        # 简化近似
        if df >= 30:
            return 2 * (1 - self._normal_cdf(t))

        # 查表近似
        critical_values = {
            1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57,
            10: 2.23, 20: 2.09, 30: 2.04,
        }

        closest_df = min(critical_values.keys(), key=lambda x: abs(x - df))
        crit = critical_values[closest_df]

        if t > crit:
            return 0.01
        elif t > crit * 0.8:
            return 0.05
        else:
            return 0.2

    def _normal_cdf(self, x: float) -> float:
        """标准正态分布CDF"""
        import math
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _generate_summary(self, results: Dict) -> str:
        """生成结果摘要"""
        lines = ["Statistical Analysis Summary", "=" * 30]

        if "t_test" in results and "error" not in results["t_test"]:
            t = results["t_test"]
            sig = "***" if t["p_value"] < 0.001 else "**" if t["p_value"] < 0.01 else "*" if t["p_value"] < 0.05 else ""
            lines.append(f"t-test: t={t['t_statistic']}, p={t['p_value']:.4f} {sig}")

        if "effect_size" in results and "error" not in results["effect_size"]:
            e = results["effect_size"]
            lines.append(f"Effect size: d={e['cohens_d']} ({e['interpretation']})")

        if "descriptive" in results:
            lines.append("\nDescriptive Statistics:")
            for name, stats in results["descriptive"].items():
                if stats:
                    lines.append(f"  {name}: mean={stats.get('mean')}, std={stats.get('std')}")

        return "\n".join(lines)

    def _save_results(self, context: SkillContext, results: Dict) -> Path:
        """保存分析结果"""
        import json

        project_dir = context.working_dir or Path.cwd()
        output_dir = project_dir / "results"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "statistical_analysis.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        return output_file


# 导出
__all__ = ["StatisticalAnalysisSkill"]
