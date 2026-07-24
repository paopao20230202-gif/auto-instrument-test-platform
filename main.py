#!/usr/bin/env python3
"""
自动仪器测试平台入口
用法:
  python main.py                  # 运行所有默认测试（仿真模式）
  python main.py --real           # 使用真实仪器
  python main.py --test voltage   # 只运行电压读取测试
"""

import sys
from pathlib import Path

# 确保项目根目录在 path 中
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import click
from rich.console import Console
from rich.panel import Panel

from src.core.station import TestStation
from src.core.runner import TestRunner
from src.tests.power_voltage_test import PowerVoltageReadTest, PowerChannelStabilityTest

console = Console()


@click.command()
@click.option("--real", is_flag=True, help="使用真实仪器（覆盖配置中的 simulation 模式）")
@click.option("--test", "test_name", default="all", type=click.Choice(["all", "voltage", "stability"]), help="选择要运行的测试")
@click.option("--config", default="config", help="配置目录路径")
def main(real: bool, test_name: str, config: str):
    """自动仪器测试平台 - 基于你的电源读取脚本构建"""
    console.print(Panel.fit(
        "[bold cyan]自动仪器测试平台 v1.0[/bold cyan]\n"
        "基于 PyVISA + 你的电源通道读取代码\n"
        "支持真实仪器与仿真模式",
        border_style="cyan",
    ))

    station = TestStation(config_dir=config)

    # 命令行强制真实模式
    if real:
        station.mode = "real"
        console.print("[bold yellow]强制切换到真实仪器模式[/bold yellow]")

    try:
        with station:  # 自动 create + connect + disconnect
            station.summary()

            runner = TestRunner(station)

            tests = []
            if test_name in ("all", "voltage"):
                tests.append(PowerVoltageReadTest)
            if test_name in ("all", "stability"):
                tests.append(PowerChannelStabilityTest)

            runner.run_all(tests)
            runner.generate_reports()

    except KeyboardInterrupt:
        console.print("\n[yellow]用户中断测试[/yellow]")
    except Exception as e:
        console.print(f"[bold red]平台运行错误: {e}[/bold red]")
        raise


if __name__ == "__main__":
    main()
