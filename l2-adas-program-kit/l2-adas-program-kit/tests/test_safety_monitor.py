from adaskit.features.safety_monitor import SafetyMonitor, SystemMode


def _step(monitor, **kw):
    args = {"dt": 0.02, "ego_speed": 28.0, "lane_signal_age_ms": 10.0, "lane_valid": True,
            "hands_on": True, "accel_cmd": 0.0, "steer_rate_cmd": 0.0}
    args.update(kw)
    return monitor.step(**args)


def test_authority_limits_are_enforced():
    out = _step(SafetyMonitor(), accel_cmd=9.0, steer_rate_cmd=9.0)
    assert out.accel_cmd == 2.0
    assert out.steer_rate_cmd == 0.35
    out = _step(SafetyMonitor(), accel_cmd=-9.0, steer_rate_cmd=-9.0)
    assert out.accel_cmd == -3.5
    assert out.steer_rate_cmd == -0.35


def test_lane_loss_degrades_lateral_only():
    out = _step(SafetyMonitor(), lane_valid=False, lane_signal_age_ms=400.0, steer_rate_cmd=0.2)
    assert out.mode is SystemMode.LATERAL_DEGRADED
    assert out.steer_rate_cmd == 0.0
    assert out.takeover_request


def test_odd_violation_latches_disengage():
    monitor = SafetyMonitor()
    _step(monitor, ego_speed=5.0)
    out = _step(monitor, ego_speed=28.0)  # back inside the ODD
    assert out.mode is SystemMode.DISENGAGED, "disengage must latch, not flicker back"


def test_hands_off_escalation_order():
    monitor = SafetyMonitor()
    for _ in range(int(16.0 / 0.02)):
        out = _step(monitor, hands_on=False)
    assert out.mode is SystemMode.TAKEOVER_REQUESTED
    for _ in range(int(10.0 / 0.02)):
        out = _step(monitor, hands_on=False)
    assert out.mode is SystemMode.DISENGAGED


def test_hands_back_on_resets_timer():
    monitor = SafetyMonitor()
    for _ in range(int(10.0 / 0.02)):
        _step(monitor, hands_on=False)
    out = _step(monitor, hands_on=True)
    assert monitor.hands_off_s == 0.0
    assert out.mode is SystemMode.ACTIVE
