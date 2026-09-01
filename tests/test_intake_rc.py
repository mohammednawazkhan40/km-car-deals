"""Phase 1 tests: RC rule-based extraction and intake message parsing."""

from km_car_deals.agents.intake_agent import CarIntakeAgent
from km_car_deals.agents.rc_document_agent import RCDocumentAgent, RC_FIELDS
from km_car_deals.schemas.vehicle import VehicleFactIn


def make_rc_text():
    return (
        "S.No: 5012\n"
        "Registration No: MH12AB3456\n"
        "Maker's Name: Hyundai\n"
        "Model/Car: CRETA\n"
        "Variant: SX (O) Diesel\n"
        "Month & Year of Mfg: Feb-2021\n"
        "Date of Registration: 15-Feb-2021\n"
        "Fuel/N.V.T: DIESEL NR\n"
        "Colour: SILVER\n"
        "Seating Capacity: 5\n"
        "Engine No: HU12345\n"
        "Chasis No: MCHNA45GHK1234567\n"
        "Owner Name: Priya Sharma\n"
    )


def test_rc_field_set_expected_fields():
    assert "registration_number" in RC_FIELDS
    assert "engine_number" in RC_FIELDS
    assert "chassis_number" in RC_FIELDS


def test_rc_rule_extraction(db):
    agent = RCDocumentAgent(db)
    facts = agent._rule_extract(make_rc_text())
    assert facts["registration_number"] == "MH12AB3456"
    assert "Hyundai" in facts["manufacturer"]
    assert "DIESEL" in facts["fuel_type"].upper()
    assert "2021" in facts["manufacturing_year"]


def test_rc_merge_builds_facts(db):
    agent = RCDocumentAgent(db)
    rule = agent._rule_extract(make_rc_text())
    merged = agent._merge(make_rc_text(), rule, [])
    assert all(isinstance(f, VehicleFactIn) for f in merged)
    assert all(f.source == "RC" for f in merged)
    # every merged fact must be an allowed RC field
    assert all(f.field in RC_FIELDS for f in merged)
    assert all(f.confidence > 0 for f in merged)


def test_intake_parses_brand_model_year(db):
    intake = CarIntakeAgent(db)
    info = intake.parse_user_message(
        "Hyundai Creta SX Diesel 2022, 22,000 km, 12.5 lakh, single owner"
    )
    assert info.get("manufacturer") == "Hyundai"
    assert info.get("vehicle_model") == "Creta"
    assert info.get("manufacturing_year") == 2022
    assert info.get("fuel_type") == "DIESEL"
    assert int(info.get("selling_price")) == 1250000
    assert info.get("owner_count") == 1


def test_intake_does_not_invent_name(db):
    intake = CarIntakeAgent(db)
    info = intake.parse_user_message("selling my car, 2020 model, 45k km, 5 lakh")
    # no known brand -> no make/model invented
    assert "manufacturer" not in info
    assert "vehicle_model" not in info
    # sensible numeric fields still parsed
    assert info.get("manufacturing_year") == 2020