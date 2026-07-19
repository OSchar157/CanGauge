from ui.gauge_widgets.needle_gauge import NeedleGauge
from ui.gauge_widgets.gauge import ParamSpec

# TODO: This is temporary (famous last words), figure out a way to make presets without classes, too much overhead
KPH_TO_MPH_SCALE = 0.621371
class Speedometer(NeedleGauge):
    name = "Speedometer"

    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        fields = super().get_fields()
        # override defaults
        for f in fields:
            if f.name == "val_offset": f.default = 0
            if f.name == "val_scale": f.default = KPH_TO_MPH_SCALE
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

    def __init__(self, val_offset, val_scale=KPH_TO_MPH_SCALE, min_val=0, max_val=140, warn_low=None, warn_high=None, 
                 danger_low=None, danger_high=None, unit="KPH", label="", maj_ticks = 14, parent=None):
        super().__init__(val_offset, val_scale, min_val, max_val, warn_low, warn_high, danger_low, 
                         danger_high, unit, label, maj_ticks, parent)

class EngineSpeedGauge(NeedleGauge):
    name = "Engine Speed Gauge"

    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        fields = super().get_fields()
        # override defaults
        for f in fields:
            if f.name == "val_offset": f.default = 0
            if f.name == "val_scale": f.default = 0.001
            if f.name == "min_val": f.default = 0
            if f.name == "danger_low": f.default = None
            if f.name == "warn_low": f.default = None
            if f.name == "warn_high": f.default = None
            if f.name == "danger_high": f.default = 5
            if f.name == "max_val": f.default = 8
            if f.name == "unit": f.default = "RPM"
            if f.name == "label":   f.default = "x1000"
            if f.name == "maj_ticks": f.default = 8
        return fields

    def __init__(self, val_offset=0, val_scale=0.001, min_val=0, max_val=8, warn_low=None, warn_high=None, 
                 danger_low=None, danger_high=5, unit="RPM", label="x1000", maj_ticks = 8, parent=None):
        super().__init__(val_offset, val_scale, min_val, max_val, warn_low, warn_high, danger_low, 
                         danger_high, unit, label, maj_ticks, parent)