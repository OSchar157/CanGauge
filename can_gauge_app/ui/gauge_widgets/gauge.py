from typing import Any
from PyQt5.QtWidgets import QWidget
from dataclasses import dataclass, field
from typing import Any

import inspect, json

@dataclass
class ParamSpec:
    name: str
    label: str
    type: type           # int, float, str, bool, etc.
    default: Any = None
    required: bool = True

class Gauge(QWidget):

    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        return [
            ParamSpec("min_val", "Minimum Value", int),
            ParamSpec("max_val", "Maximum Value", int),
            ParamSpec("warn_low", "Warning Low", int),
            ParamSpec("warn_high", "Warning High", int),
            ParamSpec("danger_low", "Danger Low", int),
            ParamSpec("danger_high", "Danger High", int),
            ParamSpec("unit", "Units", str),
            ParamSpec("label", "Label", str),
        ]

    def __init__(self, min_val: float, max_val: str, warn_low: float, 
                 warn_high: float, danger_low: float, danger_high: float, 
                 unit: str, label: str, parent = None):
        super().__init__(parent)

        self.min_val = min_val
        self.max_val = max_val
        self.warn_low = warn_low
        self.warn_high = warn_high
        self.danger_low = danger_low
        self.danger_high = danger_high
        self.unit = unit
        self.label = label
        self._value = min_val
        self._id = None

    def set_value(self, value: float):
        self._value = max(self.min_val, min(self.max_val, value))
        self.update()

    def value(self) -> float:
        return self._value
    
    def to_json(self):
        sig = inspect.signature(self.__class__.__init__)
        data = {"type": self.__class__.__name__}
        for name, param in sig.parameters.items():
            if name in ("self", "parent"):
                continue
            data[name] = getattr(self, name)
        data["id"] = self._id
        return data