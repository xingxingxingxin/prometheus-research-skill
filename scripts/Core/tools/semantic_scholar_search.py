"""
Semantic Scholar 论文搜索工具
==============================

用于 Phase 1: 文献调研阶段搜索和抓取论文。
使用 Semantic Scholar API，支持高级搜索和引用分析。
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import requests
    from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError
except ImportError:
    print("错误: 请先安装 requests 库: pip install requests")
    sys.exit(1)

from retry_decorator import retry, RetryError

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Semantic Scholar API 配置
API_BASE_URL = "https://api.semanticscholar.org/graph/v1"
SEARCH_ENDPOINT = f"{API_BASE_URL}/paper/search"
PAPER_ENDPOINT = f"{API_BASE_URL}/paper"

# 请求配置
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0  # 秒，避免触发速率限制


class SemanticScholarSearcher:
    """Semantic Scholar 搜索器"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化搜索器

        Args:
            api_key: 可选的 API 密钥（提高速率限制）
        """
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["x-api-key"] = api_key
        self._last_request_time = 0

    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _handle_rate_limit(self, response: requests.Response) -> bool:
        """
        处理速率限制响应

        Args:
            response: HTTP 响应对象

        Returns:
            True 如果需要等待并重试，False 否则
        """
        if response.status_code == 429:
            # 获取 Retry-After 头，默认 60 秒
            retry_after = int(response.headers.get('Retry-After', 60))
            logger.warning(f"达到速率限制，等待 {retry_after} 秒...")
            time.sleep(retry_after)
            return True
        return False

    @retry(
        max_attempts=3,
        delay=2.0,
        backoff_factor=2.0,
        exceptions=(RequestException, Timeout, RequestsConnectionError),
        reraise=False
    )
    def _make_request(self, url: str, params: Dict = None) -> Dict:
        """
        发送 API 请求（带自动重试）

        Args:
            url: 请求 URL
            params: 查询参数

        Returns:
            JSON 响应
        """
        self._rate_limit()

        response = requests.get(
            url,
            params=params,
            headers=self.headers,
            timeout=REQUEST_TIMEOUT
        )

        # 处理速率限制
        if self._handle_rate_limit(response):
            # 触发重试
            raise RequestsConnectionError("速率限制，需要重试")

        response.raise_for_status()
        return response.json()

    def search(
        self,
        query: str,
        max_results: int = 50,
        year_range: tuple = None,
        venue: str = None,
        fields_of_study: List[str] = None,
        open_access_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        搜索论文

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            year_range: 年份范围，如 (2020, 2024)
            venue: 发表 venue（会议/期刊）
            fields_of_study: 研究领域列表，如 ['Computer Science', 'Mathematics']
            open_access_only: 仅返回开放获取论文

        Returns:
            论文列表
        """
        # 构建查询参数
        params = {
            "query": query,
            "limit": min(max_results, 100),  # API 单次最多 100
            "fields": "paperId,title,authors,year,abstract,citationCount,referenceCount,"
                      "publicationVenue,publicationDate,openAccessPdf,url,journal,externalIds,"
                      "fieldsOfStudy,influentialCitationCount,isOpenAccess,s2FieldsOfStudy"
        }

        # 添加过滤条件
        if year_range:
            params["year"] = f"{year_range[0]}-{year_range[1]}"

        if venue:
            params["venue"] = venue

        if fields_of_study:
            # API 可能不支持多字段，取第一个
            params["fieldOfStudy"] = fields_of_study[0]

        if open_access_only:
            params["openAccessPdf"] = ""

        papers = []
        offset = 0

        while len(papers) < max_results:
            params["offset"] = offset

            try:
                data = self._make_request(SEARCH_ENDPOINT, params)
            except requests.exceptions.RequestException as e:
                print(f"请求错误: {e}")
                break

            results = data.get("data", [])
            if not results:
                break

            for paper in results:
                formatted = self._format_paper(paper)
                papers.append(formatted)

            # 检查是否还有更多结果
            if not data.get("next"):
                break

            offset += len(results)

            if offset >= max_results:
                break

        return papers[:max_results]

    def _format_paper(self, paper: Dict) -> Dict[str, Any]:
        """格式化论文信息"""
        authors = paper.get("authors", [])

        return {
            "paper_id": paper.get("paperId"),
            "title": paper.get("title", ""),
            "authors": [a.get("name", "") for a in authors],
            "author_ids": [a.get("authorId", "") for a in authors],
            "year": paper.get("year"),
            "abstract": paper.get("abstract", ""),
            "citation_count": paper.get("citationCount", 0),
            "reference_count": paper.get("referenceCount", 0),
            "influential_citation_count": paper.get("influentialCitationCount", 0),
            "publication_venue": (paper.get("publicationVenue") or {}).get("name", ""),
            "publication_date": paper.get("publicationDate"),
            "journal": paper.get("journal", {}).get("name", "") if paper.get("journal") else "",
            "fields_of_study": paper.get("fieldsOfStudy", []),
            "is_open_access": paper.get("isOpenAccess", False),
            "open_access_pdf": paper.get("openAccessPdf", {}).get("url") if paper.get("openAccessPdf") else None,
            "url": paper.get("url", ""),
            "external_ids": paper.get("externalIds", {}),
            "retrieved_at": datetime.now().isoformat()
        }

    def get_paper(self, paper_id: str) -> Dict[str, Any]:
        """
        获取单篇论文详情

        Args:
            paper_id: 论文 ID（Semantic Scholar ID 或 DOI）

        Returns:
            论文详情
        """
        params = {
            "fields": "paperId,title,authors,year,abstract,citationCount,referenceCount,"
                      "publicationVenue,publicationDate,openAccessPdf,url,journal,externalIds,"
                      "fieldsOfStudy,influentialCitationCount,isOpenAccess,s2FieldsOfStudy,"
                      "citations,references"
        }

        try:
            data = self._make_request(f"{PAPER_ENDPOINT}/{paper_id}", params)
            return self._format_paper(data)
        except requests.exceptions.RequestException as e:
            print(f"获取论文失败: {e}")
            return None

    def get_citations(self, paper_id: str, max_results: int = 100) -> List[Dict]:
        """
        获取引用该论文的论文列表

        Args:
            paper_id: 论文 ID
            max_results: 最大结果数

        Returns:
            引用论文列表
        """
        params = {
            "fields": "paperId,title,authors,year,citationCount",
            "limit": min(max_results, 1000)
        }

        try:
            data = self._make_request(f"{PAPER_ENDPOINT}/{paper_id}/citations", params)
            return [
                self._format_paper(citation.get("citingPaper", {}))
                for citation in data.get("data", [])
                if citation.get("citingPaper")
            ]
        except requests.exceptions.RequestException as e:
            print(f"获取引用失败: {e}")
            return []

    def get_references(self, paper_id: str, max_results: int = 100) -> List[Dict]:
        """
        获取该论文引用的论文列表

        Args:
            paper_id: 论文 ID
            max_results: 最大结果数

        Returns:
            参考论文列表
        """
        params = {
            "fields": "paperId,title,authors,year,citationCount",
            "limit": min(max_results, 1000)
        }

        try:
            data = self._make_request(f"{PAPER_ENDPOINT}/{paper_id}/references", params)
            return [
                self._format_paper(ref.get("citedPaper", {}))
                for ref in data.get("data", [])
                if ref.get("citedPaper")
            ]
        except requests.exceptions.RequestException as e:
            print(f"获取参考文献失败: {e}")
            return []


def save_papers(papers: List[Dict], output_path: str):
    """保存论文到 JSON 文件"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    print(f"已保存 {len(papers)} 篇论文到 {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Semantic Scholar 论文搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本搜索
  python semantic_scholar_search.py --query "transformer time series"

  # 指定年份范围
  python semantic_scholar_search.py -q "attention mechanism" --year 2020-2024

  # 指定研究领域
  python semantic_scholar_search.py -q "deep learning" --fields "Computer Science"

  # 仅开放获取
  python semantic_scholar_search.py -q "neural network" --open-access

  # 获取论文详情
  python semantic_scholar_search.py --paper-id "649def34f8be52c8b66281af98ae884c09aef38b"
        """
    )

    parser.add_argument('--query', '-q', type=str, help='搜索关键词')
    parser.add_argument('--max-results', '-m', type=int, default=50,
                        help='最大结果数 (默认: 50)')
    parser.add_argument('--output', '-o', type=str, default='semantic_scholar_papers.json',
                        help='输出文件路径 (默认: semantic_scholar_papers.json)')
    parser.add_argument('--year', type=str, help='年份范围，如 2020-2024')
    parser.add_argument('--venue', type=str, help='发表 venue')
    parser.add_argument('--fields', type=str, nargs='+', help='研究领域')
    parser.add_argument('--open-access', action='store_true', help='仅开放获取论文')
    parser.add_argument('--api-key', type=str, help='API 密钥')
    parser.add_argument('--paper-id', type=str, help='获取指定论文详情')
    parser.add_argument('--citations', action='store_true', help='获取引用（需配合 --paper-id）')
    parser.add_argument('--references', action='store_true', help='获取参考文献（需配合 --paper-id）')

    args = parser.parse_args()

    searcher = SemanticScholarSearcher(api_key=args.api_key)

    # 获取单篇论文
    if args.paper_id:
        if args.citations:
            print(f"获取论文 {args.paper_id} 的引用...")
            papers = searcher.get_citations(args.paper_id)
        elif args.references:
            print(f"获取论文 {args.paper_id} 的参考文献...")
            papers = searcher.get_references(args.paper_id)
        else:
            print(f"获取论文 {args.paper_id} 详情...")
            paper = searcher.get_paper(args.paper_id)
            if paper:
                print(f"\n标题: {paper['title']}")
                print(f"作者: {', '.join(paper['authors'][:5])}")
                print(f"年份: {paper['year']}")
                print(f"引用数: {paper['citation_count']}")
                print(f"开放获取: {'是' if paper['is_open_access'] else '否'}")
                if paper['open_access_pdf']:
                    print(f"PDF: {paper['open_access_pdf']}")
                return
            else:
                print("未找到论文")
                return

        save_papers(papers, args.output)
        return

    # 搜索论文
    if not args.query:
        parser.print_help()
        return

    # 解析年份范围
    year_range = None
    if args.year:
        parts = args.year.split('-')
        if len(parts) == 2:
            year_range = (int(parts[0]), int(parts[1]))
        else:
            year_range = (int(parts[0]), int(parts[0]))

    print(f"搜索: {args.query}")
    print(f"最大结果: {args.max_results}")
    if year_range:
        print(f"年份范围: {year_range[0]}-{year_range[1]}")
    if args.fields:
        print(f"研究领域: {args.fields}")
    if args.open_access:
        print("仅开放获取: 是")
    print()

    papers = searcher.search(
        query=args.query,
        max_results=args.max_results,
        year_range=year_range,
        venue=args.venue,
        fields_of_study=args.fields,
        open_access_only=args.open_access
    )

    save_papers(papers, args.output)

    # 显示摘要
    print()
    print("=" * 70)
    print("搜索结果摘要:")
    print("=" * 70)

    # 按引用数排序显示前 10
    sorted_papers = sorted(papers, key=lambda x: x.get('citation_count', 0), reverse=True)

    for i, paper in enumerate(sorted_papers[:10], 1):
        print(f"\n{i}. {paper['title'][:80]}...")
        print(f"   作者: {', '.join(paper['authors'][:3])}")
        print(f"   年份: {paper['year']} | 引用: {paper['citation_count']}")
        if paper['publication_venue']:
            print(f"   Venue: {paper['publication_venue']}")
        if paper['is_open_access']:
            print(f"   ✓ 开放获取")

    if len(papers) > 10:
        print(f"\n... 还有 {len(papers) - 10} 篇论文")


if __name__ == "__main__":
    main()
