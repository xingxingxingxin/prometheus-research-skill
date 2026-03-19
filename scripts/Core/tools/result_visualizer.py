"""
实验结果可视化工具
==================

生成各类实验结果图表，支持多种图表类型和输出格式。
适用于科研项目的数据分析和结果展示。
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 检查依赖
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy 未安装，部分功能可能受限")

try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    import matplotlib.colors as mcolors
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib 未安装，可视化功能不可用")

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    logger.warning("Seaborn 未安装，部分高级可视化功能可能受限")


class ResultVisualizer:
    """实验结果可视化器"""

    # 支持的图表类型
    CHART_TYPES = ['line', 'bar', 'heatmap', 'scatter', 'box', 'violin', 'histogram']

    # 支持的输出格式
    OUTPUT_FORMATS = ['png', 'pdf', 'svg', 'eps']

    # 默认颜色方案
    DEFAULT_COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]

    def __init__(self, style: str = 'seaborn', font_size: int = 12):
        """
        初始化可视化器

        Args:
            style: 绘图风格 ('seaborn', 'ggplot', 'bmh', 'default')
            font_size: 基础字体大小
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib 是必需的依赖，请先安装: pip install matplotlib")

        self.style = style
        self.font_size = font_size
        self._setup_style()

    def _setup_style(self):
        """设置绘图风格"""
        available_styles = plt.style.available

        if self.style in available_styles:
            plt.style.use(self.style)
        elif 'seaborn-v0_8' in available_styles:
            plt.style.use('seaborn-v0_8')
        elif 'seaborn' in available_styles:
            plt.style.use('seaborn')
        else:
            plt.style.use('default')

        # 设置字体
        plt.rcParams['font.size'] = self.font_size
        plt.rcParams['axes.titlesize'] = self.font_size + 2
        plt.rcParams['axes.labelsize'] = self.font_size
        plt.rcParams['xtick.labelsize'] = self.font_size - 1
        plt.rcParams['ytick.labelsize'] = self.font_size - 1
        plt.rcParams['legend.fontsize'] = self.font_size - 1

        # 支持中文显示
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

    def line_plot(
        self,
        data: Union[Dict[str, List], List[Dict]],
        x_label: str = 'X',
        y_label: str = 'Y',
        title: str = '',
        output_path: Optional[str] = None,
        format: str = 'png',
        figsize: Tuple[float, float] = (10, 6),
        show_legend: bool = True,
        show_grid: bool = True,
        markers: bool = True,
        **kwargs
    ) -> Optional[Figure]:
        """
        绘制折线图

        Args:
            data: 数据，可以是 {'x': [...], 'y1': [...], 'y2': [...]} 或
                  [{'label': 'series1', 'x': [...], 'y': [...]}, ...]
            x_label: X轴标签
            y_label: Y轴标签
            title: 图表标题
            output_path: 输出文件路径
            format: 输出格式 ('png', 'pdf', 'svg', 'eps')
            figsize: 图表尺寸
            show_legend: 是否显示图例
            show_grid: 是否显示网格
            markers: 是否显示数据点标记
            **kwargs: 其他绘图参数

        Returns:
            matplotlib Figure 对象（如果未保存到文件）
        """
        fig, ax = plt.subplots(figsize=figsize)

        # 处理不同格式的输入数据
        if isinstance(data, dict):
            x = data.get('x', list(range(len(list(data.values())[0]))))
            for i, (key, values) in enumerate(data.items()):
                if key != 'x':
                    color = kwargs.get('colors', self.DEFAULT_COLORS)[i % len(self.DEFAULT_COLORS)]
                    ax.plot(x, values, label=key, marker='o' if markers else None,
                           color=color, linewidth=2)
        elif isinstance(data, list):
            for i, series in enumerate(data):
                x = series.get('x', list(range(len(series.get('y', [])))))
                y = series.get('y', [])
                label = series.get('label', f'Series {i+1}')
                color = series.get('color', self.DEFAULT_COLORS[i % len(self.DEFAULT_COLORS)])
                ax.plot(x, y, label=label, marker='o' if markers else None,
                       color=color, linewidth=2)

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)

        if show_legend:
            ax.legend()

        if show_grid:
            ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            self._save_figure(fig, output_path, format)
            plt.close(fig)
            return None

        return fig

    def bar_plot(
        self,
        data: Union[Dict[str, List], List[Dict]],
        x_label: str = 'Category',
        y_label: str = 'Value',
        title: str = '',
        output_path: Optional[str] = None,
        format: str = 'png',
        figsize: Tuple[float, float] = (10, 6),
        show_legend: bool = True,
        orientation: str = 'vertical',
        show_values: bool = False,
        **kwargs
    ) -> Optional[Figure]:
        """
        绘制柱状图

        Args:
            data: 数据，可以是 {'categories': [...], 'values': [...]} 或
                  {'categories': [...], 'series1': [...], 'series2': [...]}
            x_label: X轴标签
            y_label: Y轴标签
            title: 图表标题
            output_path: 输出文件路径
            format: 输出格式
            figsize: 图表尺寸
            show_legend: 是否显示图例
            orientation: 方向 ('vertical' 或 'horizontal')
            show_values: 是否在柱子上显示数值
            **kwargs: 其他绘图参数

        Returns:
            matplotlib Figure 对象（如果未保存到文件）
        """
        fig, ax = plt.subplots(figsize=figsize)

        if isinstance(data, dict):
            categories = data.get('categories', data.get('x', []))

            # 获取所有数据系列（排除categories/x）
            series_keys = [k for k in data.keys() if k not in ['categories', 'x']]
            n_series = len(series_keys)
            n_categories = len(categories)

            if n_series == 0:
                # 单系列数据
                values = data.get('values', data.get('y', []))
                if orientation == 'vertical':
                    bars = ax.bar(range(len(categories)), values,
                                  color=self.DEFAULT_COLORS[:len(categories)])
                    ax.set_xticks(range(len(categories)))
                    ax.set_xticklabels(categories, rotation=45, ha='right')
                else:
                    bars = ax.barh(range(len(categories)), values,
                                   color=self.DEFAULT_COLORS[:len(categories)])
                    ax.set_yticks(range(len(categories)))
                    ax.set_yticklabels(categories)

                if show_values:
                    self._add_bar_values(ax, bars, orientation)
            else:
                # 多系列数据
                x = np.arange(n_categories)
                width = 0.8 / n_series

                for i, key in enumerate(series_keys):
                    values = data[key]
                    offset = (i - n_series / 2 + 0.5) * width
                    if orientation == 'vertical':
                        bars = ax.bar(x + offset, values, width, label=key,
                                      color=self.DEFAULT_COLORS[i % len(self.DEFAULT_COLORS)])
                    else:
                        bars = ax.barh(x + offset, values, width, label=key,
                                       color=self.DEFAULT_COLORS[i % len(self.DEFAULT_COLORS)])

                if orientation == 'vertical':
                    ax.set_xticks(x)
                    ax.set_xticklabels(categories, rotation=45, ha='right')
                else:
                    ax.set_yticks(x)
                    ax.set_yticklabels(categories)

        if orientation == 'vertical':
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
        else:
            ax.set_xlabel(y_label)
            ax.set_ylabel(x_label)

        ax.set_title(title)

        if show_legend and n_series > 1:
            ax.legend()

        plt.tight_layout()

        if output_path:
            self._save_figure(fig, output_path, format)
            plt.close(fig)
            return None

        return fig

    def _add_bar_values(self, ax, bars, orientation: str):
        """在柱状图上添加数值标签"""
        for bar in bars:
            if orientation == 'vertical':
                height = bar.get_height()
                ax.annotate(f'{height:.2f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=9)
            else:
                width = bar.get_width()
                ax.annotate(f'{width:.2f}',
                           xy=(width, bar.get_y() + bar.get_height() / 2),
                           xytext=(3, 0),
                           textcoords="offset points",
                           ha='left', va='center', fontsize=9)

    def heatmap(
        self,
        data: Union[List[List], np.ndarray],
        x_labels: Optional[List[str]] = None,
        y_labels: Optional[List[str]] = None,
        title: str = '',
        output_path: Optional[str] = None,
        format: str = 'png',
        figsize: Tuple[float, float] = (10, 8),
        cmap: str = 'viridis',
        annot: bool = True,
        fmt: str = '.2f',
        show_colorbar: bool = True,
        **kwargs
    ) -> Optional[Figure]:
        """
        绘制热力图

        Args:
            data: 二维数据矩阵
            x_labels: X轴标签
            y_labels: Y轴标签
            title: 图表标题
            output_path: 输出文件路径
            format: 输出格式
            figsize: 图表尺寸
            cmap: 颜色映射
            annot: 是否显示数值
            fmt: 数值格式
            show_colorbar: 是否显示颜色条
            **kwargs: 其他绘图参数

        Returns:
            matplotlib Figure 对象（如果未保存到文件）
        """
        if not NUMPY_AVAILABLE:
            data = np.array(data) if isinstance(data, list) else data
        else:
            data = np.array(data) if not isinstance(data, np.ndarray) else data

        fig, ax = plt.subplots(figsize=figsize)

        if SEABORN_AVAILABLE:
            # 使用 Seaborn 绘制更好的热力图
            sns.heatmap(data, ax=ax, cmap=cmap, annot=annot, fmt=fmt,
                       xticklabels=x_labels, yticklabels=y_labels,
                       cbar=show_colorbar, **kwargs)
        else:
            # 使用 Matplotlib 基础功能
            im = ax.imshow(data, cmap=cmap, aspect='auto')

            if x_labels:
                ax.set_xticks(range(len(x_labels)))
                ax.set_xticklabels(x_labels, rotation=45, ha='right')
            if y_labels:
                ax.set_yticks(range(len(y_labels)))
                ax.set_yticklabels(y_labels)

            if annot:
                for i in range(data.shape[0]):
                    for j in range(data.shape[1]):
                        text = ax.text(j, i, format(data[i, j], fmt),
                                      ha="center", va="center", color="black")

            if show_colorbar:
                plt.colorbar(im, ax=ax)

        ax.set_title(title)
        plt.tight_layout()

        if output_path:
            self._save_figure(fig, output_path, format)
            plt.close(fig)
            return None

        return fig

    def scatter_plot(
        self,
        data: Union[Dict, List[Dict]],
        x_label: str = 'X',
        y_label: str = 'Y',
        title: str = '',
        output_path: Optional[str] = None,
        format: str = 'png',
        figsize: Tuple[float, float] = (10, 8),
        show_regression: bool = False,
        show_legend: bool = True,
        **kwargs
    ) -> Optional[Figure]:
        """
        绘制散点图

        Args:
            data: 数据，可以是 {'x': [...], 'y': [...]} 或
                  [{'label': 'group1', 'x': [...], 'y': [...]}, ...]
            x_label: X轴标签
            y_label: Y轴标签
            title: 图表标题
            output_path: 输出文件路径
            format: 输出格式
            figsize: 图表尺寸
            show_regression: 是否显示回归线
            show_legend: 是否显示图例
            **kwargs: 其他绘图参数

        Returns:
            matplotlib Figure 对象（如果未保存到文件）
        """
        fig, ax = plt.subplots(figsize=figsize)

        if isinstance(data, dict):
            x = data.get('x', [])
            y = data.get('y', [])
            sizes = data.get('sizes', None)
            colors = data.get('colors', None)

            scatter = ax.scatter(x, y, s=sizes, c=colors, alpha=0.6, **kwargs)

            if show_regression and NUMPY_AVAILABLE:
                self._add_regression_line(ax, x, y)

        elif isinstance(data, list):
            for i, group in enumerate(data):
                x = group.get('x', [])
                y = group.get('y', [])
                label = group.get('label', f'Group {i+1}')
                color = group.get('color', self.DEFAULT_COLORS[i % len(self.DEFAULT_COLORS)])
                marker = group.get('marker', 'o')

                ax.scatter(x, y, label=label, c=color, marker=marker, alpha=0.6, **kwargs)

                if show_regression and NUMPY_AVAILABLE:
                    self._add_regression_line(ax, x, y, color=color)

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

        if show_legend:
            ax.legend()

        plt.tight_layout()

        if output_path:
            self._save_figure(fig, output_path, format)
            plt.close(fig)
            return None

        return fig

    def _add_regression_line(self, ax, x, y, color='red'):
        """添加回归线"""
        try:
            x_arr = np.array(x)
            y_arr = np.array(y)

            # 线性回归
            z = np.polyfit(x_arr, y_arr, 1)
            p = np.poly1d(z)

            x_line = np.linspace(min(x_arr), max(x_arr), 100)
            ax.plot(x_line, p(x_line), '--', color=color, alpha=0.8, linewidth=2)
        except Exception:
            pass  # 回归失败时忽略

    def box_plot(
        self,
        data: Union[Dict[str, List], List[List]],
        labels: Optional[List[str]] = None,
        x_label: str = '',
        y_label: str = 'Value',
        title: str = '',
        output_path: Optional[str] = None,
        format: str = 'png',
        figsize: Tuple[float, float] = (10, 6),
        show_means: bool = True,
        **kwargs
    ) -> Optional[Figure]:
        """
        绘制箱线图

        Args:
            data: 数据，可以是 {'group1': [...], 'group2': [...]} 或 [[...], [...]]
            labels: 分组标签
            x_label: X轴标签
            y_label: Y轴标签
            title: 图表标题
            output_path: 输出文件路径
            format: 输出格式
            figsize: 图表尺寸
            show_means: 是否显示均值
            **kwargs: 其他绘图参数

        Returns:
            matplotlib Figure 对象（如果未保存到文件）
        """
        fig, ax = plt.subplots(figsize=figsize)

        if isinstance(data, dict):
            labels = labels or list(data.keys())
            values = list(data.values())
        else:
            values = data
            if labels is None:
                labels = [f'Group {i+1}' for i in range(len(values))]

        bp = ax.boxplot(values, labels=labels, showmeans=show_means,
                        patch_artist=True, **kwargs)

        # 设置颜色
        for patch, color in zip(bp['boxes'], self.DEFAULT_COLORS):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if output_path:
            self._save_figure(fig, output_path, format)
            plt.close(fig)
            return None

        return fig

    def histogram(
        self,
        data: List,
        bins: int = 30,
        x_label: str = 'Value',
        y_label: str = 'Frequency',
        title: str = '',
        output_path: Optional[str] = None,
        format: str = 'png',
        figsize: Tuple[float, float] = (10, 6),
        show_kde: bool = False,
        **kwargs
    ) -> Optional[Figure]:
        """
        绘制直方图

        Args:
            data: 数据列表
            bins: 分箱数量
            x_label: X轴标签
            y_label: Y轴标签
            title: 图表标题
            output_path: 输出文件路径
            format: 输出格式
            figsize: 图表尺寸
            show_kde: 是否显示核密度估计曲线
            **kwargs: 其他绘图参数

        Returns:
            matplotlib Figure 对象（如果未保存到文件）
        """
        fig, ax = plt.subplots(figsize=figsize)

        if SEABORN_AVAILABLE and show_kde:
            sns.histplot(data, bins=bins, kde=True, ax=ax, color=self.DEFAULT_COLORS[0], **kwargs)
        else:
            ax.hist(data, bins=bins, color=self.DEFAULT_COLORS[0], alpha=0.7, edgecolor='black', **kwargs)

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if output_path:
            self._save_figure(fig, output_path, format)
            plt.close(fig)
            return None

        return fig

    def multi_plot(
        self,
        plots: List[Dict],
        layout: Tuple[int, int] = None,
        title: str = '',
        output_path: Optional[str] = None,
        format: str = 'png',
        figsize: Tuple[float, float] = None,
        **kwargs
    ) -> Optional[Figure]:
        """
        绘制多子图

        Args:
            plots: 图表配置列表，每个元素包含:
                   - type: 图表类型
                   - data: 数据
                   - title: 子图标题
                   - 其他该类型图表支持的参数
            layout: 子图布局 (rows, cols)，默认自动计算
            title: 总标题
            output_path: 输出文件路径
            format: 输出格式
            figsize: 图表尺寸

        Returns:
            matplotlib Figure 对象（如果未保存到文件）
        """
        n_plots = len(plots)

        if layout is None:
            n_cols = min(3, n_plots)
            n_rows = (n_plots + n_cols - 1) // n_cols
        else:
            n_rows, n_cols = layout

        if figsize is None:
            figsize = (5 * n_cols, 4 * n_rows)

        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = np.atleast_1d(axes).flatten()

        for i, plot_config in enumerate(plots):
            if i >= len(axes):
                break

            ax = axes[i]
            plot_type = plot_config.pop('type', 'line')
            plot_data = plot_config.pop('data', None)
            plot_title = plot_config.pop('title', '')

            # 临时保存当前轴
            self._draw_single_plot(ax, plot_type, plot_data, **plot_config)
            ax.set_title(plot_title)

        # 隐藏多余的子图
        for i in range(n_plots, len(axes)):
            axes[i].set_visible(False)

        fig.suptitle(title, fontsize=self.font_size + 4)
        plt.tight_layout()

        if output_path:
            self._save_figure(fig, output_path, format)
            plt.close(fig)
            return None

        return fig

    def _draw_single_plot(self, ax, plot_type: str, data, **kwargs):
        """在指定轴上绘制单个图表"""
        if plot_type == 'line':
            if isinstance(data, dict):
                x = data.get('x', list(range(len(list(data.values())[0]))))
                for key, values in data.items():
                    if key != 'x':
                        ax.plot(x, values, label=key, marker='o')
            ax.legend()
            ax.grid(True, alpha=0.3)

        elif plot_type == 'bar':
            if isinstance(data, dict):
                categories = data.get('categories', data.get('x', []))
                values = data.get('values', data.get('y', []))
                ax.bar(range(len(categories)), values)
                ax.set_xticks(range(len(categories)))
                ax.set_xticklabels(categories, rotation=45, ha='right')

        elif plot_type == 'scatter':
            if isinstance(data, dict):
                x = data.get('x', [])
                y = data.get('y', [])
                ax.scatter(x, y, alpha=0.6)
            ax.grid(True, alpha=0.3)

        elif plot_type == 'histogram':
            if isinstance(data, list):
                ax.hist(data, bins=kwargs.get('bins', 30), alpha=0.7)
            ax.grid(True, alpha=0.3, axis='y')

    def _save_figure(self, fig: Figure, output_path: str, format: str):
        """保存图表到文件"""
        output_file = Path(output_path)

        # 确保目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 如果路径中没有扩展名，添加格式后缀
        if not output_file.suffix:
            output_file = output_file.with_suffix(f'.{format}')

        dpi = 300 if format == 'png' else None
        fig.savefig(output_file, format=format, dpi=dpi, bbox_inches='tight')
        logger.info(f"图表已保存到: {output_file}")

    def load_data(self, file_path: str) -> Any:
        """
        从文件加载数据

        Args:
            file_path: 数据文件路径 (支持 JSON, CSV)

        Returns:
            加载的数据
        """
        file_path = Path(file_path)

        if file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        elif file_path.suffix == '.csv':
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)

        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")

    def create_comparison_chart(
        self,
        methods: List[str],
        metrics: Dict[str, List[float]],
        output_path: str,
        title: str = 'Method Comparison',
        format: str = 'png'
    ) -> None:
        """
        创建方法对比图表（常用于论文）

        Args:
            methods: 方法名称列表
            metrics: 指标数据 {'metric_name': [values...]}
            output_path: 输出路径
            title: 图表标题
            format: 输出格式
        """
        n_metrics = len(metrics)
        n_methods = len(methods)

        fig, axes = plt.subplots(1, n_metrics, figsize=(5 * n_metrics, 5))
        if n_metrics == 1:
            axes = [axes]

        for ax, (metric_name, values) in zip(axes, metrics.items()):
            x = range(n_methods)
            bars = ax.bar(x, values, color=self.DEFAULT_COLORS[:n_methods])
            ax.set_xticks(x)
            ax.set_xticklabels(methods, rotation=45, ha='right')
            ax.set_ylabel(metric_name)
            ax.set_title(metric_name)

            # 添加数值标签
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                       f'{val:.3f}', ha='center', va='bottom', fontsize=9)

        fig.suptitle(title, fontsize=self.font_size + 4)
        plt.tight_layout()

        self._save_figure(fig, output_path, format)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description='实验结果可视化工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # 通用参数
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--output', '-o', help='输出文件路径')
    parent_parser.add_argument('--format', '-f', choices=['png', 'pdf', 'svg', 'eps'],
                               default='png', help='输出格式')
    parent_parser.add_argument('--title', '-t', default='', help='图表标题')
    parent_parser.add_argument('--x-label', default='X', help='X轴标签')
    parent_parser.add_argument('--y-label', default='Y', help='Y轴标签')
    parent_parser.add_argument('--width', type=float, default=10, help='图表宽度')
    parent_parser.add_argument('--height', type=float, default=6, help='图表高度')
    parent_parser.add_argument('--style', default='seaborn', help='绘图风格')
    parent_parser.add_argument('--data', '-d', help='数据文件路径 (JSON)')

    # 折线图命令
    line_parser = subparsers.add_parser('line', parents=[parent_parser], help='绘制折线图')
    line_parser.add_argument('--no-markers', action='store_true', help='不显示数据点标记')

    # 柱状图命令
    bar_parser = subparsers.add_parser('bar', parents=[parent_parser], help='绘制柱状图')
    bar_parser.add_argument('--horizontal', action='store_true', help='水平方向')
    bar_parser.add_argument('--show-values', action='store_true', help='显示数值')

    # 热力图命令
    heatmap_parser = subparsers.add_parser('heatmap', parents=[parent_parser], help='绘制热力图')
    heatmap_parser.add_argument('--cmap', default='viridis', help='颜色映射')
    heatmap_parser.add_argument('--no-annot', action='store_true', help='不显示数值')

    # 散点图命令
    scatter_parser = subparsers.add_parser('scatter', parents=[parent_parser], help='绘制散点图')
    scatter_parser.add_argument('--regression', action='store_true', help='显示回归线')

    # 箱线图命令
    box_parser = subparsers.add_parser('box', parents=[parent_parser], help='绘制箱线图')

    # 直方图命令
    hist_parser = subparsers.add_parser('histogram', parents=[parent_parser], help='绘制直方图')
    hist_parser.add_argument('--bins', type=int, default=30, help='分箱数量')
    hist_parser.add_argument('--kde', action='store_true', help='显示核密度估计')

    # 示例命令
    example_parser = subparsers.add_parser('example', help='生成示例图表')
    example_parser.add_argument('--output-dir', '-o', default='examples', help='输出目录')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 生成示例
    if args.command == 'example':
        generate_examples(args.output_dir)
        return

    # 从文件加载数据
    if args.data:
        visualizer = ResultVisualizer(style=args.style)
        data = visualizer.load_data(args.data)
    else:
        print("错误: 请使用 --data 参数指定数据文件")
        return

    figsize = (args.width, args.height)
    output_path = args.output or f"chart.{args.format}"

    visualizer = ResultVisualizer(style=args.style)

    # 根据命令执行相应操作
    if args.command == 'line':
        visualizer.line_plot(
            data, x_label=args.x_label, y_label=args.y_label,
            title=args.title, output_path=output_path, format=args.format,
            figsize=figsize, markers=not args.no_markers
        )

    elif args.command == 'bar':
        visualizer.bar_plot(
            data, x_label=args.x_label, y_label=args.y_label,
            title=args.title, output_path=output_path, format=args.format,
            figsize=figsize, orientation='horizontal' if args.horizontal else 'vertical',
            show_values=args.show_values
        )

    elif args.command == 'heatmap':
        visualizer.heatmap(
            data, title=args.title, output_path=output_path, format=args.format,
            figsize=figsize, cmap=args.cmap, annot=not args.no_annot
        )

    elif args.command == 'scatter':
        visualizer.scatter_plot(
            data, x_label=args.x_label, y_label=args.y_label,
            title=args.title, output_path=output_path, format=args.format,
            figsize=figsize, show_regression=args.regression
        )

    elif args.command == 'box':
        visualizer.box_plot(
            data, x_label=args.x_label, y_label=args.y_label,
            title=args.title, output_path=output_path, format=args.format,
            figsize=figsize
        )

    elif args.command == 'histogram':
        visualizer.histogram(
            data, bins=args.bins, x_label=args.x_label, y_label=args.y_label,
            title=args.title, output_path=output_path, format=args.format,
            figsize=figsize, show_kde=args.kde
        )


def generate_examples(output_dir: str):
    """生成示例图表"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    visualizer = ResultVisualizer()

    print("生成示例图表...")

    # 1. 折线图示例
    line_data = {
        'x': [1, 2, 3, 4, 5],
        'Method A': [0.5, 0.6, 0.72, 0.78, 0.82],
        'Method B': [0.45, 0.55, 0.65, 0.70, 0.75],
        'Baseline': [0.4, 0.42, 0.45, 0.47, 0.50]
    }
    visualizer.line_plot(
        line_data, x_label='Epoch', y_label='Accuracy',
        title='Training Progress',
        output_path=str(output_path / 'line_plot.png')
    )
    print("  - line_plot.png")

    # 2. 柱状图示例
    bar_data = {
        'categories': ['Task 1', 'Task 2', 'Task 3', 'Task 4'],
        'Our Method': [0.92, 0.88, 0.95, 0.90],
        'Baseline': [0.85, 0.82, 0.88, 0.84]
    }
    visualizer.bar_plot(
        bar_data, x_label='Task', y_label='Accuracy',
        title='Method Comparison',
        output_path=str(output_path / 'bar_plot.png')
    )
    print("  - bar_plot.png")

    # 3. 热力图示例
    if NUMPY_AVAILABLE:
        heatmap_data = np.random.rand(5, 5)
        visualizer.heatmap(
            heatmap_data,
            x_labels=['A', 'B', 'C', 'D', 'E'],
            y_labels=['Model 1', 'Model 2', 'Model 3', 'Model 4', 'Model 5'],
            title='Correlation Matrix',
            output_path=str(output_path / 'heatmap.png')
        )
        print("  - heatmap.png")

    # 4. 散点图示例
    if NUMPY_AVAILABLE:
        scatter_data = {
            'x': np.random.randn(50),
            'y': np.random.randn(50)
        }
        visualizer.scatter_plot(
            scatter_data, x_label='Feature 1', y_label='Feature 2',
            title='Feature Distribution',
            output_path=str(output_path / 'scatter_plot.png'),
            show_regression=True
        )
        print("  - scatter_plot.png")

    # 5. 箱线图示例
    box_data = {
        'Control': [1.2, 1.5, 1.3, 1.4, 1.6, 1.3, 1.5],
        'Treatment A': [1.8, 2.0, 1.9, 2.1, 1.7, 2.2, 1.8],
        'Treatment B': [2.1, 2.3, 2.0, 2.4, 2.2, 2.5, 2.1]
    }
    visualizer.box_plot(
        box_data, x_label='Group', y_label='Measurement',
        title='Experiment Results',
        output_path=str(output_path / 'box_plot.png')
    )
    print("  - box_plot.png")

    # 6. 直方图示例
    if NUMPY_AVAILABLE:
        hist_data = list(np.random.normal(0, 1, 1000))
        visualizer.histogram(
            hist_data, bins=50, x_label='Value', y_label='Frequency',
            title='Data Distribution',
            output_path=str(output_path / 'histogram.png'),
            show_kde=True
        )
        print("  - histogram.png")

    print(f"\n示例图表已生成到 {output_path} 目录")


if __name__ == "__main__":
    main()
