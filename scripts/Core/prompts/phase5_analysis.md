# Phase 5: 数据分析 Prompt

## YOUR ROLE

你是 Project Prometheus 的数据分析专家。你的任务是对实验产生的数据进行全面、严谨的统计分析，选择合适的统计检验方法，生成高质量的可视化图表，并基于统计证据解读实验结果。你需要确保结论的科学性和可复现性，为论文撰写提供坚实的数据支撑。

---

## 工作目标

1. **数据整理**: 汇总和清洗实验数据
2. **统计检验**: 选择并执行合适的统计检验
3. **效应量计算**: 评估实验效果的实际意义
4. **可视化**: 生成清晰、专业的图表
5. **结果解读**: 基于数据得出科学结论
6. **报告生成**: 输出结构化的分析报告

---

## STEP 1: 数据整理

### 1.1 数据收集

从实验输出中收集所有结果数据：

```python
# scripts/collect_results.py

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

def collect_experiment_results(results_dir: str) -> pd.DataFrame:
    """收集实验结果数据。

    Args:
        results_dir: 实验结果目录路径

    Returns:
        包含所有实验结果的 DataFrame
    """
    results = []

    for experiment_dir in Path(results_dir).iterdir():
        if not experiment_dir.is_dir():
            continue

        # 读取实验配置
        config_path = experiment_dir / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        # 读取指标历史
        metrics_path = experiment_dir / "metrics_history.csv"
        if metrics_path.exists():
            metrics_df = pd.read_csv(metrics_path)

            # 提取最终指标
            final_metrics = metrics_df.iloc[-1].to_dict()

            # 提取最佳指标
            best_idx = metrics_df['val_loss'].idxmin()
            best_metrics = metrics_df.loc[best_idx].to_dict()

        # 读取评估结果
        eval_path = experiment_dir / "evaluation_results.json"
        if eval_path.exists():
            with open(eval_path, 'r') as f:
                eval_results = json.load(f)
        else:
            eval_results = {}

        # 合并所有信息
        result = {
            'experiment_id': experiment_dir.name,
            **config,
            **{f'final_{k}': v for k, v in final_metrics.items()},
            **{f'best_{k}': v for k, v in best_metrics.items()},
            **{f'test_{k}': v for k, v in eval_results.items()}
        }
        results.append(result)

    return pd.DataFrame(results)


def aggregate_repeat_runs(df: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
    """聚合并行运行的实验结果。

    Args:
        df: 原始结果 DataFrame
        group_cols: 用于分组的列名（实验配置）

    Returns:
        聚合后的 DataFrame，包含均值和标准差
    """
    # 定义要聚合的指标列
    metric_cols = [col for col in df.columns
                   if col.startswith(('final_', 'best_', 'test_'))]

    aggregated = df.groupby(group_cols)[metric_cols].agg(['mean', 'std', 'count'])
    aggregated.columns = ['_'.join(col) for col in aggregated.columns]

    return aggregated.reset_index()
```

### 1.2 数据清洗

```python
def clean_results(df: pd.DataFrame) -> pd.DataFrame:
    """清洗实验结果数据。

    Args:
        df: 原始结果 DataFrame

    Returns:
        清洗后的 DataFrame
    """
    # 1. 移除失败的实验（NaN 或 Inf）
    df = df.copy()
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns

    for col in numeric_cols:
        # 检查无穷值
        inf_mask = np.isinf(df[col])
        if inf_mask.any():
            print(f"[WARNING] 列 {col} 包含 {inf_mask.sum()} 个无穷值")
            df = df[~inf_mask]

        # 检查 NaN
        nan_mask = df[col].isna()
        if nan_mask.any():
            print(f"[WARNING] 列 {col} 包含 {nan_mask.sum()} 个 NaN 值")
            df = df[~nan_mask]

    # 2. 移除异常值（使用 IQR 方法）
    for col in ['test_accuracy', 'test_f1_macro']:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            outlier_mask = (df[col] < lower) | (df[col] > upper)
            if outlier_mask.any():
                print(f"[WARNING] 列 {col} 检测到 {outlier_mask.sum()} 个异常值")
                # 标记但不删除，需要人工确认
                df[f'{col}_is_outlier'] = outlier_mask

    # 3. 验证数据完整性
    required_cols = ['experiment_id', 'model_name', 'seed']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"缺少必要列: {col}")

    return df
```

### 1.3 数据结构化存储

```python
def save_structured_results(df: pd.DataFrame, output_dir: str) -> None:
    """保存结构化的实验结果。

    Args:
        df: 结果 DataFrame
        output_dir: 输出目录
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 保存为 CSV（便于查看）
    df.to_csv(output_path / "results_summary.csv", index=False)

    # 保存为 JSON（便于程序读取）
    df.to_json(output_path / "results_summary.json", orient='records', indent=2)

    # 按实验类型分组保存
    if 'model_name' in df.columns:
        for model_name in df['model_name'].unique():
            model_df = df[df['model_name'] == model_name]
            model_df.to_csv(output_path / f"results_{model_name}.csv", index=False)

    # 生成描述性统计
    desc_stats = df.describe()
    desc_stats.to_csv(output_path / "descriptive_stats.csv")

    print(f"[INFO] 结果已保存到 {output_path}")
```

---

## STEP 2: 统计检验选择

### 2.1 检验方法选择决策树

```
                    数据类型?
                        │
        ┌───────────────┼───────────────┐
        │               │               │
     连续型           计数型          分类/比例
        │               │               │
        ▼               ▼               ▼
   正态分布?       卡方检验        比例检验
        │           泊松回归        Fisher精确检验
   ┌────┴────┐
   │         │
  是        否
   │         │
   ▼         ▼
参数检验   非参数检验
   │         │
   ▼         ▼
 t-test   Mann-Whitney U
 ANOVA    Wilcoxon
   ...     Kruskal-Wallis
           ...
```

### 2.2 正态性检验

```python
import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any

def check_normality(data: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """检验数据是否符合正态分布。

    Args:
        data: 要检验的数据数组
        alpha: 显著性水平

    Returns:
        包含检验结果的字典
    """
    # Shapiro-Wilk 检验（适用于小样本，n < 50）
    if len(data) < 50:
        stat, p_value = stats.shapiro(data)
        test_name = "Shapiro-Wilk"
    else:
        # D'Agostino-Pearson 检验（适用于大样本）
        stat, p_value = stats.normaltest(data)
        test_name = "D'Agostino-Pearson"

    is_normal = p_value > alpha

    return {
        'test': test_name,
        'statistic': stat,
        'p_value': p_value,
        'is_normal': is_normal,
        'alpha': alpha,
        'conclusion': '数据符合正态分布' if is_normal else '数据不符合正态分布'
    }


def check_homogeneity_of_variance(group1: np.ndarray, group2: np.ndarray,
                                   alpha: float = 0.05) -> Dict[str, Any]:
    """检验两组数据的方差齐性。

    Args:
        group1: 第一组数据
        group2: 第二组数据
        alpha: 显著性水平

    Returns:
        包含检验结果的字典
    """
    # Levene 检验（对正态性不敏感）
    stat, p_value = stats.levene(group1, group2)

    is_equal = p_value > alpha

    return {
        'test': 'Levene',
        'statistic': stat,
        'p_value': p_value,
        'is_equal_variance': is_equal,
        'alpha': alpha,
        'conclusion': '方差齐性成立' if is_equal else '方差不齐'
    }
```

### 2.3 两组比较检验

```python
def compare_two_groups(group1: np.ndarray, group2: np.ndarray,
                       paired: bool = False, alpha: float = 0.05) -> Dict[str, Any]:
    """比较两组数据的统计检验。

    Args:
        group1: 第一组数据
        group2: 第二组数据
        paired: 是否为配对样本
        alpha: 显著性水平

    Returns:
        包含完整检验结果的字典
    """
    # 1. 正态性检验
    normality1 = check_normality(group1, alpha)
    normality2 = check_normality(group2, alpha)

    # 2. 根据正态性选择检验方法
    if normality1['is_normal'] and normality2['is_normal']:
        # 使用参数检验
        if paired:
            # 配对 t 检验
            stat, p_value = stats.ttest_rel(group1, group2)
            test_name = "Paired t-test"
        else:
            # 方差齐性检验
            homogeneity = check_homogeneity_of_variance(group1, group2, alpha)

            if homogeneity['is_equal_variance']:
                # 独立样本 t 检验（等方差）
                stat, p_value = stats.ttest_ind(group1, group2, equal_var=True)
                test_name = "Independent t-test (equal variance)"
            else:
                # Welch's t 检验（不等方差）
                stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)
                test_name = "Welch's t-test (unequal variance)"
    else:
        # 使用非参数检验
        if paired:
            # Wilcoxon 符号秩检验
            stat, p_value = stats.wilcoxon(group1, group2)
            test_name = "Wilcoxon signed-rank test"
        else:
            # Mann-Whitney U 检验
            stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
            test_name = "Mann-Whitney U test"

    # 3. 计算效应量
    effect_size = compute_effect_size(group1, group2, paired)

    # 4. 判断显著性
    is_significant = p_value < alpha

    return {
        'test': test_name,
        'statistic': stat,
        'p_value': p_value,
        'is_significant': is_significant,
        'alpha': alpha,
        'effect_size': effect_size,
        'normality': {
            'group1': normality1,
            'group2': normality2
        },
        'conclusion': generate_comparison_conclusion(test_name, is_significant,
                                                     p_value, effect_size)
    }
```

### 2.4 多组比较检验（ANOVA）

```python
def compare_multiple_groups(groups: Dict[str, np.ndarray],
                            alpha: float = 0.05) -> Dict[str, Any]:
    """多组数据的方差分析。

    Args:
        groups: 组名到数据的字典
        alpha: 显著性水平

    Returns:
        包含完整检验结果的字典
    """
    group_names = list(groups.keys())
    group_data = list(groups.values())

    # 1. 正态性检验（所有组）
    normality_results = {}
    all_normal = True
    for name, data in groups.items():
        result = check_normality(data, alpha)
        normality_results[name] = result
        if not result['is_normal']:
            all_normal = False

    # 2. 选择检验方法
    if all_normal:
        # 单因素方差分析
        stat, p_value = stats.f_oneway(*group_data)
        test_name = "One-way ANOVA"

        # 如果显著，进行事后检验
        post_hoc = None
        if p_value < alpha:
            post_hoc = perform_tukey_hsd(group_data, group_names)
    else:
        # Kruskal-Wallis 检验
        stat, p_value = stats.kruskal(*group_data)
        test_name = "Kruskal-Wallis H-test"

        # 如果显著，进行事后检验
        post_hoc = None
        if p_value < alpha:
            post_hoc = perform_dunn_test(group_data, group_names)

    # 3. 计算效应量（η²）
    effect_size = compute_eta_squared(group_data)

    return {
        'test': test_name,
        'statistic': stat,
        'p_value': p_value,
        'is_significant': p_value < alpha,
        'alpha': alpha,
        'effect_size': effect_size,
        'normality': normality_results,
        'post_hoc': post_hoc,
        'conclusion': f"ANOVA {'显著' if p_value < alpha else '不显著'} "
                      f"(F={stat:.3f}, p={p_value:.4f}, η²={effect_size:.3f})"
    }


def perform_tukey_hsd(group_data: List[np.ndarray],
                      group_names: List[str]) -> Dict[str, Any]:
    """执行 Tukey HSD 事后检验。

    Args:
        group_data: 各组数据列表
        group_names: 各组名称列表

    Returns:
        事后检验结果
    """
    from scipy.stats import tukey_hsd

    result = tukey_hsd(*group_data)

    comparisons = []
    n_groups = len(group_names)
    for i in range(n_groups):
        for j in range(i + 1, n_groups):
            comparisons.append({
                'comparison': f"{group_names[i]} vs {group_names[j]}",
                'mean_diff': np.mean(group_data[i]) - np.mean(group_data[j]),
                'p_value': result.pvalue[i, j],
                'is_significant': result.pvalue[i, j] < 0.05
            })

    return {
        'test': 'Tukey HSD',
        'comparisons': comparisons
    }
```

---

## STEP 3: 效应量计算

### 3.1 效应量类型

```python
def compute_effect_size(group1: np.ndarray, group2: np.ndarray,
                        paired: bool = False) -> Dict[str, float]:
    """计算效应量。

    Args:
        group1: 第一组数据
        group2: 第二组数据
        paired: 是否为配对样本

    Returns:
        包含各种效应量的字典
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)

    # 1. Cohen's d（标准化的均值差）
    if paired:
        # 配对样本的 Cohen's d
        diff = group1 - group2
        pooled_std = np.std(diff, ddof=1)
        cohens_d = np.mean(diff) / pooled_std if pooled_std != 0 else 0
    else:
        # 独立样本的 Cohen's d（使用 pooled SD）
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        cohens_d = (mean1 - mean2) / pooled_std if pooled_std != 0 else 0

    # 2. Hedges' g（对小样本校正的 Cohen's d）
    correction = 1 - 3 / (4 * (n1 + n2) - 9)
    hedges_g = cohens_d * correction

    # 3. Glass's Δ（使用对照组标准差）
    glass_delta = (mean1 - mean2) / np.sqrt(var2) if var2 != 0 else 0

    # 4. Cliff's delta（非参数效应量）
    cliff_delta = compute_cliff_delta(group1, group2)

    # 5. Common Language Effect Size (CLES)
    cles = compute_cles(group1, group2)

    return {
        'cohens_d': cohens_d,
        'hedges_g': hedges_g,
        'glass_delta': glass_delta,
        'cliff_delta': cliff_delta,
        'cles': cles,
        'interpretation': interpret_cohens_d(cohens_d)
    }


def compute_eta_squared(group_data: List[np.ndarray]) -> float:
    """计算 η²（方差分析效应量）。

    Args:
        group_data: 各组数据列表

    Returns:
        η² 值
    """
    all_data = np.concatenate(group_data)
    grand_mean = np.mean(all_data)

    # 总平方和
    ss_total = np.sum((all_data - grand_mean) ** 2)

    # 组间平方和
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in group_data)

    # η²
    eta_squared = ss_between / ss_total if ss_total != 0 else 0

    return eta_squared


def compute_cliff_delta(group1: np.ndarray, group2: np.ndarray) -> float:
    """计算 Cliff's delta（非参数效应量）。

    Args:
        group1: 第一组数据
        group2: 第二组数据

    Returns:
        Cliff's delta 值
    """
    n1, n2 = len(group1), len(group2)

    # 计算胜出次数
    greater = 0
    less = 0

    for x in group1:
        for y in group2:
            if x > y:
                greater += 1
            elif x < y:
                less += 1

    delta = (greater - less) / (n1 * n2)
    return delta


def compute_cles(group1: np.ndarray, group2: np.ndarray) -> float:
    """计算 Common Language Effect Size。

    Args:
        group1: 第一组数据
        group2: 第二组数据

    Returns:
        CLES 值（概率）
    """
    n1, n2 = len(group1), len(group2)
    count = 0

    for x in group1:
        for y in group2:
            if x > y:
                count += 1
            elif x == y:
                count += 0.5

    return count / (n1 * n2)


def interpret_cohens_d(d: float) -> str:
    """解释 Cohen's d 的大小。

    Args:
        d: Cohen's d 值

    Returns:
        解释文本
    """
    d_abs = abs(d)

    if d_abs < 0.2:
        return "极小效应 (negligible)"
    elif d_abs < 0.5:
        return "小效应 (small)"
    elif d_abs < 0.8:
        return "中等效应 (medium)"
    else:
        return "大效应 (large)"
```

### 3.2 置信区间

```python
def compute_confidence_interval(data: np.ndarray,
                                confidence: float = 0.95) -> Tuple[float, float]:
    """计算均值的置信区间。

    Args:
        data: 数据数组
        confidence: 置信水平

    Returns:
        置信区间 (下界, 上界)
    """
    n = len(data)
    mean = np.mean(data)
    se = stats.sem(data)

    # 使用 t 分布
    h = se * stats.t.ppf((1 + confidence) / 2, n - 1)

    return (mean - h, mean + h)


def compute_bootstrap_ci(group1: np.ndarray, group2: np.ndarray,
                         n_bootstrap: int = 10000,
                         confidence: float = 0.95) -> Dict[str, Any]:
    """使用 Bootstrap 计算均值差的置信区间。

    Args:
        group1: 第一组数据
        group2: 第二组数据
        n_bootstrap: Bootstrap 次数
        confidence: 置信水平

    Returns:
        包含置信区间和相关信息的结果
    """
    observed_diff = np.mean(group1) - np.mean(group2)

    bootstrap_diffs = []
    n1, n2 = len(group1), len(group2)

    for _ in range(n_bootstrap):
        # 有放回抽样
        sample1 = np.random.choice(group1, size=n1, replace=True)
        sample2 = np.random.choice(group2, size=n2, replace=True)
        diff = np.mean(sample1) - np.mean(sample2)
        bootstrap_diffs.append(diff)

    bootstrap_diffs = np.array(bootstrap_diffs)

    # 计算百分位置信区间
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_diffs, alpha / 2 * 100)
    upper = np.percentile(bootstrap_diffs, (1 - alpha / 2) * 100)

    return {
        'observed_difference': observed_diff,
        'ci_lower': lower,
        'ci_upper': upper,
        'confidence': confidence,
        'bootstrap_std': np.std(bootstrap_diffs),
        'contains_zero': lower <= 0 <= upper
    }
```

---

## STEP 4: 可视化规范

### 4.1 可视化工具类

```python
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Tuple

class ResultVisualizer:
    """实验结果可视化工具类。"""

    def __init__(self, style: str = "seaborn-v0_8-whitegrid",
                 font_family: str = "serif",
                 font_size: int = 12):
        """初始化可视化设置。

        Args:
            style: matplotlib 样式
            font_family: 字体族
            font_size: 基础字体大小
        """
        plt.style.use(style)
        plt.rcParams['font.family'] = font_family
        plt.rcParams['font.size'] = font_size
        plt.rcParams['axes.labelsize'] = font_size + 2
        plt.rcParams['axes.titlesize'] = font_size + 4
        plt.rcParams['legend.fontsize'] = font_size

        # 学术论文常用配色
        self.colors = {
            'primary': '#1f77b4',     # 蓝色
            'secondary': '#ff7f0e',   # 橙色
            'tertiary': '#2ca02c',    # 绿色
            'baseline': '#7f7f7f',    # 灰色
            'highlight': '#d62728'    # 红色
        }

    def plot_training_curves(self, history: Dict[str, List[float]],
                             output_path: Optional[str] = None,
                             figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """绘制训练曲线。

        Args:
            history: 包含训练历史的字典
            output_path: 输出文件路径
            figsize: 图形大小

        Returns:
            matplotlib Figure 对象
        """
        fig, axes = plt.subplots(1, 2, figsize=figsize)

        epochs = range(1, len(history['train_loss']) + 1)

        # 损失曲线
        ax = axes[0]
        ax.plot(epochs, history['train_loss'], label='Train Loss',
                color=self.colors['primary'], linewidth=2)
        ax.plot(epochs, history['val_loss'], label='Val Loss',
                color=self.colors['secondary'], linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Loss')
        ax.set_title('Training and Validation Loss')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 准确率曲线（如果有）
        ax = axes[1]
        if 'train_acc' in history:
            ax.plot(epochs, history['train_acc'], label='Train Acc',
                    color=self.colors['primary'], linewidth=2)
        if 'val_acc' in history:
            ax.plot(epochs, history['val_acc'], label='Val Acc',
                    color=self.colors['secondary'], linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Accuracy')
        ax.set_title('Training and Validation Accuracy')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_comparison_bar(self, data: pd.DataFrame,
                            x_col: str, y_col: str,
                            hue_col: Optional[str] = None,
                            ci: float = 0.95,
                            output_path: Optional[str] = None,
                            figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """绘制比较柱状图（带误差棒）。

        Args:
            data: 数据 DataFrame
            x_col: x 轴列名
            y_col: y 轴列名
            hue_col: 分组列名
            ci: 置信区间
            output_path: 输出文件路径
            figsize: 图形大小

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        sns.barplot(data=data, x=x_col, y=y_col, hue=hue_col,
                    errorbar=('ci', ci * 100), capsize=0.1,
                    palette='colorblind', ax=ax)

        ax.set_xlabel(x_col.replace('_', ' ').title())
        ax.set_ylabel(y_col.replace('_', ' ').title())
        ax.set_title(f'{y_col.replace("_", " ").title()} Comparison')

        if hue_col:
            ax.legend(title=hue_col.replace('_', ' ').title())

        plt.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_boxplot_comparison(self, data: pd.DataFrame,
                                x_col: str, y_col: str,
                                output_path: Optional[str] = None,
                                figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """绘制箱线图比较。

        Args:
            data: 数据 DataFrame
            x_col: x 轴列名（分组）
            y_col: y 轴列名（数值）
            output_path: 输出文件路径
            figsize: 图形大小

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        # 添加散点（显示原始数据）
        sns.stripplot(data=data, x=x_col, y=y_col,
                      color='black', alpha=0.3, size=4, ax=ax)

        # 绘制箱线图
        sns.boxplot(data=data, x=x_col, y=y_col,
                    palette='colorblind', width=0.5, ax=ax)

        # 添加均值标记
        means = data.groupby(x_col)[y_col].mean()
        for i, (group, mean) in enumerate(means.items()):
            ax.scatter(i, mean, marker='D', color='red', s=50, zorder=3)

        ax.set_xlabel(x_col.replace('_', ' ').title())
        ax.set_ylabel(y_col.replace('_', ' ').title())
        ax.set_title(f'{y_col.replace("_", " ").title()} Distribution by {x_col}')

        plt.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_heatmap(self, data: pd.DataFrame,
                     output_path: Optional[str] = None,
                     figsize: Tuple[int, int] = (10, 8),
                     annot: bool = True,
                     fmt: str = ".3f") -> plt.Figure:
        """绘制热力图。

        Args:
            data: 数据矩阵
            output_path: 输出文件路径
            figsize: 图形大小
            annot: 是否显示数值
            fmt: 数值格式

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        sns.heatmap(data, annot=annot, fmt=fmt, cmap='RdYlGn',
                    center=0, ax=ax, cbar_kws={'shrink': 0.8})

        ax.set_title('Performance Comparison Heatmap')

        plt.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_confusion_matrix(self, cm: np.ndarray,
                              class_names: List[str],
                              output_path: Optional[str] = None,
                              figsize: Tuple[int, int] = (10, 8)) -> plt.Figure:
        """绘制混淆矩阵。

        Args:
            cm: 混淆矩阵
            class_names: 类别名称列表
            output_path: 输出文件路径
            figsize: 图形大小

        Returns:
            matplotlib Figure 对象
        """
        fig, ax = plt.subplots(figsize=figsize)

        # 归一化
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

        sns.heatmap(cm_normalized, annot=True, fmt='.2f',
                    xticklabels=class_names, yticklabels=class_names,
                    cmap='Blues', ax=ax)

        ax.set_xlabel('Predicted')
        ax.set_ylabel('True')
        ax.set_title('Normalized Confusion Matrix')

        plt.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig
```

### 4.2 图表质量标准

```markdown
# 可视化质量检查清单

## 基本要求
- [ ] 图形分辨率 >= 300 DPI
- [ ] 使用矢量格式（PDF/SVG）或高分辨率 PNG
- [ ] 字体大小清晰可读（>= 8pt）
- [ ] 图例完整且位置适当

## 学术规范
- [ ] 坐标轴标签完整（包含单位）
- [ ] 使用适当的颜色方案（考虑色盲友好）
- [ ] 误差棒/置信区间清晰显示
- [ ] 统计显著性标记正确（*, **, ***）

## 内容要求
- [ ] 标题清晰描述图表内容
- [ ] 数据点/线可区分
- [ ] 避免过度拥挤
- [ ] 重要的对比突出显示

## 文件命名
- 使用描述性文件名
- 包含实验ID和图表类型
- 示例: `exp001_accuracy_comparison.pdf`
```

---

## STEP 5: 结果解读模板

### 5.1 分析报告模板

```python
def generate_analysis_report(results: Dict[str, Any],
                             output_path: str) -> str:
    """生成结构化的分析报告。

    Args:
        results: 分析结果字典
        output_path: 输出文件路径

    Returns:
        报告内容字符串
    """
    report = []

    # 标题
    report.append("# 实验结果分析报告\n")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n")

    # 1. 描述性统计
    report.append("## 1. 描述性统计\n")
    report.append(format_descriptive_stats(results['descriptive_stats']))

    # 2. 正态性检验
    report.append("## 2. 正态性检验\n")
    report.append(format_normality_tests(results['normality_tests']))

    # 3. 主要比较结果
    report.append("## 3. 统计检验结果\n")
    report.append(format_statistical_tests(results['statistical_tests']))

    # 4. 效应量
    report.append("## 4. 效应量分析\n")
    report.append(format_effect_sizes(results['effect_sizes']))

    # 5. 结论
    report.append("## 5. 主要结论\n")
    report.append(results['conclusions'])

    # 6. 可视化
    report.append("## 6. 可视化图表\n")
    for fig_name, fig_path in results['figures'].items():
        report.append(f"![{fig_name}]({fig_path})\n")

    # 保存报告
    report_content = "\n".join(report)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return report_content


def format_statistical_test(test_name: str, result: Dict) -> str:
    """格式化单个统计检验结果。

    Args:
        test_name: 检验名称
        result: 检验结果字典

    Returns:
        格式化的文本
    """
    lines = []
    lines.append(f"### {test_name}\n")

    # 检验统计量
    lines.append(f"- 检验方法: {result['test']}")
    lines.append(f"- 统计量: {result['statistic']:.4f}")
    lines.append(f"- p 值: {result['p_value']:.4f}")

    # 显著性标记
    if result['p_value'] < 0.001:
        sig_mark = "***"
    elif result['p_value'] < 0.01:
        sig_mark = "**"
    elif result['p_value'] < 0.05:
        sig_mark = "*"
    else:
        sig_mark = "n.s."

    lines.append(f"- 显著性: {sig_mark}")

    # 效应量（如果有）
    if 'effect_size' in result:
        es = result['effect_size']
        if isinstance(es, dict) and 'cohens_d' in es:
            lines.append(f"- 效应量 (Cohen's d): {es['cohens_d']:.3f} ({es['interpretation']})")

    # 置信区间（如果有）
    if 'confidence_interval' in result:
        ci = result['confidence_interval']
        lines.append(f"- 95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]")

    lines.append(f"\n**结论**: {result['conclusion']}\n")

    return "\n".join(lines)
```

### 5.2 结论模板

```markdown
# 结果解读模板

## 支持假设的情况

> 实验结果**支持**我们的研究假设。

**统计证据**:
- [方法名] 与 [基线] 之间存在显著差异 (p = X.XXX)
- 效应量 Cohen's d = X.XX，属于[大/中/小]效应
- 95% 置信区间为 [X.XX, Y.YY]，不包含 0

**实际意义**:
- [方法名] 在 [指标] 上提升了 X.X% (绝对值) / X.X% (相对值)
- 这一提升在[实际应用场景]中具有重要意义

**稳健性**:
- 结果在多次运行中保持一致 (std = X.XX)
- 在[子集/条件]下同样观察到显著差异

---

## 部分支持假设的情况

> 实验结果**部分支持**我们的研究假设。

**支持的方面**:
- 在[指标1/条件1]上观察到显著提升 (p = X.XXX)
- [具体描述支持的部分]

**不支持的方面**:
- 在[指标2/条件2]上未观察到显著差异 (p = X.XXX)
- [具体描述不支持的部分]

**可能原因**:
1. [原因1]
2. [原因2]

**需要进一步研究**:
- [建议1]
- [建议2]

---

## 不支持假设的情况

> 实验结果**不支持**我们的研究假设。

**统计证据**:
- [方法名] 与 [基线] 之间无显著差异 (p = X.XXX)
- 效应量 Cohen's d = X.XX，属于极小效应
- 95% 置信区间为 [X.XX, Y.YY]，包含 0

**可能原因分析**:
1. **假设问题**: [分析]
2. **实现问题**: [分析]
3. **实验设计问题**: [分析]

**下一步建议**:
- [建议1]
- [建议2]
```

---

## STEP 6: 多重比较校正

### 6.1 多重比较问题

```python
def apply_bonferroni_correction(p_values: List[float],
                                 alpha: float = 0.05) -> Dict[str, Any]:
    """应用 Bonferroni 校正。

    Args:
        p_values: 原始 p 值列表
        alpha: 原始显著性水平

    Returns:
        包含校正后结果的字典
    """
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests

    results = []
    for i, p in enumerate(p_values):
        is_significant = p < corrected_alpha
        results.append({
            'test_index': i,
            'original_p': p,
            'corrected_alpha': corrected_alpha,
            'is_significant': is_significant
        })

    return {
        'method': 'Bonferroni',
        'n_tests': n_tests,
        'original_alpha': alpha,
        'corrected_alpha': corrected_alpha,
        'results': results
    }


def apply_fdr_correction(p_values: List[float],
                         alpha: float = 0.05,
                         method: str = 'fdr_bh') -> Dict[str, Any]:
    """应用 False Discovery Rate (FDR) 校正。

    Args:
        p_values: 原始 p 值列表
        alpha: FDR 水平
        method: FDR 方法 ('fdr_bh', 'fdr_by', 'fdr_tsbh')

    Returns:
        包含校正后结果的字典
    """
    from statsmodels.stats.multitest import multipletests

    rejected, corrected_p, _, _ = multipletests(
        p_values, alpha=alpha, method=method
    )

    results = []
    for i, (p, cp, rej) in enumerate(zip(p_values, corrected_p, rejected)):
        results.append({
            'test_index': i,
            'original_p': p,
            'corrected_p': cp,
            'is_significant': rej
        })

    return {
        'method': f'FDR ({method})',
        'alpha': alpha,
        'n_significant': sum(rejected),
        'results': results
    }
```

---

## STEP 7: 综合分析流程

### 7.1 完整分析脚本

```python
def run_complete_analysis(results_dir: str, output_dir: str) -> None:
    """执行完整的数据分析流程。

    Args:
        results_dir: 实验结果目录
        output_dir: 分析输出目录
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("开始数据分析")
    print("=" * 60)

    # 1. 数据收集
    print("\n[1/7] 收集实验数据...")
    df = collect_experiment_results(results_dir)
    df = clean_results(df)
    save_structured_results(df, output_path / "data")
    print(f"  - 收集了 {len(df)} 条实验记录")

    # 2. 描述性统计
    print("\n[2/7] 计算描述性统计...")
    desc_stats = compute_descriptive_stats(df)
    print(f"  - 生成了 {len(desc_stats)} 个统计指标")

    # 3. 正态性检验
    print("\n[3/7] 执行正态性检验...")
    normality_results = {}
    for metric in ['test_accuracy', 'test_f1_macro']:
        if metric in df.columns:
            normality_results[metric] = check_normality(df[metric].values)
            print(f"  - {metric}: {normality_results[metric]['conclusion']}")

    # 4. 主要统计检验
    print("\n[4/7] 执行统计检验...")
    statistical_tests = perform_all_statistical_tests(df)
    print(f"  - 完成了 {len(statistical_tests)} 项检验")

    # 5. 效应量计算
    print("\n[5/7] 计算效应量...")
    effect_sizes = compute_all_effect_sizes(df)
    print(f"  - 计算了 {len(effect_sizes)} 个效应量")

    # 6. 生成可视化
    print("\n[6/7] 生成可视化图表...")
    visualizer = ResultVisualizer()
    figures = generate_all_figures(df, visualizer, output_path / "figures")
    print(f"  - 生成了 {len(figures)} 张图表")

    # 7. 生成报告
    print("\n[7/7] 生成分析报告...")
    results = {
        'descriptive_stats': desc_stats,
        'normality_tests': normality_results,
        'statistical_tests': statistical_tests,
        'effect_sizes': effect_sizes,
        'figures': figures,
        'conclusions': generate_conclusions(statistical_tests, effect_sizes)
    }
    report_path = output_path / "analysis_report.md"
    generate_analysis_report(results, report_path)
    print(f"  - 报告保存到: {report_path}")

    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)
```

### 7.2 分析质量检查清单

```markdown
# Phase 5 完成检查清单

## 数据质量
- [ ] 所有实验数据已收集
- [ ] 异常值已识别和处理
- [ ] 数据格式统一规范

## 统计分析
- [ ] 正态性检验已完成
- [ ] 适当的统计检验已选择
- [ ] 多重比较校正已应用（如需要）
- [ ] 效应量已计算

## 可视化
- [ ] 关键结果有对应图表
- [ ] 图表符合学术规范
- [ ] 图表文件格式正确

## 结果解读
- [ ] 统计显著性已正确解释
- [ ] 实际意义已讨论
- [ ] 局限性已说明

## 文档
- [ ] 分析报告已生成
- [ ] 结果已保存到 JSON/CSV
- [ ] 代码可复现
```

---

## 质量检查清单

在 Phase 5 完成后，确保：

### 数据处理
- [ ] 所有实验数据已汇总
- [ ] 数据清洗过程已记录
- [ ] 异常值已标记和处理

### 统计检验
- [ ] 检验方法选择正确
- [ ] 假设条件已验证
- [ ] p 值解释正确
- [ ] 多重比较已校正

### 效应量
- [ ] 效应量已计算
- [ ] 效应量解释合理
- [ ] 置信区间已报告

### 可视化
- [ ] 图表清晰易读
- [ ] 符合学术规范
- [ ] 文件命名规范

### 报告
- [ ] 结论基于数据
- [ ] 局限性已说明
- [ ] 可复现性已保证

---

## 常见问题

**Q: 如何选择参数检验还是非参数检验？**
A: 首先检验数据的正态性。如果数据符合正态分布且满足方差齐性，使用参数检验（t-test, ANOVA）；否则使用非参数检验（Mann-Whitney, Kruskal-Wallis）。

**Q: p 值小于 0.05 但效应量很小，如何解释？**
A: 统计显著性不等于实际重要性。大样本下即使很小的差异也可能显著。应同时报告效应量，讨论结果的实际意义。

**Q: 多次比较时如何控制 Type I 错误？**
A: 使用多重比较校正方法，如 Bonferroni 校正（保守）或 FDR 校正（较宽松）。根据研究目的选择适当的方法。

**Q: 数据不符合正态分布怎么办？**
A: 可以：(1) 使用非参数检验，(2) 对数据进行变换（如 log, sqrt），(3) 使用 Bootstrap 方法，(4) 使用稳健统计方法。

**Q: 如何处理缺失数据？**
A: 根据缺失机制选择：(1) 完全随机缺失 - 可删除或插补，(2) 随机缺失 - 多重插补，(3) 非随机缺失 - 需要建模处理。记录处理方法。

---

*完成此阶段后，系统将进入 Phase 6: 论文撰写*
