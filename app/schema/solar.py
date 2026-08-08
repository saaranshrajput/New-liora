from pydantic import BaseModel, Field


class SolarPlanRequest(BaseModel):
    city: str = "Your home"
    daily_kwh: float = Field(gt=0, le=10000)
    system_kw: float = Field(gt=0, le=1000)
    panel_type: str = "550 W Mono PERC"
    inverter: str = "On-grid inverter"
    mounting: str = "RCC rooftop"
    battery: str = "No battery"
    roof_area: float = Field(ge=0, le=1000000)
    daily_generation: str
    monthly_generation: str
    monthly_saving: str
    installed_cost: str
    payback: str
