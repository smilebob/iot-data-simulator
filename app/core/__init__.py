"""
Core simulation engine, physical signal generators, and equipment models.

This package encapsulates the foundational execution layer of the simulator:
- `engine`: Real-time asynchronous 3-pass causal simulation loop.
- `generators`: Deterministic and stochastic waveform generators.
- `physics`: Safe AST mathematical formula evaluator for derived metrics.
- `replay`: Historical CSV dataset replayer with linear interpolation.
- `equipment_catalog`: Domain catalog covering 32 industrial equipment presets.
- `dashboard_generator`: Automated generation of ThingsBoard SCADA dashboards.
- `scada_synoptics`: ISA-101 vector SVG process mimics.
- `security`: JWT tokens and password hashing primitives.
- `logger`: In-memory ring-buffer logging and WebSocket broadcaster.
"""

from app.core.engine import SimulationEngine
from app.core.generators import MathSignalGenerator
from app.core.replay import ReplayEngine

__all__ = ["SimulationEngine", "MathSignalGenerator", "ReplayEngine"]

