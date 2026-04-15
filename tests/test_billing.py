"""Billing: invoices, GST, payments, parking sessions (isolated in-memory DB)."""
import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloud.api.billing_service import BillingService
from cloud.api.telemetry import Base, Ticket


@pytest.fixture
def billing_svc():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return BillingService(Session)


def test_invoice_from_tickets_and_payment_marks_ticket_paid(billing_svc):
    s = billing_svc.Session()
    t = Ticket(vehicle_id="VEH-ABC", violation_type="OVERSTAY", amount=500.0, status="UNPAID")
    s.add(t)
    s.commit()
    tid = t.id
    s.close()

    inv = billing_svc.create_invoice_from_tickets([tid])
    assert inv["status"] == "OPEN"
    assert inv["lines"][0]["ticket_id"] == tid
    assert inv["subtotal"] == 500.0
    assert inv["cgst_amount"] == pytest.approx(45.0)
    assert inv["sgst_amount"] == pytest.approx(45.0)
    assert inv["total"] == pytest.approx(590.0)

    out = billing_svc.record_payment(inv["id"], inv["total"], method="UPI", reference="UTR123")
    assert out["invoice"]["status"] == "PAID"
    assert out["invoice"]["balance"] == 0.0

    s2 = billing_svc.Session()
    t2 = s2.query(Ticket).filter(Ticket.id == tid).first()
    assert t2.status == "PAID"
    s2.close()


def test_partial_payment(billing_svc):
    s = billing_svc.Session()
    t = Ticket(vehicle_id="VEH-X", violation_type="ZONE", amount=1000.0, status="UNPAID")
    s.add(t)
    s.commit()
    tid = t.id
    s.close()
    inv = billing_svc.create_invoice_from_tickets([tid])
    billing_svc.record_payment(inv["id"], 500.0, method="CARD")
    inv2 = billing_svc.get_invoice_by_id(inv["id"])
    assert inv2["status"] == "PARTIALLY_PAID"
    billing_svc.record_payment(inv["id"], inv2["balance"], method="CARD")
    inv3 = billing_svc.get_invoice_by_id(inv["id"])
    assert inv3["status"] == "PAID"


def test_parking_session_invoice(billing_svc):
    ps = billing_svc.start_parking_session("VEH-P1", slot_id=3, hourly_rate=120.0)
    sid = ps["id"]
    end = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    inv = billing_svc.close_parking_session_and_invoice(sid, ended_at=end)
    assert inv["status"] == "OPEN"
    assert any(l["line_type"] == "PARKING" for l in inv["lines"])
    assert inv["total"] > 0


def test_void_invoice_without_payments(billing_svc):
    s = billing_svc.Session()
    t = Ticket(vehicle_id="VEH-Z", violation_type="X", amount=50.0, status="UNPAID")
    s.add(t)
    s.commit()
    tid = t.id
    s.close()
    inv = billing_svc.create_invoice_from_tickets([tid])
    voided = billing_svc.void_invoice(inv["id"])
    assert voided["status"] == "VOID"


def test_billing_summary_keys(billing_svc):
    bs = billing_svc.billing_summary()
    assert "payments_completed_total" in bs
    assert "accounts_receivable_open" in bs
    assert "invoice_counts" in bs
