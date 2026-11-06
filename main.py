"""Patient Vitals API: routes, request models, and validation handling."""

from datetime import datetime, timezone

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr, field_validator

from database import create_table, get_patient_summary, get_patient_vitals, save_vitals

app = FastAPI(
    title="Patient Vitals API",
    description="A small REST API for storing and retrieving fictional patient vital records.",
    version="1.0.0",
)

# Create the table when the application starts/imports.
create_table()


class BloodPressure(BaseModel):
    """Blood pressure measurements in mmHg."""

    model_config = ConfigDict(extra="forbid")
    systolic: StrictInt = Field(ge=50, le=300, description="Systolic pressure (50–300 mmHg)")
    diastolic: StrictInt = Field(ge=30, le=200, description="Diastolic pressure (30–200 mmHg)")


class PatientVitals(BaseModel):
    """Validated patient vital-sign submission."""

    model_config = ConfigDict(extra="forbid")
    patient_id: StrictStr = Field(min_length=1, max_length=100)
    age: StrictInt = Field(ge=0, le=120)
    blood_pressure: BloodPressure
    glucose_level: StrictInt | StrictFloat = Field(gt=0)

    @field_validator("patient_id")
    @classmethod
    def validate_patient_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("patient_id cannot be empty")
        return value


@app.get("/health", tags=["Health"])
def health_check():
    """Return service status and the current UTC timestamp."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/vitals", tags=["Vitals"])
def add_vitals(vitals: PatientVitals):
    """Validate and store one set of patient vitals."""
    save_vitals(vitals)
    return {"message": "Vitals saved successfully"}


@app.get("/patients/{patient_id}/vitals", tags=["Patients"])
def patient_history(
    patient_id: str,
    limit: int | None = Query(default=None, gt=0, description="Maximum number of records to return"),
):
    """Return a patient's records, newest first."""
    records = get_patient_vitals(patient_id)
    return records[:limit] if limit is not None else records


@app.get("/patients/{patient_id}/summary", tags=["Patients"])
def patient_summary(patient_id: str):
    """Return average measurements and the number of recorded entries."""
    return get_patient_summary(patient_id)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return compact validation details with HTTP 400 (project convention)."""
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": errors})
