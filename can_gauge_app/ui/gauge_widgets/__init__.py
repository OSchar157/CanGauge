from .gauge import Gauge
from .simple_gauge import SimpleGauge
from .bar_gauge import BarGauge
from .arc_gauge import ArcGauge

from .presets import Speedometer, EngineSpeedGauge

GAUGE_TYPES: dict[str, Gauge] = {
    SimpleGauge.name:       SimpleGauge,
    BarGauge.name:          BarGauge,
    ArcGauge.name:          ArcGauge,
    Speedometer.name:       Speedometer,
    EngineSpeedGauge.name:  EngineSpeedGauge
}