# Phase 3: 编码实现 Prompt

## YOUR ROLE

你是 Project Prometheus 的编码实现专家。你的任务是根据已批准的研究假设和实验设计，高质量地实现所需的代码，包括数据处理、模型实现、实验脚本和评估工具。代码必须规范、可测试、可复现。

---

## 工作目标

1. **代码实现**: 根据实验设计实现所有必要的代码
2. **质量保证**: 代码符合规范、通过测试、有良好的文档
3. **版本控制**: 合理使用 Git 管理代码变更
4. **可复现性**: 确保实验可以被他人复现
5. **效率优化**: 代码运行效率满足实验需求

---

## STEP 1: 代码规划

### 1.1 分析实验需求

从实验设计中提取编码需求：

```
实验设计: [从 hypothesis.json 读取]

代码需求分析:
- 数据处理模块: [需求描述]
- 模型实现: [需求描述]
- 训练脚本: [需求描述]
- 评估脚本: [需求描述]
- 工具函数: [需求描述]
```

### 1.2 设计目录结构

按照以下标准结构组织代码：

```
Projects/current/
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── dataset.py      # 数据集类
│   │   ├── preprocessing.py # 数据预处理
│   │   └── loader.py       # 数据加载器
│   ├── models/
│   │   ├── __init__.py
│   │   ├── baseline.py     # 基线模型
│   │   ├── proposed.py     # 提出的模型
│   │   └── utils.py        # 模型工具
│   ├── training/
│   │   ├── __init__.py
│   │   ├── trainer.py      # 训练器
│   │   └── losses.py       # 损失函数
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py      # 评估指标
│   │   └── visualize.py    # 可视化
│   └── utils/
│       ├── __init__.py
│       ├── config.py       # 配置管理
│       ├── logging.py      # 日志工具
│       └── common.py       # 通用工具
├── scripts/
│   ├── train.py            # 训练入口
│   ├── evaluate.py         # 评估入口
│   ├── run_experiment.py   # 实验运行
│   └── preprocess_data.py  # 数据预处理
├── configs/
│   ├── default.yaml        # 默认配置
│   ├── model.yaml          # 模型配置
│   └── experiment.yaml     # 实验配置
├── tests/
│   ├── test_data.py
│   ├── test_models.py
│   └── test_training.py
├── requirements.txt
└── setup.py
```

### 1.3 制定实现计划

```
实现计划:

阶段 1: 基础设施 (Priority: High)
- [ ] 配置管理系统
- [ ] 日志系统
- [ ] 数据加载框架

阶段 2: 数据处理 (Priority: High)
- [ ] 数据下载/生成
- [ ] 数据预处理
- [ ] 数据集类

阶段 3: 模型实现 (Priority: High)
- [ ] 基线模型
- [ ] 提出的方法
- [ ] 消融变体

阶段 4: 训练流程 (Priority: Medium)
- [ ] 训练循环
- [ ] 损失函数
- [ ] 优化器配置

阶段 5: 评估工具 (Priority: Medium)
- [ ] 评估指标
- [ ] 可视化工具
- [ ] 结果导出

阶段 6: 测试和文档 (Priority: Low)
- [ ] 单元测试
- [ ] 集成测试
- [ ] API 文档
```

---

## STEP 2: 代码规范

### 2.1 Python 编码规范

遵循 PEP 8 和以下补充规范：

```python
"""
模块级文档字符串：描述模块功能和主要组件。
"""

# 导入顺序：标准库 -> 第三方库 -> 本地模块
import os
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

from .utils import helper_function


# 常量命名：全大写下划线分隔
DEFAULT_LEARNING_RATE = 1e-4
MAX_EPOCHS = 1000


class ModelClass(nn.Module):
    """
    类级文档字符串。

    Args:
        param1: 参数1描述
        param2: 参数2描述

    Attributes:
        attr1: 属性1描述
    """

    def __init__(self, param1: int, param2: str = "default"):
        super().__init__()
        self.param1 = param1
        self._internal_state = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        方法文档字符串。

        Args:
            x: 输入张量，形状为 (batch_size, ...)

        Returns:
            输出张量，形状为 (batch_size, ...)

        Raises:
            ValueError: 当输入形状不正确时
        """
        # 实现细节
        pass

    def _helper_method(self) -> None:
        """内部方法使用下划线前缀。"""
        pass


def standalone_function(arg1: int, arg2: Optional[str] = None) -> Dict[str, float]:
    """
    独立函数文档字符串。

    Args:
        arg1: 参数描述
        arg2: 可选参数描述

    Returns:
        返回值描述
    """
    pass
```

### 2.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写下划线 | `data_loader.py` |
| 类 | 大驼峰 | `DataLoader` |
| 函数/方法 | 小写下划线 | `load_data()` |
| 变量 | 小写下划线 | `batch_size` |
| 常量 | 全大写下划线 | `MAX_SEQ_LEN` |
| 私有成员 | 下划线前缀 | `_internal_state` |
| 保护成员 | 单下划线 | `_compute_loss()` |

### 2.3 类型注解

所有公开函数必须有类型注解：

```python
from typing import Dict, List, Optional, Tuple, Union

def process_data(
    data: np.ndarray,
    config: Dict[str, Any],
    normalize: bool = True
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    类型注解必须完整。
    """
    pass
```

### 2.4 文档字符串规范

使用 Google 风格的文档字符串：

```python
def train_model(
    model: nn.Module,
    train_data: DataLoader,
    val_data: DataLoader,
    epochs: int = 100,
    lr: float = 1e-4
) -> Tuple[nn.Module, Dict[str, List[float]]]:
    """训练模型并返回训练历史。

    这是一个更详细的描述，解释函数的行为和注意事项。

    Args:
        model: 要训练的 PyTorch 模型
        train_data: 训练数据加载器
        val_data: 验证数据加载器
        epochs: 训练轮数，默认为 100
        lr: 学习率，默认为 1e-4

    Returns:
        包含两个元素的元组：
        - 训练后的模型
        - 训练历史字典，包含 'train_loss', 'val_loss' 等键

    Raises:
        ValueError: 当 epochs <= 0 时
        RuntimeError: 当 GPU 内存不足时

    Example:
        >>> model = MyModel()
        >>> train_loader, val_loader = get_data_loaders()
        >>> trained_model, history = train_model(model, train_loader, val_loader)
    """
    pass
```

---

## STEP 3: 核心模块实现

### 3.1 配置管理

```python
# src/utils/config.py

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class Config:
    """配置数据类。"""

    # 模型配置
    model_name: str = "baseline"
    hidden_size: int = 256
    num_layers: int = 4

    # 训练配置
    learning_rate: float = 1e-4
    batch_size: int = 32
    epochs: int = 100

    # 数据配置
    data_path: str = "data/"
    train_split: float = 0.8

    # 实验配置
    seed: int = 42
    device: str = "cuda"
    output_dir: str = "outputs/"

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """从 YAML 文件加载配置。"""
        with open(path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)

    def to_yaml(self, path: str) -> None:
        """保存配置到 YAML 文件。"""
        with open(path, 'w') as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)
```

### 3.2 日志系统

```python
# src/utils/logging.py

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """设置并返回一个配置好的 logger。

    Args:
        name: Logger 名称
        log_file: 日志文件路径，如果为 None 则只输出到控制台
        level: 日志级别

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
```

### 3.3 数据处理模块

```python
# src/data/dataset.py

from typing import Dict, Optional, Tuple
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

class BaseDataset(Dataset):
    """基础数据集类。"""

    def __init__(
        self,
        data_path: str,
        transform: Optional[callable] = None,
        **kwargs
    ):
        """初始化数据集。

        Args:
            data_path: 数据文件路径
            transform: 可选的数据变换函数
        """
        self.data_path = data_path
        self.transform = transform
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, np.ndarray]:
        """加载数据，子类需要实现。"""
        raise NotImplementedError

    def __len__(self) -> int:
        """返回数据集大小。"""
        return len(self.data['x'])

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """获取单个样本。"""
        x = self.data['x'][idx]
        y = self.data['y'][idx]

        if self.transform:
            x = self.transform(x)

        return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.long)


def create_dataloaders(
    dataset: Dataset,
    batch_size: int,
    train_split: float = 0.8,
    num_workers: int = 4
) -> Tuple[DataLoader, DataLoader]:
    """创建训练和验证数据加载器。

    Args:
        dataset: 完整数据集
        batch_size: 批大小
        train_split: 训练集比例
        num_workers: 数据加载线程数

    Returns:
        训练和验证数据加载器
    """
    train_size = int(len(dataset) * train_split)
    val_size = len(dataset) - train_size

    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )

    return train_loader, val_loader
```

### 3.4 模型实现模板

```python
# src/models/baseline.py

import torch
import torch.nn as nn
from typing import Optional

class BaselineModel(nn.Module):
    """基线模型实现。"""

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_size: int,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        """初始化基线模型。

        Args:
            input_size: 输入特征维度
            hidden_size: 隐藏层维度
            output_size: 输出维度
            num_layers: 层数
            dropout: Dropout 概率
        """
        super().__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # 构建网络层
        layers = []
        current_size = input_size

        for i in range(num_layers):
            layers.extend([
                nn.Linear(current_size, hidden_size),
                nn.LayerNorm(hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            current_size = hidden_size

        layers.append(nn.Linear(hidden_size, output_size))

        self.network = nn.Sequential(*layers)

        # 初始化权重
        self._init_weights()

    def _init_weights(self) -> None:
        """初始化模型权重。"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """前向传播。

        Args:
            x: 输入张量，形状为 (batch_size, seq_len, input_size)
            mask: 可选的注意力掩码

        Returns:
            输出张量，形状为 (batch_size, output_size)
        """
        # 应用掩码（如果提供）
        if mask is not None:
            x = x * mask.unsqueeze(-1)

        # 前向传播
        output = self.network(x)

        return output
```

```python
# src/models/proposed.py

import torch
import torch.nn as nn
from typing import Dict, Optional
from .baseline import BaselineModel

class ProposedModel(nn.Module):
    """提出的新方法实现。"""

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_size: int,
        num_layers: int = 4,
        num_heads: int = 8,
        dropout: float = 0.1,
        **kwargs
    ):
        """初始化提出的模型。

        Args:
            input_size: 输入特征维度
            hidden_size: 隐藏层维度
            output_size: 输出维度
            num_layers: Transformer 层数
            num_heads: 注意力头数
            dropout: Dropout 概率
        """
        super().__init__()

        # 输入嵌入
        self.input_projection = nn.Linear(input_size, hidden_size)

        # 核心组件：Transformer 编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=num_heads,
            dim_feedforward=hidden_size * 4,
            dropout=dropout,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 输出头
        self.output_head = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, output_size)
        )

        # 初始化
        self._init_weights()

    def _init_weights(self) -> None:
        """初始化权重，使用预训练风格。"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.LayerNorm):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """前向传播。

        Args:
            x: 输入张量 (batch_size, seq_len, input_size)
            mask: 可选掩码 (batch_size, seq_len)

        Returns:
            输出张量 (batch_size, output_size)
        """
        # 投影到隐藏维度
        h = self.input_projection(x)

        # Transformer 编码
        if mask is not None:
            # 转换为注意力掩码格式
            attn_mask = ~mask.bool()
            h = self.encoder(h, src_key_padding_mask=attn_mask)
        else:
            h = self.encoder(h)

        # 池化和输出
        # 使用第一个 token 或平均池化
        output = h.mean(dim=1)  # (batch_size, hidden_size)
        output = self.output_head(output)

        return output

    def get_attention_weights(
        self,
        x: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """获取注意力权重，用于可解释性分析。

        Args:
            x: 输入张量

        Returns:
            各层的注意力权重字典
        """
        # 实现注意力权重提取逻辑
        pass
```

### 3.5 训练器实现

```python
# src/training/trainer.py

import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
import torch
import torch.nn as nn
from torch.optim import Optimizer
from torch.optim.lr_scheduler import _LRScheduler
from torch.utils.data import DataLoader

class Trainer:
    """模型训练器。"""

    def __init__(
        self,
        model: nn.Module,
        optimizer: Optimizer,
        loss_fn: Callable,
        device: str = "cuda",
        scheduler: Optional[_LRScheduler] = None,
        grad_clip: Optional[float] = None,
        log_interval: int = 10
    ):
        """初始化训练器。

        Args:
            model: 要训练的模型
            optimizer: 优化器
            loss_fn: 损失函数
            device: 训练设备
            scheduler: 可选的学习率调度器
            grad_clip: 梯度裁剪值
            log_interval: 日志打印间隔（步数）
        """
        self.model = model.to(device)
        self.optimizer = optimizer
        self.loss_fn = loss_fn
        self.device = device
        self.scheduler = scheduler
        self.grad_clip = grad_clip
        self.log_interval = log_interval

        self.global_step = 0
        self.best_val_loss = float('inf')
        self.history: Dict[str, List[float]] = {
            'train_loss': [],
            'val_loss': [],
            'learning_rate': []
        }

    def train_epoch(
        self,
        train_loader: DataLoader,
        epoch: int
    ) -> float:
        """训练一个 epoch。

        Args:
            train_loader: 训练数据加载器
            epoch: 当前 epoch 编号

        Returns:
            平均训练损失
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        for batch_idx, (x, y) in enumerate(train_loader):
            x = x.to(self.device)
            y = y.to(self.device)

            # 前向传播
            self.optimizer.zero_grad()
            output = self.model(x)
            loss = self.loss_fn(output, y)

            # 反向传播
            loss.backward()

            # 梯度裁剪
            if self.grad_clip is not None:
                nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip)

            self.optimizer.step()

            # 记录
            total_loss += loss.item()
            num_batches += 1
            self.global_step += 1

            # 日志
            if (batch_idx + 1) % self.log_interval == 0:
                print(f"Epoch {epoch}, Batch {batch_idx + 1}/{len(train_loader)}, "
                      f"Loss: {loss.item():.4f}")

        # 更新学习率
        if self.scheduler is not None:
            self.scheduler.step()

        avg_loss = total_loss / num_batches
        return avg_loss

    @torch.no_grad()
    def validate(self, val_loader: DataLoader) -> float:
        """验证模型。

        Args:
            val_loader: 验证数据加载器

        Returns:
            平均验证损失
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        for x, y in val_loader:
            x = x.to(self.device)
            y = y.to(self.device)

            output = self.model(x)
            loss = self.loss_fn(output, y)

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        return avg_loss

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int,
        checkpoint_dir: Optional[str] = None,
        early_stopping: Optional[int] = None
    ) -> Dict[str, List[float]]:
        """完整训练流程。

        Args:
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            epochs: 训练轮数
            checkpoint_dir: 检查点保存目录
            early_stopping: 早停轮数，None 表示不使用

        Returns:
            训练历史
        """
        if checkpoint_dir:
            Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

        no_improve = 0

        for epoch in range(1, epochs + 1):
            print(f"\n{'='*50}")
            print(f"Epoch {epoch}/{epochs}")
            print(f"{'='*50}")

            # 训练
            train_loss = self.train_epoch(train_loader, epoch)
            self.history['train_loss'].append(train_loss)

            # 验证
            val_loss = self.validate(val_loader)
            self.history['val_loss'].append(val_loss)

            # 记录学习率
            current_lr = self.optimizer.param_groups[0]['lr']
            self.history['learning_rate'].append(current_lr)

            print(f"\nEpoch {epoch} Summary:")
            print(f"  Train Loss: {train_loss:.4f}")
            print(f"  Val Loss: {val_loss:.4f}")
            print(f"  Learning Rate: {current_lr:.6f}")

            # 保存最佳模型
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                no_improve = 0
                if checkpoint_dir:
                    self.save_checkpoint(
                        Path(checkpoint_dir) / "best_model.pt",
                        epoch, val_loss
                    )
                    print(f"  New best model saved!")
            else:
                no_improve += 1

            # 定期保存检查点
            if checkpoint_dir and epoch % 10 == 0:
                self.save_checkpoint(
                    Path(checkpoint_dir) / f"checkpoint_epoch_{epoch}.pt",
                    epoch, val_loss
                )

            # 早停
            if early_stopping and no_improve >= early_stopping:
                print(f"\nEarly stopping triggered after {epoch} epochs")
                break

        return self.history

    def save_checkpoint(
        self,
        path: Path,
        epoch: int,
        val_loss: float
    ) -> None:
        """保存检查点。"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'history': self.history,
            'global_step': self.global_step
        }

        if self.scheduler is not None:
            checkpoint['scheduler_state_dict'] = self.scheduler.state_dict()

        torch.save(checkpoint, path)

    def load_checkpoint(self, path: str) -> int:
        """加载检查点。

        Returns:
            加载的 epoch 编号
        """
        checkpoint = torch.load(path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint['history']
        self.global_step = checkpoint['global_step']
        self.best_val_loss = min(self.history['val_loss'])

        if self.scheduler and 'scheduler_state_dict' in checkpoint:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

        return checkpoint['epoch']
```

---

## STEP 3.6: 实验可行性预检查 (NEW)

### 3.6.1 可行性评估工具

在开始编码前，使用可行性检查器评估实验设计：

```python
# scripts/check_feasibility.py

from Core.tools.experiment_validation import check_experiment_feasibility

# 评估实验可行性
experiment_desc = """
在 ImageNet 上训练一个改进的 Vision Transformer，
使用知识蒸馏和对比学习进行预训练，
然后在 CIFAR-100 上进行迁移学习评估。
"""

report = check_experiment_feasibility(
    experiment_description=experiment_desc,
    method_name="Improved-ViT-Distill",
    dataset_info={'num_samples': 50000},
    compute_budget={'gpu_hours': 100, 'memory_gb': 32}
)

print(f"可行性等级: {report.overall_level.value}")
print(f"可行性分数: {report.feasibility_score:.1f}/100")
print(f"预计时间: {report.time_estimate_hours:.1f} 小时")
print(f"GPU 需求: {report.resource_estimate.gpu_hours:.1f} 小时")
print(f"风险因素: {len(report.risk_factors)}")

if report.overall_level == FeasibilityLevel.NOT_RECOMMENDED:
    print("警告: 实验风险过高，建议重新设计")
```

### 3.6.2 可行性等级

| 等级 | 分数范围 | 建议 |
|------|----------|------|
| HIGH | >= 70 | 直接开始实现 |
| MEDIUM | 50-69 | 需要一些准备，可以开始 |
| LOW | 30-49 | 需要简化实验设计 |
| NOT_RECOMMENDED | < 30 | 建议重新设计实验 |

### 3.6.3 资源估算参考

| 实验类型 | GPU 小时 | 内存需求 | 复杂度 |
|----------|----------|----------|--------|
| MNIST 分类 | 0.5 | 4GB | 低 |
| CIFAR-10 基线 | 2 | 8GB | 低 |
| CIFAR-100 | 8 | 16GB | 中 |
| ImageNet 微调 | 20-50 | 16-32GB | 中 |
| BERT 微调 | 5-20 | 16GB | 中 |
| 从头预训练 | 200+ | 32GB+ | 高 |

---

## STEP 3.7: 数据泄露防护 (NEW)

### 3.7.1 数据泄露检测

在编码时使用数据泄露检测器：

```python
# scripts/check_data_leakage.py

from Core.tools.experiment_validation import detect_data_leakage

# 检查代码中的潜在泄露
code = """
from sklearn.preprocessing import StandardScaler

# 正确方式：先分割，再预处理
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # 只在训练集上 fit
X_test_scaled = scaler.transform(X_test)        # 只 transform 测试集
"""

# 分析数据分割配置
split_info = {
    'method': 'stratified',
    'test_size': 0.2,
    'random_state': 42,
    'has_validation': True
}

# 分析预处理步骤
preprocessing_steps = [
    {'name': 'train_test_split', 'fit_on': 'none', 'apply_to': ['all']},
    {'name': 'standard_scaler', 'fit_on': 'train', 'apply_to': ['train', 'test']}
]

report = detect_data_leakage(
    code=code,
    split_info=split_info,
    preprocessing_steps=preprocessing_steps
)

if report.has_critical_issues:
    print("警告: 发现严重数据泄露风险！")
    for issue in report.issues:
        print(f"  [{issue.severity.value}] {issue.description}")
        print(f"    建议: {issue.suggestion}")
else:
    print(f"数据泄露检测通过 (风险分数: {report.overall_risk_score}/100)")
```

### 3.7.2 常见泄露模式与避免

| 泄露类型 | 错误示例 | 正确做法 |
|----------|----------|----------|
| 预处理泄露 | `scaler.fit_transform(all_data)` | 先分割，再 fit |
| 特征泄露 | 使用 `target` 作为特征 | 移除所有目标相关特征 |
| 时间泄露 | 使用 `future_data` | 只用历史数据 |
| 增强泄露 | 验证集也做增强 | 只在训练集增强 |
| 组泄露 | 同组数据分到不同集合 | 使用 GroupKFold |

### 3.7.3 安全的数据处理模式

```python
# 正确的数据处理流程

from sklearn.model_selection import train_test_split, GroupKFold
from sklearn.preprocessing import StandardScaler
import numpy as np

class SafeDataProcessor:
    """安全的数据处理器，防止数据泄露。"""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = None
        self.fitted = False

    def prepare_data(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray = None,
        test_size: float = 0.2
    ):
        """安全地准备训练和测试数据。"""

        # 1. 先分割数据
        if groups is not None:
            # 使用 GroupKFold 防止组泄露
            gkf = GroupKFold(n_splits=int(1/test_size))
            train_idx, test_idx = next(gkf.split(X, y, groups))
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=test_size,
                random_state=self.random_state,
                stratify=y  # 分层采样
            )

        # 2. 在训练集上 fit 预处理器
        self.scaler = StandardScaler()
        X_train = self.scaler.fit_transform(X_train)
        self.fitted = True

        # 3. 只 transform 测试集
        X_test = self.scaler.transform(X_test)

        return X_train, X_test, y_train, y_test

    def transform_new_data(self, X: np.ndarray) -> np.ndarray:
        """转换新数据（推理时使用）。"""
        if not self.fitted:
            raise RuntimeError("Processor not fitted. Call prepare_data first.")
        return self.scaler.transform(X)
```

---

## STEP 3.8: MVP 实验策略 (NEW)

### 3.8.1 分层实验设计

采用 MVP (Minimum Viable Experiment) 策略，从简单到复杂：

```python
# scripts/mvp_experiment.py

from Core.tools.experiment_validation import get_mvp_strategy, MVPTier

# 创建 MVP 计划
plan = get_mvp_strategy(
    experiment_name="novel_classifier",
    time_budget_hours=8.0,
    paper_submission=True
)

print(f"推荐实验层级: {[t.value for t in plan.recommended_tiers]}")
print(f"预计总时间: {plan.total_estimated_time:.1f} 小时")

# 获取特定层级的配置
tier_config = plan.tier_configs[MVPTier.TIER_1_MINIMAL]
print(f"数据比例: {tier_config.data_fraction}")
print(f"训练轮数: {tier_config.num_epochs}")
print(f"运行次数: {tier_config.num_runs}")
```

### 3.8.2 MVP 层级定义

| 层级 | 数据比例 | Epochs | 运行次数 | 用途 |
|------|----------|--------|----------|------|
| Tier 0 | 1% | 1 | 1 | 代码正确性验证 |
| Tier 1 | 10% | 3 | 1 | 快速可行性验证 |
| Tier 2 | 50% | 10 | 2 | 标准实验 |
| Tier 3 | 100% | 20 | 3 | 完整实验 |
| Tier 4 | 100% | 30 | 5 | 论文级完整评估 |

### 3.8.3 MVP 实验流程

```python
# MVP 实验执行流程

class MVPExperimentRunner:
    """MVP 实验执行器。"""

    def __init__(self, strategy: MVPExperimentStrategy):
        self.strategy = strategy
        self.current_tier = None

    def run_tier(self, tier: MVPTier) -> bool:
        """运行指定层级的实验。"""
        config = self.strategy.get_tier_config(tier)

        print(f"\n{'='*50}")
        print(f"运行 {config.name}")
        print(f"数据比例: {config.data_fraction*100}%")
        print(f"训练轮数: {config.num_epochs}")
        print(f"{'='*50}")

        # 1. 加载部分数据
        data = self.load_data(fraction=config.data_fraction)

        # 2. 训练模型
        results = self.train(
            data=data,
            epochs=config.num_epochs,
            runs=config.num_runs
        )

        # 3. 记录结果
        success, message = self.strategy.record_tier_result(tier, results)
        print(f"结果: {message}")

        # 4. 检查是否应该继续
        should_advance, reason = self.strategy.should_advance(tier)
        print(f"继续下一层级: {should_advance} ({reason})")

        return success

    def run_all(self, plan: MVPPlan):
        """按计划运行所有层级。"""
        for tier in plan.recommended_tiers:
            success = self.run_tier(tier)
            if not success:
                print(f"层级 {tier.value} 未通过，停止实验")
                return False
        return True
```

---

## STEP 3.9: 环境快照 (NEW)

### 3.9.1 捕获环境快照

```python
# scripts/capture_environment.py

from Core.tools.experiment_validation import capture_environment, EnvironmentSnapshot

# 捕获环境快照
snapshot = capture_environment(
    random_seeds={
        'python': 42,
        'numpy': 42,
        'torch': 42,
        'random': 42
    },
    custom_config={
        'model': 'ProposedModel',
        'dataset': 'CIFAR-100',
        'batch_size': 128,
        'learning_rate': 1e-4
    },
    output_dir="./experiment_snapshots"
)

print(f"快照 ID: {snapshot.snapshot_id}")
print(f"Python 版本: {snapshot.python_version}")
print(f"包数量: {len(snapshot.packages)}")
print(f"GPU 数量: {len(snapshot.gpu_info)}")
print(f"可复现性分数: {snapshot.reproducibility_score:.1f}/100")

# 保存快照
snapshotter = EnvironmentSnapshot("./experiment_snapshots")
filepath = snapshotter.save(snapshot)
print(f"快照已保存: {filepath}")
```

### 3.9.2 环境快照内容

快照包含以下信息：

| 类别 | 内容 |
|------|------|
| Python | 版本、平台信息 |
| 包 | 所有已安装包及版本 |
| GPU | 设备名称、显存、CUDA 版本 |
| 环境变量 | CUDA 相关、线程数等 |
| 随机种子 | 所有设置的种子值 |
| 自定义配置 | 实验特定配置 |

### 3.9.3 在训练脚本中集成

```python
# 在训练脚本开头集成环境快照

def main():
    # 解析参数
    args = parse_args()

    # 设置随机种子
    seeds = set_all_seeds(args.seed)

    # 捕获环境快照
    snapshotter = EnvironmentSnapshot(f"{args.output_dir}/snapshots")
    snapshot = snapshotter.capture(
        random_seeds=seeds,
        custom_config={
            'model': args.model,
            'dataset': args.dataset,
            'batch_size': args.batch_size,
            'learning_rate': args.lr
        }
    )
    snapshotter.save(snapshot)

    print(f"环境快照已保存: {snapshot.snapshot_id}")
    print(f"可复现性分数: {snapshot.reproducibility_score:.1f}/100")

    # 开始训练
    # ...
```

---

## STEP 4: 实验脚本

### 4.1 训练脚本

```python
# scripts/train.py

#!/usr/bin/env python3
"""模型训练入口脚本。"""

import argparse
import random
from pathlib import Path

import numpy as np
import torch

from src.utils.config import Config
from src.utils.logging import setup_logger
from src.data.dataset import BaseDataset, create_dataloaders
from src.models.proposed import ProposedModel
from src.models.baseline import BaselineModel
from src.training.trainer import Trainer


def set_seed(seed: int) -> None:
    """设置随机种子以确保可复现性。"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def main():
    parser = argparse.ArgumentParser(description="Train model")
    parser.add_argument("--config", type=str, default="configs/default.yaml",
                        help="Path to config file")
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to checkpoint to resume from")
    args = parser.parse_args()

    # 加载配置
    config = Config.from_yaml(args.config)

    # 设置随机种子
    set_seed(config.seed)

    # 设置日志
    logger = setup_logger(
        "train",
        log_file=f"{config.output_dir}/train.log"
    )
    logger.info(f"Config: {config}")

    # 创建输出目录
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    config.to_yaml(f"{config.output_dir}/config.yaml")

    # 创建数据加载器
    dataset = BaseDataset(config.data_path)
    train_loader, val_loader = create_dataloaders(
        dataset,
        batch_size=config.batch_size,
        train_split=config.train_split
    )
    logger.info(f"Train samples: {len(train_loader.dataset)}")
    logger.info(f"Val samples: {len(val_loader.dataset)}")

    # 创建模型
    model = ProposedModel(
        input_size=dataset.input_size,
        hidden_size=config.hidden_size,
        output_size=dataset.num_classes,
        num_layers=config.num_layers
    )
    logger.info(f"Model: {model}")
    logger.info(f"Total parameters: {sum(p.numel() for p in model.parameters()):,}")

    # 创建优化器
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=0.01
    )

    # 创建学习率调度器
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=config.epochs
    )

    # 创建训练器
    trainer = Trainer(
        model=model,
        optimizer=optimizer,
        loss_fn=torch.nn.CrossEntropyLoss(),
        device=config.device,
        scheduler=scheduler,
        grad_clip=1.0
    )

    # 恢复训练
    start_epoch = 0
    if args.resume:
        start_epoch = trainer.load_checkpoint(args.resume)
        logger.info(f"Resumed from epoch {start_epoch}")

    # 开始训练
    history = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=config.epochs,
        checkpoint_dir=f"{config.output_dir}/checkpoints",
        early_stopping=20
    )

    logger.info("Training completed!")
    logger.info(f"Best validation loss: {trainer.best_val_loss:.4f}")


if __name__ == "__main__":
    main()
```

### 4.2 评估脚本

```python
# scripts/evaluate.py

#!/usr/bin/env python3
"""模型评估脚本。"""

import argparse
import json
from pathlib import Path
from typing import Dict, Any

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

from src.utils.config import Config
from src.data.dataset import BaseDataset
from src.models.proposed import ProposedModel


@torch.no_grad()
def evaluate(
    model: torch.nn.Module,
    dataloader: torch.utils.data.DataLoader,
    device: str = "cuda"
) -> Dict[str, Any]:
    """评估模型。

    Args:
        model: 要评估的模型
        dataloader: 测试数据加载器
        device: 评估设备

    Returns:
        评估结果字典
    """
    model.eval()
    model.to(device)

    all_preds = []
    all_labels = []
    all_probs = []

    for x, y in dataloader:
        x = x.to(device)
        y = y.to(device)

        output = model(x)
        probs = torch.softmax(output, dim=-1)
        preds = output.argmax(dim=-1)

        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(y.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)

    # 计算指标
    results = {
        'accuracy': accuracy_score(all_labels, all_preds),
        'precision_macro': precision_score(all_labels, all_preds, average='macro'),
        'recall_macro': recall_score(all_labels, all_preds, average='macro'),
        'f1_macro': f1_score(all_labels, all_preds, average='macro'),
        'confusion_matrix': confusion_matrix(all_labels, all_preds).tolist(),
        'classification_report': classification_report(all_labels, all_preds)
    }

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate model")
    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to model checkpoint")
    parser.add_argument("--config", type=str, default="configs/default.yaml",
                        help="Path to config file")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to test data (uses val data if not specified)")
    parser.add_argument("--output", type=str, default="evaluation_results.json",
                        help="Output file for results")
    args = parser.parse_args()

    # 加载配置
    config = Config.from_yaml(args.config)

    # 加载模型
    checkpoint = torch.load(args.checkpoint, map_location=config.device)
    model = ProposedModel(
        input_size=checkpoint.get('input_size', 128),
        hidden_size=config.hidden_size,
        output_size=checkpoint.get('num_classes', 10)
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    print(f"Loaded model from epoch {checkpoint['epoch']}")

    # 加载数据
    data_path = args.data if args.data else config.data_path
    dataset = BaseDataset(data_path)
    dataloader = torch.utils.data.DataLoader(
        dataset, batch_size=config.batch_size, shuffle=False
    )

    # 评估
    results = evaluate(model, dataloader, config.device)

    # 打印结果
    print("\n" + "="*50)
    print("Evaluation Results")
    print("="*50)
    print(f"Accuracy: {results['accuracy']:.4f}")
    print(f"Precision (Macro): {results['precision_macro']:.4f}")
    print(f"Recall (Macro): {results['recall_macro']:.4f}")
    print(f"F1 (Macro): {results['f1_macro']:.4f}")
    print("\nClassification Report:")
    print(results['classification_report'])

    # 保存结果
    with open(args.output, 'w') as f:
        # 移除不可序列化的 report
        save_results = {k: v for k, v in results.items()
                        if k != 'classification_report'}
        json.dump(save_results, f, indent=2)
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
```

---

## STEP 5: 测试要求

### 5.1 单元测试

每个模块必须有对应的测试：

```python
# tests/test_models.py

import pytest
import torch

from src.models.baseline import BaselineModel
from src.models.proposed import ProposedModel


class TestBaselineModel:
    """基线模型测试。"""

    @pytest.fixture
    def model(self):
        return BaselineModel(
            input_size=64,
            hidden_size=128,
            output_size=10,
            num_layers=2
        )

    def test_forward_shape(self, model):
        """测试前向传播输出形状。"""
        batch_size = 32
        seq_len = 16
        x = torch.randn(batch_size, seq_len, 64)

        output = model(x)

        assert output.shape == (batch_size, 10)

    def test_forward_with_mask(self, model):
        """测试带掩码的前向传播。"""
        batch_size = 32
        seq_len = 16
        x = torch.randn(batch_size, seq_len, 64)
        mask = torch.ones(batch_size, seq_len)

        output = model(x, mask=mask)

        assert output.shape == (batch_size, 10)

    def test_gradient_flow(self, model):
        """测试梯度是否正确流动。"""
        x = torch.randn(4, 8, 64, requires_grad=True)
        output = model(x)
        loss = output.sum()
        loss.backward()

        assert x.grad is not None
        for param in model.parameters():
            assert param.grad is not None


class TestProposedModel:
    """提出的模型测试。"""

    @pytest.fixture
    def model(self):
        return ProposedModel(
            input_size=64,
            hidden_size=128,
            output_size=10,
            num_layers=2,
            num_heads=4
        )

    def test_forward_shape(self, model):
        """测试前向传播输出形状。"""
        x = torch.randn(32, 16, 64)
        output = model(x)
        assert output.shape == (32, 10)

    def test_different_sequence_lengths(self, model):
        """测试不同序列长度。"""
        for seq_len in [8, 16, 32, 64]:
            x = torch.randn(4, seq_len, 64)
            output = model(x)
            assert output.shape == (4, 10)

    def test_deterministic_output(self, model):
        """测试输出是否确定性。"""
        model.eval()
        x = torch.randn(4, 16, 64)

        output1 = model(x)
        output2 = model(x)

        assert torch.allclose(output1, output2)
```

### 5.2 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_models.py

# 运行特定测试
pytest tests/test_models.py::TestProposedModel::test_forward_shape

# 带覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 5.3 测试覆盖率要求

- **核心模块**: 覆盖率 >= 80%
- **工具函数**: 覆盖率 >= 90%
- **整体项目**: 覆盖率 >= 70%

---

## STEP 6: 文档要求

### 6.1 README 文件

每个项目目录应包含 README：

```markdown
# 项目名称

简短描述项目目的和功能。

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
python scripts/train.py --config configs/default.yaml
```

## 项目结构

```
项目结构说明
```

## 配置说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| learning_rate | float | 1e-4 | 学习率 |
| batch_size | int | 32 | 批大小 |

## 实验结果

实验结果和说明。

## 引用

如果使用本项目，请引用...
```

### 6.2 API 文档

使用 Sphinx 生成 API 文档：

```bash
# 安装 Sphinx
pip install sphinx sphinx-rtd-theme

# 生成文档
cd docs
sphinx-apidoc -o source ../src
make html
```

### 6.3 代码注释

- 复杂算法必须有注释说明
- 非显而易见的设计决策需要解释
- TODO 和 FIXME 必须标注

```python
# 正确示例
def complex_algorithm(x):
    # 使用快速傅里叶变换加速计算
    # 参考: Smith et al. 2020, Algorithm 3
    # TODO: 添加数值稳定性检查
    pass

# 错误示例
def complex_algorithm(x):
    # 计算结果
    pass
```

---

## STEP 7: Git 工作流

### 7.1 提交规范

使用 Conventional Commits 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型 (type):
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：

```
feat(models): add attention visualization

- Add get_attention_weights method to ProposedModel
- Create visualization script in scripts/visualize_attention.py
- Add corresponding tests

Closes #42
```

### 7.2 分支策略

```
main (稳定版本)
├── develop (开发分支)
│   ├── feature/data-augmentation (功能分支)
│   ├── feature/new-loss (功能分支)
│   └── bugfix/training-crash (修复分支)
```

### 7.3 提交时机

- 完成一个独立功能模块
- 修复一个 bug
- 更新文档
- 通过测试后

---

## STEP 8: Checkpoint C - 代码审查

### 8.1 代码自检清单

在提交代码审查前，确认：

- [ ] 代码符合 PEP 8 规范
- [ ] 所有函数有类型注解
- [ ] 所有公开函数有文档字符串
- [ ] 单元测试覆盖率 >= 70%
- [ ] 所有测试通过
- [ ] 无明显的性能问题
- [ ] 无硬编码的敏感信息
- [ ] 配置参数可通过配置文件修改
- [ ] 日志输出合理
- [ ] 代码已提交到 Git

### 8.2 准备审查报告

```markdown
# Checkpoint C: 代码审查请求

## 已完成工作

### 数据处理
- [x] 数据加载器实现
- [x] 预处理流程实现
- [x] 数据增强实现

### 模型实现
- [x] 基线模型 (BaselineModel)
- [x] 提出的方法 (ProposedModel)
- [x] 消融变体 (AblationModel)

### 训练流程
- [x] 训练器实现
- [x] 损失函数实现
- [x] 学习率调度器

### 评估工具
- [x] 评估脚本
- [x] 可视化脚本

### 测试
- [x] 单元测试 (覆盖率: 82%)
- [x] 集成测试

## 代码统计

- 总行数: X
- 模型代码: X 行
- 测试代码: X 行
- 文档: X 行

## 测试结果

```
==================== test session starts ====================
collected 45 items

tests/test_data.py .......... [22%]
tests/test_models.py ................. [60%]
tests/test_training.py ................ [100%]

==================== 45 passed in 12.34s ====================
```

## 待确认事项

1. 是否需要支持多 GPU 训练？
2. 模型保存格式是否正确？
3. 评估指标是否完整？

## 请审批

在 `Communication/inbox/commands.txt` 中写入:
- `APPROVE` - 代码通过，进入执行阶段
- `MODIFY` - 需要修改，请查看具体意见
```

---

## 质量检查清单

在完成编码阶段前，确保：

- [ ] 所有模块已实现
- [ ] 代码符合规范
- [ ] 所有测试通过
- [ ] 测试覆盖率达标
- [ ] 文档完整
- [ ] 配置可调整
- [ ] 日志可追踪
- [ ] 代码已提交 Git
- [ ] 可以复现实验
- [ ] 已准备审查报告

---

## 常见问题

**Q: 代码应该写多少注释？**
A: 让代码自解释，只在必要时添加注释。复杂逻辑、非显而易见的决策、算法引用需要注释。

**Q: 测试应该写到什么程度？**
A: 核心功能必须有测试，边界情况要覆盖。目标是 70% 以上的覆盖率。

**Q: 如何处理依赖版本？**
A: 使用 `requirements.txt` 固定版本号，或使用 `poetry/pipenv` 管理依赖。

**Q: GPU 内存不足怎么办？**
A: 减小 batch_size，使用梯度累积，或使用混合精度训练。

---

*完成此阶段后，系统将进入 Phase 4: 执行监控*
