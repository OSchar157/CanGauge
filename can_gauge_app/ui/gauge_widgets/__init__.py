from .gauge import Gauge
from .needle_gauge import NeedleGauge
from .bar_gauge import BarGauge
from .presets import Speedometer, EngineSpeedGauge

GAUGE_TYPES: dict[str, Gauge] = {
    NeedleGauge.name:       NeedleGauge,
    Speedometer.name:       Speedometer,
    EngineSpeedGauge.name:  EngineSpeedGauge,
    BarGauge.name:          BarGauge,
}