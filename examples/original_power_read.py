"""
你原始的「电源读取电参数」脚本（原样保留作为参考）
来源：desktop-tutorial 仓库
"""

import pyvisa
import time
import datetime

POWER_RESOURCE = 'TCPIP0::192.168.200.100::inst0::INSTR'
POWER_CHANNELS = [1, 3, 5, 7]

print("=== 通道读取测试版 ===")
print("按 Ctrl+C 停止")

rm = pyvisa.ResourceManager()
power = rm.open_resource(POWER_RESOURCE)
power.timeout = 10000
power.write("SYST:REM")

while True:
    now = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"\n[{now}] 开始读取4个通道...")

    for ch in POWER_CHANNELS:
        try:
            power.write(f"INST:SEL CH{ch}")
            time.sleep(0.3)                    # 等待通道切换
            v = float(power.query(f"MEAS:VOLT? CH{ch}").strip())
            print(f"  CH{ch} → {v:.3f} V")
        except Exception as e:
            print(f"  CH{ch} 读取失败: {str(e)}")

    time.sleep(2)
