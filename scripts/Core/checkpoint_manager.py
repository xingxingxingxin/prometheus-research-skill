"""
Project Prometheus - 检查点管理器
================================

管理检查点的创建、恢复、删除，支持定期自动创建检查点。
"""

import json
import os
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, List, Dict, Callable


# 默认路径
DEFAULT_BASE_DIR = Path(__file__).parent.parent
CHECKPOINT_DIR = DEFAULT_BASE_DIR / "Checkpoints"
STATE_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "state.json"
TASKS_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "research_tasks.json"
KNOWLEDGE_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "knowledge_base.json"
SESSIONS_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "sessions.json"
RALPH_STATE_FILE = DEFAULT_BASE_DIR / ".claude" / "ralph-loop.local.md"


class CheckpointManager:
    """检查点管理器

    管理项目检查点的创建、恢复、删除，支持定期自动创建检查点。
    检查点包含完整的项目状态，可用于灾难恢复和版本回溯。
    """

    def __init__(self, checkpoint_dir: Optional[Path] = None,
                 base_dir: Optional[Path] = None,
                 auto_save_interval: int = 300):
        """
        初始化检查点管理器

        Args:
            checkpoint_dir: 检查点存储目录
            base_dir: 项目基础目录
            auto_save_interval: 自动保存间隔（秒），默认 5 分钟
        """
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else CHECKPOINT_DIR
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_BASE_DIR
        self.auto_save_interval = auto_save_interval
        self._auto_save_thread: Optional[threading.Thread] = None
        self._auto_save_running = False
        self._on_checkpoint_created: Optional[Callable[[dict], None]] = None
        self._index_file = self.checkpoint_dir / "checkpoint_index.json"
        self._index = None

    def _load_index(self) -> dict:
        """加载检查点索引"""
        if not self._index_file.exists():
            return self._create_default_index()
        with open(self._index_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_index(self, index: dict) -> None:
        """保存检查点索引"""
        index['last_updated'] = datetime.now().isoformat()
        self._index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def _create_default_index(self) -> dict:
        """创建默认索引结构"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_checkpoints": 0,
            "checkpoints": []
        }

    @property
    def index(self) -> dict:
        """懒加载索引"""
        if self._index is None:
            self._index = self._load_index()
        return self._index

    def _get_checkpoint_path(self, checkpoint_id: str) -> Path:
        """获取检查点目录路径"""
        return self.checkpoint_dir / checkpoint_id

    def _collect_state_files(self) -> Dict[str, Path]:
        """收集需要保存的状态文件"""
        files = {
            "state": STATE_FILE,
            "tasks": TASKS_FILE,
            "knowledge": KNOWLEDGE_FILE,
            "sessions": SESSIONS_FILE,
            "ralph_loop": RALPH_STATE_FILE  # Ralph Loop state
        }
        return {name: path for name, path in files.items() if path.exists()}

    def create(self, name: Optional[str] = None,
               description: Optional[str] = None,
               tags: Optional[List[str]] = None,
               include_logs: bool = False) -> str:
        """
        创建检查点

        Args:
            name: 检查点名称（可选）
            description: 检查点描述
            tags: 标签列表
            include_logs: 是否包含日志文件

        Returns:
            检查点 ID
        """
        checkpoint_id = f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)

        # 创建检查点目录
        checkpoint_path.mkdir(parents=True, exist_ok=True)

        # 收集并复制状态文件
        state_files = self._collect_state_files()
        metadata = {
            "checkpoint_id": checkpoint_id,
            "name": name or f"Checkpoint {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "description": description,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "files": {},
            "auto_created": False
        }

        for name, source_path in state_files.items():
            dest_path = checkpoint_path / source_path.name
            shutil.copy2(source_path, dest_path)
            metadata["files"][name] = source_path.name

        # 记录 Ralph Loop 状态
        if "ralph_loop" in state_files:
            metadata["ralph_loop_active"] = True
            # 尝试读取 Ralph Loop 迭代次数
            try:
                with open(RALPH_STATE_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    import re
                    match = re.search(r'iteration:\s*(\d+)', content)
                    if match:
                        metadata["ralph_iteration"] = int(match.group(1))
            except Exception:
                pass
        else:
            metadata["ralph_loop_active"] = False

        # 可选：包含日志
        if include_logs:
            logs_dir = self.base_dir / "Logs"
            if logs_dir.exists():
                dest_logs = checkpoint_path / "Logs"
                shutil.copytree(logs_dir, dest_logs)
                metadata["include_logs"] = True

        # 保存元数据
        metadata_path = checkpoint_path / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # 更新索引
        index = self.index
        index['checkpoints'].append(metadata)
        index['total_checkpoints'] = len(index['checkpoints'])
        self._save_index(index)
        self._index = index

        # 触发回调
        if self._on_checkpoint_created:
            self._on_checkpoint_created(metadata)

        return checkpoint_id

    def restore(self, checkpoint_id: str,
                restore_state: bool = True,
                restore_tasks: bool = True,
                restore_knowledge: bool = True,
                restore_sessions: bool = True) -> bool:
        """
        从检查点恢复

        Args:
            checkpoint_id: 检查点 ID
            restore_state: 是否恢复状态文件
            restore_tasks: 是否恢复任务文件
            restore_knowledge: 是否恢复知识库文件
            restore_sessions: 是否恢复会话文件

        Returns:
            是否成功恢复
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        if not checkpoint_path.exists():
            return False

        metadata_path = checkpoint_path / "metadata.json"
        if not metadata_path.exists():
            return False

        # 加载元数据
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        files_to_restore = {
            "state": (restore_state, STATE_FILE),
            "tasks": (restore_tasks, TASKS_FILE),
            "knowledge": (restore_knowledge, KNOWLEDGE_FILE),
            "sessions": (restore_sessions, SESSIONS_FILE),
            "ralph_loop": (True, RALPH_STATE_FILE)  # Always restore Ralph state if present
        }

        for name, (should_restore, dest_path) in files_to_restore.items():
            if not should_restore:
                continue
            if name not in metadata.get("files", {}):
                continue

            source_file = checkpoint_path / metadata["files"][name]
            if source_file.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, dest_path)

        return True

    def delete(self, checkpoint_id: str) -> bool:
        """
        删除检查点

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            是否成功删除
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        if not checkpoint_path.exists():
            return False

        # 删除目录
        shutil.rmtree(checkpoint_path)

        # 更新索引
        index = self.index
        original_count = len(index.get('checkpoints', []))
        index['checkpoints'] = [
            cp for cp in index.get('checkpoints', [])
            if cp.get('checkpoint_id') != checkpoint_id
        ]
        index['total_checkpoints'] = len(index['checkpoints'])
        self._save_index(index)
        self._index = index

        return len(index['checkpoints']) < original_count

    def get_checkpoint(self, checkpoint_id: str) -> Optional[dict]:
        """
        获取检查点信息

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            检查点元数据或 None
        """
        for cp in self.index.get('checkpoints', []):
            if cp.get('checkpoint_id') == checkpoint_id:
                return cp
        return None

    def list_checkpoints(self, tags: Optional[List[str]] = None,
                         auto_only: bool = False,
                         limit: int = 50) -> List[dict]:
        """
        列出检查点

        Args:
            tags: 按标签筛选
            auto_only: 仅显示自动创建的检查点
            limit: 返回数量限制

        Returns:
            检查点列表
        """
        checkpoints = self.index.get('checkpoints', [])

        # 筛选
        if tags:
            checkpoints = [
                cp for cp in checkpoints
                if any(tag in cp.get('tags', []) for tag in tags)
            ]

        if auto_only:
            checkpoints = [
                cp for cp in checkpoints
                if cp.get('auto_created', False)
            ]

        # 按创建时间倒序
        checkpoints.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return checkpoints[:limit]

    def get_latest_checkpoint(self, auto_only: bool = False) -> Optional[dict]:
        """
        获取最新检查点

        Args:
            auto_only: 仅查找自动创建的检查点

        Returns:
            最新检查点元数据或 None
        """
        checkpoints = self.list_checkpoints(auto_only=auto_only, limit=1)
        return checkpoints[0] if checkpoints else None

    def cleanup_old_checkpoints(self, keep_count: int = 10,
                                keep_manual: bool = True,
                                days: Optional[int] = None) -> int:
        """
        清理旧检查点

        Args:
            keep_count: 保留的检查点数量
            keep_manual: 是否保留手动创建的检查点
            days: 保留最近多少天的检查点（可选）

        Returns:
            删除的检查点数量
        """
        checkpoints = self.index.get('checkpoints', [])
        deleted_count = 0

        # 按创建时间排序
        checkpoints.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        to_delete = []
        kept_count = 0

        cutoff_date = None
        if days:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        for cp in checkpoints:
            should_keep = False

            # 检查是否应该保留
            if keep_manual and not cp.get('auto_created', False):
                should_keep = True
            elif kept_count < keep_count:
                if cutoff_date is None or cp.get('created_at', '') >= cutoff_date:
                    should_keep = True
                    kept_count += 1

            if not should_keep:
                to_delete.append(cp.get('checkpoint_id'))

        # 删除检查点
        for cp_id in to_delete:
            if self.delete(cp_id):
                deleted_count += 1

        return deleted_count

    def set_callback(self, callback: Optional[Callable[[dict], None]]) -> None:
        """
        设置检查点创建回调

        Args:
            callback: 回调函数，接收检查点元数据作为参数
        """
        self._on_checkpoint_created = callback

    def start_auto_save(self, interval: Optional[int] = None) -> None:
        """
        启动自动保存

        Args:
            interval: 保存间隔（秒），默认使用初始化时的值
        """
        if interval:
            self.auto_save_interval = interval

        if self._auto_save_running:
            return

        self._auto_save_running = True

        def auto_save_loop():
            while self._auto_save_running:
                import time
                time.sleep(self.auto_save_interval)
                if self._auto_save_running:
                    self._create_auto_checkpoint()

        self._auto_save_thread = threading.Thread(target=auto_save_loop, daemon=True)
        self._auto_save_thread.start()

    def stop_auto_save(self) -> None:
        """停止自动保存"""
        self._auto_save_running = False
        if self._auto_save_thread:
            self._auto_save_thread.join(timeout=5)
            self._auto_save_thread = None

    def _create_auto_checkpoint(self) -> str:
        """创建自动检查点（内部方法）"""
        checkpoint_id = self.create(
            name=f"Auto Checkpoint {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description="Automatically created checkpoint",
            tags=["auto"],
            include_logs=False
        )

        # 更新元数据标记为自动创建
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        metadata_path = checkpoint_path / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            metadata['auto_created'] = True
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 更新索引
            index = self.index
            for cp in index.get('checkpoints', []):
                if cp.get('checkpoint_id') == checkpoint_id:
                    cp['auto_created'] = True
                    break
            self._save_index(index)
            self._index = index

        return checkpoint_id

    def get_statistics(self) -> dict:
        """
        获取检查点统计信息

        Returns:
            统计信息字典
        """
        checkpoints = self.index.get('checkpoints', [])

        # 按自动/手动分类
        auto_count = sum(1 for cp in checkpoints if cp.get('auto_created', False))
        manual_count = len(checkpoints) - auto_count

        # 按标签统计
        tags_count: Dict[str, int] = {}
        for cp in checkpoints:
            for tag in cp.get('tags', []):
                tags_count[tag] = tags_count.get(tag, 0) + 1

        # 计算总大小
        total_size = 0
        for checkpoint in checkpoints:
            cp_path = self._get_checkpoint_path(checkpoint.get('checkpoint_id', ''))
            if cp_path.exists():
                for file_path in cp_path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size

        # 时间范围
        oldest = None
        newest = None
        if checkpoints:
            timestamps = [cp.get('created_at', '') for cp in checkpoints]
            timestamps = [t for t in timestamps if t]
            if timestamps:
                oldest = min(timestamps)
                newest = max(timestamps)

        return {
            "total_checkpoints": len(checkpoints),
            "auto_checkpoints": auto_count,
            "manual_checkpoints": manual_count,
            "tags_distribution": tags_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_checkpoint": oldest,
            "newest_checkpoint": newest,
            "checkpoint_dir": str(self.checkpoint_dir)
        }

    def export_checkpoint(self, checkpoint_id: str,
                          export_path: Path,
                          format: str = "directory") -> Optional[Path]:
        """
        导出检查点

        Args:
            checkpoint_id: 检查点 ID
            export_path: 导出路径
            format: 导出格式（directory 或 zip）

        Returns:
            导出路径或 None
        """
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        if not checkpoint_path.exists():
            return None

        export_path = Path(export_path)

        if format == "directory":
            if export_path.exists():
                shutil.rmtree(export_path)
            shutil.copytree(checkpoint_path, export_path)
            return export_path

        elif format == "zip":
            if not export_path.suffix:
                export_path = export_path.with_suffix('.zip')
            shutil.make_archive(
                str(export_path.with_suffix('')),
                'zip',
                checkpoint_path
            )
            return export_path

        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def import_checkpoint(self, source_path: Path,
                          new_name: Optional[str] = None) -> Optional[str]:
        """
        导入检查点

        Args:
            source_path: 源路径（目录或 zip 文件）
            new_name: 新名称（可选）

        Returns:
            新检查点 ID 或 None
        """
        source_path = Path(source_path)

        if not source_path.exists():
            return None

        # 如果是 zip 文件，先解压
        temp_dir = None
        if source_path.suffix == '.zip':
            import tempfile
            temp_dir = Path(tempfile.mkdtemp())
            shutil.unpack_archive(str(source_path), str(temp_dir))
            source_path = temp_dir

        try:
            # 检查元数据文件
            metadata_path = source_path / "metadata.json"
            if not metadata_path.exists():
                return None

            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 生成新的检查点 ID
            new_id = f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            new_path = self._get_checkpoint_path(new_id)

            # 复制文件
            shutil.copytree(source_path, new_path)

            # 更新元数据
            metadata['checkpoint_id'] = new_id
            metadata['imported_at'] = datetime.now().isoformat()
            if new_name:
                metadata['name'] = new_name

            with open(new_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 更新索引
            index = self.index
            index['checkpoints'].append(metadata)
            index['total_checkpoints'] = len(index['checkpoints'])
            self._save_index(index)
            self._index = index

            return new_id

        finally:
            # 清理临时目录
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)

    def compare_checkpoints(self, checkpoint_id1: str,
                            checkpoint_id2: str) -> dict:
        """
        比较两个检查点

        Args:
            checkpoint_id1: 第一个检查点 ID
            checkpoint_id2: 第二个检查点 ID

        Returns:
            比较结果
        """
        cp1 = self.get_checkpoint(checkpoint_id1)
        cp2 = self.get_checkpoint(checkpoint_id2)

        if not cp1 or not cp2:
            return {"error": "一个或两个检查点不存在"}

        def load_checkpoint_file(cp_id: str, filename: str) -> Optional[dict]:
            cp_path = self._get_checkpoint_path(cp_id)
            file_path = cp_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None

        result = {
            "checkpoint1": {
                "id": checkpoint_id1,
                "name": cp1.get('name'),
                "created_at": cp1.get('created_at')
            },
            "checkpoint2": {
                "id": checkpoint_id2,
                "name": cp2.get('name'),
                "created_at": cp2.get('created_at')
            },
            "time_difference": None,
            "files_difference": {}
        }

        # 计算时间差
        try:
            time1 = datetime.fromisoformat(cp1.get('created_at', ''))
            time2 = datetime.fromisoformat(cp2.get('created_at', ''))
            result["time_difference"] = str(time2 - time1)
        except (ValueError, TypeError):
            pass

        # 比较状态文件
        for file_key in ['state', 'tasks', 'knowledge', 'sessions']:
            file1 = load_checkpoint_file(checkpoint_id1, cp1.get('files', {}).get(file_key, ''))
            file2 = load_checkpoint_file(checkpoint_id2, cp2.get('files', {}).get(file_key, ''))

            if file1 and file2:
                result["files_difference"][file_key] = {
                    "identical": file1 == file2,
                    "size1": len(json.dumps(file1)),
                    "size2": len(json.dumps(file2))
                }

        return result


# 便捷函数
def get_checkpoint_manager(checkpoint_dir: Optional[Path] = None) -> CheckpointManager:
    """获取检查点管理器实例"""
    return CheckpointManager(checkpoint_dir)


def create_checkpoint(name: Optional[str] = None,
                      description: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> str:
    """快捷创建检查点"""
    return get_checkpoint_manager().create(name, description, tags)


def restore_checkpoint(checkpoint_id: str) -> bool:
    """快捷恢复检查点"""
    return get_checkpoint_manager().restore(checkpoint_id)


def list_checkpoints(limit: int = 20) -> List[dict]:
    """快捷列出检查点"""
    return get_checkpoint_manager().list_checkpoints(limit=limit)


def get_latest_checkpoint() -> Optional[dict]:
    """快捷获取最新检查点"""
    return get_checkpoint_manager().get_latest_checkpoint()


if __name__ == "__main__":
    # 测试
    print("Testing CheckpointManager...")

    cm = CheckpointManager()
    print(f"Checkpoint directory: {cm.checkpoint_dir}")

    # 测试创建检查点
    checkpoint_id = cm.create(
        name="Test Checkpoint",
        description="This is a test checkpoint",
        tags=["test", "demo"]
    )
    print(f"Created checkpoint: {checkpoint_id}")

    # 测试列出检查点
    checkpoints = cm.list_checkpoints()
    print(f"Total checkpoints: {len(checkpoints)}")

    # 测试获取检查点
    cp_info = cm.get_checkpoint(checkpoint_id)
    print(f"Checkpoint info: {cp_info}")

    # 测试获取统计
    stats = cm.get_statistics()
    print(f"Statistics: {stats}")

    # 测试自动保存功能
    print("\nTesting auto-save...")
    cm.start_auto_save(interval=60)  # 60秒间隔
    print("Auto-save started (will create checkpoint every 60 seconds)")

    # 测试比较检查点
    if len(checkpoints) >= 2:
        comparison = cm.compare_checkpoints(
            checkpoints[0]['checkpoint_id'],
            checkpoints[1]['checkpoint_id']
        )
        print(f"Comparison: {comparison}")

    # 停止自动保存
    cm.stop_auto_save()
    print("Auto-save stopped")

    # 测试删除检查点（清理测试数据）
    deleted = cm.delete(checkpoint_id)
    print(f"Deleted checkpoint: {deleted}")

    print("\nAll tests passed!")
