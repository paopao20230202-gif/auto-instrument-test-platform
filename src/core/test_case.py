"""测试用例与步骤定义"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from .measurement import MeasurementResult


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestStep:
    """单个测试步骤"""
    name: str
    func: Callable  # 实际执行函数
    description: str = ""
    critical: bool = True  # 失败是否终止整个测试
    retry: int = 0
    status: StepStatus = StepStatus.PENDING
    error: Optional[str] = None
    duration_sec: float = 0.0


@dataclass
class TestResult:
    """完整测试结果"""
    test_name: str
    status: StepStatus = StepStatus.PENDING
    steps: List[Dict] = field(default_factory=list)
    measurement_result: Optional[MeasurementResult] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "test_name": self.test_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message,
            "steps": self.steps,
            "measurements": self.measurement_result.to_dict() if self.measurement_result else None,
        }


class TestCase(ABC):
    """测试用例基类 - 用户自定义测试需继承此类"""

    name: str = "UnnamedTest"
    description: str = ""

    def __init__(self, station: Any):
        self.station = station
        self.steps: List[TestStep] = []
        self.result = TestResult(test_name=self.name)

    def add_step(
        self,
        name: str,
        func: Callable,
        description: str = "",
        critical: bool = True,
        retry: int = 0,
    ) -> None:
        self.steps.append(
            TestStep(name=name, func=func, description=description, critical=critical, retry=retry)
        )

    @abstractmethod
    def setup(self) -> None:
        """测试前准备：定义步骤、初始化测量等"""
        pass

    def teardown(self) -> None:
        """测试后清理（可选重写）"""
        pass

    def run(self) -> TestResult:
        """执行整个测试用例"""
        self.result.start_time = datetime.now()
        self.result.status = StepStatus.RUNNING

        try:
            self.setup()
            for step in self.steps:
                self._execute_step(step)
                if step.status == StepStatus.FAILED and step.critical:
                    self.result.status = StepStatus.FAILED
                    self.result.error_message = step.error
                    break
                if step.status == StepStatus.ERROR and step.critical:
                    self.result.status = StepStatus.ERROR
                    self.result.error_message = step.error
                    break
            else:
                # 所有步骤完成
                failed = any(s.status in (StepStatus.FAILED, StepStatus.ERROR) for s in self.steps)
                self.result.status = StepStatus.FAILED if failed else StepStatus.PASSED
        except Exception as e:
            self.result.status = StepStatus.ERROR
            self.result.error_message = str(e)
        finally:
            try:
                self.teardown()
            except Exception:
                pass
            self.result.end_time = datetime.now()
            self.result.steps = [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "error": s.error,
                    "duration_sec": s.duration_sec,
                    "description": s.description,
                }
                for s in self.steps
            ]

        return self.result

    def _execute_step(self, step: TestStep) -> None:
        import time
        step.status = StepStatus.RUNNING
        start = time.time()
        attempts = step.retry + 1
        last_error = None

        for attempt in range(attempts):
            try:
                step.func()
                step.status = StepStatus.PASSED
                last_error = None
                break
            except Exception as e:
                last_error = str(e)
                if attempt < attempts - 1:
                    time.sleep(1.0)  # 重试间隔

        step.duration_sec = time.time() - start
        if last_error:
            step.status = StepStatus.FAILED
            step.error = last_error
