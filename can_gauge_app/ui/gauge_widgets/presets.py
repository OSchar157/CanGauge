from ui.gauge_widgets.needle_gauge import NeedleGauge
from ui.gauge_widgets.gauge import ParamSpec

# TODO: This is temporary (famous last words), figure out a way to make presets without classes, too much overhead

class Speedometer(NeedleGauge):
    name = "Speedometer"

    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        fields = super().get_fields()  # get parent fields
        # override defaults
        for f in fields:
            if f.name == "val_offset": f.default = 0
            if f.name == "val_scale": f.default = 0.621371
            if f.name == "min_val": f.default = 0
            if f.name == "danger_low": f.default = None
            if f.name == "warn_low": f.default = None
            if f.name == "warn_high": f.default = None
            if f.name == "danger_high": f.default = None
            if f.name == "max_val": f.default = 140
            if f.name == "unit": f.default = "MPH"
            if f.name == "label":   f.default = "Speedometer"
            if f.name == "maj_ticks":   f.default = 14
        return fields

    def __init__(self, val_offset, val_scale, min_val=0, max_val=140, warn_low=None, warn_high=None, 
                 danger_low=None, danger_high=None, unit="KPH", label="", maj_ticks = 14, parent=None):
        super().__init__(val_offset, val_scale, min_val, max_val, warn_low, warn_high, danger_low, 
                         danger_high, unit, label, maj_ticks, parent)

class EngineSpeedGauge(NeedleGauge):
    name = "Engine Speed Gauge"

    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        fields = super().get_fields()  # get parent fields
        # override defaults
        for f in fields:
            if f.name == "min_val": f.default = 0
            if f.name == "danger_low": f.default = None
            if f.name == "warn_low": f.default = None
            if f.name == "warn_high": f.default = None
            if f.name == "danger_high": f.default = 5000
            if f.name == "max_val": f.default = 8000
            if f.name == "unit": f.default = "RPM"
            if f.name == "label":   f.default = ""
            if f.name == "maj_ticks": f.default = 8
        return fields

    def __init__(self, min_val=0, max_val=8000, warn_low=None, warn_high=None, 
                 danger_low=None, danger_high=5000, unit="RPM", label="", maj_ticks = 8, parent=None):
        super().__init__(min_val, max_val, warn_low, warn_high, danger_low, 
                         danger_high, unit, label, maj_ticks, parent)