# 自动仪器测试平台 (Auto Instrument Test Platform)

> 基于你 GitHub 仓库中「电源读取电参数」脚本构建的完整自动化硬件测试框架  
> 支持真实仪器（PyVISA）与仿真模式（pyvisa-sim），可扩展多仪器、多测试用例

---

## 功能亮点

| 功能 | 说明 |
|------|------|
| **仪器抽象层** | 统一 `InstrumentBase`，已实现 `PowerSupply`（直接复用你的通道选择与测量逻辑） |
| **仿真模式** | 默认启用 `pyvisa-sim`，无需真实硬件即可完整跑通测试流程 |
| **测试框架** | 步骤化 TestCase + 自动重试 + 测量限值判断 + 详细结果收集 |
| **报告系统** | 自动生成 JSON / CSV / 美观 HTML 报告 |
| **可扩展** | 轻松添加示波器、万用表、电子负载等新仪器与测试用例 |
| **CLI 友好** | 一键运行，支持 `--real` 切换真实仪器 |

---

## 快速开始

### 1. 克隆仓库并安装依赖

```bash
git clone https://github.com/paopao20230202-gif/auto-instrument-test-platform.git
cd auto-instrument-test-platform
pip install -r requirements.txt
```

### 2. 运行（仿真模式，推荐先试）

```bash
python main.py
```

你会看到完整的测试流程：连接仿真电源 → 读取 CH1/3/5/7 电压 → 稳定性测试 → 生成报告。

### 3. 切换到真实仪器

编辑 `config/instruments.yaml`：

```yaml
mode: real   # 改为 real
```

或使用命令行参数：

```bash
python main.py --real
```

确保你的电源 IP 仍是 `192.168.200.100`（或修改配置中的 `resource`）。

### 4. 只运行特定测试

```bash
python main.py --test voltage     # 仅电压读取
python main.py --test stability   # 仅稳定性测试
```

---

## 项目结构

```
auto-instrument-test-platform/
├── main.py                      # 入口 CLI
├── requirements.txt
├── config/
│   ├── instruments.yaml         # 仪器资源、通道、模式配置
│   └── settings.yaml            # 日志、报告、重试等全局设置
├── src/
│   ├── instruments/
│   │   ├── base.py              # 仪器基类（连接/写/查）
│   │   └── power_supply.py      # 电源驱动（核心逻辑来自你的原脚本）
│   ├── core/
│   │   ├── station.py           # 测试站（加载配置 + 管理仪器）
│   │   ├── test_case.py         # 测试用例与步骤抽象
│   │   ├── measurement.py       # 测量结果与限值判断
│   │   └── runner.py            # 运行器 + 多格式报告生成
│   └── tests/
│       └── power_voltage_test.py # 示例测试用例
├── sim/
│   └── power_supply.yaml        # pyvisa-sim 仿真定义
└── reports/                     # 自动生成的测试报告（运行后出现）
```

---

## 如何添加新测试用例

1. 在 `src/tests/` 下新建文件，继承 `TestCase`：

```python
from src.core.test_case import TestCase
from src.core.measurement import Measurement, MeasurementResult

class MyNewTest(TestCase):
    name = "MyNewTest"
    description = "我的新测试"

    def setup(self):
        self.psu = self.station.get("power_supply")
        self.add_step("步骤1", self._step1, critical=True)
        # ...

    def _step1(self):
        v = self.psu.measure_voltage(1)
        # 做断言或记录 Measurement
```

2. 在 `main.py` 中注册并运行。

---

## 如何添加新仪器

1. 在 `src/instruments/` 新建驱动类，继承 `InstrumentBase`。
2. 在 `config/instruments.yaml` 添加配置。
3. 在 `TestStation.create_instruments()` 中增加对应 `type` 分支。

---

## 与你原始代码的对应关系

| 你的原始脚本 | 平台中的位置 |
|-------------|-------------|
| `POWER_RESOURCE = 'TCPIP0::192.168.200.100::inst0::INSTR'` | `config/instruments.yaml` → `resource` |
| `POWER_CHANNELS = [1, 3, 5, 7]` | 同上 `channels` |
| `power.write("SYST:REM")` | `PowerSupply._post_connect()` |
| `power.write(f"INST:SEL CH{ch}")` + `time.sleep(0.3)` | `PowerSupply.select_channel()` |
| `power.query(f"MEAS:VOLT? CH{ch}")` | `PowerSupply.measure_voltage()` |
| `while True` 循环读取 | 被 `PowerVoltageReadTest` 和 `PowerChannelStabilityTest` 结构化替代 |

---

## 推荐后续扩展方向

- 集成 **OpenHTF**（你已 star）作为更专业的测试编排引擎
- 使用 **InstrumentKit** 补充更多仪器驱动
- 添加 **python-can** 支持 CAN 总线设备测试
- 接入 **Prometheus** 做长期监控指标
- 增加 Web UI（Streamlit / FastAPI + 前端）实时查看测试进度
- 支持测试计划（YAML 描述的完整产线测试序列）

---

## 许可证

MIT License – 自由使用与修改。

有任何问题或想增加特定仪器/测试逻辑，直接告诉我，我可以继续帮你迭代这个仓库！
