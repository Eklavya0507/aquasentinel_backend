from datetime import date
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    status: str
    full_name: str


class RegisterUserIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8, max_length=128)


class RegisterDoctorIn(RegisterUserIn):
    registration_number: str
    specialization: str
    qualification: str | None = None
    years_experience: int | None = Field(default=None, ge=0, le=80)
    languages: list[str] = []


class RegisterGovernmentIn(RegisterUserIn):
    department: str
    designation: str
    organization: str
    employee_id: str
    state: str | None = None
    district: str | None = None
    jurisdiction_level: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ProfileCreate(BaseModel):
    name: str
    relationship: str = "Self"
    date_of_birth: date
    gender: str | None = None
    caregiver_managed: bool = False
    primary_state: str | None = None
    primary_district: str | None = None
    primary_locality: str | None = None
    current_state: str | None = None
    current_district: str | None = None
    current_locality: str | None = None
    current_latitude: float | None = None
    current_longitude: float | None = None
    preferred_languages: list[str] = []


class MedicalHistoryCreate(BaseModel):
    disease_name: str
    diagnosis_year: int | None = Field(default=None, ge=1900, le=2100)
    current_status: str | None = None
    doctor_confirmed: str | None = None
    notes: str | None = None


class CommunityReportCreate(BaseModel):
    concern_type: str = "COMMUNITY_SIGNAL"
    summary: str = Field(min_length=3, max_length=300)
    state: str
    district: str
    locality: str | None = None
    description: str | None = None
    urgency: str | None = None
    water_source: str | None = None
    people_affected: int | None = Field(default=None, ge=0)
    latitude: float | None = None
    longitude: float | None = None
    anonymous: bool = False
    reporter_name: str | None = None
    reporter_phone: str | None = None
    reporter_email: EmailStr | None = None


class CommunityReportReview(BaseModel):
    status: Literal["UNDER_REVIEW", "VERIFIED", "REJECTED"]
    review_notes: str | None = Field(default=None, max_length=1000)


class CaseCreate(BaseModel):
    disease: str
    case_date: date
    state: str
    district: str
    confirmed_cases: int = Field(default=0, ge=0)
    suspected_cases: int = Field(default=0, ge=0)
    notes: str | None = None


class B1EnvironmentalInput(BaseModel):
    state: str
    district: str
    latitude: float
    longitude: float
    is_urban: int = Field(ge=0, le=1)
    population_density: float = Field(ge=0)
    age: int = Field(ge=0, le=120)
    gender: str
    water_source: str
    water_treatment: str
    ph: float
    turbidity_ntu: float = Field(ge=0)
    dissolved_oxygen_mg_l: float = Field(ge=0)
    bod_mg_l: float = Field(ge=0)
    fecal_coliform_per_100ml: float = Field(ge=0)
    total_coliform_per_100ml: float = Field(ge=0)
    tds_mg_l: float = Field(ge=0)
    nitrate_mg_l: float = Field(ge=0)
    fluoride_mg_l: float = Field(ge=0)
    arsenic_ug_l: float = Field(ge=0)
    open_defecation_rate: float = Field(ge=0, le=100)
    toilet_access: int = Field(ge=0, le=1)
    sewage_treatment_pct: float = Field(ge=0, le=100)
    handwashing_practice: str
    month: int = Field(ge=1, le=12)
    season: str
    avg_temperature_c: float
    avg_rainfall_mm: float = Field(ge=0)
    avg_humidity_pct: float = Field(ge=0, le=100)
    flooding: int = Field(ge=0, le=1)
