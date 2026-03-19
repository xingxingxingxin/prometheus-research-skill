"""
Arxiv 论文搜索工具
==================

用于 Phase 1: 文献调研阶段搜索和抓取论文。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    import arxiv
except ImportError:
    print("错误: 请先安装 arxiv 库: pip install arxiv")
    sys.exit(1)


def search_papers(query: str, max_results: int = 50,
                  categories: List[str] = None) -> List[Dict[str, Any]]:
    """
    搜索 Arxiv 论文

    Args:
        query: 搜索关键词
        max_results: 最大结果数
        categories: 限制类别 (如 ['cs.LG', 'cs.AI'])

    Returns:
        论文列表
    """
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending
    )

    papers = []
    for result in search.results():
        paper = {
            'arxiv_id': result.entry_id.split('/')[-1],
            'title': result.title,
            'authors': [a.name for a in result.authors],
            'summary': result.summary,
            'published': result.published.isoformat() if result.published else None,
            'updated': result.updated.isoformat() if result.updated else None,
            'categories': result.categories,
            'pdf_url': result.pdf_url,
            'abs_url': result.entry_id,
            'primary_category': result.primary_category,
            'retrieved_at': datetime.now().isoformat()
        }

        # 过滤类别
        if categories:
            if not any(cat in result.categories for cat in categories):
                continue

        papers.append(paper)

    return papers


def save_papers(papers: List[Dict], output_path: str):
    """保存论文到 JSON 文件"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    print(f"已保存 {len(papers)} 篇论文到 {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Arxiv 论文搜索工具')
    parser.add_argument('--query', '-q', type=str, required=True,
                        help='搜索关键词')
    parser.add_argument('--max-results', '-m', type=int, default=50,
                        help='最大结果数 (默认: 50)')
    parser.add_argument('--output', '-o', type=str, default='papers.json',
                        help='输出文件路径 (默认: papers.json)')
    parser.add_argument('--categories', '-c', type=str, nargs='+',
                        help='限制类别 (如 cs.LG cs.AI)')

    args = parser.parse_args()

    print(f"搜索: {args.query}")
    print(f"最大结果: {args.max_results}")
    if args.categories:
        print(f"类别限制: {args.categories}")
    print()

    papers = search_papers(
        query=args.query,
        max_results=args.max_results,
        categories=args.categories
    )

    save_papers(papers, args.output)

    # 显示摘要
    print()
    print("=" * 60)
    print("搜索结果摘要:")
    print("=" * 60)
    for i, paper in enumerate(papers[:10], 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   作者: {', '.join(paper['authors'][:3])}")
        print(f"   ID: {paper['arxiv_id']}")
        print(f"   类别: {paper['primary_category']}")

    if len(papers) > 10:
        print(f"\n... 还有 {len(papers) - 10} 篇论文")


if __name__ == "__main__":
    main()
