import enum
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now_utc():
    return datetime.utcnow()


class Role(str, enum.Enum):
    USER = "USER"
    DOCTOR = "DOCTOR"
    GOVERNMENT = "GOVERNMENT"
    ADMIN = "ADMIN"


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class CaseStatus(str, enum.Enum):
    PENDING = "PENDING"
    DOCTOR_VERIFIED = "DOCTOR_VERIFIED"
    FULLY_VERIFIED = "FULLY_VERIFIED"
    REJECTED = "REJECTED"


class ReviewStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    VISIBLE = "VISIBLE"
    FLAGGED = "FLAGGED"
    REMOVED = "REMOVED"


class CommunityReportStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class AlertSeverity(str, enum.Enum):
    NORMAL = "NORMAL"
    SEASONAL = "SEASONAL"
    WATCH = "WATCH"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER)
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.APPROVED
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    profiles = relationship("Profile", back_populates="account", cascade="all, delete-orphan")
    doctor_profile = relationship("DoctorProfile", back_populates="account", uselist=False)
    government_profile = relationship("GovernmentOfficial", back_populates="account", uselist=False)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)

    name: Mapped[str] = mapped_column(String(160))
    relationship: Mapped[str] = mapped_column(String(50), default="Self")
    date_of_birth: Mapped[date] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    caregiver_managed: Mapped[bool] = mapped_column(Boolean, default=False)

    primary_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primary_district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    primary_locality: Mapped[str | None] = mapped_column(String(180), nullable=True)

    current_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    current_locality: Mapped[str | None] = mapped_column(String(180), nullable=True)
    current_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    preferred_languages: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)

    account = relationship("Account", back_populates="profiles")
    histories = relationship("MedicalHistory", back_populates="profile", cascade="all, delete-orphan")
    model_a_assessments = relationship("ModelAAssessment", back_populates="profile")
    model_b_snapshots = relationship("ModelBRiskSnapshot", back_populates="profile")


class MedicalHistory(Base):
    __tablename__ = "medical_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), index=True)

    disease_name: Mapped[str] = mapped_column(String(160))
    diagnosis_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    doctor_confirmed: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    profile = relationship("Profile", back_populates="histories")
    documents = relationship("MedicalDocument", back_populates="history", cascade="all, delete-orphan")


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), index=True)
    history_id: Mapped[int | None] = mapped_column(ForeignKey("medical_history.id"), nullable=True)

    document_type: Mapped[str] = mapped_column(String(80))
    original_name: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))

    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    history = relationship("MedicalHistory", back_populates="documents")


class DoctorProfile(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), unique=True)

    registration_number: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    specialization: Mapped[str] = mapped_column(String(160))
    qualification: Mapped[str | None] = mapped_column(String(255), nullable=True)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.PENDING
    )

    account = relationship("Account", back_populates="doctor_profile")
    languages = relationship("DoctorLanguage", back_populates="doctor", cascade="all, delete-orphan")
    schedules = relationship("DoctorSchedule", back_populates="doctor", cascade="all, delete-orphan")
    reviews = relationship("DoctorReview", back_populates="doctor")


class DoctorLanguage(Base):
    __tablename__ = "doctor_languages"
    __table_args__ = (UniqueConstraint("doctor_id", "language_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    language_code: Mapped[str] = mapped_column(String(30))
    proficiency: Mapped[str | None] = mapped_column(String(40), nullable=True)

    doctor = relationship("DoctorProfile", back_populates="languages")


class GovernmentOfficial(Base):
    __tablename__ = "government_officials"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), unique=True)

    department: Mapped[str] = mapped_column(String(160))
    designation: Mapped[str] = mapped_column(String(160))
    organization: Mapped[str] = mapped_column(String(200))
    employee_id: Mapped[str] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    jurisdiction_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.PENDING
    )

    account = relationship("Account", back_populates="government_profile")


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(220), index=True)
    hospital_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(100), index=True)
    district: Mapped[str] = mapped_column(String(120), index=True)
    locality: Mapped[str | None] = mapped_column(String(180), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_available: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    hours = relationship("HospitalHour", back_populates="hospital", cascade="all, delete-orphan")
    exceptions = relationship("HospitalScheduleException", back_populates="hospital", cascade="all, delete-orphan")
    specialists = relationship("HospitalSpecialist", back_populates="hospital", cascade="all, delete-orphan")
    doctor_schedules = relationship("DoctorSchedule", back_populates="hospital")


class HospitalHour(Base):
    __tablename__ = "hospital_hours"
    __table_args__ = (UniqueConstraint("hospital_id", "day_of_week"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))
    day_of_week: Mapped[int] = mapped_column(Integer)  # Monday=0
    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)

    hospital = relationship("Hospital", back_populates="hours")


class HospitalScheduleException(Base):
    __tablename__ = "hospital_schedule_exceptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))
    exception_date: Mapped[date] = mapped_column(Date)
    exception_type: Mapped[str] = mapped_column(String(80))
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    hospital = relationship("Hospital", back_populates="exceptions")


class HospitalSpecialist(Base):
    __tablename__ = "hospital_specialists"

    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))
    specialization: Mapped[str] = mapped_column(String(160))
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    hospital = relationship("Hospital", back_populates="specialists")


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"))

    day_of_week: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    doctor = relationship("DoctorProfile", back_populates="schedules")
    hospital = relationship("Hospital", back_populates="doctor_schedules")


class DoctorReview(Base):
    __tablename__ = "doctor_reviews"
    __table_args__ = (UniqueConstraint("doctor_id", "reviewer_account_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    reviewer_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)

    overall_rating: Mapped[int] = mapped_column(Integer)
    communication_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    professional_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    availability_accurate: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    preferred_language_met: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.VISIBLE)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    doctor = relationship("DoctorProfile", back_populates="reviews")


class CaseReport(Base):
    __tablename__ = "case_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    disease: Mapped[str] = mapped_column(String(160), index=True)
    case_date: Mapped[date] = mapped_column(Date, index=True)
    state: Mapped[str] = mapped_column(String(100), index=True)
    district: Mapped[str] = mapped_column(String(120), index=True)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitals.id"), nullable=True)

    confirmed_cases: Mapped[int] = mapped_column(Integer, default=0)
    suspected_cases: Mapped[int] = mapped_column(Integer, default=0)
    recovered_cases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deaths: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_type: Mapped[str] = mapped_column(String(80), default="MANUAL")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_by_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    doctor_verified_by_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    government_verified_by_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), default=CaseStatus.PENDING)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    doctor_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    government_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CommunityReport(Base):
    __tablename__ = "community_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profiles.id"), nullable=True)
    reporter_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)

    concern_type: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)

    state: Mapped[str] = mapped_column(String(100))
    district: Mapped[str] = mapped_column(String(120))
    locality: Mapped[str | None] = mapped_column(String(180), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    people_affected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[CommunityReportStatus] = mapped_column(
        Enum(CommunityReportStatus), default=CommunityReportStatus.SUBMITTED
    )
    reviewed_by_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ModelAAssessment(Base):
    __tablename__ = "model_a_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), index=True)
    symptoms: Mapped[dict] = mapped_column(JSON)
    inputs: Mapped[dict] = mapped_column(JSON)

    predicted_label: Mapped[str] = mapped_column(String(160))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    probabilities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    profile = relationship("Profile", back_populates="model_a_assessments")


class ModelBRiskSnapshot(Base):
    __tablename__ = "model_b_risk_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), index=True)

    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(50))
    regional_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    inputs: Mapped[dict] = mapped_column(JSON)
    model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    profile = relationship("Profile", back_populates="model_b_snapshots")


class RegionalAlert(Base):
    __tablename__ = "regional_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column(String(100), index=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    disease: Mapped[str | None] = mapped_column(String(160), nullable=True)

    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity))
    title: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(Text)
    current_cases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profiles.id"), nullable=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("regional_alerts.id"), nullable=True)

    category: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(120))
    entity_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
