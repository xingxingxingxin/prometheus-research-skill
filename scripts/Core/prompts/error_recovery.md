# 错误恢复与调试指南

## YOUR ROLE

你是 Project Prometheus 的错误恢复专家。当系统在执行过程中遇到错误时，你的任务是快速诊断问题、定位根因、实施修复，并从检查点恢复执行。你需要确保错误处理的系统性和可追溯性，最大限度减少对实验进度的影响。

---

## 工作目标

1. **快速诊断**: 准确识别错误类型和根本原因
2. **有效修复**: 实施正确的修复策略
3. **安全恢复**: 从最近的检查点恢复执行
4. **预防改进**: 记录错误并改进系统以防止复发
5. **最小影响**: 确保错误处理对实验进度影响最小

---

## STEP 1: 错误分类体系

### 1.1 错误类型枚举

```python
class ErrorCategory:
    """错误类型分类"""

    # 数据相关错误
    DATA_NOT_FOUND = "data_not_found"           # 数据文件缺失
    DATA_FORMAT_ERROR = "data_format_error"     # 数据格式不正确
    DATA_SHAPE_MISMATCH = "data_shape_mismatch" # 数据形状不匹配
    DATA_CORRUPTION = "data_corruption"         # 数据损坏

    # 模型相关错误
    MODEL_INIT_ERROR = "model_init_error"       # 模型初始化失败
    MODEL_FORWARD_ERROR = "model_forward_error" # 前向传播失败
    MODEL_LOAD_ERROR = "model_load_error"       # 模型加载失败
    MODEL_SAVE_ERROR = "model_save_error"       # 模型保存失败

    # 训练相关错误
    GRADIENT_EXPLOSION = "gradient_explosion"   # 梯度爆炸
    GRADIENT_VANISHING = "gradient_vanishing"   # 梯度消失
    LOSS_NAN = "loss_nan"                       # Loss 变为 NaN
    LOSS_INF = "loss_inf"                       # Loss 变为 Inf
    CONVERGENCE_FAILURE = "convergence_failure" # 不收敛

    # 资源相关错误
    GPU_OOM = "gpu_oom"                         # GPU 内存不足
    CPU_OOM = "cpu_oom"                         # CPU 内存不足
    DISK_FULL = "disk_full"                     # 磁盘空间不足
    NETWORK_ERROR = "network_error"             # 网络错误

    # 系统相关错误
    FILE_PERMISSION = "file_permission"         # 文件权限错误
    DEPENDENCY_ERROR = "dependency_error"       # 依赖包错误
    CONFIG_ERROR = "config_error"               # 配置错误
    VERSION_MISMATCH = "version_mismatch"       # 版本不匹配

    # 代码相关错误
    SYNTAX_ERROR = "syntax_error"               # 语法错误
    RUNTIME_ERROR = "runtime_error"             # 运行时错误
    LOGIC_ERROR = "logic_error"                 # 逻辑错误
    ASSERTION_ERROR = "assertion_error"         # 断言失败
```

### 1.2 错误严重程度

```python
class ErrorSeverity:
    """错误严重程度"""

    LOW = "low"           # 可忽略，不影响主流程
    MEDIUM = "medium"     # 需要处理，但可自动恢复
    HIGH = "high"         # 需要人工干预
    CRITICAL = "critical" # 必须立即停止
```

### 1.3 错误上下文收集

```python
def collect_error_context(error: Exception) -> dict:
    """收集错误上下文信息"""

    import traceback
    import sys
    from datetime import datetime

    context = {
        # 基本信息
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),

        # 堆栈信息
        "traceback": traceback.format_exc(),

        # 系统状态
        "python_version": sys.version,
        "working_directory": os.getcwd(),

        # 资源状态
        "memory_usage": get_memory_usage(),
        "gpu_memory": get_gpu_memory() if torch.cuda.is_available() else None,

        # 实验状态
        "current_phase": get_current_phase(),
        "current_epoch": get_current_epoch(),
        "last_checkpoint": get_last_checkpoint_path(),
    }

    return context
```

---

## STEP 2: 常见错误诊断

### 2.1 数据错误诊断

#### 数据文件缺失

```python
# 错误表现
FileNotFoundError: [Errno 2] No such file or directory: 'data/train.csv'

# 诊断步骤
1. 检查数据路径配置
   - 配置文件中的路径是否正确
   - 相对路径还是绝对路径
   - 路径中是否有特殊字符

2. 检查数据文件状态
   - 文件是否存在: os.path.exists(path)
   - 是否是目录: os.path.isdir(path)
   - 文件权限: os.access(path, os.R_OK)

3. 检查数据生成流程
   - 数据是否需要先生成
   - 下载脚本是否执行
   - 解压步骤是否完成

# 修复策略
- 如果路径错误: 修正配置文件
- 如果文件未生成: 执行数据准备脚本
- 如果文件被删除: 重新下载或从备份恢复
```

#### 数据形状不匹配

```python
# 错误表现
RuntimeError: shape '[32, 10]' is invalid for input of size 3200

# 诊断步骤
1. 打印实际形状
   print(f"Input shape: {x.shape}")
   print(f"Expected shape: {expected_shape}")

2. 检查数据处理流程
   - 预处理是否正确
   - 是否有未预期的维度变化
   - Batch 维度是否正确

3. 检查模型定义
   - 输入维度配置是否与数据匹配
   - 是否有多余的维度操作

# 修复策略
def diagnose_shape_mismatch(actual, expected, tensor_name="tensor"):
    """诊断形状不匹配问题"""
    print(f"=== {tensor_name} 形状诊断 ===")
    print(f"实际形状: {actual}")
    print(f"期望形状: {expected}")

    if len(actual) != len(expected):
        print(f"维度数不同: 实际 {len(actual)} vs 期望 {len(expected)}")

    for i, (a, e) in enumerate(zip(actual, expected)):
        if a != e:
            print(f"维度 {i} 不匹配: 实际 {a} vs 期望 {e}")

    # 常见修复建议
    if actual[-1] == expected[-1] * 2:
        print("建议: 可能需要 reshape 或 view 操作")
    if actual[0] != expected[0]:
        print("建议: 可能是 batch size 不匹配")
```

#### 数据损坏

```python
# 错误表现
Pickle.UnpicklingError: invalid load key
EOFError: Ran out of input

# 诊断步骤
1. 检查文件完整性
   - 文件大小是否为 0
   - 文件是否被截断
   - 校验和是否匹配

2. 尝试部分读取
   try:
       data = torch.load(path)
   except Exception as e:
       print(f"文件损坏: {e}")

# 修复策略
def verify_data_integrity(file_path, expected_hash=None):
    """验证数据完整性"""
    import hashlib

    # 检查文件是否存在
    if not os.path.exists(file_path):
        return False, "文件不存在"

    # 检查文件大小
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return False, "文件为空"

    # 校验哈希
    if expected_hash:
        with open(file_path, 'rb') as f:
            actual_hash = hashlib.md5(f.read()).hexdigest()
        if actual_hash != expected_hash:
            return False, f"哈希不匹配: {actual_hash} != {expected_hash}"

    # 尝试加载
    try:
        if file_path.endswith('.pt'):
            torch.load(file_path)
        elif file_path.endswith('.npy'):
            np.load(file_path)
    except Exception as e:
        return False, f"加载失败: {e}"

    return True, "验证通过"
```

### 2.2 模型错误诊断

#### 模型初始化失败

```python
# 错误表现
RuntimeError: CUDA out of memory during model initialization

# 诊断步骤
1. 检查模型大小
   total_params = sum(p.numel() for p in model.parameters())
   print(f"模型参数量: {total_params:,}")

2. 检查 GPU 内存
   print(f"GPU 内存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

3. 估算内存需求
   # 参数内存 (FP32)
   params_memory = total_params * 4 / 1e9  # GB
   # 梯度内存
   grads_memory = params_memory
   # 激活内存 (估算)
   activations_memory = batch_size * seq_len * hidden_size * 4 / 1e9
   total_memory = params_memory + grads_memory + activations_memory

# 修复策略
- 使用更小的模型
- 使用梯度检查点 (gradient checkpointing)
- 使用混合精度训练
- 使用模型并行
```

#### 前向传播失败

```python
# 错误表现
RuntimeError: mat1 and mat2 shapes cannot be multiplied

# 诊断工具
def debug_forward_pass(model, sample_input):
    """调试前向传播"""
    print("=== 前向传播调试 ===")

    # 使用 hooks 记录每层的输入输出
    shapes = {}

    def hook_fn(name):
        def hook(module, input, output):
            shapes[name] = {
                'input': [i.shape for i in input] if isinstance(input, tuple) else input.shape,
                'output': output.shape if hasattr(output, 'shape') else type(output)
            }
        return hook

    # 注册 hooks
    for name, module in model.named_modules():
        if len(list(module.children())) == 0:  # 只对叶子模块
            module.register_forward_hook(hook_fn(name))

    # 执行前向传播
    try:
        output = model(sample_input)
        print("前向传播成功!")
        for name, shape_info in shapes.items():
            print(f"{name}: {shape_info['input']} -> {shape_info['output']}")
    except Exception as e:
        print(f"前向传播失败: {e}")
        print("\n成功的层:")
        for name, shape_info in shapes.items():
            print(f"  {name}: {shape_info}")

    return shapes
```

### 2.3 训练错误诊断

#### Loss 变为 NaN

```python
# 错误表现
训练过程中 loss 突然变为 nan

# 诊断步骤
def diagnose_nan_loss(model, batch, optimizer):
    """诊断 NaN Loss"""
    print("=== NaN Loss 诊断 ===")

    model.train()
    x, y = batch

    # 1. 检查输入数据
    print("1. 检查输入数据")
    if torch.isnan(x).any():
        print("  [ERROR] 输入包含 NaN")
    if torch.isinf(x).any():
        print("  [ERROR] 输入包含 Inf")
    print(f"  输入范围: [{x.min():.4f}, {x.max():.4f}]")

    # 2. 检查模型参数
    print("2. 检查模型参数")
    for name, param in model.named_parameters():
        if torch.isnan(param).any():
            print(f"  [ERROR] {name} 包含 NaN")
        if torch.isinf(param).any():
            print(f"  [ERROR] {name} 包含 Inf")

    # 3. 前向传播检查
    print("3. 前向传播检查")
    optimizer.zero_grad()
    output = model(x)

    if torch.isnan(output).any():
        print("  [ERROR] 输出包含 NaN")

    # 4. Loss 计算
    print("4. Loss 计算")
    loss = criterion(output, y)
    print(f"  Loss 值: {loss.item()}")

    # 5. 反向传播
    print("5. 反向传播检查")
    loss.backward()

    for name, param in model.named_parameters():
        if param.grad is not None:
            if torch.isnan(param.grad).any():
                print(f"  [ERROR] {name} 梯度包含 NaN")
            grad_norm = param.grad.norm().item()
            print(f"  {name} 梯度范数: {grad_norm:.6f}")

# 常见原因和修复
nan_causes = {
    "学习率过大": "降低学习率到 1/10",
    "梯度爆炸": "添加梯度裁剪 clip_grad_norm_(max_norm=1.0)",
    "数据异常": "检查并过滤异常值",
    "除零错误": "在除法中添加 eps=1e-8",
    "log(0)": "使用 log(x + eps) 或 torch.log1p",
    "数值溢出": "使用 torch.clamp 限制范围",
}
```

#### 梯度爆炸/消失

```python
# 诊断工具
def monitor_gradients(model, log_file=None):
    """监控梯度状态"""

    stats = {}

    for name, param in model.named_parameters():
        if param.grad is not None:
            grad = param.grad.data
            stats[name] = {
                'norm': grad.norm().item(),
                'max': grad.max().item(),
                'min': grad.min().item(),
                'mean': grad.mean().item(),
                'has_nan': torch.isnan(grad).any().item(),
                'has_inf': torch.isinf(grad).any().item(),
            }

    # 检测问题
    total_norm = sum(s['norm']**2 for s in stats.values())**0.5

    if total_norm > 100:
        print(f"[WARNING] 梯度爆炸! 总范数: {total_norm:.2f}")
        return "explosion"
    elif total_norm < 1e-7:
        print(f"[WARNING] 梯度消失! 总范数: {total_norm:.2e}")
        return "vanishing"

    return "normal"

# 修复策略
gradient_fixes = {
    "梯度爆炸": [
        "降低学习率",
        "添加梯度裁剪: torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)",
        "使用 LayerNorm 替代 BatchNorm",
        "检查模型初始化",
    ],
    "梯度消失": [
        "使用残差连接",
        "使用 LSTM/GRU 替代 RNN",
        "使用 LayerNorm",
        "使用更好的初始化 (Xavier/He)",
    ],
}
```

### 2.4 资源错误诊断

#### GPU 内存不足

```python
# 错误表现
RuntimeError: CUDA out of memory

# 诊断工具
def diagnose_gpu_memory():
    """诊断 GPU 内存使用"""
    if not torch.cuda.is_available():
        print("CUDA 不可用")
        return

    for i in range(torch.cuda.device_count()):
        print(f"\n=== GPU {i}: {torch.cuda.get_device_name(i)} ===")
        total = torch.cuda.get_device_properties(i).total_memory / 1e9
        reserved = torch.cuda.memory_reserved(i) / 1e9
        allocated = torch.cuda.memory_allocated(i) / 1e9
        free = total - reserved

        print(f"总内存: {total:.2f} GB")
        print(f"已保留: {reserved:.2f} GB")
        print(f"已分配: {allocated:.2f} GB")
        print(f"可用: {free:.2f} GB")

# 修复策略
gpu_oom_solutions = [
    {
        "方法": "减小 batch size",
        "代码": "batch_size = batch_size // 2",
        "效果": "立竿见影，但可能影响性能",
    },
    {
        "方法": "梯度累积",
        "代码": """
accumulation_steps = 4
for i, batch in enumerate(dataloader):
    loss = model(batch) / accumulation_steps
    loss.backward()
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
""",
        "效果": "等效于大 batch，不损失性能",
    },
    {
        "方法": "混合精度训练",
        "代码": """
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()
with autocast():
    loss = model(batch)
scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
""",
        "效果": "减少约 50% 显存",
    },
    {
        "方法": "梯度检查点",
        "代码": """
from torch.utils.checkpoint import checkpoint
# 在模型中使用
def forward(self, x):
    x = checkpoint(self.layer1, x)
    x = checkpoint(self.layer2, x)
    return x
""",
        "效果": "以计算换内存",
    },
    {
        "方法": "清理缓存",
        "代码": """
import gc
gc.collect()
torch.cuda.empty_cache()
""",
        "效果": "立即释放碎片内存",
    },
]
```

---

## STEP 3: 恢复策略

### 3.1 检查点恢复

```python
class CheckpointRecovery:
    """检查点恢复管理器"""

    def __init__(self, checkpoint_dir, max_checkpoints=5):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max_checkpoints
        self.checkpoint_history = []

    def find_valid_checkpoints(self):
        """找到所有有效的检查点"""
        checkpoints = []

        for path in self.checkpoint_dir.glob("checkpoint_*.pt"):
            try:
                # 尝试加载检查点元数据
                checkpoint = torch.load(path, map_location='cpu')
                checkpoints.append({
                    'path': path,
                    'epoch': checkpoint.get('epoch', 0),
                    'metrics': checkpoint.get('metrics', {}),
                    'timestamp': checkpoint.get('timestamp', ''),
                })
            except Exception as e:
                print(f"[WARNING] 检查点损坏: {path} - {e}")

        # 按时间排序
        checkpoints.sort(key=lambda x: x['epoch'], reverse=True)
        return checkpoints

    def find_best_checkpoint(self, metric_name='val_loss', mode='min'):
        """找到最佳检查点"""
        checkpoints = self.find_valid_checkpoints()

        if not checkpoints:
            return None

        if mode == 'min':
            best = min(checkpoints, key=lambda x: x['metrics'].get(metric_name, float('inf')))
        else:
            best = max(checkpoints, key=lambda x: x['metrics'].get(metric_name, float('-inf')))

        return best['path']

    def recover(self, model, optimizer=None, scheduler=None, checkpoint_path=None):
        """从检查点恢复"""
        if checkpoint_path is None:
            # 自动找最新的有效检查点
            checkpoints = self.find_valid_checkpoints()
            if not checkpoints:
                raise ValueError("没有找到有效的检查点")
            checkpoint_path = checkpoints[0]['path']

        print(f"从检查点恢复: {checkpoint_path}")

        checkpoint = torch.load(checkpoint_path)

        # 恢复模型
        model.load_state_dict(checkpoint['model_state_dict'])

        # 恢复优化器
        if optimizer is not None and 'optimizer_state_dict' in checkpoint:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

        # 恢复调度器
        if scheduler is not None and 'scheduler_state_dict' in checkpoint:
            scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

        return {
            'epoch': checkpoint.get('epoch', 0),
            'metrics': checkpoint.get('metrics', {}),
            'history': checkpoint.get('history', {}),
        }
```

### 3.2 自动重试机制

```python
class RetryManager:
    """自动重试管理器"""

    def __init__(self, max_retries=3, backoff_factor=2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_history = []

    def execute_with_retry(self, func, *args, **kwargs):
        """带重试的执行"""
        import time

        last_error = None

        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)

                # 成功后记录
                if attempt > 0:
                    self.retry_history.append({
                        'function': func.__name__,
                        'attempts': attempt + 1,
                        'success': True,
                    })

                return result

            except Exception as e:
                last_error = e

                # 记录失败
                self.retry_history.append({
                    'function': func.__name__,
                    'attempt': attempt + 1,
                    'error': str(e),
                    'success': False,
                })

                # 判断是否应该重试
                if not self._should_retry(e):
                    raise

                # 等待后重试
                wait_time = self.backoff_factor ** attempt
                print(f"尝试 {attempt + 1}/{self.max_retries} 失败: {e}")
                print(f"等待 {wait_time:.1f} 秒后重试...")
                time.sleep(wait_time)

        raise last_error

    def _should_retry(self, error):
        """判断是否应该重试"""
        # 网络错误通常可以重试
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True

        # GPU OOM 可以尝试减小 batch size 后重试
        if "out of memory" in str(error).lower():
            return True

        # 配置错误、代码错误不应该重试
        if isinstance(error, (ValueError, SyntaxError, AssertionError)):
            return False

        # 默认可以重试
        return True
```

### 3.3 降级策略

```python
class DegradationStrategy:
    """降级策略"""

    def __init__(self, config):
        self.original_config = config
        self.degradation_levels = [
            {'batch_size': config.batch_size},
            {'batch_size': config.batch_size // 2},
            {'batch_size': config.batch_size // 4, 'gradient_accumulation': 4},
            {'batch_size': 1, 'gradient_accumulation': 16, 'mixed_precision': True},
        ]
        self.current_level = 0

    def degrade(self):
        """降级到下一级别"""
        if self.current_level >= len(self.degradation_levels) - 1:
            raise RuntimeError("已达最低配置，无法继续降级")

        self.current_level += 1
        new_config = self.degradation_levels[self.current_level]

        print(f"降级到配置级别 {self.current_level}:")
        for key, value in new_config.items():
            print(f"  {key}: {value}")

        return new_config

    def get_current_config(self):
        """获取当前配置"""
        return self.degradation_levels[self.current_level]
```

---

## STEP 4: 调试工具集

### 4.1 交互式调试

```python
def debug_training_step(model, batch, criterion, optimizer):
    """单步调试训练过程"""

    print("=" * 60)
    print("训练步骤调试")
    print("=" * 60)

    x, y = batch

    # 1. 输入检查
    print("\n1. 输入检查")
    print(f"   x shape: {x.shape}, dtype: {x.dtype}")
    print(f"   y shape: {y.shape}, dtype: {y.dtype}")
    print(f"   x range: [{x.min():.4f}, {x.max():.4f}]")
    print(f"   y unique values: {torch.unique(y)}")

    # 2. 模型状态检查
    print("\n2. 模型状态")
    for name, param in model.named_parameters():
        print(f"   {name}: shape={param.shape}, mean={param.mean():.6f}")

    # 3. 前向传播
    print("\n3. 前向传播")
    optimizer.zero_grad()
    output = model(x)
    print(f"   output shape: {output.shape}")
    print(f"   output range: [{output.min():.4f}, {output.max():.4f}]")

    # 4. Loss 计算
    print("\n4. Loss 计算")
    loss = criterion(output, y)
    print(f"   loss: {loss.item():.6f}")

    # 5. 反向传播
    print("\n5. 反向传播")
    loss.backward()

    gradient_stats = []
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_norm = param.grad.norm().item()
            gradient_stats.append((name, grad_norm))

    print("   梯度范数 (前5):")
    for name, norm in sorted(gradient_stats, key=lambda x: -x[1])[:5]:
        print(f"     {name}: {norm:.6f}")

    # 6. 参数更新预览
    print("\n6. 参数更新预览")
    print(f"   优化器类型: {type(optimizer).__name__}")
    print(f"   学习率: {optimizer.param_groups[0]['lr']}")

    return {
        'loss': loss.item(),
        'output': output,
        'gradient_stats': gradient_stats,
    }
```

### 4.2 日志分析工具

```python
def analyze_error_logs(log_dir):
    """分析错误日志"""

    error_patterns = {}
    timeline = []

    # 读取所有日志文件
    for log_file in Path(log_dir).glob("*.log"):
        with open(log_file, 'r') as f:
            for line in f:
                if 'ERROR' in line or 'CRITICAL' in line:
                    # 提取错误类型
                    error_type = extract_error_type(line)
                    error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

                    # 记录时间线
                    timestamp = extract_timestamp(line)
                    timeline.append({
                        'time': timestamp,
                        'type': error_type,
                        'message': line.strip(),
                    })

    # 生成报告
    print("\n=== 错误分析报告 ===")
    print("\n错误类型统计:")
    for error_type, count in sorted(error_patterns.items(), key=lambda x: -x[1]):
        print(f"  {error_type}: {count} 次")

    print("\n错误时间线 (最近10个):")
    for event in timeline[-10:]:
        print(f"  [{event['time']}] {event['type']}")

    return {
        'error_patterns': error_patterns,
        'timeline': timeline,
    }
```

### 4.3 断言检查工具

```python
class TrainingAssertions:
    """训练过程中的断言检查"""

    @staticmethod
    def assert_valid_input(x, name="input"):
        """验证输入有效性"""
        assert not torch.isnan(x).any(), f"{name} 包含 NaN"
        assert not torch.isinf(x).any(), f"{name} 包含 Inf"
        assert x.dim() > 0, f"{name} 维度为 0"

    @staticmethod
    def assert_valid_loss(loss, prev_loss=None, max_increase_ratio=10.0):
        """验证 Loss 有效性"""
        assert not torch.isnan(loss), "Loss 为 NaN"
        assert not torch.isinf(loss), "Loss 为 Inf"
        assert loss > 0, "Loss 为负数"

        if prev_loss is not None:
            ratio = loss.item() / prev_loss
            assert ratio < max_increase_ratio, \
                f"Loss 增长异常: {prev_loss:.4f} -> {loss.item():.4f}"

    @staticmethod
    def assert_valid_gradients(model, max_norm=1000.0, min_norm=1e-10):
        """验证梯度有效性"""
        total_norm = 0
        for param in model.parameters():
            if param.grad is not None:
                assert not torch.isnan(param.grad).any(), "梯度包含 NaN"
                assert not torch.isinf(param.grad).any(), "梯度包含 Inf"
                total_norm += param.grad.norm().item() ** 2

        total_norm = total_norm ** 0.5
        assert total_norm < max_norm, f"梯度爆炸: norm={total_norm:.2f}"
        assert total_norm > min_norm, f"梯度消失: norm={total_norm:.2e}"

    @staticmethod
    def assert_memory_available(min_free_gb=1.0):
        """验证内存充足"""
        if torch.cuda.is_available():
            free = (torch.cuda.get_device_properties(0).total_memory -
                   torch.cuda.memory_allocated(0)) / 1e9
            assert free > min_free_gb, f"GPU 内存不足: 可用 {free:.2f} GB"
```

---

## STEP 5: 求助模板

### 5.1 错误报告模板

```markdown
# 错误报告

## 基本信息
- **时间**: [YYYY-MM-DD HH:MM:SS]
- **阶段**: Phase [N] - [阶段名称]
- **任务**: [当前任务描述]

## 错误描述
- **错误类型**: [错误类型]
- **严重程度**: [LOW/MEDIUM/HIGH/CRITICAL]
- **错误消息**:
```
[完整的错误消息]
```

## 上下文信息
- **Python 版本**: [版本]
- **PyTorch 版本**: [版本]
- **CUDA 版本**: [版本]
- **GPU**: [型号和数量]
- **可用内存**: [内存大小]

## 堆栈跟踪
```
[完整的堆栈跟踪]
```

## 最近操作
1. [操作1]
2. [操作2]
3. [操作3]

## 已尝试的修复
1. [修复尝试1] - [结果]
2. [修复尝试2] - [结果]

## 相关文件
- 配置文件: [路径]
- 日志文件: [路径]
- 检查点: [路径]

## 请求帮助
- [ ] 需要人工干预
- [ ] 需要更多资源
- [ ] 需要修改代码
- [ ] 需要回滚到上一个检查点
```

### 5.2 人工干预请求模板

```markdown
# 人工干预请求

## 情况摘要
[简要描述当前情况和无法自动处理的原因]

## 问题详情
[详细描述问题]

## 影响范围
- [ ] 训练无法继续
- [ ] 数据可能丢失
- [ ] 结果可能不正确
- [ ] 需要修改实验设计

## 建议操作
1. [建议1]
2. [建议2]
3. [建议3]

## 可用选项
- `APPROVE [option]` - 批准某个建议
- `ROLLBACK [checkpoint]` - 回滚到指定检查点
- `SKIP` - 跳过当前任务
- `ABORT` - 终止实验

## 等待时间
[已等待时间] / [最大等待时间]
```

### 5.3 回滚请求模板

```markdown
# 回滚请求

## 回滚原因
[描述为什么需要回滚]

## 当前状态
- **当前 Epoch**: [N]
- **当前 Loss**: [value]
- **最佳 Loss**: [value] @ Epoch [N]

## 目标检查点
- **检查点路径**: [path]
- **检查点 Epoch**: [N]
- **检查点 Loss**: [value]

## 回滚影响
- 将丢失 [N] 个 epoch 的训练进度
- 将丢失以下实验数据: [list]
- 需要 [time] 重新训练

## 确认
- `CONFIRM ROLLBACK` - 确认回滚
- `CANCEL` - 取消，尝试其他修复
- `CHANGE TARGET [checkpoint]` - 选择其他检查点
```

---

## STEP 6: 错误预防

### 6.1 预检查清单

```python
def pre_training_checks(config, model, data_loader):
    """训练前预检查"""

    checks = []

    # 1. 数据检查
    try:
        sample_batch = next(iter(data_loader))
        x, y = sample_batch
        assert not torch.isnan(x).any(), "输入数据包含 NaN"
        assert not torch.isinf(x).any(), "输入数据包含 Inf"
        checks.append(("数据完整性", True, ""))
    except Exception as e:
        checks.append(("数据完整性", False, str(e)))

    # 2. 模型检查
    try:
        model.eval()
        with torch.no_grad():
            output = model(x)
        assert output.shape[0] == x.shape[0], "输出 batch size 不匹配"
        checks.append(("模型前向传播", True, ""))
    except Exception as e:
        checks.append(("模型前向传播", False, str(e)))

    # 3. 内存检查
    try:
        if torch.cuda.is_available():
            total_mem = torch.cuda.get_device_properties(0).total_memory
            free_mem = total_mem - torch.cuda.memory_allocated(0)
            assert free_mem > 1e9, f"GPU 内存不足: {free_mem/1e9:.2f} GB 可用"
        checks.append(("内存充足", True, ""))
    except Exception as e:
        checks.append(("内存充足", False, str(e)))

    # 4. 配置检查
    try:
        assert config.learning_rate > 0, "学习率必须为正"
        assert config.batch_size > 0, "batch size 必须为正"
        assert config.epochs > 0, "epochs 必须为正"
        checks.append(("配置有效性", True, ""))
    except Exception as e:
        checks.append(("配置有效性", False, str(e)))

    # 打印结果
    print("\n=== 预检查结果 ===")
    all_passed = True
    for name, passed, error in checks:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
        if not passed:
            print(f"       Error: {error}")
            all_passed = False

    return all_passed
```

### 6.2 运行时监控

```python
class RuntimeMonitor:
    """运行时监控器"""

    def __init__(self, check_interval=100):
        self.check_interval = check_interval
        self.step_count = 0
        self.loss_history = []
        self.gradient_history = []

    def check(self, loss, model):
        """定期检查"""
        self.step_count += 1

        if self.step_count % self.check_interval != 0:
            return None

        issues = []

        # 检查 Loss
        self.loss_history.append(loss)
        if len(self.loss_history) > 10:
            recent = self.loss_history[-10:]
            if all(l > recent[0] for l in recent[1:]):
                issues.append("Loss 连续上升")

        # 检查梯度
        total_grad_norm = 0
        for param in model.parameters():
            if param.grad is not None:
                total_grad_norm += param.grad.norm().item() ** 2
        total_grad_norm = total_grad_norm ** 0.5
        self.gradient_history.append(total_grad_norm)

        if total_grad_norm > 100:
            issues.append(f"梯度爆炸 (norm={total_grad_norm:.2f})")
        elif total_grad_norm < 1e-7:
            issues.append(f"梯度消失 (norm={total_grad_norm:.2e})")

        # 检查内存
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1e9
            if allocated > 0.9 * torch.cuda.get_device_properties(0).total_memory / 1e9:
                issues.append(f"GPU 内存即将耗尽 ({allocated:.1f} GB)")

        return issues if issues else None
```

### 6.3 最佳实践

```markdown
# 错误预防最佳实践

## 1. 数据处理
- [ ] 在加载后立即验证数据完整性
- [ ] 使用 try-except 包裹数据加载
- [ ] 对数据进行归一化/标准化
- [ ] 检查并处理异常值

## 2. 模型定义
- [ ] 使用适当的权重初始化
- [ ] 添加 LayerNorm 稳定训练
- [ ] 避免过深的网络（除非有残差连接）
- [ ] 使用 dropout 防止过拟合

## 3. 训练配置
- [ ] 使用梯度裁剪 (max_norm=1.0)
- [ ] 使用学习率预热
- [ ] 定期保存检查点
- [ ] 使用混合精度训练

## 4. 代码质量
- [ ] 添加类型注解
- [ ] 编写单元测试
- [ ] 使用断言检查
- [ ] 记录详细日志

## 5. 资源管理
- [ ] 监控内存使用
- [ ] 及时释放不需要的变量
- [ ] 使用生成器处理大数据
- [ ] 定期清理缓存
```

---

## STEP 7: 错误日志模板

### 7.1 结构化错误日志

```python
def log_structured_error(error, context, action_taken, recovery_status):
    """记录结构化错误日志"""

    import json
    from datetime import datetime

    log_entry = {
        # 时间戳
        "timestamp": datetime.now().isoformat(),

        # 错误信息
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "severity": classify_severity(error),
        },

        # 上下文
        "context": {
            "phase": context.get("phase"),
            "epoch": context.get("epoch"),
            "step": context.get("step"),
            "loss": context.get("loss"),
        },

        # 采取的行动
        "action": {
            "type": action_taken.get("type"),
            "details": action_taken.get("details"),
        },

        # 恢复状态
        "recovery": {
            "status": recovery_status,
            "retry_count": context.get("retry_count", 0),
        },
    }

    # 写入日志文件
    with open("logs/errors.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return log_entry
```

### 7.2 错误摘要报告

```python
def generate_error_summary(log_file="logs/errors.jsonl"):
    """生成错误摘要报告"""

    import json
    from collections import Counter

    errors = []
    with open(log_file, "r") as f:
        for line in f:
            errors.append(json.loads(line))

    # 统计
    error_types = Counter(e["error"]["type"] for e in errors)
    severity_dist = Counter(e["error"]["severity"] for e in errors)
    recovery_success = sum(1 for e in errors if e["recovery"]["status"] == "success")

    report = f"""
# 错误摘要报告

## 统计概览
- 总错误数: {len(errors)}
- 成功恢复: {recovery_success} ({recovery_success/len(errors)*100:.1f}%)

## 错误类型分布
"""
    for error_type, count in error_types.most_common():
        report += f"- {error_type}: {count}\n"

    report += f"""
## 严重程度分布
"""
    for severity, count in severity_dist.items():
        report += f"- {severity}: {count}\n"

    report += f"""
## 最近错误
"""
    for error in errors[-5:]:
        report += f"- [{error['timestamp']}] {error['error']['type']}: {error['error']['message'][:50]}\n"

    return report
```

---

## 质量检查清单

在处理错误恢复时，确保：

### 诊断阶段
- [ ] 正确识别错误类型
- [ ] 收集完整的上下文信息
- [ ] 分析根本原因
- [ ] 评估影响范围

### 修复阶段
- [ ] 选择合适的修复策略
- [ ] 验证修复的有效性
- [ ] 确保不引入新问题
- [ ] 记录修复过程

### 恢复阶段
- [ ] 从最近的检查点恢复
- [ ] 验证恢复后的状态
- [ ] 继续执行后续步骤
- [ ] 监控是否复发

### 记录阶段
- [ ] 记录完整的错误信息
- [ ] 记录修复步骤
- [ ] 更新知识库
- [ ] 改进预防措施

---

## 常见问题

**Q: 如何判断是否应该重试？**
A: 网络错误、临时资源不足等可恢复错误应该重试；配置错误、代码错误等需要修复后才能继续。

**Q: 检查点损坏怎么办？**
A: 尝试加载更早的检查点；如果没有有效检查点，需要从头开始训练。

**Q: 多次降级后仍然失败？**
A: 说明问题不是简单的资源不足，需要深入诊断代码或配置问题，可能需要人工干预。

**Q: 如何避免重复出现相同的错误？**
A: 记录错误到知识库，更新预检查清单，添加运行时监控，改进代码质量。

**Q: 什么时候应该请求人工干预？**
A: 当自动恢复尝试全部失败、无法确定正确的修复策略、或需要做出重大决策时。

---

## STEP 8: Ralph Debug Loop (推荐)

Ralph Debug Loop 是一种更高级的调试机制，通过迭代改进来修复错误。

### 8.1 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                    Ralph Debug Loop                          │
│                                                              │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│   │ 执行代码 │ ──▶ │ 遇到错误 │ ──▶ │ 分析错误 │              │
│   └─────────┘     └─────────┘     └─────────┘              │
│        │                                │                   │
│        │         ┌─────────┐            │                   │
│        │         │ 修复代码 │◀───────────┘                   │
│        │         └─────────┘                                │
│        │              │                                      │
│        │         ┌────▼────┐                                │
│        └────────▶│ 验证修复 │                                │
│                  └────┬────┘                                │
│                       │                                      │
│            ┌──────────┴──────────┐                          │
│            │                     │                          │
│       ┌────▼────┐          ┌─────▼─────┐                   │
│       │ 成功    │          │ 再次失败   │──▶ 迭代修复       │
│       │ <promise>│          └───────────┘                   │
│       └─────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 使用方式

```python
from agent.ralph_debug import with_ralph_debug, get_debugger

# 方式 1: 装饰器模式
result = with_ralph_debug(
    func=lambda: run_experiment(),
    task_id="EXP-001",
    phase="execution",
    max_iterations=5
)

# 方式 2: 调试器模式
debugger = get_debugger()
result = debugger.execute_with_debug(
    func=lambda: train_model(),
    error_context={'task_id': 'TRAIN-001', 'phase': 'training'},
    validate_func=lambda: check_model_accuracy() > 0.9
)

if result.success:
    print(f"Fixed after {result.iteration} iterations")
elif result.needs_human_help:
    print("Requires human intervention")
```

### 8.3 完成承诺

调试成功时输出：
```
<promise>DEBUG_FIXED</promise>
```

需要人工帮助时输出：
```
<promise type="blocked">NEEDS_DEBUG_HELP</promise>
```

### 8.4 可修复的错误类型

| 错误类型 | 可自动修复 | 说明 |
|---------|----------|------|
| SyntaxError | ✅ | 语法问题通常容易修复 |
| IndentationError | ✅ | 缩进问题 |
| NameError | ✅ | 变量名错误 |
| TypeError | ✅ | 类型错误 |
| ValueError | ✅ | 值错误 |
| AttributeError | ✅ | 属性错误 |
| ImportError | ✅ | 导入错误 |
| FileNotFoundError | ✅ | 文件路径问题 |
| KeyError | ✅ | 键错误 |
| IndexError | ✅ | 索引错误 |
| MemoryError | ❌ | 需要配置调整 |
| RecursionError | ❌ | 需要算法修改 |
| SystemError | ❌ | 系统级问题 |

### 8.5 调试状态文件

Ralph Debug 会创建 `.claude/ralph-debug.local.md` 状态文件：

```markdown
---
active: true
iteration: 2
max_iterations: 5
task_id: "EXP-001"
phase: "execution"
error_type: "TypeError"
---

# Ralph Debug Session

## Task: EXP-001
## Iteration: 2 / 5

## Current Error (TypeError)
```
unsupported operand type(s) for +: 'int' and 'str'
```

## Previous Attempts

### Attempt 1
- Error: TypeError
- Message: unsupported operand type(s)...

## Your Mission
Fix this error through iterative debugging...
```

### 8.6 与传统重试的对比

| 特性 | 传统重试 | Ralph Debug |
|------|---------|-------------|
| 策略 | 简单重试 | 迭代改进 |
| 上下文 | 无 | 保留错误历史 |
| 学习 | 不学习 | 从错误中学习 |
| 人工介入 | 阈值后请求 | 智能判断 |
| 成功率 | 较低 | 较高 |

### 8.7 最佳实践

1. **先分析错误**: 不要盲目修复，理解根本原因
2. **查看历史**: 检查 `Previous Attempts` 避免重复
3. **小步修改**: 每次只改一处，便于验证
4. **验证修复**: 修复后运行测试确认
5. **及时求助**: 超过 3 次失败考虑请求帮助

---

*本文档为 Project Prometheus 提供全面的错误恢复和调试指南*
