from app.schema.solar import SolarPlanRequest
from app.utils.solar_plan_pdf import create_solar_plan_pdf


def test_solar_plan_details_do_not_overlap_explanation_panel():
    plan = SolarPlanRequest(
        daily_kwh=20.3,
        system_kw=4.5,
        roof_area=300,
        daily_generation="20.3-21.9 kWh",
        monthly_generation="607.5 kWh",
        monthly_saving="Rs 3,969",
        installed_cost="Rs 3,24,000",
        payback="6.8 years",
    )

    pdf = create_solar_plan_pdf(plan)

    last_table_row = b"1 0 0 1 316 389 Tm (Recommended system)"
    explanation_panel = b"0.032 0.125 0.101 rg 42 248 511 100 re f"
    assert last_table_row in pdf
    assert explanation_panel in pdf
    assert pdf.index(last_table_row) < pdf.index(explanation_panel)
