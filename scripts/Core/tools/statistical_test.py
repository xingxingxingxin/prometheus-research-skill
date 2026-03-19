"""
统计显著性检验工具
==================

执行各种统计显著性检验，支持 t-test, Wilcoxon, ANOVA, Mann-Whitney 等。
输入实验结果数据（CSV/JSON），输出 p-value、effect size 和可视化图表。
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class TestResult:
    """统计检验结果"""
    test_name: str
    statistic: float
    p_value: float
    effect_size: float
    effect_size_type: str
    interpretation: str
    significant: bool
    alpha: float
    details: Dict[str, Any]


class StatisticalTest:
    """统计显著性检验工具"""

    def __init__(self, alpha: float = 0.05):
        """
        初始化

        Args:
            alpha: 显著性水平，默认 0.05
        """
        self.alpha = alpha

    def load_data(self, file_path: str,
                  group_column: str = None,
                  value_column: str = None) -> pd.DataFrame:
        """
        从 CSV 或 JSON 文件加载数据

        Args:
            file_path: 数据文件路径
            group_column: 分组列名（用于多组比较）
            value_column: 数值列名

        Returns:
            DataFrame
        """
        path = Path(file_path)

        if path.suffix == '.csv':
            df = pd.read_csv(path)
        elif path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                raise ValueError("不支持的 JSON 格式")
        else:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

        return df

    def _interpret_effect_size(self, effect_size: float,
                                effect_type: str = 'cohen_d') -> str:
        """
        解释效应量大小

        Args:
            effect_size: 效应量值
            effect_type: 效应量类型

        Returns:
            解释文本
        """
        abs_es = abs(effect_size)

        if effect_type in ['cohen_d', 'd', 'glass_delta']:
            if abs_es < 0.2:
                return "极小效应 (negligible)"
            elif abs_es < 0.5:
                return "小效应 (small)"
            elif abs_es < 0.8:
                return "中等效应 (medium)"
            else:
                return "大效应 (large)"
        elif effect_type in ['r', 'eta_squared', 'partial_eta_squared']:
            if abs_es < 0.1:
                return "极小效应 (negligible)"
            elif abs_es < 0.3:
                return "小效应 (small)"
            elif abs_es < 0.5:
                return "中等效应 (medium)"
            else:
                return "大效应 (large)"
        else:
            return f"效应量: {effect_size:.4f}"

    def _calculate_cohens_d(self, group1: np.ndarray,
                            group2: np.ndarray) -> float:
        """
        计算 Cohen's d 效应量

        Args:
            group1: 第一组数据
            group2: 第二组数据

        Returns:
            Cohen's d 值
        """
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)

        # 合并标准差
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0.0

        return (np.mean(group1) - np.mean(group2)) / pooled_std

    def _calculate_eta_squared(self, groups: List[np.ndarray]) -> float:
        """
        计算 Eta-squared 效应量（用于 ANOVA）

        Args:
            groups: 各组数据

        Returns:
            Eta-squared 值
        """
        all_data = np.concatenate(groups)
        grand_mean = np.mean(all_data)

        # 总平方和
        ss_total = np.sum((all_data - grand_mean) ** 2)

        # 组间平方和
        ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)

        if ss_total == 0:
            return 0.0

        return ss_between / ss_total

    def _calculate_rank_biserial(self, group1: np.ndarray,
                                  group2: np.ndarray) -> float:
        """
        计算秩二列相关系数（用于非参数检验）

        Args:
            group1: 第一组数据
            group2: 第二组数据

        Returns:
            秩二列相关系数
        """
        # 使用 Wilcoxon 的 W 统计量计算效应量
        n1, n2 = len(group1), len(group2)
        all_data = np.concatenate([group1, group2])
        ranks = stats.rankdata(all_data)

        r1 = np.sum(ranks[:n1])
        r2 = np.sum(ranks[n1:])

        # 计算 r 效应量
        u1 = r1 - n1 * (n1 + 1) / 2
        u2 = r2 - n2 * (n2 + 1) / 2

        # 秩二列相关
        r = 1 - (2 * u1) / (n1 * n2)

        return r

    def t_test_independent(self, group1: Union[np.ndarray, List],
                           group2: Union[np.ndarray, List],
                           equal_var: bool = True) -> TestResult:
        """
        独立样本 t 检验

        Args:
            group1: 第一组数据
            group2: 第二组数据
            equal_var: 是否假设方差相等（True: Student's t-test, False: Welch's t-test）

        Returns:
            TestResult
        """
        g1 = np.array(group1)
        g2 = np.array(group2)

        # 执行 t 检验
        if equal_var:
            statistic, p_value = stats.ttest_ind(g1, g2)
            test_name = "Independent Samples t-test (Student's)"
        else:
            statistic, p_value = stats.ttest_ind(g1, g2, equal_var=False)
            test_name = "Independent Samples t-test (Welch's)"

        # 计算 Cohen's d
        effect_size = self._calculate_cohens_d(g1, g2)

        # 判断显著性
        significant = p_value < self.alpha

        # 构建解释
        interpretation = f"{'拒绝' if significant else '无法拒绝'}原假设 (p = {p_value:.4f} {'<' if significant else '>'} {self.alpha})。"
        interpretation += f" 效应量: {self._interpret_effect_size(effect_size, 'cohen_d')}。"

        return TestResult(
            test_name=test_name,
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=effect_size,
            effect_size_type="Cohen's d",
            interpretation=interpretation,
            significant=significant,
            alpha=self.alpha,
            details={
                'n1': len(g1),
                'n2': len(g2),
                'mean1': float(np.mean(g1)),
                'mean2': float(np.mean(g2)),
                'std1': float(np.std(g1, ddof=1)),
                'std2': float(np.std(g2, ddof=1)),
                'equal_variance': equal_var
            }
        )

    def t_test_paired(self, before: Union[np.ndarray, List],
                      after: Union[np.ndarray, List]) -> TestResult:
        """
        配对样本 t 检验

        Args:
            before: 前测数据
            after: 后测数据

        Returns:
            TestResult
        """
        b = np.array(before)
        a = np.array(after)

        # 执行配对 t 检验
        statistic, p_value = stats.ttest_rel(b, a)

        # 计算效应量（使用差值的标准差）
        diff = a - b
        mean_diff = np.mean(diff)
        std_diff = np.std(diff, ddof=1)

        if std_diff > 0:
            effect_size = mean_diff / std_diff
        else:
            effect_size = 0.0

        significant = p_value < self.alpha

        interpretation = f"{'拒绝' if significant else '无法拒绝'}原假设 (p = {p_value:.4f} {'<' if significant else '>'} {self.alpha})。"
        interpretation += f" 平均差异: {mean_diff:.4f}。效应量: {self._interpret_effect_size(effect_size, 'cohen_d')}。"

        return TestResult(
            test_name="Paired Samples t-test",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=effect_size,
            effect_size_type="Cohen's d (paired)",
            interpretation=interpretation,
            significant=significant,
            alpha=self.alpha,
            details={
                'n': len(b),
                'mean_before': float(np.mean(b)),
                'mean_after': float(np.mean(a)),
                'mean_difference': float(mean_diff),
                'std_difference': float(std_diff)
            }
        )

    def t_test_one_sample(self, sample: Union[np.ndarray, List],
                          pop_mean: float) -> TestResult:
        """
        单样本 t 检验

        Args:
            sample: 样本数据
            pop_mean: 总体均值

        Returns:
            TestResult
        """
        s = np.array(sample)

        statistic, p_value = stats.ttest_1samp(s, pop_mean)

        # 计算效应量
        sample_mean = np.mean(s)
        sample_std = np.std(s, ddof=1)

        if sample_std > 0:
            effect_size = (sample_mean - pop_mean) / sample_std
        else:
            effect_size = 0.0

        significant = p_value < self.alpha

        interpretation = f"{'拒绝' if significant else '无法拒绝'}原假设 (p = {p_value:.4f} {'<' if significant else '>'} {self.alpha})。"
        interpretation += f" 样本均值 ({sample_mean:.4f}) 与总体均值 ({pop_mean}) {'有' if significant else '无'}显著差异。"

        return TestResult(
            test_name="One-Sample t-test",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=effect_size,
            effect_size_type="Cohen's d",
            interpretation=interpretation,
            significant=significant,
            alpha=self.alpha,
            details={
                'n': len(s),
                'sample_mean': float(sample_mean),
                'sample_std': float(sample_std),
                'population_mean': pop_mean
            }
        )

    def wilcoxon_test(self, x: Union[np.ndarray, List],
                      y: Union[np.ndarray, List] = None,
                      alternative: str = 'two-sided') -> TestResult:
        """
        Wilcoxon 符号秩检验（配对样本非参数检验）

        Args:
            x: 第一组数据（或差值）
            y: 第二组数据（可选，如果提供则计算 x-y）
            alternative: 备择假设类型 ('two-sided', 'less', 'greater')

        Returns:
            TestResult
        """
        x = np.array(x)
        if y is not None:
            y = np.array(y)
            diff = x - y
        else:
            diff = x

        # 移除零差值
        diff = diff[diff != 0]

        if len(diff) < 2:
            return TestResult(
                test_name="Wilcoxon Signed-Rank Test",
                statistic=0,
                p_value=1.0,
                effect_size=0.0,
                effect_size_type="r",
                interpretation="数据不足，无法进行检验",
                significant=False,
                alpha=self.alpha,
                details={'error': 'Insufficient non-zero differences'}
            )

        # 执行 Wilcoxon 检验
        try:
            statistic, p_value = stats.wilcoxon(diff, alternative=alternative)
        except ValueError as e:
            return TestResult(
                test_name="Wilcoxon Signed-Rank Test",
                statistic=0,
                p_value=1.0,
                effect_size=0.0,
                effect_size_type="r",
                interpretation=f"检验失败: {str(e)}",
                significant=False,
                alpha=self.alpha,
                details={'error': str(e)}
            )

        # 计算效应量 (r = Z / sqrt(N))
        n = len(diff)
        z = stats.norm.ppf(p_value / 2) if alternative == 'two-sided' else stats.norm.ppf(p_value)
        effect_size = abs(z) / np.sqrt(n)

        significant = p_value < self.alpha

        interpretation = f"{'拒绝' if significant else '无法拒绝'}原假设 (p = {p_value:.4f})。"
        interpretation += f" 效应量: {self._interpret_effect_size(effect_size, 'r')}。"

        return TestResult(
            test_name="Wilcoxon Signed-Rank Test",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=effect_size,
            effect_size_type="r (rank correlation)",
            interpretation=interpretation,
            significant=significant,
            alpha=self.alpha,
            details={
                'n': n,
                'alternative': alternative,
                'median_diff': float(np.median(diff))
            }
        )

    def mann_whitney_u(self, group1: Union[np.ndarray, List],
                       group2: Union[np.ndarray, List],
                       alternative: str = 'two-sided') -> TestResult:
        """
        Mann-Whitney U 检验（独立样本非参数检验）

        Args:
            group1: 第一组数据
            group2: 第二组数据
            alternative: 备择假设类型

        Returns:
            TestResult
        """
        g1 = np.array(group1)
        g2 = np.array(group2)

        # 执行 Mann-Whitney U 检验
        statistic, p_value = stats.mannwhitneyu(g1, g2, alternative=alternative)

        # 计算效应量 (rank-biserial correlation)
        effect_size = self._calculate_rank_biserial(g1, g2)

        significant = p_value < self.alpha

        interpretation = f"{'拒绝' if significant else '无法拒绝'}原假设 (p = {p_value:.4f})。"
        interpretation += f" 效应量: {self._interpret_effect_size(effect_size, 'r')}。"

        return TestResult(
            test_name="Mann-Whitney U Test",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=effect_size,
            effect_size_type="r (rank-biserial)",
            interpretation=interpretation,
            significant=significant,
            alpha=self.alpha,
            details={
                'n1': len(g1),
                'n2': len(g2),
                'median1': float(np.median(g1)),
                'median2': float(np.median(g2)),
                'alternative': alternative
            }
        )

    def anova_one_way(self, *groups: Union[np.ndarray, List]) -> TestResult:
        """
        单因素方差分析 (One-way ANOVA)

        Args:
            *groups: 各组数据

        Returns:
            TestResult
        """
        groups = [np.array(g) for g in groups]
        n_groups = len(groups)

        if n_groups < 2:
            return TestResult(
                test_name="One-way ANOVA",
                statistic=0,
                p_value=1.0,
                effect_size=0.0,
                effect_size_type="eta_squared",
                interpretation="至少需要两组数据",
                significant=False,
                alpha=self.alpha,
                details={'error': 'At least 2 groups required'}
            )

        # 执行 ANOVA
        statistic, p_value = stats.f_oneway(*groups)

        # 计算 eta-squared
        effect_size = self._calculate_eta_squared(groups)

        significant = p_value < self.alpha

        interpretation = f"{'拒绝' if significant else '无法拒绝'}原假设 (F = {statistic:.4f}, p = {p_value:.4f})。"
        if significant:
            interpretation += " 组间存在显著差异。"
        else:
            interpretation += " 组间无显著差异。"
        interpretation += f" 效应量: {self._interpret_effect_size(effect_size, 'eta_squared')}。"

        details = {
            'n_groups': n_groups,
            'group_sizes': [len(g) for g in groups],
            'group_means': [float(np.mean(g)) for g in groups],
            'group_stds': [float(np.std(g, ddof=1)) for g in groups]
        }

        return TestResult(
            test_name="One-way ANOVA",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=effect_size,
            effect_size_type="eta-squared",
            interpretation=interpretation,
            significant=significant,
            alpha=self.alpha,
            details=details
        )

    def kruskal_wallis(self, *groups: Union[np.ndarray, List]) -> TestResult:
        """
        Kruskal-Wallis H 检验（非参数 ANOVA）

        Args:
            *groups: 各组数据

        Returns:
            TestResult
        """
        groups = [np.array(g) for g in groups]
        n_groups = len(groups)

        if n_groups < 2:
            return TestResult(
                test_name="Kruskal-Wallis H Test",
                statistic=0,
                p_value=1.0,
                effect_size=0.0,
                effect_size_type="eta_squared",
                interpretation="至少需要两组数据",
                significant=False,
                alpha=self.alpha,
                details={'error': 'At least 2 groups required'}
            )

        # 执行 Kruskal-Wallis 检验
        statistic, p_value = stats.kruskal(*groups)

        # 计算效应量 (epsilon squared)
        n_total = sum(len(g) for g in groups)
        effect_size = (statistic - n_groups + 1) / (n_total - n_groups)

        significant = p_value < self.alpha

        interpretation = f"{'拒绝' if significant else '无法拒绝'}原假设 (H = {statistic:.4f}, p = {p_value:.4f})。"
        if significant:
            interpretation += " 组间分布存在显著差异。"
        interpretation += f" 效应量 (epsilon squared): {effect_size:.4f}。"

        details = {
            'n_groups': n_groups,
            'group_sizes': [len(g) for g in groups],
            'group_medians': [float(np.median(g)) for g in groups],
            'group_mean_ranks': []
        }

        # 计算各组的平均秩
        all_data = np.concatenate(groups)
        ranks = stats.rankdata(all_data)
        idx = 0
        for g in groups:
            group_ranks = ranks[idx:idx + len(g)]
            details['group_mean_ranks'].append(float(np.mean(group_ranks)))
            idx += len(g)

        return TestResult(
            test_name="Kruskal-Wallis H Test",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=effect_size,
            effect_size_type="epsilon-squared",
            interpretation=interpretation,
            significant=significant,
            alpha=self.alpha,
            details=details
        )

    def chi_square(self, observed: np.ndarray) -> TestResult:
        """
        卡方独立性检验

        Args:
            observed: 观测频数表（二维数组）

        Returns:
            TestResult
        """
        observed = np.array(observed)

        # 执行卡方检验
        statistic, p_value, dof, expected = stats.chi2_contingency(observed)

        # 计算效应量 (Cramer's V)
        n = observed.sum()
        min_dim = min(observed.shape[0] - 1, observed.shape[1] - 1)

        if min_dim > 0 and n > 0:
            cramers_v = np.sqrt(statistic / (n * min_dim))
        else:
            cramers_v = 0.0

        significant = p_value < self.alpha

        interpretation = f"{'拒绝' if significant else '无法拒绝'}原假设 (chi2 = {statistic:.4f}, df = {dof}, p = {p_value:.4f})。"
        interpretation += f" 效应量 (Cramer's V): {self._interpret_effect_size(cramers_v, 'r')}。"

        return TestResult(
            test_name="Chi-Square Test of Independence",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=cramers_v,
            effect_size_type="Cramer's V",
            interpretation=interpretation,
            significant=significant,
            alpha=self.alpha,
            details={
                'degrees_of_freedom': int(dof),
                'observed': observed.tolist(),
                'expected': expected.tolist()
            }
        )

    def post_hoc_tukey(self, *groups: Union[np.ndarray, List],
                       labels: List[str] = None) -> Dict[str, Any]:
        """
        Tukey HSD 事后检验（需要 statsmodels）

        Args:
            *groups: 各组数据
            labels: 组标签

        Returns:
            事后检验结果
        """
        try:
            from statsmodels.stats.multicomp import pairwise_tukeyhsd
        except ImportError:
            return {'error': 'statsmodels 库未安装，无法执行 Tukey HSD 检验'}

        groups = [np.array(g) for g in groups]

        if labels is None:
            labels = [f'Group {i+1}' for i in range(len(groups))]

        # 准备数据
        all_data = np.concatenate(groups)
        group_labels = np.concatenate([[labels[i]] * len(groups[i])
                                       for i in range(len(groups))])

        # 执行 Tukey HSD
        tukey = pairwise_tukeyhsd(all_data, group_labels, alpha=self.alpha)

        return {
            'test_name': 'Tukey HSD Post-hoc Test',
            'results': tukey._results_table.data.tolist(),
            'summary': str(tukey)
        }

    def result_to_dict(self, result: TestResult) -> Dict[str, Any]:
        """将 TestResult 转换为字典"""
        return {
            'test_name': result.test_name,
            'statistic': round(result.statistic, 6),
            'p_value': round(result.p_value, 6),
            'effect_size': round(result.effect_size, 4),
            'effect_size_type': result.effect_size_type,
            'interpretation': result.interpretation,
            'significant': result.significant,
            'alpha': result.alpha,
            'details': result.details
        }

    def save_result(self, result: TestResult, output_path: str,
                    format: str = 'json') -> None:
        """
        保存检验结果

        Args:
            result: 检验结果
            output_path: 输出路径
            format: 输出格式 (json, txt, markdown)
        """
        result_dict = self.result_to_dict(result)
        path = Path(output_path)

        if format == 'json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)

        elif format == 'txt':
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"统计检验结果: {result.test_name}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"统计量: {result.statistic:.4f}\n")
                f.write(f"p-value: {result.p_value:.6f}\n")
                f.write(f"显著性水平: {result.alpha}\n")
                f.write(f"是否显著: {'是' if result.significant else '否'}\n\n")
                f.write(f"效应量 ({result.effect_size_type}): {result.effect_size:.4f}\n")
                f.write(f"\n解释: {result.interpretation}\n")
                f.write(f"\n详细信息:\n")
                for key, value in result.details.items():
                    f.write(f"  {key}: {value}\n")

        elif format == 'markdown':
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# 统计检验结果: {result.test_name}\n\n")
                f.write(f"## 检验统计量\n\n")
                f.write(f"| 指标 | 值 |\n")
                f.write(f"|------|----|\n")
                f.write(f"| 统计量 | {result.statistic:.4f} |\n")
                f.write(f"| p-value | {result.p_value:.6f} |\n")
                f.write(f"| 显著性水平 (α) | {result.alpha} |\n")
                f.write(f"| 结果 | **{'显著' if result.significant else '不显著'}** |\n\n")
                f.write(f"## 效应量\n\n")
                f.write(f"- {result.effect_size_type}: {result.effect_size:.4f}\n\n")
                f.write(f"## 解释\n\n{result.interpretation}\n\n")
                f.write(f"## 详细信息\n\n```json\n")
                f.write(json.dumps(result.details, indent=2))
                f.write("\n```\n")

        print(f"结果已保存到 {path}")


class Visualizer:
    """统计可视化工具"""

    def __init__(self):
        """初始化可视化器"""
        self._check_matplotlib()

    def _check_matplotlib(self):
        """检查 matplotlib 是否可用"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # 非交互式后端
            import matplotlib.pyplot as plt
            self.plt = plt
            self.available = True
        except ImportError:
            self.available = False
            self.plt = None

    def plot_comparison(self, groups: List[np.ndarray],
                        labels: List[str] = None,
                        title: str = "Group Comparison",
                        output_path: str = None) -> Optional[str]:
        """
        绘制组间比较图

        Args:
            groups: 各组数据
            labels: 组标签
            title: 图表标题
            output_path: 输出路径

        Returns:
            保存的文件路径（如果保存了的话）
        """
        if not self.available:
            print("警告: matplotlib 未安装，无法生成图表")
            return None

        if labels is None:
            labels = [f'Group {i+1}' for i in range(len(groups))]

        fig, axes = self.plt.subplots(1, 2, figsize=(12, 5))

        # 箱线图
        axes[0].boxplot(groups, labels=labels)
        axes[0].set_title('Box Plot')
        axes[0].set_ylabel('Value')
        axes[0].grid(True, alpha=0.3)

        # 均值柱状图（带误差棒）
        means = [np.mean(g) for g in groups]
        stds = [np.std(g, ddof=1) for g in groups]
        x_pos = range(len(groups))

        axes[1].bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7, color='steelblue')
        axes[1].set_xticks(x_pos)
        axes[1].set_xticklabels(labels)
        axes[1].set_title('Mean ± SD')
        axes[1].set_ylabel('Value')
        axes[1].grid(True, alpha=0.3, axis='y')

        fig.suptitle(title)
        self.plt.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存到 {output_path}")

        self.plt.close(fig)
        return output_path

    def plot_paired(self, before: np.ndarray, after: np.ndarray,
                    title: str = "Paired Comparison",
                    output_path: str = None) -> Optional[str]:
        """
        绘制配对数据比较图

        Args:
            before: 前测数据
            after: 后测数据
            title: 图表标题
            output_path: 输出路径

        Returns:
            保存的文件路径
        """
        if not self.available:
            print("警告: matplotlib 未安装，无法生成图表")
            return None

        fig, axes = self.plt.subplots(1, 2, figsize=(12, 5))

        # 连接线图
        x = np.arange(len(before))
        axes[0].plot([x, x], [before, after], 'b-', alpha=0.3)
        axes[0].scatter(x, before, c='red', label='Before', zorder=3)
        axes[0].scatter(x, after, c='green', label='After', zorder=3)
        axes[0].set_xlabel('Sample')
        axes[0].set_ylabel('Value')
        axes[0].set_title('Paired Data')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # 差值分布
        diff = after - before
        axes[1].hist(diff, bins=20, alpha=0.7, color='steelblue', edgecolor='black')
        axes[1].axvline(0, color='red', linestyle='--', label='No change')
        axes[1].axvline(np.mean(diff), color='green', linestyle='-', label=f'Mean diff: {np.mean(diff):.2f}')
        axes[1].set_xlabel('Difference (After - Before)')
        axes[1].set_ylabel('Frequency')
        axes[1].set_title('Distribution of Differences')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        fig.suptitle(title)
        self.plt.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存到 {output_path}")

        self.plt.close(fig)
        return output_path

    def plot_effect_sizes(self, results: List[TestResult],
                          title: str = "Effect Size Comparison",
                          output_path: str = None) -> Optional[str]:
        """
        绘制效应量比较图

        Args:
            results: 多个检验结果
            title: 图表标题
            output_path: 输出路径

        Returns:
            保存的文件路径
        """
        if not self.available:
            print("警告: matplotlib 未安装，无法生成图表")
            return None

        labels = [r.test_name for r in results]
        effect_sizes = [abs(r.effect_size) for r in results]
        colors = ['green' if r.significant else 'red' for r in results]

        fig, ax = self.plt.subplots(figsize=(10, 6))

        y_pos = range(len(labels))
        ax.barh(y_pos, effect_sizes, color=colors, alpha=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.set_xlabel('Effect Size (absolute value)')
        ax.set_title(title)

        # 添加效应量参考线
        ax.axvline(0.2, color='gray', linestyle='--', alpha=0.5, label='Small (0.2)')
        ax.axvline(0.5, color='gray', linestyle='-.', alpha=0.5, label='Medium (0.5)')
        ax.axvline(0.8, color='gray', linestyle=':', alpha=0.5, label='Large (0.8)')
        ax.legend(loc='lower right')

        ax.grid(True, alpha=0.3, axis='x')
        self.plt.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存到 {output_path}")

        self.plt.close(fig)
        return output_path


def main():
    parser = argparse.ArgumentParser(description='统计显著性检验工具')
    parser.add_argument('--alpha', '-a', type=float, default=0.05,
                        help='显著性水平 (默认: 0.05)')

    subparsers = parser.add_subparsers(dest='test_type', help='检验类型')

    # t-test 命令
    ttest_parser = subparsers.add_parser('ttest', help='t 检验')
    ttest_parser.add_argument('file', help='数据文件 (CSV/JSON)')
    ttest_parser.add_argument('--group1', '-g1', required=True, help='第一组数据列名')
    ttest_parser.add_argument('--group2', '-g2', help='第二组数据列名（独立样本）')
    ttest_parser.add_argument('--paired', '-p', action='store_true', help='配对样本')
    ttest_parser.add_argument('--pop-mean', '-m', type=float, help='总体均值（单样本）')
    ttest_parser.add_argument('--welch', '-w', action='store_true', help='使用 Welch t-test')
    ttest_parser.add_argument('--output', '-o', help='输出文件路径')

    # Mann-Whitney 命令
    mw_parser = subparsers.add_parser('mann-whitney', help='Mann-Whitney U 检验')
    mw_parser.add_argument('file', help='数据文件 (CSV/JSON)')
    mw_parser.add_argument('--group1', '-g1', required=True, help='第一组数据列名')
    mw_parser.add_argument('--group2', '-g2', required=True, help='第二组数据列名')
    mw_parser.add_argument('--output', '-o', help='输出文件路径')

    # Wilcoxon 命令
    wilcox_parser = subparsers.add_parser('wilcoxon', help='Wilcoxon 符号秩检验')
    wilcox_parser.add_argument('file', help='数据文件 (CSV/JSON)')
    wilcox_parser.add_argument('--before', '-b', required=True, help='前测数据列名')
    wilcox_parser.add_argument('--after', '-a', required=True, help='后测数据列名')
    wilcox_parser.add_argument('--output', '-o', help='输出文件路径')

    # ANOVA 命令
    anova_parser = subparsers.add_parser('anova', help='单因素方差分析')
    anova_parser.add_argument('file', help='数据文件 (CSV/JSON)')
    anova_parser.add_argument('--columns', '-c', nargs='+', required=True,
                              help='各组数据列名')
    anova_parser.add_argument('--nonparametric', '-n', action='store_true',
                              help='使用 Kruskal-Wallis 非参数检验')
    anova_parser.add_argument('--posthoc', action='store_true', help='执行 Tukey HSD 事后检验')
    anova_parser.add_argument('--output', '-o', help='输出文件路径')

    # 卡方检验命令
    chi_parser = subparsers.add_parser('chi2', help='卡方独立性检验')
    chi_parser.add_argument('file', help='数据文件 (CSV/JSON)')
    chi_parser.add_argument('--columns', '-c', nargs=2, required=True,
                            help='两个分类变量的列名')
    chi_parser.add_argument('--output', '-o', help='输出文件路径')

    # 可视化命令
    viz_parser = subparsers.add_parser('plot', help='生成可视化图表')
    viz_parser.add_argument('file', help='数据文件 (CSV/JSON)')
    viz_parser.add_argument('--columns', '-c', nargs='+', required=True,
                            help='要可视化的列名')
    viz_parser.add_argument('--type', '-t', choices=['comparison', 'paired'],
                            default='comparison', help='图表类型')
    viz_parser.add_argument('--output', '-o', required=True, help='输出图片路径')

    args = parser.parse_args()

    if not args.test_type:
        parser.print_help()
        return

    tester = StatisticalTest(alpha=args.alpha)
    visualizer = Visualizer()

    # 加载数据
    df = tester.load_data(args.file)

    if args.test_type == 'ttest':
        g1 = df[args.group1].dropna().values

        if args.pop_mean is not None:
            # 单样本 t 检验
            result = tester.t_test_one_sample(g1, args.pop_mean)
        elif args.paired and args.group2:
            # 配对 t 检验
            g2 = df[args.group2].dropna().values
            result = tester.t_test_paired(g1, g2)
        elif args.group2:
            # 独立样本 t 检验
            g2 = df[args.group2].dropna().values
            result = tester.t_test_independent(g1, g2, equal_var=not args.welch)
        else:
            print("错误: 请指定 --group2 或 --pop-mean")
            return

        print_result(result)
        if args.output:
            tester.save_result(result, args.output, 'json')

        # 生成可视化
        if args.group2:
            visualizer.plot_paired(g1, g2, title="Paired Comparison",
                                   output_path=args.output.replace('.json', '.png') if args.output else None)

    elif args.test_type == 'mann-whitney':
        g1 = df[args.group1].dropna().values
        g2 = df[args.group2].dropna().values
        result = tester.mann_whitney_u(g1, g2)
        print_result(result)
        if args.output:
            tester.save_result(result, args.output, 'json')

    elif args.test_type == 'wilcoxon':
        before = df[args.before].dropna().values
        after = df[args.after].dropna().values
        result = tester.wilcoxon_test(before, after)
        print_result(result)
        if args.output:
            tester.save_result(result, args.output, 'json')

    elif args.test_type == 'anova':
        groups = [df[col].dropna().values for col in args.columns]

        if args.nonparametric:
            result = tester.kruskal_wallis(*groups)
        else:
            result = tester.anova_one_way(*groups)

        print_result(result)

        if args.posthoc and not args.nonparametric:
            posthoc = tester.post_hoc_tukey(*groups, labels=args.columns)
            print("\n事后检验 (Tukey HSD):")
            print(posthoc.get('summary', ''))

        if args.output:
            tester.save_result(result, args.output, 'json')

        # 生成可视化
        visualizer.plot_comparison(groups, labels=args.columns,
                                   output_path=args.output.replace('.json', '.png') if args.output else None)

    elif args.test_type == 'chi2':
        # 创建列联表
        contingency = pd.crosstab(df[args.columns[0]], df[args.columns[1]])
        result = tester.chi_square(contingency.values)
        print_result(result)
        if args.output:
            tester.save_result(result, args.output, 'json')

    elif args.test_type == 'plot':
        columns_data = [df[col].dropna().values for col in args.columns]

        if args.type == 'comparison':
            visualizer.plot_comparison(columns_data, labels=args.columns,
                                       output_path=args.output)
        elif args.type == 'paired' and len(args.columns) == 2:
            visualizer.plot_paired(columns_data[0], columns_data[1],
                                   output_path=args.output)


def print_result(result: TestResult):
    """打印检验结果"""
    print("\n" + "=" * 60)
    print(f"统计检验: {result.test_name}")
    print("=" * 60)
    print(f"统计量: {result.statistic:.4f}")
    print(f"p-value: {result.p_value:.6f}")
    print(f"显著性水平 (α): {result.alpha}")
    print(f"结果: {'✓ 显著' if result.significant else '✗ 不显著'}")
    print(f"\n效应量 ({result.effect_size_type}): {result.effect_size:.4f}")
    print(f"\n解释: {result.interpretation}")
    print("=" * 60)


if __name__ == "__main__":
    main()
