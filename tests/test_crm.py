"""Phase 1 tests: customer CRM, dedupe, consent, followups, handoffs."""

from sqlalchemy import select

from km_car_deals.models.customer import (
    Customer,
    CustomerConsent,
    CustomerFollowup,
    HumanHandoffTask,
)
from km_car_deals.models.enums import ConsentStatus, FollowupStatus, HumanHandoffStatus
from km_car_deals.services import crm


def test_normalize_phone():
    assert crm.normalize_phone("9876543210") == "919876543210"
    assert crm.normalize_phone("+91 98765 43210") == "919876543210"
    assert crm.normalize_phone("09876543210") == "919876543210"


def test_get_or_create_dedupes(db):
    c1, created1 = crm.get_or_create_customer(db, whatsapp="9876543210", name="Rahul")
    c2, created2 = crm.get_or_create_customer(db, whatsapp="+91 98765 43210", name="Rahul")
    assert created1 is True and created2 is False
    assert c1.customer_id == c2.customer_id
    assert c2.whatsapp_number == "919876543210"


def test_dedupe_on_different_channels(db):
    c1, _ = crm.get_or_create_customer(db, email="a@x.com", name="A")
    # new customer, different email
    c2, created = crm.get_or_create_customer(db, email="b@x.com", phone="9811111111")
    assert created is True
    assert c1.customer_id != c2.customer_id


def test_opt_in_and_out(db):
    c, _ = crm.get_or_create_customer(db, whatsapp="9111111111")
    crm.mark_opt_in(db, c.customer_id)
    db.refresh(c)
    assert c.consent_status == ConsentStatus.OPTED_IN.value
    assert c.opt_in is True

    crm.mark_opt_out(db, c.customer_id, reason="no interest", source_message="STOP")
    db.refresh(c)
    assert c.opt_out is True
    assert c.consent_status == ConsentStatus.OPTED_OUT.value
    consents = db.execute(select(CustomerConsent)).scalars().all()
    assert any(con.status == ConsentStatus.OPTED_OUT.value for con in consents)


def test_followup_and_handoff(db):
    c, _ = crm.get_or_create_customer(db, whatsapp="9111111111")
    fu = crm.create_followup(db, c.customer_id, reason="test drive follow up")
    assert fu.status == FollowupStatus.PENDING.value

    handoff = crm.create_handoff(db, reason="needs human", summary="complex", customer_id=c.customer_id)
    assert handoff.status == HumanHandoffStatus.OPEN.value


def test_add_interaction_stores_metadata(db):
    c, _ = crm.get_or_create_customer(db, whatsapp="9111111111")
    inter = crm.add_interaction(
        db, c.customer_id, "NOTE", summary="called customer",
        interaction_metadata={"campaign": "diwali"},
    )
    db.refresh(inter)
    assert inter.interaction_metadata == {"campaign": "diwali"}