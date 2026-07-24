"""电源电压读取与稳定性测试用例 - 直接基于你原始脚本逻辑"""

from typing import Dict
from src.core.test_case import TestCase
from src.core.measurement import Measurement, MeasurementResult
from rich.console import Console

console = Console()


class PowerVoltageReadTest(TestCase):
    """
    基础电压读取测试
    对应你原始脚本「电源读取电参数」的自动化版本
    """

    name = "PowerVoltageReadTest"
    description = "读取电源所有配置通道的电压，并检查是否在合理范围内"

    def setup(self) -> None:
        self.psu = self.station.get("power_supply")
        self.meas_result = MeasurementResult(test_name=self.name)

        self.add_step(
            name="连接检查",
            func=self._check_connection,
            description="确认电源已连接",
            critical=True,
        )
        self.add_step(
            name="读取所有通道电压",
            func=self._read_all_voltages,
            description="循环读取 CH1/3/5/7 电压",
            critical=True,
            retry=2,
        )
        self.add_step(
            name="电压限值检查",
            func=self._check_limits,
            description="检查电压是否在 0~35V 范围内",
            critical=False,
        )

    def _check_connection(self) -> None:
        if not self.psu.is_connected():
            raise RuntimeError("电源未连接")
        console.print(f"  仪器识别: {self.psu.identify()}")

    def _read_all_voltages(self) -> None:
        data = self.psu.measure_all_channels()
        console.print("  测量结果:")
        for ch, vals in data.items():
            v = vals.get("voltage")
            if v is not None:
                console.print(f"    CH{ch} → {v:.3f} V")
                self.meas_result.add(
                    Measurement(
                        name=f"CH{ch}_voltage",
                        value=v,
                        unit="V",
                        lower_limit=0.0,
                        upper_limit=35.0,
                    )
                )
            else:
                raise RuntimeError(f"CH{ch} 电压读取失败: {vals.get('error')}")

        self.result.measurement_result = self.meas_result
        self.meas_result.finish()

    def _check_limits(self) -> None:
        failed = []
        for m in self.meas_result.measurements:
            if m.passed is False:
                failed.append(f"{m.name}={m.value}{m.unit}")
        if failed:
            raise AssertionError(f"以下通道超出限值: {', '.join(failed)}")
        console.print("  [green]所有通道电压均在限值内[/green]")


class PowerChannelStabilityTest(TestCase):
    """
    通道稳定性测试：连续多次读取，计算波动范围
    """

    name = "PowerChannelStabilityTest"
    description = "连续读取同一通道多次，评估电压稳定性（峰峰值）"

    def setup(self) -> None:
        self.psu = self.station.get("power_supply")
        self.samples = 5
        self.channel = self.psu.channels[0]  # 默认测第一个通道
        self.meas_result = MeasurementResult(test_name=self.name)

        self.add_step(
            name=f"CH{self.channel} 连续采样",
            func=self._sample_channel,
            description=f"连续读取 {self.samples} 次",
            critical=True,
        )
        self.add_step(
            name="计算稳定性指标",
            func=self._analyze_stability,
            description="计算平均值与峰峰值",
            critical=False,
        )

    def _sample_channel(self) -> None:
        import time
        values = []
        for i in range(self.samples):
            v = self.psu.measure_voltage(self.channel)
            values.append(v)
            console.print(f"    采样 {i+1}/{self.samples}: {v:.4f} V")
            time.sleep(0.5)
        self._values = values

    def _analyze_stability(self) -> None:
        values = self._values
        avg = sum(values) / len(values)
        peak_to_peak = max(values) - min(values)
        console.print(f"  平均值: {avg:.4f} V")
        console.print(f"  峰峰值: {peak_to_peak:.4f} V")

        self.meas_result.add(Measurement(name="average_voltage", value=avg, unit="V"))
        self.meas_result.add(
            Measurement(
                name="peak_to_peak",
                value=peak_to_peak,
                unit="V",
                upper_limit=0.05,  # 示例限值：波动不超过 50mV
            )
        )
        self.meas_result.finish()
        self.result.measurement_result = self.meas_result

        if peak_to_peak > 0.05:
            raise AssertionError(f"电压波动过大: {peak_to_peak:.4f} V > 0.05 V")
