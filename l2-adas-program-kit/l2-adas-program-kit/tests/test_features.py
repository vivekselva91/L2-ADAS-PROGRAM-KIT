from adaskit.features.acc import ACCController
from adaskit.features.lka import LKAController


def test_acc_degrades_to_speed_control_without_radar():
    acc = ACCController(set_speed=30.0)
    cmd = acc.step(ego_speed=25.0, gap_m=None, rel_speed=None)
    assert cmd > 0, "should accelerate toward set speed when blind"


def test_acc_brakes_when_gap_closes():
    acc = ACCController(set_speed=30.0)
    cmd = acc.step(ego_speed=28.0, gap_m=20.0, rel_speed=-8.0)
    assert cmd < -1.0


def test_acc_command_is_bounded():
    acc = ACCController(set_speed=300.0)
    assert acc.step(10.0, None, None) == 2.0
    assert acc.step(10.0, 1.0, -50.0) == -3.5


def test_lka_returns_zero_when_blind():
    lka = LKAController()
    assert lka.step(28.0, None, None, 0.0) == 0.0
    assert lka.step(28.0, 0.5, None, 0.0) == 0.0


def test_lka_steers_back_toward_center():
    lka = LKAController()
    left_of_center = lka.step(28.0, lane_offset=0.5, heading_error=0.0, current_steer=0.0)
    right_of_center = lka.step(28.0, lane_offset=-0.5, heading_error=0.0, current_steer=0.0)
    assert left_of_center < 0 < right_of_center


def test_lka_rate_is_bounded():
    lka = LKAController()
    assert abs(lka.step(28.0, 50.0, 3.0, -0.4)) <= 0.35
