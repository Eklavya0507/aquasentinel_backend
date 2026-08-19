from datetime import date, time
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    status: str


class RegisterUserIn(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8)


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


class DoctorScheduleCreate(BaseModel):
    hospital_id: int
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    valid_from: date | None = None
    valid_until: date | None = None


class HospitalCreate(BaseModel):
    name: str
    hospital_type: str | None = None
    address: str | None = None
    state: str
    district: str
    locality: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    email: EmailStr | None = None
    emergency_available: bool = False


class HospitalHourIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    open_time: time | None = None
    close_time: time | None = None
    is_closed: bool = False


class HospitalExceptionIn(BaseModel):
    exception_date: date
    exception_type: str
    reason: str | None = None
    open_time: time | None = None
    close_time: time | None = None


class HospitalSpecialistIn(BaseModel):
    specialization: str
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None


class DoctorReviewCreate(BaseModel):
    overall_rating: int = Field(ge=1, le=5)
    communication_rating: int | None = Field(default=None, ge=1, le=5)
    language_rating: int | None = Field(default=None, ge=1, le=5)
    professional_rating: int | None = Field(default=None, ge=1, le=5)
    availability_accurate: bool | None = None
    preferred_language_met: Literal["YES", "PARTIALLY", "NO"] | None = None
    language_used: str | None = None
    comment: str | None = Field(default=None, max_length=3000)


class CaseCreate(BaseModel):
    disease: str
    case_date: date
    state: str
    district: str
    hospital_id: int | None = None
    confirmed_cases: int = Field(default=0, ge=0)
    suspected_cases: int = Field(default=0, ge=0)
    recovered_cases: int | None = Field(default=None, ge=0)
    deaths: int | None = Field(default=None, ge=0)
    source_type: str = "MANUAL"
    notes: str | None = None


class CommunityReportCreate(BaseModel):
    profile_id: int | None = None
    concern_type: str
    summary: str = Field(max_length=255)
    description: str
    state: str
    district: str
    locality: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    people_affected: int | None = Field(default=None, ge=0)
    urgency: str | None = None


class CommunityReportReview(BaseModel):
    status: Literal["UNDER_REVIEW", "VERIFIED", "REJECTED"]
    review_notes: str | None = None


class AlertCreate(BaseModel):
    state: str
    district: str | None = None
    disease: str | None = None
    severity: Literal["NORMAL", "SEASONAL", "WATCH", "HIGH", "CRITICAL"]
    title: str
    reason: str
    current_cases: int | None = None
    expected_min: int | None = None
    expected_max: int | None = None


class ModelAPredictIn(BaseModel):
    profile_id: int
    symptoms: dict[str, Any]
    extra_inputs: dict[str, Any] = {}


class ModelBPredictIn(BaseModel):
    profile_id: int
    regional_inputs: dict[str, Any] = {}
    extra_inputs: dict[str, Any] = {}


class RecommendationQuery(BaseModel):
    profile_id: int
    specialization: str | None = None
    preferred_language: str | None = None
    max_distance_km: float | None = Field(default=50, ge=1, le=500)
