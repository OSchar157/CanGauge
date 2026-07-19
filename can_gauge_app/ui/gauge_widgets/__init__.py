from .gauge import Gauge
from .needle_gauge import NeedleGauge
from .bar_gauge import BarGauge
from .arc_gauge import ArcGauge

from .presets import Speedometer, EngineSpeedGauge

GAUGE_TYPES: dict[str, Gauge] = {
    NeedleGauge.name:       NeedleGauge,
    BarGauge.name:          BarGauge,
    ArcGauge.name:          ArcGauge,
    Speedometer.name:       Speedometer,
    EngineSpeedGauge.name:  EngineSpeedGauge
}