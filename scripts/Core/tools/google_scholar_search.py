"""
Google Scholar 论文搜索工具
============================

用于 Phase 1: 文献调研阶段搜索和抓取论文。
使用 scholarly 库搜索 Google Scholar，支持获取引用数等指标。

注意：Google Scholar 有反爬机制，请合理使用：
- 设置适当的请求间隔
- 避免频繁大量请求
- 必要时使用代理
"""

import argparse
import json
import sys
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator

try:
    from scholarly import scholarly, ProxyGenerator
except ImportError:
    print("错误: 请先安装 scholarly 库: pip install scholarly")
    sys.exit(1)


# 请求配置
DEFAULT_MAX_RESULTS = 20  # 默认结果数，避免触发限制
MIN_DELAY = 2.0  # 最小请求间隔（秒）
MAX_DELAY = 5.0  # 最大请求间隔（秒）
MAX_RETRIES = 3  # 最大重试次数


class GoogleScholarSearcher:
    """Google Scholar 搜索器"""

    def __init__(
        self,
        use_proxy: bool = False,
        proxy_config: Optional[Dict] = None
    ):
        """
        初始化搜索器

        Args:
            use_proxy: 是否使用代理
            proxy_config: 代理配置，如 {'type': 'tor'} 或 {'type': 'http', 'addr': '...'}
        """
        self.use_proxy = use_proxy
        self.proxy_config = proxy_config
        self._last_request_time = 0

        if use_proxy:
            self._setup_proxy()

    def _setup_proxy(self):
        """设置代理"""
        try:
            pg = ProxyGenerator()

            if self.proxy_config:
                proxy_type = self.proxy_config.get('type', 'tor')

                if proxy_type == 'tor':
                    # 使用 Tor 代理
                    pg.Tor_Internal(
                        tor_sock_port=self.proxy_config.get('sock_port', 9050),
                        tor_control_port=self.proxy_config.get('control_port', 9051),
                        tor_password=self.proxy_config.get('password')
                    )
                elif proxy_type == 'http':
                    # 使用 HTTP 代理
                    pg.SingleProxy(
                        http=self.proxy_config.get('http'),
                        https=self.proxy_config.get('https')
                    )
                elif proxy_type == 'rotate':
                    # 使用轮换代理（如 Luminati）
                    pg.RotateProxy(
                        package=self.proxy_config.get('package'),
                        api_key=self.proxy_config.get('api_key')
                    )
            else:
                # 默认使用免费的 Tor 代理
                pg.FreeProxies()

            scholarly.use_proxy(pg)
            print("代理设置成功")

        except Exception as e:
            print(f"警告: 代理设置失败: {e}")
            print("将直接连接（可能触发反爬限制）")

    def _rate_limit(self):
        """速率限制 - 随机延迟避免检测"""
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        elapsed = time.time() - self._last_request_time

        if elapsed < delay:
            sleep_time = delay - elapsed
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _retry_request(self, func, *args, **kwargs):
        """
        带重试的请求

        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数

        Returns:
            函数返回值，失败返回 None
        """
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                self._rate_limit()
                return func(*args, **kwargs)

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # 检测是否被封锁
                if 'captcha' in error_msg or 'blocked' in error_msg:
                    wait_time = 60 * (attempt + 1)  # 递增等待时间
                    print(f"检测到反爬限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

                elif 'rate' in error_msg or 'limit' in error_msg:
                    wait_time = 30 * (attempt + 1)
                    print(f"达到速率限制，等待 {wait_time} 秒...")
                    time.sleep(wait_time)

                else:
                    print(f"请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                    time.sleep(10 * (attempt + 1))

        print(f"请求最终失败: {last_error}")
        return None

    def search(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        year_low: Optional[int] = None,
        year_high: Optional[int] = None,
        sort_by: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        搜索论文

        Args:
            query: 搜索关键词
            max_results: 最大结果数（建议不超过 50）
            year_low: 年份下限
            year_high: 年份上限
            sort_by: 排序方式 ("relevance" 或 "date")

        Returns:
            论文列表
        """
        papers = []

        try:
            # 构建搜索对象
            search_query = scholarly.search_pubs(
                query,
                sort_by=sort_by if sort_by == "date" else None
            )

            count = 0
            for result in search_query:
                if count >= max_results:
                    break

                # 年份过滤
                year = result.bib.get('year')
                if year:
                    try:
                        year = int(year)
                        if year_low and year < year_low:
                            continue
                        if year_high and year > year_high:
                            continue
                    except (ValueError, TypeError):
                        pass

                # 格式化论文信息
                formatted = self._format_paper(result)
                papers.append(formatted)
                count += 1

                # 显示进度
                if count % 5 == 0:
                    print(f"已获取 {count} 篇论文...")

        except Exception as e:
            print(f"搜索错误: {e}")

        return papers

    def _format_paper(self, result) -> Dict[str, Any]:
        """格式化论文信息"""
        bib = result.bib

        return {
            "title": bib.get("title", ""),
            "authors": bib.get("author", []),
            "year": bib.get("year"),
            "abstract": bib.get("abstract", ""),
            "citation_count": self._safe_int(bib.get("cites", "0")),
            "url": bib.get("url", ""),
            "pub_url": bib.get("pub_url", ""),
            "eprint_url": bib.get("eprint_url", ""),
            "venue": bib.get("venue", bib.get("journal", "")),
            "publisher": bib.get("publisher", ""),
            "gs_rank": getattr(result, "gs_rank", None),
            "source": "google_scholar",
            "retrieved_at": datetime.now().isoformat()
        }

    def _safe_int(self, value) -> int:
        """安全转换为整数"""
        if value is None:
            return 0
        try:
            # 移除可能的逗号
            if isinstance(value, str):
                value = value.replace(",", "")
            return int(value)
        except (ValueError, TypeError):
            return 0

    def get_author(self, author_name: str) -> Optional[Dict[str, Any]]:
        """
        获取作者信息

        Args:
            author_name: 作者名称

        Returns:
            作者信息字典
        """
        def _fetch():
            search_query = scholarly.search_author(author_name)
            author = next(search_query, None)
            if author:
                return scholarly.fill(author)
            return None

        result = self._retry_request(_fetch)

        if result:
            return {
                "name": result.bib.get("name", ""),
                "affiliation": result.bib.get("affiliation", ""),
                "interests": result.bib.get("interests", []),
                "url_picture": result.bib.get("url_picture", ""),
                "citations": self._safe_int(result.bib.get("citations", "0")),
                "h_index": self._safe_int(result.bib.get("hindex", "0")),
                "i10_index": self._safe_int(result.bib.get("i10index", "0")),
                "source": "google_scholar",
                "retrieved_at": datetime.now().isoformat()
            }

        return None

    def get_citations(
        self,
        paper_title: str,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取引用该论文的论文列表

        Args:
            paper_title: 论文标题
            max_results: 最大结果数

        Returns:
            引用论文列表
        """
        papers = []

        try:
            # 先搜索原论文
            search_query = scholarly.search_pubs(paper_title)
            original = next(search_query, None)

            if not original:
                print("未找到原论文")
                return papers

            # 获取引用
            filled = scholarly.fill(original)
            citations = scholarly.citedby(filled)

            count = 0
            for citation in citations:
                if count >= max_results:
                    break

                formatted = self._format_paper(citation)
                papers.append(formatted)
                count += 1

        except Exception as e:
            print(f"获取引用错误: {e}")

        return papers

    def get_related_papers(
        self,
        paper_title: str,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取相关论文

        Args:
            paper_title: 论文标题
            max_results: 最大结果数

        Returns:
            相关论文列表
        """
        papers = []

        try:
            # 搜索原论文
            search_query = scholarly.search_pubs(paper_title)
            original = next(search_query, None)

            if not original:
                print("未找到原论文")
                return papers

            # 获取相关论文
            filled = scholarly.fill(original)
            related = scholarly.bibtex(filled)

            # 使用原论文的关键词搜索相关论文
            # 这里简化为返回搜索结果中的其他论文
            # 实际 scholarly 库的相关论文功能有限

            print("注意: scholarly 库的相关论文功能有限")
            print("建议使用原论文标题中的关键词进行新搜索")

        except Exception as e:
            print(f"获取相关论文错误: {e}")

        return papers


def save_papers(papers: List[Dict], output_path: str):
    """保存论文到 JSON 文件"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    print(f"已保存 {len(papers)} 篇论文到 {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Google Scholar 论文搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本搜索
  python google_scholar_search.py --query "transformer time series"

  # 指定最大结果数和年份范围
  python google_scholar_search.py -q "attention mechanism" -m 30 --year-low 2020 --year-high 2024

  # 按日期排序
  python google_scholar_search.py -q "deep learning" --sort-by date

  # 获取作者信息
  python google_scholar_search.py --author "Yann LeCun"

  # 获取论文引用
  python google_scholar_search.py --citations "Attention Is All You Need"

  # 使用代理（推荐用于大量请求）
  python google_scholar_search.py -q "neural network" --use-proxy

注意:
  - Google Scholar 有反爬机制，请勿频繁大量请求
  - 建议每次搜索不超过 50 条结果
  - 如需大量搜索，请使用 --use-proxy 或配置代理
        """
    )

    parser.add_argument('--query', '-q', type=str, help='搜索关键词')
    parser.add_argument('--max-results', '-m', type=int, default=DEFAULT_MAX_RESULTS,
                        help=f'最大结果数 (默认: {DEFAULT_MAX_RESULTS})')
    parser.add_argument('--output', '-o', type=str, default='google_scholar_papers.json',
                        help='输出文件路径 (默认: google_scholar_papers.json)')
    parser.add_argument('--year-low', type=int, help='年份下限')
    parser.add_argument('--year-high', type=int, help='年份上限')
    parser.add_argument('--sort-by', type=str, choices=['relevance', 'date'],
                        default='relevance', help='排序方式 (默认: relevance)')
    parser.add_argument('--author', type=str, help='获取作者信息')
    parser.add_argument('--citations', type=str, help='获取引用该论文的论文')
    parser.add_argument('--use-proxy', action='store_true', help='使用代理')
    parser.add_argument('--proxy-type', type=str, choices=['tor', 'http', 'rotate'],
                        help='代理类型')
    parser.add_argument('--proxy-addr', type=str, help='代理地址 (HTTP代理)')
    parser.add_argument('--proxy-port', type=int, help='代理端口 (HTTP代理)')

    args = parser.parse_args()

    # 设置代理
    proxy_config = None
    if args.use_proxy:
        if args.proxy_type == 'http' and args.proxy_addr:
            proxy_config = {
                'type': 'http',
                'http': f"{args.proxy_addr}:{args.proxy_port or 8080}",
                'https': f"{args.proxy_addr}:{args.proxy_port or 8080}"
            }
        else:
            proxy_config = {'type': args.proxy_type or 'tor'}

    searcher = GoogleScholarSearcher(
        use_proxy=args.use_proxy,
        proxy_config=proxy_config
    )

    # 获取作者信息
    if args.author:
        print(f"获取作者信息: {args.author}...")
        author = searcher.get_author(args.author)

        if author:
            print(f"\n作者: {author['name']}")
            print(f"机构: {author['affiliation']}")
            print(f"研究方向: {', '.join(author['interests'][:5])}")
            print(f"引用数: {author['citations']}")
            print(f"h-index: {author['h_index']}")
            print(f"i10-index: {author['i10_index']}")

            # 保存到文件
            save_papers([author], args.output)
        else:
            print("未找到作者")
        return

    # 获取论文引用
    if args.citations:
        print(f"获取论文引用: {args.citations}...")
        papers = searcher.get_citations(args.citations, args.max_results)
        save_papers(papers, args.output)
        return

    # 搜索论文
    if not args.query:
        parser.print_help()
        return

    print(f"搜索: {args.query}")
    print(f"最大结果: {args.max_results}")
    if args.year_low or args.year_high:
        year_range = f"{args.year_low or 'any'} - {args.year_high or 'any'}"
        print(f"年份范围: {year_range}")
    print(f"排序方式: {args.sort_by}")
    print()

    papers = searcher.search(
        query=args.query,
        max_results=args.max_results,
        year_low=args.year_low,
        year_high=args.year_high,
        sort_by=args.sort_by
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
        title = paper['title'][:70] + "..." if len(paper['title']) > 70 else paper['title']
        print(f"\n{i}. {title}")
        authors = paper['authors']
        if isinstance(authors, list):
            author_str = ', '.join(authors[:3])
        else:
            author_str = str(authors)[:50]
        print(f"   作者: {author_str}")
        print(f"   年份: {paper['year']} | 引用: {paper['citation_count']}")
        if paper['venue']:
            print(f"   Venue: {paper['venue']}")

    if len(papers) > 10:
        print(f"\n... 还有 {len(papers) - 10} 篇论文")


if __name__ == "__main__":
    main()
