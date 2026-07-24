"""仪器抽象基类 - 所有仪器驱动的父类"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pyvisa
from rich.console import Console

console = Console()


class InstrumentBase(ABC):
    """所有仪器的基类，封装PyVISA连接与通用操作"""

    def __init__(
        self,
        resource: str,
        timeout: int = 10000,
        name: str = "Instrument",
        sim_mode: bool = False,
    ):
        self.resource = resource
        self.timeout = timeout
        self.name = name
        self.sim_mode = sim_mode
        self._rm: Optional[pyvisa.ResourceManager] = None
        self._inst: Optional[pyvisa.resources.Resource] = None
        self._connected = False

    def connect(self) -> None:
        """建立与仪器的连接"""
        if self._connected:
            return
        try:
            # 仿真模式使用 @sim 后端
            if self.sim_mode:
                self._rm = pyvisa.ResourceManager("@sim")
            else:
                self._rm = pyvisa.ResourceManager()
            self._inst = self._rm.open_resource(self.resource)
            self._inst.timeout = self.timeout
            self._connected = True
            console.print(f"[green]✓[/green] {self.name} 已连接: {self.resource}")
            self._post_connect()
        except Exception as e:
            console.print(f"[red]✗[/red] {self.name} 连接失败: {e}")
            raise

    def disconnect(self) -> None:
        """断开连接并释放资源"""
        if self._inst is not None:
            try:
                self._inst.close()
            except Exception:
                pass
            self._inst = None
        if self._rm is not None:
            try:
                self._rm.close()
            except Exception:
                pass
            self._rm = None
        self._connected = False
        console.print(f"[yellow]•[/yellow] {self.name} 已断开")

    def _post_connect(self) -> None:
        """连接后钩子，子类可重写做初始化命令"""
        pass

    def write(self, cmd: str) -> None:
        """发送命令"""
        if not self._connected or self._inst is None:
            raise RuntimeError(f"{self.name} 未连接")
        self._inst.write(cmd)

    def query(self, cmd: str) -> str:
        """发送查询并返回结果"""
        if not self._connected or self._inst is None:
            raise RuntimeError(f"{self.name} 未连接")
        return self._inst.query(cmd).strip()

    def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    def identify(self) -> str:
        """返回仪器识别信息 (*IDN?)"""
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
