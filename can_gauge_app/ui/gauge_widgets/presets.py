from ui.gauge_widgets.simple_gauge import SimpleGauge
from ui.gauge_widgets.gauge import ParamSpec

# TODO: This is temporary (famous last words), figure out a way to make presets without classes, too much overhead

class Speedometer(SimpleGauge):
    name = "Speedometer"

    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        fields = super().get_fields()  # get parent fields
        # override defaults
        for f in fields:
            if f.name == "min_val": f.default = 0
            if f.name == "danger_low": f.default = None
            if f.name == "warn_low": f.default = None
            if f.name == "warn_high": f.default = None
            if f.name == "danger_high": f.default = None
            if f.name == "max_val": f.default = 140
            if f.name == "unit": f.default = "KPH"
            if f.name == "label":   f.default = "Speedometer"
        return fields

    def __init__(self, min_val=0, max_val=140, warn_low=None, warn_high=None, 
                 danger_low=None, danger_high=None, unit="KPH", label="", parent=None):
        super().__init__(min_val, max_val, warn_low, warn_high, danger_low, 
                         danger_high, unit, label, parent)

class EngineSpeedGauge(SimpleGauge):
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
        return fields

    def __init__(self, min_val=0, max_val=8000, warn_low=None, warn_high=None, 
                 danger_low=None, danger_high=5000, unit="RPM", label="", parent=None):
        super().__init__(min_val, max_val, warn_low, warn_high, danger_low, 
                         danger_high, unit, label, parent)