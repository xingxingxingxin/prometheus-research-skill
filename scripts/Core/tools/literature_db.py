"""
文献数据库管理工具
==================

管理科研项目的文献数据库，支持存储、查询、去重和分析。
使用 SQLite 作为后端存储。
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager


# 默认数据库路径
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "Projects" / "literature.db"


class LiteratureDB:
    """文献数据库管理器"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径，默认为 Projects/literature.db
        """
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_schema(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 论文表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    title_normalized TEXT,
                    authors TEXT,
                    abstract TEXT,
                    year INTEGER,
                    citation_count INTEGER DEFAULT 0,
                    reference_count INTEGER DEFAULT 0,
                    publication_venue TEXT,
                    journal TEXT,
                    doi TEXT UNIQUE,
                    arxiv_id TEXT,
                    semantic_scholar_id TEXT,
                    pdf_url TEXT,
                    source_url TEXT,
                    is_open_access INTEGER DEFAULT 0,
                    fields_of_study TEXT,
                    keywords TEXT,
                    reading_status TEXT DEFAULT 'unread',
                    importance_score REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 作者表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS authors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    name_normalized TEXT,
                    affiliation TEXT,
                    semantic_scholar_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 论文-作者关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_authors (
                    paper_id INTEGER,
                    author_id INTEGER,
                    author_order INTEGER,
                    PRIMARY KEY (paper_id, author_id),
                    FOREIGN KEY (paper_id) REFERENCES papers(id),
                    FOREIGN KEY (author_id) REFERENCES authors(id)
                )
            ''')

            # 引用关系表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS citations (
                    citing_paper_id INTEGER,
                    cited_paper_id INTEGER,
                    PRIMARY KEY (citing_paper_id, cited_paper_id),
                    FOREIGN KEY (citing_paper_id) REFERENCES papers(id),
                    FOREIGN KEY (cited_paper_id) REFERENCES papers(id)
                )
            ''')

            # 标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT
                )
            ''')

            # 论文-标签关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_tags (
                    paper_id INTEGER,
                    tag_id INTEGER,
                    PRIMARY KEY (paper_id, tag_id),
                    FOREIGN KEY (paper_id) REFERENCES papers(id),
                    FOREIGN KEY (tag_id) REFERENCES tags(id)
                )
            ''')

            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_citations ON papers(citation_count)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title_normalized)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(reading_status)')

    def _normalize_title(self, title: str) -> str:
        """标准化标题（用于去重）"""
        import re
        # 移除标点、转小写、合并空格
        title = re.sub(r'[^\w\s]', '', title.lower())
        title = re.sub(r'\s+', ' ', title).strip()
        return title

    def insert_paper(self, paper: Dict[str, Any]) -> Optional[int]:
        """
        插入论文记录

        Args:
            paper: 论文信息字典

        Returns:
            插入的记录 ID，如果已存在则返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            title = paper.get('title', '')
            title_normalized = self._normalize_title(title)

            # 检查是否已存在（通过标题或 DOI）
            if paper.get('doi'):
                cursor.execute('SELECT id FROM papers WHERE doi = ?', (paper['doi'],))
                if cursor.fetchone():
                    return None

            cursor.execute('SELECT id FROM papers WHERE title_normalized = ?', (title_normalized,))
            if cursor.fetchone():
                return None

            # 插入论文
            cursor.execute('''
                INSERT INTO papers (
                    title, title_normalized, authors, abstract, year,
                    citation_count, reference_count, publication_venue, journal,
                    doi, arxiv_id, semantic_scholar_id, pdf_url, source_url,
                    is_open_access, fields_of_study, keywords, importance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                title_normalized,
                json.dumps(paper.get('authors', [])),
                paper.get('abstract', ''),
                paper.get('year'),
                paper.get('citation_count', 0),
                paper.get('reference_count', 0),
                paper.get('publication_venue', ''),
                paper.get('journal', ''),
                paper.get('doi') or paper.get('external_ids', {}).get('DOI'),
                paper.get('arxiv_id') or paper.get('external_ids', {}).get('ArXiv'),
                paper.get('paper_id') or paper.get('semantic_scholar_id'),
                paper.get('open_access_pdf') or paper.get('pdf_url'),
                paper.get('url', ''),
                1 if paper.get('is_open_access') else 0,
                json.dumps(paper.get('fields_of_study', [])),
                json.dumps(paper.get('keywords', [])),
                self._calculate_importance(paper)
            ))

            return cursor.lastrowid

    def _calculate_importance(self, paper: Dict) -> float:
        """计算论文重要性分数"""
        score = 0.0

        # 引用数权重
        citations = paper.get('citation_count', 0)
        score += min(citations / 100, 10)  # 最多 10 分

        # 年份权重（越新越好）
        year = paper.get('year')
        if year:
            current_year = datetime.now().year
            age = current_year - year
            score += max(0, 5 - age)  # 最多 5 分

        # 开放获取权重
        if paper.get('is_open_access') or paper.get('open_access_pdf'):
            score += 2

        return round(score, 2)

    def insert_papers(self, papers: List[Dict]) -> Tuple[int, int]:
        """
        批量插入论文

        Args:
            papers: 论文列表

        Returns:
            (成功数量, 跳过数量)
        """
        success = 0
        skipped = 0

        for paper in papers:
            result = self.insert_paper(paper)
            if result:
                success += 1
            else:
                skipped += 1

        return success, skipped

    def search(self, query: str, limit: int = 50) -> List[Dict]:
        """
        搜索论文

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            论文列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            search_term = f"%{query}%"
            cursor.execute('''
                SELECT * FROM papers
                WHERE title LIKE ? OR abstract LIKE ? OR authors LIKE ?
                ORDER BY importance_score DESC, citation_count DESC
                LIMIT ?
            ''', (search_term, search_term, search_term, limit))

            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_top_cited(self, limit: int = 20, year_range: Tuple[int, int] = None) -> List[Dict]:
        """
        获取高引用论文

        Args:
            limit: 返回数量
            year_range: 年份范围

        Returns:
            论文列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if year_range:
                cursor.execute('''
                    SELECT * FROM papers
                    WHERE year BETWEEN ? AND ?
                    ORDER BY citation_count DESC
                    LIMIT ?
                ''', (year_range[0], year_range[1], limit))
            else:
                cursor.execute('''
                    SELECT * FROM papers
                    ORDER BY citation_count DESC
                    LIMIT ?
                ''', (limit,))

            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_recent(self, limit: int = 20) -> List[Dict]:
        """获取最近添加的论文"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM papers
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_by_status(self, status: str) -> List[Dict]:
        """
        按阅读状态获取论文

        Args:
            status: 状态 (unread, reading, read, important)

        Returns:
            论文列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM papers
                WHERE reading_status = ?
                ORDER BY importance_score DESC
            ''', (status,))

            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def update_status(self, paper_id: int, status: str, notes: str = None) -> bool:
        """
        更新论文阅读状态

        Args:
            paper_id: 论文 ID
            status: 新状态
            notes: 备注

        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if notes:
                cursor.execute('''
                    UPDATE papers
                    SET reading_status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, notes, paper_id))
            else:
                cursor.execute('''
                    UPDATE papers
                    SET reading_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, paper_id))

            return cursor.rowcount > 0

    def add_tag(self, paper_id: int, tag_name: str, category: str = None) -> bool:
        """
        为论文添加标签

        Args:
            paper_id: 论文 ID
            tag_name: 标签名
            category: 标签类别

        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建或获取标签
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            row = cursor.fetchone()

            if row:
                tag_id = row['id']
            else:
                cursor.execute(
                    'INSERT INTO tags (name, category) VALUES (?, ?)',
                    (tag_name, category)
                )
                tag_id = cursor.lastrowid

            # 关联论文和标签
            try:
                cursor.execute(
                    'INSERT INTO paper_tags (paper_id, tag_id) VALUES (?, ?)',
                    (paper_id, tag_id)
                )
                return True
            except sqlite3.IntegrityError:
                return False  # 已存在

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # 总数
            cursor.execute('SELECT COUNT(*) as count FROM papers')
            stats['total_papers'] = cursor.fetchone()['count']

            # 按年份统计
            cursor.execute('''
                SELECT year, COUNT(*) as count
                FROM papers
                WHERE year IS NOT NULL
                GROUP BY year
                ORDER BY year DESC
            ''')
            stats['by_year'] = {row['year']: row['count'] for row in cursor.fetchall()}

            # 按阅读状态统计
            cursor.execute('''
                SELECT reading_status, COUNT(*) as count
                FROM papers
                GROUP BY reading_status
            ''')
            stats['by_status'] = {row['reading_status']: row['count'] for row in cursor.fetchall()}

            # 开放获取统计
            cursor.execute('SELECT COUNT(*) as count FROM papers WHERE is_open_access = 1')
            stats['open_access_count'] = cursor.fetchone()['count']

            return stats

    def export(self, output_path: str, format: str = 'json') -> None:
        """
        导出数据库

        Args:
            output_path: 输出文件路径
            format: 导出格式 (json, csv, bibtex)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM papers ORDER BY importance_score DESC')
            papers = [self._row_to_dict(row) for row in cursor.fetchall()]

        output_file = Path(output_path)

        if format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)

        elif format == 'csv':
            import csv
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                if papers:
                    writer = csv.DictWriter(f, fieldnames=papers[0].keys())
                    writer.writeheader()
                    writer.writerows(papers)

        elif format == 'bibtex':
            with open(output_file, 'w', encoding='utf-8') as f:
                for paper in papers:
                    f.write(self._to_bibtex(paper))
                    f.write('\n\n')

        print(f"已导出 {len(papers)} 篇论文到 {output_file}")

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """将数据库行转换为字典"""
        result = dict(row)

        # 解析 JSON 字段
        for field in ['authors', 'fields_of_study', 'keywords']:
            if result.get(field):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    pass

        return result

    def _to_bibtex(self, paper: Dict) -> str:
        """转换为 BibTeX 格式"""
        # 生成 citation key
        authors = paper.get('authors', [])
        if authors:
            first_author = authors[0].split()[-1].lower()
        else:
            first_author = 'unknown'

        year = paper.get('year', 'xxxx')
        key = f"{first_author}{year}"

        lines = [f"@article{{{key},"]
        lines.append(f"  title = {{{paper.get('title', '')}}}")

        if authors:
            lines.append(f"  author = {{{' and '.join(authors)}}}")

        if paper.get('year'):
            lines.append(f"  year = {{{paper['year']}}}")

        if paper.get('journal'):
            lines.append(f"  journal = {{{paper['journal']}}}")
        elif paper.get('publication_venue'):
            lines.append(f"  journal = {{{paper['publication_venue']}}}")

        if paper.get('doi'):
            lines.append(f"  doi = {{{paper['doi']}}}")

        lines.append("}")

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='文献数据库管理工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # 导入命令
    import_parser = subparsers.add_parser('import', help='导入论文')
    import_parser.add_argument('file', help='JSON 文件路径')
    import_parser.add_argument('--db', help='数据库路径')

    # 搜索命令
    search_parser = subparsers.add_parser('search', help='搜索论文')
    search_parser.add_argument('query', help='搜索关键词')
    search_parser.add_argument('--limit', '-l', type=int, default=20, help='返回数量')
    search_parser.add_argument('--db', help='数据库路径')

    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    stats_parser.add_argument('--db', help='数据库路径')

    # 导出命令
    export_parser = subparsers.add_parser('export', help='导出数据库')
    export_parser.add_argument('output', help='输出文件路径')
    export_parser.add_argument('--format', '-f', choices=['json', 'csv', 'bibtex'],
                               default='json', help='导出格式')
    export_parser.add_argument('--db', help='数据库路径')

    # 更新状态命令
    status_parser = subparsers.add_parser('status', help='更新论文状态')
    status_parser.add_argument('paper_id', type=int, help='论文 ID')
    status_parser.add_argument('status', choices=['unread', 'reading', 'read', 'important'],
                               help='新状态')
    status_parser.add_argument('--notes', '-n', help='备注')
    status_parser.add_argument('--db', help='数据库路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    db = LiteratureDB(args.db) if hasattr(args, 'db') and args.db else LiteratureDB()

    if args.command == 'import':
        with open(args.file, 'r', encoding='utf-8') as f:
            papers = json.load(f)

        if isinstance(papers, dict) and 'papers' in papers:
            papers = papers['papers']

        success, skipped = db.insert_papers(papers)
        print(f"导入完成: 成功 {success}, 跳过 {skipped}")

    elif args.command == 'search':
        papers = db.search(args.query, args.limit)
        print(f"找到 {len(papers)} 篇论文:\n")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. [{paper['id']}] {paper['title'][:60]}...")
            print(f"   年份: {paper['year']} | 引用: {paper['citation_count']}")

    elif args.command == 'stats':
        stats = db.get_statistics()
        print("数据库统计:")
        print(f"  总论文数: {stats['total_papers']}")
        print(f"  开放获取: {stats['open_access_count']}")
        print(f"\n按年份:")
        for year, count in sorted(stats['by_year'].items(), reverse=True)[:10]:
            print(f"  {year}: {count}")
        print(f"\n按状态:")
        for status, count in stats['by_status'].items():
            print(f"  {status}: {count}")

    elif args.command == 'export':
        db.export(args.output, args.format)

    elif args.command == 'status':
        if db.update_status(args.paper_id, args.status, args.notes):
            print(f"已更新论文 {args.paper_id} 状态为 {args.status}")
        else:
            print(f"更新失败，论文 {args.paper_id} 不存在")


if __name__ == "__main__":
    main()
