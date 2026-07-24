"""测试站（Station）- 管理仪器连接与全局配置"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from rich.console import Console
from rich.table import Table

from src.instruments.power_supply import PowerSupply
from src.instruments.base import InstrumentBase

console = Console()


class TestStation:
    """
    测试站：负责加载配置、创建仪器实例、提供统一访问接口
    类似 OpenHTF 的 Station 概念，但更轻量
    """

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.instruments: Dict[str, InstrumentBase] = {}
        self.settings: Dict[str, Any] = {}
        self.mode: str = "simulation"
        self._load_configs()

    def _load_configs(self) -> None:
        """加载 instruments.yaml 与 settings.yaml"""
        inst_path = self.config_dir / "instruments.yaml"
        settings_path = self.config_dir / "settings.yaml"

        if not inst_path.exists():
            raise FileNotFoundError(f"找不到仪器配置: {inst_path}")

        with open(inst_path, "r", encoding="utf-8") as f:
            inst_cfg = yaml.safe_load(f)

        self.mode = inst_cfg.get("mode", "simulation")
        self._raw_instruments = inst_cfg.get("instruments", {})

        if settings_path.exists():
            with open(settings_path, "r", encoding="utf-8") as f:
                self.settings = yaml.safe_load(f) or {}

        console.print(f"[bold cyan]测试站模式:[/bold cyan] {self.mode}")

    def create_instruments(self) -> None:
        """根据配置创建所有仪器实例（不立即连接）"""
        for name, cfg in self._raw_instruments.items():
            itype = cfg.get("type", "").lower()
            sim = self.mode == "simulation"
            resource = cfg.get("sim_resource" if sim else "resource")

            if not resource:
                console.print(f"[yellow]跳过 {name}: 无有效资源字符串[/yellow]")
                continue

            if itype == "power_supply":
                inst = PowerSupply(
                    resource=resource,
                    channels=cfg.get("channels", [1, 3, 5, 7]),
                    timeout=cfg.get("timeout", 10000),
                    name=name,
                    sim_mode=sim,
                )
                self.instruments[name] = inst
            else:
                console.print(f"[yellow]未知仪器类型 {itype}，跳过 {name}[/yellow]")

        console.print(f"[green]已创建 {len(self.instruments)} 个仪器实例[/green]")

    def connect_all(self) -> None:
        """连接所有仪器"""
        for name, inst in self.instruments.items():
            try:
                inst.connect()
                idn = inst.identify()
                console.print(f"  [dim]{name} IDN: {idn}[/dim]")
            except Exception as e:
                console.print(f"[red]无法连接 {name}: {e}[/red]")
                if self.mode != "simulation":
                    raise

    def disconnect_all(self) -> None:
        """断开所有仪器"""
        for inst in self.instruments.values():
            try:
                inst.disconnect()
            except Exception:
                pass

    def get(self, name: str) -> InstrumentBase:
        """获取仪器实例"""
        if name not in self.instruments:
            raise KeyError(f"仪器 '{name}' 未配置或未创建")
        return self.instruments[name]

    def summary(self) -> None:
        """打印测试站摘要"""
        table = Table(title="测试站仪器状态")
        table.add_column("名称", style="cyan")
        table.add_column("类型", style="magenta")
        table.add_column("资源", style="green")
        table.add_column("已连接", style="yellow")

        for name, inst in self.instruments.items():
            table.add_row(
                name,
                type(inst).__name__,
                inst.resource,
                "✓" if inst.is_connected() else "✗",
            )
        console.print(table)

    def __enter__(self):
        self.create_instruments()
        self.connect_all()
        return self

    def __exit__(self, *args):
        self.disconnect_all()
