import pytest

from adaskit.program.artifacts import derive_asil, load_hazards, load_interfaces, load_requirements


def test_asil_table_matches_iso26262():
    assert derive_asil("S3", "E4", "C3") == "ASIL-D"
    assert derive_asil("S3", "E4", "C2") == "ASIL-C"
    assert derive_asil("S1", "E1", "C1") == "QM"
    with pytest.raises(ValueError):
        derive_asil("S9", "E1", "C1")


def test_every_hazard_derives_an_asil_and_names_a_goal():
    for hazard in load_hazards():
        assert hazard["derived_asil"].startswith(("QM", "ASIL"))
        assert hazard["goal_id"]
        assert hazard["mitigates"], f"{hazard['id']} mitigated by no requirement"


def test_hazard_mitigations_point_at_real_requirements():
    ids = {r["id"] for r in load_requirements()}
    for hazard in load_hazards():
        for requirement in hazard["mitigates"]:
            assert requirement in ids, f"{hazard['id']} references unknown {requirement}"


def test_interfaces_define_timeout_behaviour():
    for interface in load_interfaces():
        assert interface["timeout_ms"] > interface["period_ms"]
        assert interface["on_timeout"], f"{interface['id']} has no failure behaviour"
        assert interface["owner"] in {"OEM", "Supplier"}
