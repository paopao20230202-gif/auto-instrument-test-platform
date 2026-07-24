"""测量结果数据结构"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional, List
import json


@dataclass
class Measurement:
    """单次测量定义"""
    name: str
    value: Any
    unit: str = ""
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def passed(self) -> Optional[bool]:
        """判断是否在限值范围内（无限制则返回 None）"""
        if self.value is None:
            return False
        if not isinstance(self.value, (int, float)):
            return None
        if self.lower_limit is not None and self.value < self.lower_limit:
            return False
        if self.upper_limit is not None and self.value > self.upper_limit:
            return False
        if self.lower_limit is None and self.upper_limit is None:
            return None
        return True

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["passed"] = self.passed
        return d


@dataclass
class MeasurementResult:
    """一组测量的集合结果"""
    test_name: str
    measurements: List[Measurement] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def add(self, measurement: Measurement) -> None:
        self.measurements.append(measurement)

    def finish(self) -> None:
        self.end_time = datetime.now()

    @property
    def overall_passed(self) -> bool:
        results = [m.passed for m in self.measurements if m.passed is not None]
        if not results:
            return True
        return all(results)

    def to_dict(self) -> Dict:
        return {
            "test_name": self.test_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "overall_passed": self.overall_passed,
            "measurements": [m.to_dict() for m in self.measurements],
            "extra": self.extra,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
