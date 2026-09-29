"""Lane keeping assist: Stanley-style lateral control with a rate limit."""

from __future__ import annotations

import math
from dataclasses import dataclass

STEER_RATE_LIMIT = 0.35  # rad/s, SYS-REQ-008


@dataclass
class LKAController:
    """Gains chosen by sweep against SCN-004 (300 m curve at 28 m/s).

    A high cross-track gain fights the heading term at highway speed and the
    loop goes unstable: an early sweep at k_cross_track=2.6 diverged to 885 m.
    The tuned set holds 0.09 m of lateral deviation with a peak steering rate of
    0.22 rad/s, leaving margin under the 0.35 rad/s driver-override limit.
    """

    k_cross_track: float = 0.20
    k_heading: float = 1.20
    k_steer: float = 3.00

    def step(
        self,
        speed: float,
        lane_offset: float | None,
        heading_error: float | None,
        current_steer: float,
        curvature: float = 0.0,
    ) -> float:
        """Return a bounded steering-rate command, or zero when blind."""
        if lane_offset is None or heading_error is None:
            return 0.0

        cross_track_term = math.atan2(self.k_cross_track * -lane_offset, max(speed, 1.0))
        feedforward = math.atan(2.8 * curvature)
        target_steer = self.k_heading * heading_error + cross_track_term + feedforward
        rate = self.k_steer * (target_steer - current_steer)
        return max(-STEER_RATE_LIMIT, min(STEER_RATE_LIMIT, rate))
