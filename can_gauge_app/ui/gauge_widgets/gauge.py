from typing import Any
from PyQt5.QtWidgets import QWidget
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ParamSpec:
    name: str
    label: str
    type: type
    default: Any = None
    required: bool = True

class Gauge(QWidget):

    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        return [
            ParamSpec("val_offset", "Value Offset", float, 0.0),
            ParamSpec("val_scale", "Value Scale", float, 1.0),
            ParamSpec("min_val", "Minimum Value", float, 0.0),
            ParamSpec("max_val", "Maximum Value", float, 100.0),
            ParamSpec("warn_low", "Warning Low", float, 20.0),
            ParamSpec("warn_high", "Warning High", float, 80.0),
            ParamSpec("danger_low", "Danger Low", float, 10.0),
            ParamSpec("danger_high", "Danger High", float, 90.0),
            ParamSpec("unit", "Units", str, "unit"),
            ParamSpec("label", "Label", str, "label"),
        ]

    def __init__(
        self, 
        val_offset: float, 
        val_scale: float, 
        min_val: float, 
        max_val: float,
        warn_low: float | None, 
        warn_high: float | None, 
        danger_low: float | None, 
        danger_high: float | None, 
        unit: str | None, 
        label: str | None, 
        parent = None):
        super().__init__(parent)

        # --- type checks ---
        for name, val in [("val_offset", val_offset), ("val_scale", val_scale),
                        ("min_val", min_val), ("max_val", max_val)]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be a float, got {type(val).__name__}.")

        for name, val in [("warn_low", warn_low), ("warn_high", warn_high),
                        ("danger_low", danger_low), ("danger_high", danger_high)]:
            if val is not None and not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be a float or None, got {type(val).__name__}.")

        for name, val in [("unit", unit), ("label", label)]:
            if val is not None and not isinstance(val, str):
                raise TypeError(f"{name} must be a str or None, got {type(val).__name__}.")

        # --- range/ordering checks ---
        if min_val >= max_val:
            raise ValueError(f"min_val ({min_val}) must be less than max_val ({max_val}).")

        if (warn_low is not None) and (warn_high is not None) and (warn_low >= warn_high):
            raise ValueError(f"warn_low ({warn_low}) must be less than warn_high ({warn_high}).")

        if (danger_low is not None) and (danger_high is not None) and (danger_low >= danger_high):
            raise ValueError(f"danger_low ({danger_low}) must be less than danger_high ({danger_high}).")

        # warn/danger thresholds should sit within [min_val, max_val]
        for name, val in [("warn_low", warn_low), ("warn_high", warn_high),
                        ("danger_low", danger_low), ("danger_high", danger_high)]:
            if val is not None and not (min_val <= val <= max_val):
                raise ValueError(f"{name} ({val}) must be within [min_val, max_val] = [{min_val}, {max_val}].")

        # danger bounds should be outside (or equal to) the warn bounds, if both are set
        if (danger_low is not None) and (warn_low is not None) and (danger_low > warn_low):
            raise ValueError(f"danger_low ({danger_low}) must be less than or equal to warn_low ({warn_low}).")

        if (danger_high is not None) and (warn_high is not None) and (danger_high < warn_high):
            raise ValueError(f"danger_high ({danger_high}) must be greater than or equal to warn_high ({warn_high}).")
        

        self.val_offset = val_offset
        self.val_scale = val_scale
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
        set_val = (value * self.val_scale) + self.val_offset
        self._value = max(self.min_val, min(self.max_val, set_val))
        self.update()