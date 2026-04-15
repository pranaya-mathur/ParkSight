"""Accounts receivable: invoices, GST, payments, parking sessions."""
from __future__ import annotations

import datetime
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .revenue_service import RevenueService
from .telemetry import Invoice, InvoiceLine, ParkingSession, Payment, Ticket

GST_CGST_RATE = 0.09
GST_SGST_RATE = 0.09


class BillingService:
    def __init__(self, session_factory):
        self.Session = session_factory

    def _next_invoice_number(self, session: Session) -> str:
        n = session.query(func.count(Invoice.id)).scalar() or 0
        day = datetime.datetime.utcnow().strftime("%Y%m%d")
        return f"INV-{day}-{(n + 1):05d}"

    def _apply_gst(self, subtotal: float) -> tuple:
        cgst = round(subtotal * GST_CGST_RATE, 2)
        sgst = round(subtotal * GST_SGST_RATE, 2)
        total = round(subtotal + cgst + sgst, 2)
        return cgst, sgst, total

    def _recalculate_invoice_totals(self, session: Session, inv: Invoice) -> None:
        lines = session.query(InvoiceLine).filter(InvoiceLine.invoice_id == inv.id).all()
        subtotal = round(sum(l.amount for l in lines), 2)
        cgst, sgst, total = self._apply_gst(subtotal)
        inv.subtotal = subtotal
        inv.cgst_amount = cgst
        inv.sgst_amount = sgst
        inv.total = total

    def create_invoice_from_tickets(
        self,
        ticket_ids: List[int],
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not ticket_ids:
            raise ValueError("ticket_ids required")
        session = self.Session()
        try:
            tickets = (
                session.query(Ticket)
                .filter(Ticket.id.in_(ticket_ids), Ticket.status == "UNPAID")
                .all()
            )
            if len(tickets) != len(ticket_ids):
                raise ValueError("Some tickets are missing or already paid")
            vehicle_ids = {t.vehicle_id for t in tickets}
            if len(vehicle_ids) != 1:
                raise ValueError("All tickets on one invoice must share the same vehicle_id")
            vehicle_id = tickets[0].vehicle_id

            inv = Invoice(
                number=self._next_invoice_number(session),
                vehicle_id=vehicle_id,
                status="OPEN",
                due_date=datetime.datetime.utcnow() + datetime.timedelta(days=7),
                notes=notes,
            )
            session.add(inv)
            session.flush()

            for t in tickets:
                line = InvoiceLine(
                    invoice_id=inv.id,
                    description=f"Violation: {t.violation_type} (Ticket #{t.id})",
                    line_type="VIOLATION",
                    quantity=1.0,
                    unit_price=t.amount,
                    amount=t.amount,
                    ticket_id=t.id,
                )
                session.add(line)

            self._recalculate_invoice_totals(session, inv)
            session.commit()
            inv_id = inv.id
        finally:
            session.close()
        return self.get_invoice_by_id(inv_id)

    def create_manual_invoice(
        self,
        vehicle_id: str,
        lines: List[Dict[str, Any]],
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        session = self.Session()
        try:
            inv = Invoice(
                number=self._next_invoice_number(session),
                vehicle_id=vehicle_id,
                status="OPEN",
                due_date=datetime.datetime.utcnow() + datetime.timedelta(days=7),
                notes=notes,
            )
            session.add(inv)
            session.flush()
            for row in lines:
                amt = round(float(row["quantity"]) * float(row["unit_price"]), 2)
                session.add(
                    InvoiceLine(
                        invoice_id=inv.id,
                        description=row["description"],
                        line_type=row.get("line_type", "OTHER"),
                        quantity=float(row["quantity"]),
                        unit_price=float(row["unit_price"]),
                        amount=amt,
                    )
                )
            self._recalculate_invoice_totals(session, inv)
            session.commit()
            inv_id = inv.id
        finally:
            session.close()
        return self.get_invoice_by_id(inv_id)

    def start_parking_session(
        self,
        vehicle_id: str,
        slot_id: int,
        hourly_rate: Optional[float] = None,
        vehicle_type: str = "STANDARD",
        occupancy_percent: float = 0.0,
    ) -> Dict[str, Any]:
        rs = RevenueService()
        rate_info = rs.calculate_current_rate(occupancy_percent, vehicle_type)
        rate = hourly_rate if hourly_rate is not None else float(rate_info["final_rate"])
        session = self.Session()
        try:
            ps = ParkingSession(
                vehicle_id=vehicle_id,
                slot_id=slot_id,
                hourly_rate=rate,
                vehicle_type=vehicle_type,
                status="ACTIVE",
            )
            session.add(ps)
            session.commit()
            session.refresh(ps)
            return self._parking_session_to_dict(ps)
        finally:
            session.close()

    def close_parking_session_and_invoice(
        self,
        session_id: int,
        ended_at: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        end = ended_at or datetime.datetime.utcnow()
        session = self.Session()
        try:
            ps = session.query(ParkingSession).filter(ParkingSession.id == session_id).first()
            if not ps:
                raise ValueError("Parking session not found")
            if ps.status != "ACTIVE":
                raise ValueError("Session is not active")
            if end < ps.started_at:
                raise ValueError("ended_at before started_at")

            ps.ended_at = end
            hours = (end - ps.started_at).total_seconds() / 3600.0
            hours = max(hours, 1.0 / 60.0)  # minimum 1 minute billable
            sub = round(hours * ps.hourly_rate, 2)

            inv = Invoice(
                number=self._next_invoice_number(session),
                vehicle_id=ps.vehicle_id,
                status="OPEN",
                due_date=end + datetime.timedelta(days=7),
                notes=f"Parking slot {ps.slot_id}, session #{ps.id}",
            )
            session.add(inv)
            session.flush()

            session.add(
                InvoiceLine(
                    invoice_id=inv.id,
                    description=f"Parking {hours:.2f} h @ ₹{ps.hourly_rate}/h (slot {ps.slot_id})",
                    line_type="PARKING",
                    quantity=round(hours, 4),
                    unit_price=ps.hourly_rate,
                    amount=sub,
                    parking_session_id=ps.id,
                )
            )
            self._recalculate_invoice_totals(session, inv)
            ps.invoice_id = inv.id
            ps.status = "BILLED"
            session.commit()
            inv_id = inv.id
        finally:
            session.close()
        return self.get_invoice_by_id(inv_id)

    def record_payment(
        self,
        invoice_id: int,
        amount: float,
        method: str = "UPI",
        reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("amount must be positive")
        session = self.Session()
        try:
            inv = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not inv or inv.status == "VOID":
                raise ValueError("Invoice not found or voided")
            remaining = round(inv.total - inv.amount_paid, 2)
            if remaining <= 0:
                raise ValueError("Invoice already fully paid")

            pay_amt = round(min(amount, remaining), 2)
            pay = Payment(
                invoice_id=inv.id,
                amount=pay_amt,
                method=method,
                reference=reference,
                status="COMPLETED",
            )
            session.add(pay)
            session.flush()
            pay_dict = self._payment_to_dict(pay)
            inv.amount_paid = round(inv.amount_paid + pay_amt, 2)

            if inv.amount_paid + 0.005 >= inv.total:
                inv.status = "PAID"
                self._sync_tickets_paid_for_invoice(session, inv)
            else:
                inv.status = "PARTIALLY_PAID"

            session.commit()
            inv_id = inv.id
        finally:
            session.close()
        return {"invoice": self.get_invoice_by_id(inv_id), "payment": pay_dict}

    def _sync_tickets_paid_for_invoice(self, session: Session, inv: Invoice) -> None:
        lines = session.query(InvoiceLine).filter(InvoiceLine.invoice_id == inv.id).all()
        for line in lines:
            if line.ticket_id:
                t = session.query(Ticket).filter(Ticket.id == line.ticket_id).first()
                if t:
                    t.status = "PAID"

    def void_invoice(self, invoice_id: int) -> Dict[str, Any]:
        session = self.Session()
        try:
            inv = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not inv:
                raise ValueError("Invoice not found")
            paid = (
                session.query(func.sum(Payment.amount))
                .filter(Payment.invoice_id == inv.id, Payment.status == "COMPLETED")
                .scalar()
            )
            if paid and float(paid) > 0:
                raise ValueError("Cannot void invoice with payments")
            inv.status = "VOID"
            session.commit()
            inv_id = inv.id
        finally:
            session.close()
        return self.get_invoice_by_id(inv_id)

    def list_invoices(
        self,
        status: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        session = self.Session()
        try:
            q = session.query(Invoice).order_by(Invoice.issue_date.desc())
            if status:
                q = q.filter(Invoice.status == status)
            if vehicle_id:
                q = q.filter(Invoice.vehicle_id == vehicle_id)
            return [self._invoice_summary_dict(i) for i in q.limit(limit).all()]
        finally:
            session.close()

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        session = self.Session()
        try:
            rows = (
                session.query(ParkingSession)
                .filter(ParkingSession.status == "ACTIVE")
                .order_by(ParkingSession.started_at.desc())
                .all()
            )
            return [self._parking_session_to_dict(r) for r in rows]
        finally:
            session.close()

    def billing_summary(self) -> Dict[str, Any]:
        session = self.Session()
        try:
            paid_inv = (
                session.query(func.sum(Invoice.total))
                .filter(Invoice.status == "PAID")
                .scalar()
            )
            payments_total = (
                session.query(func.sum(Payment.amount))
                .filter(Payment.status == "COMPLETED")
                .scalar()
            )
            open_rows = (
                session.query(Invoice)
                .filter(Invoice.status.in_(["OPEN", "PARTIALLY_PAID"]))
                .all()
            )
            open_total = sum(max(0.0, float(r.total) - float(r.amount_paid)) for r in open_rows)
            inv_counts = {
                "open": session.query(Invoice).filter(Invoice.status == "OPEN").count(),
                "partial": session.query(Invoice).filter(Invoice.status == "PARTIALLY_PAID").count(),
                "paid": session.query(Invoice).filter(Invoice.status == "PAID").count(),
            }
            return {
                "currency": "INR",
                "invoice_paid_total": float(paid_inv or 0),
                "payments_completed_total": float(payments_total or 0),
                "accounts_receivable_open": float(open_total or 0),
                "invoice_counts": inv_counts,
                "gst_cgst_rate": GST_CGST_RATE,
                "gst_sgst_rate": GST_SGST_RATE,
            }
        finally:
            session.close()

    def _serialize_invoice(self, session: Session, invoice_id: int) -> Dict[str, Any]:
        inv = session.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not inv:
            raise ValueError("Invoice not found")
        lines = session.query(InvoiceLine).filter(InvoiceLine.invoice_id == inv.id).all()
        pays = session.query(Payment).filter(Payment.invoice_id == inv.id).order_by(Payment.created_at).all()
        return {
            "id": inv.id,
            "number": inv.number,
            "vehicle_id": inv.vehicle_id,
            "status": inv.status,
            "currency": inv.currency,
            "subtotal": inv.subtotal,
            "cgst_amount": inv.cgst_amount,
            "sgst_amount": inv.sgst_amount,
            "total": inv.total,
            "amount_paid": inv.amount_paid,
            "balance": round(inv.total - inv.amount_paid, 2),
            "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "notes": inv.notes,
            "lines": [self._line_to_dict(l) for l in lines],
            "payments": [self._payment_to_dict(p) for p in pays],
        }

    def get_invoice_by_id(self, invoice_id: int) -> Dict[str, Any]:
        session = self.Session()
        try:
            return self._serialize_invoice(session, invoice_id)
        finally:
            session.close()

    def _invoice_summary_dict(self, inv: Invoice) -> Dict[str, Any]:
        return {
            "id": inv.id,
            "number": inv.number,
            "vehicle_id": inv.vehicle_id,
            "status": inv.status,
            "total": inv.total,
            "amount_paid": inv.amount_paid,
            "balance": round(inv.total - inv.amount_paid, 2),
            "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
        }

    def _line_to_dict(self, line: InvoiceLine) -> Dict[str, Any]:
        return {
            "id": line.id,
            "description": line.description,
            "line_type": line.line_type,
            "quantity": line.quantity,
            "unit_price": line.unit_price,
            "amount": line.amount,
            "ticket_id": line.ticket_id,
            "parking_session_id": line.parking_session_id,
        }

    def _payment_to_dict(self, p: Payment) -> Dict[str, Any]:
        return {
            "id": p.id,
            "amount": p.amount,
            "method": p.method,
            "reference": p.reference,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }

    def _parking_session_to_dict(self, ps: ParkingSession) -> Dict[str, Any]:
        return {
            "id": ps.id,
            "vehicle_id": ps.vehicle_id,
            "slot_id": ps.slot_id,
            "started_at": ps.started_at.isoformat() if ps.started_at else None,
            "ended_at": ps.ended_at.isoformat() if ps.ended_at else None,
            "hourly_rate": ps.hourly_rate,
            "vehicle_type": ps.vehicle_type,
            "status": ps.status,
            "invoice_id": ps.invoice_id,
        }
