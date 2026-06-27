from .gauge import Gauge
from .simple_gauge import SimpleGauge
from .bar_gauge import BarGauge

from .presets import Speedometer, EngineSpeedGauge

GAUGE_TYPES: dict[str, Gauge] = {
    SimpleGauge.name:       SimpleGauge,
    BarGauge.name:          BarGauge,
    Speedometer.name:       Speedometer,
    EngineSpeedGauge.name:  EngineSpeedGauge
}