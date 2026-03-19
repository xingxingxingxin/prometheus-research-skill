"""
Project Prometheus - 导出管理器
=================================

管理项目报告的导出功能，支持多种格式：Markdown, PDF, HTML
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# 默认路径
DEFAULT_BASE_DIR = Path(__file__).parent.parent
EXPORT_DIR = DEFAULT_BASE_DIR / "Exports"
STATE_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "state.json"
TASKS_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "research_tasks.json"
LOG_FILE = DEFAULT_BASE_DIR / "Logs" / "operational.log"
ERROR_LOG = DEFAULT_BASE_DIR / "Logs" / "error_trace.log"
KNOWLEDGE_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "knowledge_base.json"
SESSION_FILE = DEFAULT_BASE_DIR / "Core" / "workflow" / "sessions.json"


class ExportManager:
    """导出管理器

    支持导出项目报告（进度、知识库、日志）到多种格式。
    """

    def __init__(self, export_dir: Optional[Path] = None):
        """
        初始化导出管理器

        Args:
            export_dir: 导出目录路径
        """
        self.export_dir = Path(export_dir) if export_dir else EXPORT_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_project(self,
                       components: Optional[List[str]] = None,
                       format: str = "markdown",
                       output_file: Optional[str] = None,
                       include_logs: bool = True,
                       log_lines: int = 100) -> Dict[str, Any]:
        """
        导出项目报告

        Args:
            components: 要导出的组件列表（progress, knowledge, logs, all）
                       默认为 ['all']，即导出所有组件
            format: 导出格式（markdown, html, pdf）
            output_file: 输出文件名（不含扩展名）
            include_logs: 是否包含日志
            log_lines: 包含的日志行数

        Returns:
            导出结果字典，包含文件路径和统计信息
        """
        # 默认导出所有组件
        if not components:
            components = ['all']

        # 如果包含 'all'，则导出所有组件
        if 'all' in components:
            components = ['progress', 'knowledge', 'logs', 'sessions']

        # 收集数据
        data = {
            "export_time": datetime.now().isoformat(),
            "project_info": self._get_project_info(),
            "progress": None,
            "knowledge": None,
            "logs": None,
            "sessions": None
        }

        if 'progress' in components:
            data['progress'] = self._collect_progress_data()

        if 'knowledge' in components:
            data['knowledge'] = self._collect_knowledge_data()

        if 'logs' in components and include_logs:
            data['logs'] = self._collect_logs_data(log_lines)

        if 'sessions' in components:
            data['sessions'] = self._collect_sessions_data()

        # 生成输出文件名
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"project_report_{timestamp}"

        # 根据格式导出
        if format.lower() == "markdown" or format.lower() == "md":
            output_path = self._export_markdown(data, output_file)
        elif format.lower() == "html":
            output_path = self._export_html(data, output_file)
        elif format.lower() == "pdf":
            output_path = self._export_pdf(data, output_file)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

        return {
            "success": True,
            "output_path": str(output_path),
            "format": format,
            "components": components,
            "export_time": data['export_time']
        }

    def _get_project_info(self) -> Dict[str, Any]:
        """获取项目基本信息"""
        info = {
            "name": "Unknown",
            "domain": "Unknown",
            "question": "Unknown",
            "created_at": None
        }

        # 尝试从任务文件获取
        if TASKS_FILE.exists():
            try:
                with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                    info['name'] = tasks.get('project_name', 'Unknown')
                    info['domain'] = tasks.get('research_domain', 'Unknown')
                    info['question'] = tasks.get('research_question', 'Unknown')
                    info['created_at'] = tasks.get('created_at')
            except Exception:
                pass

        return info

    def _collect_progress_data(self) -> Dict[str, Any]:
        """收集进度数据"""
        progress = {
            "state": None,
            "tasks_summary": None,
            "phases": []
        }

        # 读取状态
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    progress['state'] = json.load(f)
            except Exception:
                pass

        # 读取任务进度
        if TASKS_FILE.exists():
            try:
                with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)

                    # 计算摘要
                    total = 0
                    passed = 0
                    phases = tasks.get('phases', [])

                    for phase in phases:
                        phase_tasks = phase.get('tasks', [])
                        phase_total = len(phase_tasks)
                        phase_passed = sum(1 for t in phase_tasks if t.get('passes', False))
                        total += phase_total
                        passed += phase_passed

                        progress['phases'].append({
                            "id": phase.get('phase_id'),
                            "name": phase.get('phase_name'),
                            "status": phase.get('status', 'pending'),
                            "total": phase_total,
                            "passed": phase_passed,
                            "tasks": phase_tasks
                        })

                    progress['tasks_summary'] = {
                        "total": total,
                        "passed": passed,
                        "pending": total - passed,
                        "progress_percent": round(passed / total * 100, 1) if total > 0 else 0
                    }
            except Exception:
                pass

        return progress

    def _collect_knowledge_data(self) -> Dict[str, Any]:
        """收集知识库数据"""
        knowledge = {
            "exists": False,
            "data": None,
            "statistics": None
        }

        if KNOWLEDGE_FILE.exists():
            try:
                with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    knowledge['exists'] = True
                    knowledge['data'] = data

                    # 计算统计
                    findings = data.get('key_findings', [])
                    practices = data.get('best_practices', {})
                    lessons = data.get('lessons_learned', [])

                    knowledge['statistics'] = {
                        "papers_read": data.get('papers_read', 0),
                        "total_findings": len(findings),
                        "total_best_practices": len(practices),
                        "total_lessons_learned": len(lessons)
                    }
            except Exception:
                pass

        return knowledge

    def _collect_logs_data(self, lines: int = 100) -> Dict[str, Any]:
        """收集日志数据"""
        logs = {
            "operational": [],
            "errors": []
        }

        # 读取操作日志
        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    logs['operational'] = all_lines[-lines:] if len(all_lines) > lines else all_lines
            except Exception:
                pass

        # 读取错误日志
        if ERROR_LOG.exists():
            try:
                with open(ERROR_LOG, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logs['errors'] = content.split('\n')[-lines * 5:]  # 错误日志可能更详细
            except Exception:
                pass

        return logs

    def _collect_sessions_data(self) -> Dict[str, Any]:
        """收集会话数据"""
        sessions = {
            "exists": False,
            "statistics": None,
            "recent_sessions": []
        }

        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions['exists'] = True

                    # 获取统计
                    all_sessions = data.get('sessions', [])
                    total_tokens = sum(s.get('tokens_used', 0) for s in all_sessions)

                    sessions['statistics'] = {
                        "total_sessions": len(all_sessions),
                        "total_tokens_used": total_tokens,
                        "total_context_windows": data.get('total_context_windows', 0)
                    }

                    # 获取最近的会话（最多10个）
                    recent = sorted(
                        all_sessions,
                        key=lambda x: x.get('started_at', ''),
                        reverse=True
                    )[:10]
                    sessions['recent_sessions'] = recent
            except Exception:
                pass

        return sessions

    def _export_markdown(self, data: Dict[str, Any], filename: str) -> Path:
        """导出为 Markdown 格式"""
        output_path = self.export_dir / f"{filename}.md"

        lines = []

        # 标题
        lines.append("# Project Prometheus 项目报告")
        lines.append(f"\n**导出时间**: {data['export_time']}")
        lines.append("\n---\n")

        # 项目信息
        project_info = data.get('project_info', {})
        lines.append("## 项目信息\n")
        lines.append(f"- **项目名称**: {project_info.get('name', 'N/A')}")
        lines.append(f"- **研究领域**: {project_info.get('domain', 'N/A')}")
        lines.append(f"- **研究问题**: {project_info.get('question', 'N/A')}")
        if project_info.get('created_at'):
            lines.append(f"- **创建时间**: {project_info.get('created_at')}")
        lines.append("")

        # 进度
        if data.get('progress'):
            lines.append("## 项目进度\n")
            progress = data['progress']

            if progress.get('tasks_summary'):
                summary = progress['tasks_summary']
                lines.append("### 总体进度\n")
                lines.append(f"- 总任务数: {summary['total']}")
                lines.append(f"- 已完成: {summary['passed']}")
                lines.append(f"- 待完成: {summary['pending']}")
                lines.append(f"- 完成度: {summary['progress_percent']}%")
                lines.append("")

            if progress.get('phases'):
                lines.append("### 各阶段进度\n")
                lines.append("| 阶段 | 状态 | 进度 |")
                lines.append("|------|------|------|")
                for phase in progress['phases']:
                    status_icon = "[x]" if phase['status'] == 'completed' else "[ ]"
                    progress_str = f"{phase['passed']}/{phase['total']}"
                    lines.append(f"| {phase['name']} | {status_icon} | {progress_str} |")
                lines.append("")

            if progress.get('state'):
                state = progress['state']
                lines.append("### 当前状态\n")
                lines.append(f"- 当前阶段: {state.get('current_phase', 'N/A')}")
                lines.append(f"- 当前任务: {state.get('current_task', 'N/A')}")
                lines.append(f"- 系统状态: {state.get('status', 'N/A')}")
                if state.get('last_updated'):
                    lines.append(f"- 最后更新: {state.get('last_updated')}")
                lines.append("")

        # 知识库
        if data.get('knowledge') and data['knowledge'].get('exists'):
            lines.append("## 知识库\n")
            knowledge = data['knowledge']

            if knowledge.get('statistics'):
                stats = knowledge['statistics']
                lines.append("### 统计信息\n")
                lines.append(f"- 已读论文: {stats['papers_read']} 篇")
                lines.append(f"- 关键发现: {stats['total_findings']} 条")
                lines.append(f"- 最佳实践: {stats['total_best_practices']} 条")
                lines.append(f"- 经验教训: {stats['total_lessons_learned']} 条")
                lines.append("")

            # 关键发现
            if knowledge.get('data', {}).get('key_findings'):
                lines.append("### 关键发现\n")
                for finding in knowledge['data']['key_findings'][:10]:  # 最多显示10条
                    importance = finding.get('importance', 1)
                    stars = "*" * importance
                    lines.append(f"- **[{stars}]** {finding.get('content', 'N/A')}")
                    if finding.get('source'):
                        lines.append(f"  - 来源: {finding.get('source')}")
                if len(knowledge['data']['key_findings']) > 10:
                    lines.append(f"\n_...还有 {len(knowledge['data']['key_findings']) - 10} 条发现_")
                lines.append("")

            # 最佳实践
            if knowledge.get('data', {}).get('best_practices'):
                lines.append("### 最佳实践\n")
                for key, practice in list(knowledge['data']['best_practices'].items())[:10]:
                    lines.append(f"- **{key}**: {practice.get('value', 'N/A')}")
                    if practice.get('description'):
                        lines.append(f"  - {practice.get('description')}")
                lines.append("")

        # 会话统计
        if data.get('sessions') and data['sessions'].get('exists'):
            lines.append("## 会话统计\n")
            sessions = data['sessions']

            if sessions.get('statistics'):
                stats = sessions['statistics']
                lines.append("### 总体统计\n")
                lines.append(f"- 总会话数: {stats['total_sessions']}")
                lines.append(f"- 总 Token 使用: {stats['total_tokens_used']}")
                lines.append(f"- 总上下文窗口: {stats['total_context_windows']}")
                lines.append("")

        # 日志
        if data.get('logs'):
            logs = data['logs']
            lines.append("## 日志摘要\n")

            if logs.get('operational'):
                lines.append("### 最近操作日志\n")
                lines.append("```")
                for line in logs['operational'][-20:]:  # 显示最后20行
                    lines.append(line.rstrip())
                lines.append("```\n")

            if logs.get('errors'):
                lines.append("### 错误日志\n")
                lines.append("```")
                for line in logs['errors'][-30:]:  # 显示最后30行
                    if line.strip():
                        lines.append(line.rstrip())
                lines.append("```\n")

        # 页脚
        lines.append("\n---\n")
        lines.append("*由 Project Prometheus 自动生成*")

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return output_path

    def _export_html(self, data: Dict[str, Any], filename: str) -> Path:
        """导出为 HTML 格式"""
        output_path = self.export_dir / f"{filename}.html"

        # 生成 HTML 内容
        html = self._generate_html(data)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path

    def _generate_html(self, data: Dict[str, Any]) -> str:
        """生成 HTML 内容"""
        # CSS 样式
        css = """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }
            h3 {
                color: #7f8c8d;
            }
            .meta {
                color: #95a5a6;
                font-size: 0.9em;
                margin-bottom: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #3498db;
                color: white;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .progress-bar {
                background-color: #ecf0f1;
                border-radius: 4px;
                overflow: hidden;
                height: 20px;
            }
            .progress-fill {
                background-color: #2ecc71;
                height: 100%;
                transition: width 0.3s ease;
            }
            .stat-box {
                display: inline-block;
                background: #ecf0f1;
                padding: 15px 25px;
                margin: 5px;
                border-radius: 4px;
                text-align: center;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #3498db;
            }
            .stat-label {
                color: #7f8c8d;
                font-size: 0.9em;
            }
            pre {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
            }
            .footer {
                text-align: center;
                color: #95a5a6;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }
            .tag {
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 0.8em;
                margin: 2px;
            }
        </style>
        """

        # 开始构建 HTML
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='zh-CN'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "<title>Project Prometheus - 项目报告</title>",
            css,
            "</head>",
            "<body>",
            "<div class='container'>",
            "<h1>Project Prometheus 项目报告</h1>",
            f"<p class='meta'>导出时间: {data['export_time']}</p>"
        ]

        # 项目信息
        project_info = data.get('project_info', {})
        html_parts.append("<h2>项目信息</h2>")
        html_parts.append("<table>")
        html_parts.append(f"<tr><th>项目名称</th><td>{project_info.get('name', 'N/A')}</td></tr>")
        html_parts.append(f"<tr><th>研究领域</th><td>{project_info.get('domain', 'N/A')}</td></tr>")
        html_parts.append(f"<tr><th>研究问题</th><td>{project_info.get('question', 'N/A')}</td></tr>")
        if project_info.get('created_at'):
            html_parts.append(f"<tr><th>创建时间</th><td>{project_info.get('created_at')}</td></tr>")
        html_parts.append("</table>")

        # 进度
        if data.get('progress'):
            progress = data['progress']

            html_parts.append("<h2>项目进度</h2>")

            if progress.get('tasks_summary'):
                summary = progress['tasks_summary']
                percent = summary['progress_percent']

                html_parts.append("<h3>总体进度</h3>")
                html_parts.append("<div class='stat-box'>")
                html_parts.append(f"<div class='stat-number'>{summary['passed']}/{summary['total']}</div>")
                html_parts.append("<div class='stat-label'>已完成任务</div>")
                html_parts.append("</div>")
                html_parts.append("<div class='stat-box'>")
                html_parts.append(f"<div class='stat-number'>{percent}%</div>")
                html_parts.append("<div class='stat-label'>完成度</div>")
                html_parts.append("</div>")
                html_parts.append("<div class='stat-box'>")
                html_parts.append(f"<div class='stat-number'>{summary['pending']}</div>")
                html_parts.append("<div class='stat-label'>待完成</div>")
                html_parts.append("</div>")

                html_parts.append("<div style='margin: 20px 0;'>")
                html_parts.append("<div class='progress-bar'>")
                html_parts.append(f"<div class='progress-fill' style='width: {percent}%'></div>")
                html_parts.append("</div>")
                html_parts.append("</div>")

            if progress.get('phases'):
                html_parts.append("<h3>各阶段进度</h3>")
                html_parts.append("<table>")
                html_parts.append("<tr><th>阶段</th><th>状态</th><th>进度</th></tr>")
                for phase in progress['phases']:
                    status = "[x]" if phase['status'] == 'completed' else "[ ]"
                    progress_str = f"{phase['passed']}/{phase['total']}"
                    html_parts.append(f"<tr><td>{phase['name']}</td><td>{status}</td><td>{progress_str}</td></tr>")
                html_parts.append("</table>")

        # 知识库
        if data.get('knowledge') and data['knowledge'].get('exists'):
            knowledge = data['knowledge']
            html_parts.append("<h2>知识库</h2>")

            if knowledge.get('statistics'):
                stats = knowledge['statistics']
                html_parts.append("<div class='stat-box'>")
                html_parts.append(f"<div class='stat-number'>{stats['papers_read']}</div>")
                html_parts.append("<div class='stat-label'>已读论文</div>")
                html_parts.append("</div>")
                html_parts.append("<div class='stat-box'>")
                html_parts.append(f"<div class='stat-number'>{stats['total_findings']}</div>")
                html_parts.append("<div class='stat-label'>关键发现</div>")
                html_parts.append("</div>")
                html_parts.append("<div class='stat-box'>")
                html_parts.append(f"<div class='stat-number'>{stats['total_best_practices']}</div>")
                html_parts.append("<div class='stat-label'>最佳实践</div>")
                html_parts.append("</div>")

            # 关键发现列表
            if knowledge.get('data', {}).get('key_findings'):
                html_parts.append("<h3>关键发现</h3>")
                html_parts.append("<ul>")
                for finding in knowledge['data']['key_findings'][:10]:
                    importance = finding.get('importance', 1)
                    stars = "*" * importance
                    content = finding.get('content', 'N/A')
                    html_parts.append(f"<li><strong>[{stars}]</strong> {content}</li>")
                html_parts.append("</ul>")

        # 会话统计
        if data.get('sessions') and data['sessions'].get('exists'):
            sessions = data['sessions']

            html_parts.append("<h2>会话统计</h2>")

            if sessions.get('statistics'):
                stats = sessions['statistics']
                html_parts.append("<div class='stat-box'>")
                html_parts.append(f"<div class='stat-number'>{stats['total_sessions']}</div>")
                html_parts.append("<div class='stat-label'>总会话数</div>")
                html_parts.append("</div>")
                html_parts.append("<div class='stat-box'>")
                html_parts.append(f"<div class='stat-number'>{stats['total_tokens_used']}</div>")
                html_parts.append("<div class='stat-label'>Token 使用</div>")
                html_parts.append("</div>")

        # 日志
        if data.get('logs'):
            logs = data['logs']
            html_parts.append("<h2>日志摘要</h2>")

            if logs.get('operational'):
                html_parts.append("<h3>最近操作日志</h3>")
                html_parts.append("<pre>")
                for line in logs['operational'][-20:]:
                    html_parts.append(line.rstrip() + "\n")
                html_parts.append("</pre>")

        # 页脚
        html_parts.append("<div class='footer'>")
        html_parts.append("<p>由 Project Prometheus 自动生成</p>")
        html_parts.append("</div>")

        html_parts.append("</div>")  # container
        html_parts.append("</body>")
        html_parts.append("</html>")

        return '\n'.join(html_parts)

    def _export_pdf(self, data: Dict[str, Any], filename: str) -> Path:
        """导出为 PDF 格式

        注意：PDF 导出需要安装额外的依赖（如 weasyprint 或 pdfkit）
        如果依赖不可用，将回退到先生成 HTML 再提示用户
        """
        output_path = self.export_dir / f"{filename}.pdf"

        # 首先生成 HTML
        html_content = self._generate_html(data)
        html_path = self.export_dir / f"{filename}_temp.html"

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 尝试使用不同方法生成 PDF
        pdf_generated = False

        # 方法 1: 尝试使用 weasyprint
        try:
            from weasyprint import HTML
            HTML(str(html_path)).write_pdf(str(output_path))
            pdf_generated = True
        except ImportError:
            pass
        except Exception:
            pass

        # 方法 2: 尝试使用 pdfkit (需要 wkhtmltopdf)
        if not pdf_generated:
            try:
                import pdfkit
                pdfkit.from_file(str(html_path), str(output_path))
                pdf_generated = True
            except ImportError:
                pass
            except Exception:
                pass

        # 方法 3: 尝试使用 playwright
        if not pdf_generated:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page()
                    page.goto(f"file://{html_path.absolute()}")
                    page.pdf_output(path=str(output_path))
                    browser.close()
                pdf_generated = True
            except ImportError:
                pass
            except Exception:
                pass

        # 清理临时 HTML 文件
        if pdf_generated and html_path.exists():
            html_path.unlink()

        if not pdf_generated:
            # 如果无法生成 PDF，返回 HTML 文件并提示
            final_html_path = self.export_dir / f"{filename}.html"
            if html_path.exists():
                html_path.rename(final_html_path)

            raise RuntimeError(
                "PDF 导出需要安装以下任一库:\n"
                "  - weasyprint: pip install weasyprint\n"
                "  - pdfkit: pip install pdfkit (还需要安装 wkhtmltopdf)\n"
                "  - playwright: pip install playwright && playwright install chromium\n\n"
                f"已生成 HTML 格式报告: {final_html_path}"
            )

        return output_path

    def export_progress(self, format: str = "markdown",
                        output_file: Optional[str] = None) -> Dict[str, Any]:
        """仅导出进度报告"""
        return self.export_project(
            components=['progress'],
            format=format,
            output_file=output_file or "progress_report",
            include_logs=False
        )

    def export_knowledge(self, format: str = "markdown",
                         output_file: Optional[str] = None) -> Dict[str, Any]:
        """仅导出知识库报告"""
        return self.export_project(
            components=['knowledge'],
            format=format,
            output_file=output_file or "knowledge_report",
            include_logs=False
        )

    def export_logs(self, format: str = "markdown",
                    output_file: Optional[str] = None,
                    lines: int = 500) -> Dict[str, Any]:
        """仅导出日志报告"""
        return self.export_project(
            components=['logs'],
            format=format,
            output_file=output_file or "logs_report",
            include_logs=True,
            log_lines=lines
        )

    def list_exports(self) -> List[Dict[str, Any]]:
        """列出所有导出的报告"""
        exports = []

        for file in self.export_dir.glob("*"):
            if file.is_file() and file.suffix in ['.md', '.html', '.pdf']:
                stat = file.stat()
                exports.append({
                    "filename": file.name,
                    "path": str(file),
                    "format": file.suffix[1:].upper(),
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        # 按修改时间倒序排序
        exports.sort(key=lambda x: x['modified_at'], reverse=True)

        return exports

    def get_export_dir(self) -> Path:
        """获取导出目录路径"""
        return self.export_dir


# 便捷函数
def get_export_manager() -> ExportManager:
    """获取导出管理器实例"""
    return ExportManager()


if __name__ == "__main__":
    # 测试导出功能
    print("Testing ExportManager...")

    manager = ExportManager()

    # 测试导出完整报告
    print("\n1. 导出完整报告 (Markdown)...")
    result = manager.export_project(
        components=['all'],
        format="markdown",
        output_file="test_full_report"
    )
    print(f"   输出: {result['output_path']}")
    print(f"   组件: {result['components']}")

    # 测试导出 HTML
    print("\n2. 导出 HTML 报告...")
    result = manager.export_project(
        components=['progress', 'knowledge'],
        format="html",
        output_file="test_html_report"
    )
    print(f"   输出: {result['output_path']}")

    # 测试仅导出进度
    print("\n3. 仅导出进度...")
    result = manager.export_progress(format="markdown")
    print(f"   输出: {result['output_path']}")

    # 测试仅导出知识库
    print("\n4. 仅导出知识库...")
    result = manager.export_knowledge(format="markdown")
    print(f"   输出: {result['output_path']}")

    # 列出所有导出
    print("\n5. 已导出的报告:")
    exports = manager.list_exports()
    for exp in exports:
        print(f"   - {exp['filename']} ({exp['format']}, {exp['size_bytes']} bytes)")

    print("\n测试完成!")
