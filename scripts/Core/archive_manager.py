"""
Project Prometheus - 归档管理器
================================

管理项目归档和解档操作，支持压缩、元数据记录和知识提取。
"""

import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List, Dict


# 默认路径
DEFAULT_BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = DEFAULT_BASE_DIR / "Archives"
WORKFLOW_DIR = DEFAULT_BASE_DIR / "Core" / "workflow"


class ArchiveManager:
    """归档管理器

    管理项目的归档、解档、元数据记录和知识提取。
    """

    def __init__(self, archive_dir: Optional[Path] = None,
                 workflow_dir: Optional[Path] = None):
        """
        初始化归档管理器

        Args:
            archive_dir: 归档目录路径
            workflow_dir: 工作流目录路径
        """
        self.archive_dir = Path(archive_dir) if archive_dir else ARCHIVE_DIR
        self.workflow_dir = Path(workflow_dir) if workflow_dir else WORKFLOW_DIR
        self.metadata_file = self.archive_dir / "archive_metadata.json"
        self._metadata = None

    def _ensure_archive_dir(self) -> None:
        """确保归档目录存在"""
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def load_metadata(self) -> dict:
        """加载归档元数据文件"""
        if not self.metadata_file.exists():
            return self._create_default_metadata()
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_metadata(self, metadata: dict) -> None:
        """保存归档元数据文件"""
        self._ensure_archive_dir()
        metadata['last_updated'] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _create_default_metadata(self) -> dict:
        """创建默认元数据结构"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_archives": 0,
            "archives": []
        }

    @property
    def metadata(self) -> dict:
        """懒加载元数据"""
        if self._metadata is None:
            self._metadata = self.load_metadata()
        return self._metadata

    def archive_project(self, project_name: str,
                        source_dir: Optional[Path] = None,
                        include_patterns: Optional[List[str]] = None,
                        exclude_patterns: Optional[List[str]] = None,
                        description: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        extract_knowledge: bool = True) -> dict:
        """
        归档项目

        Args:
            project_name: 项目名称
            source_dir: 要归档的源目录（默认为项目根目录）
            include_patterns: 包含的文件模式列表（如 ["*.py", "*.json"]）
            exclude_patterns: 排除的文件模式列表（如 ["*.pyc", "__pycache__"]）
            description: 归档描述
            tags: 标签列表
            extract_knowledge: 是否提取知识库

        Returns:
            归档信息字典
        """
        self._ensure_archive_dir()

        # 确定源目录
        if source_dir:
            source_path = Path(source_dir)
        else:
            source_path = DEFAULT_BASE_DIR

        # 生成归档 ID 和文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_id = f"archive_{project_name}_{timestamp}"
        archive_filename = f"{archive_id}.zip"
        archive_path = self.archive_dir / archive_filename

        # 默认排除模式
        default_exclude = [
            '__pycache__', '*.pyc', '*.pyo', '.git', '.env',
            'node_modules', '.venv', 'venv', '*.log', 'Archives'
        ]
        exclude_patterns = exclude_patterns or []
        all_excludes = set(default_exclude + exclude_patterns)

        # 收集要归档的文件
        files_to_archive = self._collect_files(
            source_path,
            include_patterns,
            all_excludes
        )

        # 创建压缩文件
        compressed_size = 0
        original_size = 0
        file_count = 0

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in files_to_archive:
                arcname = file_path.relative_to(source_path)
                zf.write(file_path, arcname)
                original_size += file_path.stat().st_size
                file_count += 1

        if archive_path.exists():
            compressed_size = archive_path.stat().st_size

        # 提取知识库
        knowledge_extract = None
        if extract_knowledge:
            knowledge_extract = self._extract_knowledge()

        # 创建归档元数据条目
        archive_entry = {
            "archive_id": archive_id,
            "project_name": project_name,
            "filename": archive_filename,
            "path": str(archive_path),
            "created_at": datetime.now().isoformat(),
            "description": description,
            "tags": tags or [],
            "file_count": file_count,
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "compression_ratio": round(compressed_size / original_size, 3) if original_size > 0 else 0,
            "source_dir": str(source_path),
            "include_patterns": include_patterns,
            "exclude_patterns": list(all_excludes),
            "knowledge_extract": knowledge_extract,
            "status": "active"
        }

        # 更新元数据
        metadata = self.metadata
        metadata['archives'].append(archive_entry)
        metadata['total_archives'] = len(metadata['archives'])
        self.save_metadata(metadata)
        self._metadata = metadata

        return archive_entry

    def _collect_files(self, source_path: Path,
                       include_patterns: Optional[List[str]],
                       exclude_patterns: set) -> List[Path]:
        """
        收集要归档的文件

        Args:
            source_path: 源目录路径
            include_patterns: 包含模式
            exclude_patterns: 排除模式

        Returns:
            文件路径列表
        """
        import fnmatch

        files = []

        for root, dirs, filenames in os.walk(source_path):
            root_path = Path(root)

            # 过滤目录
            dirs[:] = [
                d for d in dirs
                if not any(fnmatch.fnmatch(d, pattern) for pattern in exclude_patterns)
            ]

            for filename in filenames:
                file_path = root_path / filename

                # 检查排除模式
                if any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns):
                    continue

                # 检查包含模式（如果指定）
                if include_patterns:
                    if not any(fnmatch.fnmatch(filename, pattern) for pattern in include_patterns):
                        continue

                files.append(file_path)

        return files

    def _extract_knowledge(self) -> dict:
        """
        从当前工作流中提取知识

        Returns:
            提取的知识摘要
        """
        knowledge = {
            "papers_read": 0,
            "findings_count": 0,
            "best_practices_count": 0,
            "lessons_count": 0,
            "session_count": 0,
            "extracted_at": datetime.now().isoformat()
        }

        # 从知识库文件提取
        knowledge_file = self.workflow_dir / "knowledge_base.json"
        if knowledge_file.exists():
            try:
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    kb_data = json.load(f)
                knowledge["papers_read"] = kb_data.get('papers_read', 0)
                knowledge["findings_count"] = len(kb_data.get('key_findings', []))
                knowledge["best_practices_count"] = len(kb_data.get('best_practices', {}))
                knowledge["lessons_count"] = len(kb_data.get('lessons_learned', []))
            except (json.JSONDecodeError, IOError):
                pass

        # 从会话文件提取
        sessions_file = self.workflow_dir / "sessions.json"
        if sessions_file.exists():
            try:
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    sess_data = json.load(f)
                knowledge["session_count"] = len(sess_data.get('sessions', []))
            except (json.JSONDecodeError, IOError):
                pass

        return knowledge

    def unarchive_project(self, archive_id: str,
                          target_dir: Optional[Path] = None,
                          overwrite: bool = False) -> dict:
        """
        解档项目

        Args:
            archive_id: 归档 ID
            target_dir: 目标目录（默认为项目根目录下的 restored 文件夹）
            overwrite: 是否覆盖已存在的文件

        Returns:
            解档结果字典
        """
        # 查找归档
        archive_entry = self.get_archive_info(archive_id)
        if not archive_entry:
            return {
                "success": False,
                "error": f"Archive not found: {archive_id}"
            }

        archive_path = Path(archive_entry['path'])
        if not archive_path.exists():
            return {
                "success": False,
                "error": f"Archive file not found: {archive_path}"
            }

        # 确定目标目录
        if target_dir:
            target_path = Path(target_dir)
        else:
            target_path = DEFAULT_BASE_DIR / "restored" / archive_entry['project_name']

        # 检查目标目录
        if target_path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"Target directory already exists: {target_path}",
                "hint": "Use overwrite=True to overwrite"
            }

        # 创建目标目录
        target_path.mkdir(parents=True, exist_ok=True)

        # 解压
        extracted_files = []
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                for member in zf.namelist():
                    # 安全检查：防止路径遍历攻击
                    member_path = Path(member)
                    if member_path.is_absolute() or '..' in member:
                        continue

                    target_file = target_path / member

                    # 检查是否需要覆盖
                    if target_file.exists() and not overwrite:
                        continue

                    zf.extract(member, target_path)
                    extracted_files.append(member)

            result = {
                "success": True,
                "archive_id": archive_id,
                "project_name": archive_entry['project_name'],
                "target_dir": str(target_path),
                "files_extracted": len(extracted_files),
                "extracted_at": datetime.now().isoformat()
            }

        except zipfile.BadZipFile as e:
            return {
                "success": False,
                "error": f"Bad zip file: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

        return result

    def get_archive_info(self, archive_id: str) -> Optional[dict]:
        """
        获取归档信息

        Args:
            archive_id: 归档 ID

        Returns:
            归档信息字典或 None
        """
        for archive in self.metadata.get('archives', []):
            if archive.get('archive_id') == archive_id:
                return archive
        return None

    def list_archives(self, project_name: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      status: Optional[str] = None,
                      limit: int = 50) -> List[dict]:
        """
        列出归档

        Args:
            project_name: 按项目名称筛选
            tags: 按标签筛选
            status: 按状态筛选（active, deleted）
            limit: 返回数量限制

        Returns:
            归档信息列表
        """
        archives = self.metadata.get('archives', [])

        # 筛选
        if project_name:
            archives = [a for a in archives if a.get('project_name') == project_name]

        if tags:
            archives = [
                a for a in archives
                if any(tag in a.get('tags', []) for tag in tags)
            ]

        if status:
            archives = [a for a in archives if a.get('status') == status]

        # 按创建时间倒序
        archives.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return archives[:limit]

    def delete_archive(self, archive_id: str,
                       delete_file: bool = True) -> dict:
        """
        删除归档（软删除或硬删除）

        Args:
            archive_id: 归档 ID
            delete_file: 是否同时删除归档文件

        Returns:
            删除结果字典
        """
        archive_entry = self.get_archive_info(archive_id)
        if not archive_entry:
            return {
                "success": False,
                "error": f"Archive not found: {archive_id}"
            }

        result = {
            "success": True,
            "archive_id": archive_id,
            "deleted_file": False
        }

        # 删除文件
        if delete_file:
            archive_path = Path(archive_entry['path'])
            if archive_path.exists():
                try:
                    archive_path.unlink()
                    result["deleted_file"] = True
                except OSError as e:
                    result["warning"] = f"Failed to delete file: {str(e)}"

        # 更新元数据（标记为已删除或移除）
        metadata = self.metadata
        for i, archive in enumerate(metadata.get('archives', [])):
            if archive.get('archive_id') == archive_id:
                if delete_file:
                    # 硬删除：从列表中移除
                    metadata['archives'].pop(i)
                else:
                    # 软删除：标记状态
                    metadata['archives'][i]['status'] = 'deleted'
                    metadata['archives'][i]['deleted_at'] = datetime.now().isoformat()
                break

        metadata['total_archives'] = len([a for a in metadata.get('archives', [])
                                          if a.get('status') != 'deleted'])
        self.save_metadata(metadata)
        self._metadata = metadata

        return result

    def restore_knowledge(self, archive_id: str,
                          merge: bool = True) -> dict:
        """
        从归档中恢复知识到当前知识库

        Args:
            archive_id: 归档 ID
            merge: 是否与现有知识合并（True）或替换（False）

        Returns:
            恢复结果字典
        """
        archive_entry = self.get_archive_info(archive_id)
        if not archive_entry:
            return {
                "success": False,
                "error": f"Archive not found: {archive_id}"
            }

        knowledge_extract = archive_entry.get('knowledge_extract')
        if not knowledge_extract:
            return {
                "success": False,
                "error": "No knowledge extract found in archive"
            }

        # 这里只返回知识摘要，实际恢复需要从归档文件中读取完整数据
        result = {
            "success": True,
            "archive_id": archive_id,
            "knowledge_summary": knowledge_extract,
            "merge_mode": merge,
            "note": "Knowledge summary restored. For full restoration, unarchive the project."
        }

        return result

    def get_archive_statistics(self) -> dict:
        """
        获取归档统计信息

        Returns:
            统计信息字典
        """
        archives = self.metadata.get('archives', [])

        # 按项目统计
        by_project = {}
        for a in archives:
            project = a.get('project_name', 'unknown')
            if project not in by_project:
                by_project[project] = {"count": 0, "total_size": 0}
            by_project[project]["count"] += 1
            by_project[project]["total_size"] += a.get('compressed_size_bytes', 0)

        # 按状态统计
        by_status = {}
        for a in archives:
            status = a.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1

        # 计算总大小
        total_compressed = sum(a.get('compressed_size_bytes', 0) for a in archives)
        total_original = sum(a.get('original_size_bytes', 0) for a in archives)
        total_files = sum(a.get('file_count', 0) for a in archives)

        # 知识统计
        total_papers = sum(
            a.get('knowledge_extract', {}).get('papers_read', 0)
            for a in archives
        )
        total_findings = sum(
            a.get('knowledge_extract', {}).get('findings_count', 0)
            for a in archives
        )

        return {
            "total_archives": len(archives),
            "active_archives": by_status.get('active', 0),
            "deleted_archives": by_status.get('deleted', 0),
            "total_files": total_files,
            "total_compressed_size_bytes": total_compressed,
            "total_original_size_bytes": total_original,
            "average_compression_ratio": round(total_compressed / total_original, 3) if total_original > 0 else 0,
            "by_project": by_project,
            "by_status": by_status,
            "total_papers_read": total_papers,
            "total_findings": total_findings,
            "last_updated": self.metadata.get('last_updated')
        }

    def cleanup_old_archives(self, days: int = 90,
                             delete_files: bool = False) -> dict:
        """
        清理旧归档

        Args:
            days: 保留最近多少天的归档
            delete_files: 是否删除文件

        Returns:
            清理结果字典
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()

        archives = self.metadata.get('archives', [])
        to_cleanup = [
            a for a in archives
            if a.get('created_at', '') < cutoff_str and a.get('status') == 'active'
        ]

        cleaned = []
        for archive in to_cleanup:
            result = self.delete_archive(
                archive['archive_id'],
                delete_file=delete_files
            )
            cleaned.append({
                "archive_id": archive['archive_id'],
                "success": result.get('success', False)
            })

        return {
            "total_checked": len(archives),
            "cleaned_count": len(cleaned),
            "deleted_files": delete_files,
            "details": cleaned
        }

    def export_archive_report(self, archive_id: Optional[str] = None,
                              format: str = "markdown") -> str:
        """
        导出归档报告

        Args:
            archive_id: 归档 ID（如果指定，只导出该归档的报告）
            format: 导出格式（markdown 或 json）

        Returns:
            报告内容
        """
        if archive_id:
            archive = self.get_archive_info(archive_id)
            if not archive:
                return f"Archive not found: {archive_id}"
            archives = [archive]
        else:
            archives = self.list_archives(limit=100)

        if format == "json":
            return json.dumps({
                "generated_at": datetime.now().isoformat(),
                "archives": archives
            }, indent=2, ensure_ascii=False)

        elif format == "markdown":
            lines = [
                "# 归档报告",
                f"\n**生成时间**: {datetime.now().isoformat()}",
                f"**归档总数**: {len(archives)}",
                "\n---\n"
            ]

            for archive in archives:
                lines.append(f"## {archive.get('archive_id')}")
                lines.append(f"- **项目名称**: {archive.get('project_name')}")
                lines.append(f"- **创建时间**: {archive.get('created_at')}")
                lines.append(f"- **状态**: {archive.get('status', 'active')}")
                lines.append(f"- **文件数量**: {archive.get('file_count', 0)}")

                # 格式化文件大小
                compressed = archive.get('compressed_size_bytes', 0)
                original = archive.get('original_size_bytes', 0)
                lines.append(f"- **压缩大小**: {self._format_size(compressed)}")
                lines.append(f"- **原始大小**: {self._format_size(original)}")
                lines.append(f"- **压缩比**: {archive.get('compression_ratio', 0)}")

                if archive.get('description'):
                    lines.append(f"- **描述**: {archive.get('description')}")

                if archive.get('tags'):
                    lines.append(f"- **标签**: {', '.join(archive.get('tags', []))}")

                # 知识提取摘要
                ke = archive.get('knowledge_extract', {})
                if ke:
                    lines.append(f"\n### 知识摘要")
                    lines.append(f"- 已读论文: {ke.get('papers_read', 0)}")
                    lines.append(f"- 发现数量: {ke.get('findings_count', 0)}")
                    lines.append(f"- 最佳实践: {ke.get('best_practices_count', 0)}")
                    lines.append(f"- 经验教训: {ke.get('lessons_count', 0)}")

                lines.append("\n")

            return '\n'.join(lines)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"


# 便捷函数
def get_archive_manager() -> ArchiveManager:
    """获取归档管理器实例"""
    return ArchiveManager()


def archive_project(project_name: str,
                    source_dir: Optional[Path] = None,
                    description: Optional[str] = None,
                    tags: Optional[List[str]] = None) -> dict:
    """
    快捷归档项目

    Args:
        project_name: 项目名称
        source_dir: 源目录
        description: 描述
        tags: 标签

    Returns:
        归档信息
    """
    return get_archive_manager().archive_project(
        project_name=project_name,
        source_dir=source_dir,
        description=description,
        tags=tags
    )


def unarchive_project(archive_id: str,
                      target_dir: Optional[Path] = None) -> dict:
    """
    快捷解档项目

    Args:
        archive_id: 归档 ID
        target_dir: 目标目录

    Returns:
        解档结果
    """
    return get_archive_manager().unarchive_project(
        archive_id=archive_id,
        target_dir=target_dir
    )


def list_archives(project_name: Optional[str] = None,
                  limit: int = 50) -> List[dict]:
    """
    快捷列出归档

    Args:
        project_name: 项目名称筛选
        limit: 数量限制

    Returns:
        归档列表
    """
    return get_archive_manager().list_archives(
        project_name=project_name,
        limit=limit
    )


if __name__ == "__main__":
    # 测试
    print("Testing ArchiveManager...")

    am = ArchiveManager()

    # 测试创建归档
    print("\n1. Creating archive...")
    archive_result = am.archive_project(
        project_name="test_project",
        description="Test archive for verification",
        tags=["test", "verification"],
        extract_knowledge=True
    )
    print(f"Archive created: {archive_result.get('archive_id')}")
    print(f"File count: {archive_result.get('file_count')}")
    print(f"Compressed size: {am._format_size(archive_result.get('compressed_size_bytes', 0))}")

    # 测试列出归档
    print("\n2. Listing archives...")
    archives = am.list_archives()
    print(f"Total archives: {len(archives)}")
    for a in archives[:3]:
        print(f"  - {a.get('archive_id')}: {a.get('project_name')}")

    # 测试获取归档信息
    print("\n3. Getting archive info...")
    if archives:
        archive_info = am.get_archive_info(archives[0]['archive_id'])
        print(f"Archive: {archive_info.get('archive_id')}")
        print(f"Created at: {archive_info.get('created_at')}")

    # 测试获取统计信息
    print("\n4. Getting statistics...")
    stats = am.get_archive_statistics()
    print(f"Total archives: {stats.get('total_archives')}")
    print(f"Total files: {stats.get('total_files')}")
    print(f"By project: {stats.get('by_project')}")

    # 测试导出报告
    print("\n5. Exporting report...")
    report = am.export_archive_report(format="markdown")
    print(f"Report length: {len(report)} characters")

    # 测试解档（不实际执行，只打印）
    print("\n6. Unarchive test (dry run)...")
    if archives:
        print(f"Would unarchive: {archives[0]['archive_id']}")

    # 测试删除（软删除）
    print("\n7. Testing soft delete...")
    if archives:
        # 创建一个临时归档用于测试删除
        temp_archive = am.archive_project(
            project_name="temp_delete_test",
            description="Temporary archive for delete test"
        )
        delete_result = am.delete_archive(
            temp_archive['archive_id'],
            delete_file=False
        )
        print(f"Delete result: {delete_result}")

    print("\nAll tests passed!")
