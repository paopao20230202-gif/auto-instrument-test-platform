"""电源供应器驱动 - 基于你 GitHub 仓库中的原始通道读取代码扩展"""

import time
from typing import List, Dict, Optional
from .base import InstrumentBase
from rich.console import Console

console = Console()


class PowerSupply(InstrumentBase):
    """
    可编程电源供应器控制类
    支持多通道电压/电流测量与设置
    原始逻辑来自你的「电源读取电参数」脚本
    """

    def __init__(
        self,
        resource: str,
        channels: List[int] = None,
        timeout: int = 10000,
        name: str = "PowerSupply",
        sim_mode: bool = False,
    ):
        super().__init__(resource, timeout, name, sim_mode)
        self.channels = channels or [1, 3, 5, 7]
        self._channel_delay = 0.3  # 通道切换等待时间（与你原始代码一致）

    def _post_connect(self) -> None:
        """连接后进入远程模式（与你原始代码一致）"""
        try:
            self.write("SYST:REM")
            console.print(f"  [dim]已切换到远程控制模式 (SYST:REM)[/dim]")
        except Exception as e:
            console.print(f"  [yellow]警告: 无法进入远程模式: {e}[/yellow]")

    def identify(self) -> str:
        """查询仪器身份"""
        try:
            return self.query("*IDN?")
        except Exception:
            return "Unknown Power Supply (simulation or no *IDN? support)"

    def select_channel(self, channel: int) -> None:
        """选择通道（与你原始代码 INST:SEL CHx 一致）"""
        if channel not in self.channels:
            raise ValueError(f"通道 {channel} 不在配置列表 {self.channels} 中")
        self.write(f"INST:SEL CH{channel}")
        time.sleep(self._channel_delay)

    def measure_voltage(self, channel: int) -> float:
        """测量指定通道电压（核心逻辑来自你的原始脚本）"""
        self.select_channel(channel)
        # 兼容你原始的 MEAS:VOLT? CHx 写法
        try:
            raw = self.query(f"MEAS:VOLT? CH{channel}")
            return float(raw)
        except Exception:
            # 备用写法（部分电源支持）
            raw = self.query("MEAS:VOLT?")
            return float(raw)

    def measure_current(self, channel: int) -> float:
        """测量指定通道电流"""
        self.select_channel(channel)
        try:
            raw = self.query(f"MEAS:CURR? CH{channel}")
            return float(raw)
        except Exception:
            raw = self.query("MEAS:CURR?")
            return float(raw)

    def measure_all_channels(self) -> Dict[int, Dict[str, float]]:
        """
        一次性读取所有配置通道的电压与电流
        返回格式: {ch: {"voltage": v, "current": i}, ...}
        """
        results = {}
        for ch in self.channels:
            try:
                v = self.measure_voltage(ch)
                # 电流测量可选，失败时记为 None
                try:
                    i = self.measure_current(ch)
                except Exception:
                    i = None
                results[ch] = {"voltage": v, "current": i}
            except Exception as e:
                console.print(f"  [red]CH{ch} 读取失败: {e}[/red]")
                results[ch] = {"voltage": None, "current": None, "error": str(e)}
        return results

    def set_voltage(self, channel: int, voltage: float) -> None:
        """设置指定通道电压"""
        self.select_channel(channel)
        self.write(f"VOLT {voltage}")

    def set_current_limit(self, channel: int, current: float) -> None:
        """设置指定通道电流限制"""
        self.select_channel(channel)
        self.write(f"CURR {current}")

    def output_on(self, channel: Optional[int] = None) -> None:
        """打开输出"""
        if channel is not None:
            self.select_channel(channel)
        self.write("OUTP ON")

    def output_off(self, channel: Optional[int] = None) -> None:
        """关闭输出"""
        if channel is not None:
            self.select_channel(channel)
        self.write("OUTP OFF")

    def get_status_summary(self) -> str:
        """返回当前所有通道的快速状态摘要"""
        data = self.measure_all_channels()
        lines = [f"{self.name} 状态摘要:"]
        for ch, vals in data.items():
            v = vals.get("voltage")
            i = vals.get("current")
            if v is not None:
                line = f"  CH{ch}: {v:.3f} V"
                if i is not None:
                    line += f"  {i:.3f} A"
                lines.append(line)
            else:
                lines.append(f"  CH{ch}: 读取失败")
        return "\n".join(lines)
