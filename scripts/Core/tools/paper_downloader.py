"""
论文 PDF 下载工具
==================

用于 Phase 1: 文献调研阶段下载论文 PDF。
支持从 Arxiv、OpenReview、Semantic Scholar、ACL Anthology 等平台下载。
"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, unquote

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


# 下载配置
REQUEST_TIMEOUT = 60
CHUNK_SIZE = 8192
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # 秒
RATE_LIMIT_DELAY = 1.0  # 秒

# 用户代理
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 支持的下载源
SUPPORTED_SOURCES = {
    'arxiv': {
        'patterns': [
            r'arxiv\.org/abs/(\d+\.\d+)',
            r'arxiv\.org/pdf/(\d+\.\d+)',
            r'arxiv\.org/abs/([a-z\-]+/\d+)',
        ],
        'pdf_template': 'https://arxiv.org/pdf/{paper_id}.pdf',
    },
    'openreview': {
        'patterns': [
            r'openreview\.net/forum\?id=([A-Za-z0-9]+)',
            r'openreview\.net/pdf\?id=([A-Za-z0-9]+)',
        ],
        'api_template': 'https://api.openreview.net/api/notes?id={paper_id}',
    },
    'semantic_scholar': {
        'patterns': [
            r'semanticscholar\.org/paper/([a-f0-9]+)',
        ],
        'api_template': 'https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=openAccessPdf',
    },
    'acl': {
        'patterns': [
            r'aclanthology\.org/([A-Z0-9\-]+)',
        ],
        'pdf_template': 'https://aclanthology.org/{paper_id}.pdf',
    },
    'neurips': {
        'patterns': [
            r'papers\.nips\.cc/paper/(\d+)/',
            r'proceedings\.neurips\.cc/paper_files/paper/(\d+)/',
        ],
    },
    'pmlr': {
        'patterns': [
            r'proceedings\.mlr\.press/v(\d+)/',
        ],
    },
}


class PaperDownloader:
    """论文下载器"""

    def __init__(self, output_dir: str = './papers', max_retries: int = MAX_RETRIES):
        """
        初始化下载器

        Args:
            output_dir: 下载保存目录
            max_retries: 最大重试次数
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self._last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})

        # 下载统计
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }

    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符

        Args:
            filename: 原始文件名

        Returns:
            合法的文件名
        """
        # 替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除多余的空格和下划线
        filename = re.sub(r'[\s_]+', '_', filename)
        # 限制长度
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip('._')

    def _detect_source(self, url: str) -> Optional[Tuple[str, str]]:
        """
        检测 URL 来源并提取论文 ID

        Args:
            url: 论文 URL

        Returns:
            (source_name, paper_id) 或 None
        """
        for source, config in SUPPORTED_SOURCES.items():
            for pattern in config['patterns']:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    return (source, match.group(1))
        return None

    def _get_pdf_url(self, url: str) -> Optional[str]:
        """
        从 URL 获取 PDF 下载链接

        Args:
            url: 论文 URL

        Returns:
            PDF URL 或 None
        """
        # 检测来源
        source_info = self._detect_source(url)

        if not source_info:
            # 尝试直接使用 URL
            if url.endswith('.pdf'):
                return url
            return None

        source, paper_id = source_info
        config = SUPPORTED_SOURCES[source]

        # Arxiv: 直接构建 PDF URL
        if source == 'arxiv':
            return config['pdf_template'].format(paper_id=paper_id)

        # ACL: 直接构建 PDF URL
        if source == 'acl':
            return config['pdf_template'].format(paper_id=paper_id)

        # Semantic Scholar: 需要查询 API 获取 PDF URL
        if source == 'semantic_scholar':
            return self._get_semantic_scholar_pdf(paper_id)

        # OpenReview: 需要查询 API
        if source == 'openreview':
            return self._get_openreview_pdf(paper_id)

        # 其他源暂不支持
        return None

    def _get_semantic_scholar_pdf(self, paper_id: str) -> Optional[str]:
        """从 Semantic Scholar API 获取 PDF URL"""
        try:
            self._rate_limit()
            api_url = SUPPORTED_SOURCES['semantic_scholar']['api_template'].format(paper_id=paper_id)
            response = self.session.get(api_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            pdf_info = data.get('openAccessPdf')
            if pdf_info:
                return pdf_info.get('url')
        except Exception as e:
            print(f"  警告: 获取 Semantic Scholar PDF 失败: {e}")

        return None

    def _get_openreview_pdf(self, paper_id: str) -> Optional[str]:
        """从 OpenReview API 获取 PDF URL"""
        try:
            self._rate_limit()
            api_url = SUPPORTED_SOURCES['openreview']['api_template'].format(paper_id=paper_id)
            response = self.session.get(api_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            notes = data.get('notes', [])
            if notes:
                content = notes[0].get('content', {})
                # 尝试获取 PDF 链接
                pdf_url = content.get('pdf')
                if pdf_url:
                    if pdf_url.startswith('/'):
                        return f"https://openreview.net{pdf_url}"
                    return pdf_url

                # 尝试从 http 域名获取
                paper_url = content.get('_bibtex', {})
                if isinstance(paper_url, dict):
                    return paper_url.get('url')
        except Exception as e:
            print(f"  警告: 获取 OpenReview PDF 失败: {e}")

        return None

    def _do_download(self, url: str, output_path: Path) -> bool:
        """
        执行实际的文件下载（内部方法）

        Args:
            url: 下载 URL
            output_path: 输出路径

        Returns:
            是否成功
        """
        self._rate_limit()

        # 流式下载
        response = self.session.get(url, stream=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))

        # 写入文件
        with open(output_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # 显示进度（如果知道总大小）
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(f"\r  进度: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')

        print()  # 换行
        return True

    def download_file(self, url: str, output_path: Path, title: str = None) -> bool:
        """
        下载文件（带自动重试）

        Args:
            url: 下载 URL
            output_path: 输出路径
            title: 论文标题（用于显示）

        Returns:
            是否成功
        """
        # 显示进度
        display_name = title[:50] + '...' if title and len(title) > 50 else title or url
        print(f"  下载: {display_name}")
        print(f"  URL: {url}")

        # 创建带重试的下载函数
        @retry(
            max_attempts=self.max_retries,
            delay=RETRY_DELAY,
            backoff_factor=2.0,
            exceptions=(RequestException, Timeout, RequestsConnectionError),
            reraise=False
        )
        def download_with_retry():
            return self._do_download(url, output_path)

        try:
            return download_with_retry()
        except RetryError as e:
            logger.error(f"下载失败: {url}, 错误: {e.last_exception}")
            self.stats['errors'].append({
                'url': url,
                'title': title,
                'error': str(e.last_exception)
            })
            return False

    def download_from_url(self, url: str, filename: str = None, title: str = None) -> Optional[Path]:
        """
        从 URL 下载论文

        Args:
            url: 论文 URL
            filename: 自定义文件名
            title: 论文标题

        Returns:
            下载文件路径或 None
        """
        self.stats['total'] += 1

        # 获取 PDF URL
        pdf_url = self._get_pdf_url(url)

        if not pdf_url:
            print(f"  跳过: 无法获取 PDF URL - {url}")
            self.stats['skipped'] += 1
            return None

        # 生成文件名
        if not filename:
            if title:
                filename = self._sanitize_filename(title)
            else:
                # 从 URL 提取
                parsed = urlparse(pdf_url)
                filename = Path(unquote(parsed.path)).stem
                filename = self._sanitize_filename(filename)

        output_path = self.output_dir / f"{filename}.pdf"

        # 检查是否已存在
        if output_path.exists():
            print(f"  跳过: 文件已存在 - {output_path.name}")
            self.stats['skipped'] += 1
            return output_path

        # 下载
        if self.download_file(pdf_url, output_path, title):
            self.stats['success'] += 1
            return output_path
        else:
            self.stats['failed'] += 1
            return None

    def download_from_json(self, json_path: str, url_field: str = 'pdf_url',
                          title_field: str = 'title') -> List[Path]:
        """
        从 JSON 文件批量下载论文

        Args:
            json_path: JSON 文件路径
            url_field: URL 字段名
            title_field: 标题字段名

        Returns:
            下载文件路径列表
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            papers = json.load(f)

        downloaded = []

        print(f"\n开始下载 {len(papers)} 篇论文...")
        print(f"保存目录: {self.output_dir.absolute()}")
        print("=" * 60)

        for i, paper in enumerate(papers, 1):
            print(f"\n[{i}/{len(papers)}]")

            url = paper.get(url_field) or paper.get('arxiv_url') or paper.get('open_access_pdf')
            title = paper.get(title_field, '')

            if not url:
                print(f"  跳过: 无 URL - {title[:50]}...")
                self.stats['skipped'] += 1
                continue

            result = self.download_from_url(url, title=title)
            if result:
                downloaded.append(result)

        return downloaded

    def download_from_list(self, urls: List[str], titles: List[str] = None) -> List[Path]:
        """
        从 URL 列表批量下载

        Args:
            urls: URL 列表
            titles: 标题列表（可选）

        Returns:
            下载文件路径列表
        """
        downloaded = []

        print(f"\n开始下载 {len(urls)} 篇论文...")
        print(f"保存目录: {self.output_dir.absolute()}")
        print("=" * 60)

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]")

            title = titles[i - 1] if titles and i <= len(titles) else None
            result = self.download_from_url(url, title=title)
            if result:
                downloaded.append(result)

        return downloaded

    def print_summary(self):
        """打印下载统计"""
        print("\n" + "=" * 60)
        print("下载统计:")
        print("=" * 60)
        print(f"总计: {self.stats['total']}")
        print(f"成功: {self.stats['success']}")
        print(f"失败: {self.stats['failed']}")
        print(f"跳过: {self.stats['skipped']}")

        if self.stats['errors']:
            print("\n错误详情:")
            for error in self.stats['errors']:
                print(f"  - {error.get('title', error.get('url', 'Unknown'))}")
                print(f"    错误: {error.get('error')}")

    def save_log(self, output_path: str = None):
        """保存下载日志"""
        if not output_path:
            output_path = str(self.output_dir / 'download_log.json')

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'output_dir': str(self.output_dir),
            'stats': self.stats
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"\n日志已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='论文 PDF 下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从单个 URL 下载
  python paper_downloader.py --url "https://arxiv.org/abs/2301.12345"

  # 从 JSON 文件批量下载
  python paper_downloader.py --json papers.json

  # 指定 URL 字段和保存目录
  python paper_downloader.py --json papers.json --url-field "open_access_pdf" --output ./downloads

  # 从 URL 列表文件下载
  python paper_downloader.py --url-list urls.txt

支持的来源:
  - Arxiv (arxiv.org)
  - ACL Anthology (aclanthology.org)
  - Semantic Scholar (semanticscholar.org)
  - OpenReview (openreview.net)
  - 直接 PDF 链接
        """
    )

    parser.add_argument('--url', '-u', type=str, help='单个论文 URL')
    parser.add_argument('--json', '-j', type=str, help='JSON 文件路径（包含论文列表）')
    parser.add_argument('--url-list', type=str, help='URL 列表文件路径（每行一个 URL）')
    parser.add_argument('--output', '-o', type=str, default='./papers',
                        help='保存目录 (默认: ./papers)')
    parser.add_argument('--url-field', type=str, default='pdf_url',
                        help='JSON 中的 URL 字段名 (默认: pdf_url)')
    parser.add_argument('--title-field', type=str, default='title',
                        help='JSON 中的标题字段名 (默认: title)')
    parser.add_argument('--max-retries', type=int, default=MAX_RETRIES,
                        help=f'最大重试次数 (默认: {MAX_RETRIES})')
    parser.add_argument('--title', '-t', type=str, help='论文标题（配合 --url 使用）')

    args = parser.parse_args()

    # 检查参数
    if not any([args.url, args.json, args.url_list]):
        parser.print_help()
        print("\n错误: 请指定 --url, --json 或 --url-list")
        sys.exit(1)

    # 创建下载器
    downloader = PaperDownloader(
        output_dir=args.output,
        max_retries=args.max_retries
    )

    # 单个 URL
    if args.url:
        result = downloader.download_from_url(args.url, title=args.title)
        if result:
            print(f"\n成功: {result}")
        else:
            print("\n下载失败")

    # JSON 文件
    elif args.json:
        downloader.download_from_json(
            args.json,
            url_field=args.url_field,
            title_field=args.title_field
        )

    # URL 列表文件
    elif args.url_list:
        with open(args.url_list, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        downloader.download_from_list(urls)

    # 打印统计和保存日志
    downloader.print_summary()
    downloader.save_log()


if __name__ == "__main__":
    main()
