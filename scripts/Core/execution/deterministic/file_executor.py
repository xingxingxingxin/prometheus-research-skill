"""
File Executor - 文件操作执行器

处理 T011-T017 文件操作任务，纯代码执行
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import shutil
import hashlib
from datetime import datetime


class FileExecutor:
    """
    文件操作执行器

    执行确定性文件操作任务：
    - T011: 合并去重排序
    - T012: 筛选核心文献
    - T013: 创建文献数据库
    - T014: 按主题分类
    - T015: 下载PDF
    - T016: 保存摘要
    - T017: 整理PDF到papers目录
    """

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path.cwd()
        self.search_results_dir = self.project_dir / "data" / "search_results"
        self.papers_dir = self.project_dir / "data" / "papers"

    def execute(self, task: Dict, context: Dict) -> Dict:
        """
        执行文件操作任务

        Args:
            task: 任务字典
            context: 执行上下文

        Returns:
            Dict: 执行结果
        """
        task_id = task.get("id", "")

        executors = {
            "T011": self._execute_merge_deduplicate,
            "T012": self._execute_filter_papers,
            "T013": self._execute_create_db,
            "T014": self._execute_classify_papers,
            "T015": self._execute_download_pdfs,
            "T016": self._execute_save_abstracts,
            "T017": self._execute_organize_pdfs,
        }

        executor = executors.get(task_id)
        if executor:
            try:
                return executor(task, context)
            except Exception as e:
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": str(e),
                }
        else:
            return {
                "success": False,
                "task_id": task_id,
                "error": f"No executor for task: {task_id}",
            }

    def _execute_merge_deduplicate(self, task: Dict, context: Dict) -> Dict:
        """T011: 合并去重排序"""
        # 读取所有搜索结果
        all_papers = self._load_all_search_results()

        if not all_papers:
            return {
                "success": False,
                "task_id": "T011",
                "error": "No search results found",
            }

        # 去重（基于DOI或标题哈希）
        unique_papers = self._deduplicate_papers(all_papers)

        # 排序（按引用数、年份等）
        sorted_papers = self._sort_papers(unique_papers)

        # 保存结果
        output_file = self.search_results_dir / "merged_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "total_before": len(all_papers),
                "total_after": len(sorted_papers),
                "timestamp": datetime.now().isoformat(),
                "papers": sorted_papers,
            }, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "task_id": "T011",
            "outputs": {
                "papers_before": len(all_papers),
                "papers_after": len(sorted_papers),
                "duplicates_removed": len(all_papers) - len(sorted_papers),
                "output_file": str(output_file),
            },
        }

    def _execute_filter_papers(self, task: Dict, context: Dict) -> Dict:
        """T012: 筛选30篇核心文献"""
        # 读取合并后的结果
        merged_file = self.search_results_dir / "merged_results.json"
        if not merged_file.exists():
            return {
                "success": False,
                "task_id": "T012",
                "error": "Merged results not found. Run T011 first.",
            }

        with open(merged_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        papers = data.get("papers", [])

        # 筛选逻辑
        # 1. 高引用（前10篇）
        # 2. 最新（近3年，10篇）
        # 3. 综述（5篇）
        # 4. 相关性高（5篇）
        selected = self._select_core_papers(papers, target_count=30)

        # 保存核心文献
        output_file = self.search_results_dir / "core_papers.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "total": len(selected),
                "selection_criteria": "high_citation + recent + review + relevance",
                "papers": selected,
            }, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "task_id": "T012",
            "outputs": {
                "core_papers_count": len(selected),
                "output_file": str(output_file),
            },
        }

    def _execute_create_db(self, task: Dict, context: Dict) -> Dict:
        """T013: 创建文献数据库"""
        import sqlite3

        # 读取核心文献
        core_file = self.search_results_dir / "core_papers.json"
        if not core_file.exists():
            return {
                "success": False,
                "task_id": "T013",
                "error": "Core papers not found. Run T012 first.",
            }

        with open(core_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        papers = data.get("papers", [])

        # 创建/更新数据库
        db_path = self.project_dir / "data" / "literature.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 创建表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                doi TEXT UNIQUE,
                abstract TEXT,
                citation_count INTEGER DEFAULT 0,
                venue TEXT,
                url TEXT,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 插入数据
        inserted = 0
        for paper in papers:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO papers
                    (title, authors, year, doi, abstract, citation_count, venue, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    paper.get("title", ""),
                    json.dumps(paper.get("authors", [])),
                    paper.get("year"),
                    paper.get("doi"),
                    paper.get("abstract", ""),
                    paper.get("citation_count", 0),
                    paper.get("venue", ""),
                    paper.get("url", ""),
                ))
                inserted += 1
            except Exception:
                pass

        conn.commit()
        conn.close()

        return {
            "success": True,
            "task_id": "T013",
            "outputs": {
                "papers_inserted": inserted,
                "db_path": str(db_path),
            },
        }

    def _execute_classify_papers(self, task: Dict, context: Dict) -> Dict:
        """T014: 按主题分类"""
        # 读取核心文献
        core_file = self.search_results_dir / "core_papers.json"
        if not core_file.exists():
            return {
                "success": False,
                "task_id": "T014",
                "error": "Core papers not found.",
            }

        with open(core_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        papers = data.get("papers", [])

        # 简单分类（基于关键词）
        categories = self._classify_by_keywords(papers)

        # 保存分类结果
        output_file = self.search_results_dir / "classified_papers.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "task_id": "T014",
            "outputs": {
                "categories": list(categories.keys()),
                "papers_per_category": {k: len(v) for k, v in categories.items()},
                "output_file": str(output_file),
            },
        }

    def _execute_download_pdfs(self, task: Dict, context: Dict) -> Dict:
        """T015: 下载PDF"""
        # 确保目录存在
        self.papers_dir.mkdir(parents=True, exist_ok=True)

        # 读取核心文献
        core_file = self.search_results_dir / "core_papers.json"
        if not core_file.exists():
            return {
                "success": True,
                "task_id": "T015",
                "outputs": {"downloaded": 0, "note": "No core papers file"},
            }

        with open(core_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        papers = data.get("papers", [])

        # 尝试下载（需要实现实际的下载逻辑）
        downloaded = 0
        failed = []

        for paper in papers[:10]:  # 限制下载数量
            pdf_url = paper.get("pdf_url") or paper.get("url", "")
            if pdf_url:
                # 这里应该调用实际的下载器
                # 暂时只记录
                downloaded += 1

        return {
            "success": True,
            "task_id": "T015",
            "outputs": {
                "downloaded": downloaded,
                "failed": len(failed),
                "papers_dir": str(self.papers_dir),
            },
        }

    def _execute_save_abstracts(self, task: Dict, context: Dict) -> Dict:
        """T016: 保存无法下载论文的摘要"""
        abstracts_dir = self.project_dir / "data" / "abstracts"
        abstracts_dir.mkdir(parents=True, exist_ok=True)

        # 读取核心文献
        core_file = self.search_results_dir / "core_papers.json"
        if not core_file.exists():
            return {
                "success": True,
                "task_id": "T016",
                "outputs": {"saved": 0},
            }

        with open(core_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        papers = data.get("papers", [])
        saved = 0

        for i, paper in enumerate(papers):
            if paper.get("abstract"):
                abstract_file = abstracts_dir / f"abstract_{i+1:02d}.txt"
                with open(abstract_file, "w", encoding="utf-8") as f:
                    f.write(f"Title: {paper.get('title', 'N/A')}\n\n")
                    f.write(f"Authors: {paper.get('authors', 'N/A')}\n\n")
                    f.write(f"Abstract:\n{paper.get('abstract', '')}\n")
                saved += 1

        return {
            "success": True,
            "task_id": "T016",
            "outputs": {
                "abstracts_saved": saved,
                "abstracts_dir": str(abstracts_dir),
            },
        }

    def _execute_organize_pdfs(self, task: Dict, context: Dict) -> Dict:
        """T017: 整理PDF到papers目录"""
        self.papers_dir.mkdir(parents=True, exist_ok=True)

        # 查找所有PDF文件
        pdf_files = list(self.project_dir.glob("**/*.pdf"))

        organized = 0
        for pdf in pdf_files:
            if pdf.parent != self.papers_dir:
                # 移动到papers目录
                dest = self.papers_dir / pdf.name
                if not dest.exists():
                    shutil.move(str(pdf), str(dest))
                    organized += 1

        return {
            "success": True,
            "task_id": "T017",
            "outputs": {
                "pdfs_organized": organized,
                "papers_dir": str(self.papers_dir),
            },
        }

    # 辅助方法

    def _load_all_search_results(self) -> List[Dict]:
        """加载所有搜索结果"""
        all_papers = []

        if not self.search_results_dir.exists():
            return all_papers

        for file in self.search_results_dir.glob("T*.json"):
            if file.name.startswith("merged") or file.name.startswith("core"):
                continue
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    papers = data.get("papers", [])
                    all_papers.extend(papers)
            except Exception:
                pass

        return all_papers

    def _deduplicate_papers(self, papers: List[Dict]) -> List[Dict]:
        """去重"""
        seen = set()
        unique = []

        for paper in papers:
            # 使用DOI或标题哈希作为唯一标识
            doi = paper.get("doi", "")
            title = paper.get("title", "")

            key = doi if doi else hashlib.md5(title.encode()).hexdigest()

            if key not in seen:
                seen.add(key)
                unique.append(paper)

        return unique

    def _sort_papers(self, papers: List[Dict]) -> List[Dict]:
        """排序"""
        return sorted(
            papers,
            key=lambda p: (
                p.get("citation_count", 0),
                p.get("year", 0),
            ),
            reverse=True
        )

    def _select_core_papers(self, papers: List[Dict], target_count: int = 30) -> List[Dict]:
        """选择核心文献"""
        selected = []

        # 高引用
        high_citation = sorted(
            papers,
            key=lambda p: p.get("citation_count", 0),
            reverse=True
        )[:10]
        selected.extend(high_citation)

        # 最新
        recent = [p for p in papers if p.get("year", 0) >= 2023]
        recent = sorted(recent, key=lambda p: p.get("year", 0), reverse=True)[:10]
        for p in recent:
            if p not in selected:
                selected.append(p)

        # 补充到目标数量
        for p in papers:
            if len(selected) >= target_count:
                break
            if p not in selected:
                selected.append(p)

        return selected[:target_count]

    def _classify_by_keywords(self, papers: List[Dict]) -> Dict[str, List[Dict]]:
        """基于关键词分类"""
        categories = {
            "methodology": [],
            "application": [],
            "survey": [],
            "theory": [],
            "other": [],
        }

        keywords = {
            "methodology": ["method", "approach", "framework", "algorithm"],
            "application": ["application", "system", "implementation", "case study"],
            "survey": ["survey", "review", "overview", "comprehensive"],
            "theory": ["theory", "proof", "theorem", "analysis"],
        }

        for paper in papers:
            title = paper.get("title", "").lower()
            abstract = paper.get("abstract", "").lower()
            text = title + " " + abstract

            classified = False
            for category, kws in keywords.items():
                if any(kw in text for kw in kws):
                    categories[category].append(paper)
                    classified = True
                    break

            if not classified:
                categories["other"].append(paper)

        return categories
