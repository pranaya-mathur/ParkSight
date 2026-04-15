"""RevenueService: occupancy surge, EV discount, VIP premium."""
import pytest

from cloud.api.revenue_service import RevenueService


def test_standard_below_surge():
    rs = RevenueService(base_rate=100.0)
    out = rs.calculate_current_rate(50.0, "STANDARD")
    assert out["final_rate"] == 100.0
    assert out["is_surge"] is False
    assert out["currency"] == "INR"


def test_surge_at_eighty_percent():
    rs = RevenueService(base_rate=100.0)
    out = rs.calculate_current_rate(80.0, "STANDARD")
    assert out["is_surge"] is True
    assert out["final_rate"] == 150.0


def test_ev_discount_applied_after_surge():
    rs = RevenueService(base_rate=100.0)
    out = rs.calculate_current_rate(85.0, "EV")
    # 100 * 1.5 surge = 150, then * 0.8 for EV = 120
    assert out["final_rate"] == 120.0
    assert out["vehicle_type"] == "EV"


def test_vip_premium_no_surge():
    rs = RevenueService(base_rate=100.0)
    out = rs.calculate_current_rate(40.0, "VIP")
    assert out["is_surge"] is False
    assert out["final_rate"] == 120.0  # 100 * 1.2


@pytest.mark.parametrize("path", ["/revenue/summary", "/revenue/tickets"])
def test_revenue_http_routes_exist(path):
    from fastapi.testclient import TestClient
    from cloud.api.main import app

    r = TestClient(app).get(path)
    assert r.status_code == 200
    if path == "/revenue/summary":
        j = r.json()
        for k in ("billing_payments_total", "billing_ar_open", "billing_invoice_paid_total", "billing_invoice_counts"):
            assert k in j


@pytest.mark.parametrize(
    "path",
    ["/billing/summary", "/billing/invoices", "/billing/sessions"],
)
def test_billing_http_routes_exist(path):
    from fastapi.testclient import TestClient
    from cloud.api.main import app

    assert TestClient(app).get(path).status_code == 200
