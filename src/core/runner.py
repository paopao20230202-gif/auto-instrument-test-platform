"""测试运行器 - 执行测试用例并生成报告"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Type, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .station import TestStation
from .test_case import TestCase, TestResult, StepStatus

console = Console()


class TestRunner:
    """负责调度测试用例、收集结果、生成多格式报告"""

    def __init__(self, station: TestStation, report_dir: str = "reports"):
        self.station = station
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TestResult] = []

    def run_test(self, test_cls: Type[TestCase]) -> TestResult:
        """运行单个测试用例"""
        console.print(Panel(f"[bold]开始测试: {test_cls.name}[/bold]\n{test_cls.description}", style="blue"))
        test = test_cls(self.station)
        result = test.run()
        self.results.append(result)

        # 打印结果
        status_style = {
            StepStatus.PASSED: "green",
            StepStatus.FAILED: "red",
            StepStatus.ERROR: "bold red",
        }.get(result.status, "yellow")

        console.print(f"[{status_style}]测试结束: {result.status.value.upper()}[/{status_style}]")
        if result.error_message:
            console.print(f"[red]错误信息: {result.error_message}[/red]")

        # 步骤详情
        if result.steps:
            table = Table(title="步骤详情")
            table.add_column("步骤")
            table.add_column("状态")
            table.add_column("耗时(s)")
            table.add_column("错误")
            for s in result.steps:
                style = "green" if s["status"] == "passed" else "red"
                table.add_row(
                    s["name"],
                    f"[{style}]{s['status']}[/{style}]",
                    f"{s['duration_sec']:.2f}",
                    s.get("error") or "",
                )
            console.print(table)

        return result

    def run_all(self, test_classes: List[Type[TestCase]]) -> List[TestResult]:
        """顺序运行多个测试"""
        for cls in test_classes:
            self.run_test(cls)
        return self.results

    def generate_reports(self, prefix: Optional[str] = None) -> Dict[str, Path]:
        """生成 JSON / CSV / 简易 HTML 报告"""
        if not self.results:
            console.print("[yellow]无结果可生成报告[/yellow]")
            return {}

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = prefix or f"report_{ts}"
        paths = {}

        # JSON
        json_path = self.report_dir / f"{prefix}.json"
        data = {
            "station": self.station.settings.get("station", {}),
            "mode": self.station.mode,
            "generated_at": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        paths["json"] = json_path

        # CSV (扁平化测量值)
        csv_path = self.report_dir / f"{prefix}.csv"
        rows = []
        for r in self.results:
            base = {
                "test_name": r.test_name,
                "status": r.status.value,
                "start_time": r.start_time.isoformat(),
                "end_time": r.end_time.isoformat() if r.end_time else "",
            }
            if r.measurement_result:
                for m in r.measurement_result.measurements:
                    row = base.copy()
                    row.update({
                        "measurement": m.name,
                        "value": m.value,
                        "unit": m.unit,
                        "passed": m.passed,
                        "lower_limit": m.lower_limit,
                        "upper_limit": m.upper_limit,
                    })
                    rows.append(row)
            else:
                rows.append(base)

        if rows:
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            paths["csv"] = csv_path

        # 简易 HTML
        html_path = self.report_dir / f"{prefix}.html"
        html = self._render_html(data)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        paths["html"] = html_path

        console.print(Panel(
            "\n".join(f"{k.upper()}: {v}" for k, v in paths.items()),
            title="[green]报告已生成[/green]",
            border_style="green",
        ))
        return paths

    def _render_html(self, data: dict) -> str:
        rows = ""
        for r in data["results"]:
            status_color = {"passed": "#28a745", "failed": "#dc3545", "error": "#dc3545"}.get(r["status"], "#6c757d")
            rows += f"""
            <tr>
                <td>{r['test_name']}</td>
                <td style="color:{status_color};font-weight:bold">{r['status'].upper()}</td>
                <td>{r.get('start_time', '')}</td>
                <td>{r.get('end_time', '')}</td>
                <td>{r.get('error_message') or '-'}</td>
            </tr>"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>自动测试报告</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #f8f9fa; }}
.container {{ max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
h1 {{ color: #212529; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; }}
th {{ background: #e9ecef; font-weight: 600; }}
.meta {{ color: #6c757d; margin-bottom: 20px; }}
</style>
</head>
<body>
<div class="container">
<h1>自动仪器测试报告</h1>
<div class="meta">
生成时间: {data['generated_at']}<br>
模式: {data['mode']}<br>
测试站: {data.get('station', {}).get('name', 'N/A')}
</div>
<table>
<thead><tr><th>测试名称</th><th>状态</th><th>开始时间</th><th>结束时间</th><th>错误信息</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
</body>
</html>"""
