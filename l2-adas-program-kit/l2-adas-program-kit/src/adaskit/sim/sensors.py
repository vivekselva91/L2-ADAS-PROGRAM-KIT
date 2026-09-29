"""Sensor models with the failure modes that actually drive ADAS requirements.

Real integration problems are rarely "the algorithm is wrong". They are latency,
dropout, and noise. Each model here can inject all three, which is what makes
the degradation requirements (SYS-REQ-005, SYS-REQ-010) testable.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field


@dataclass
class SensorSignal:
    value: float | None
    age_ms: float
    valid: bool


@dataclass
class ModeledSensor:
    """Applies transport latency, gaussian noise and dropout windows."""

    name: str
    period_ms: float
    latency_ms: float
    noise_sigma: float = 0.0
    timeout_ms: float = 200.0
    dropout_windows: list[tuple[float, float]] = field(default_factory=list)
    seed: int = 7
    _buffer: deque = field(default_factory=deque, init=False)
    _rng: random.Random = field(init=False)
    _last_good_t: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def sample(self, t: float, truth: float) -> SensorSignal:
        dropped = any(lo <= t < hi for lo, hi in self.dropout_windows)
        if not dropped:
            measured = truth + self._rng.gauss(0.0, self.noise_sigma)
            self._buffer.append((t + self.latency_ms / 1000.0, measured))

        value = None
        while self._buffer and self._buffer[0][0] <= t:
            _, value = self._buffer.popleft()

        if value is not None:
            self._last_good_t = t
            return SensorSignal(value, self.latency_ms, True)

        age_ms = (t - self._last_good_t) * 1000.0
        return SensorSignal(None, age_ms, age_ms <= self.timeout_ms)
