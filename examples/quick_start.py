"""
最简快速示例：直接使用 PowerSupply 类读取电压
无需完整测试框架，适合快速验证仪器连接
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.instruments.power_supply import PowerSupply
from rich.console import Console

console = Console()

def main():
    # 仿真模式示例（无需真实硬件）
    with PowerSupply(
        resource="ASRL1::INSTR",
        channels=[1, 3, 5, 7],
        sim_mode=True,
        name="仿真电源"
    ) as psu:
        console.print(psu.get_status_summary())

        # 单通道测量
        v = psu.measure_voltage(1)
        console.print(f"\nCH1 单独测量: {v:.3f} V")

if __name__ == "__main__":
    main()
