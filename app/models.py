from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from .database import Base


class Role(str, Enum):
    USER = "USER"
    DOCTOR = "DOCTOR"
    GOVERNMENT = "GOVERNMENT"


class AccountStatus(str, Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(30), default=Role.USER.value)
    status: Mapped[str] = mapped_column(String(30), default=AccountStatus.APPROVED.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profiles = orm_relationship("Profile", back_populates="account", cascade="all, delete-orphan")
    doctor_profile = orm_relationship("DoctorProfile", back_populates="account", uselist=False, cascade="all, delete-orphan")
    government_profile = orm_relationship("GovernmentProfile", back_populates="account", uselist=False, cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    relationship: Mapped[str] = mapped_column(String(50), default="Self")
    date_of_birth: Mapped[date] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(40), nullable=True)
    caregiver_managed: Mapped[bool] = mapped_column(Boolean, default=False)
    primary_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    primary_district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    primary_locality: Mapped[str | None] = mapped_column(String(150), nullable=True)
    current_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    current_locality: Mapped[str | None] = mapped_column(String(150), nullable=True)
    current_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_languages: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    account = orm_relationship("Account", back_populates="profiles")
    histories = orm_relationship("MedicalHistory", back_populates="profile", cascade="all, delete-orphan")


class MedicalHistory(Base):
    __tablename__ = "medical_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), index=True)
    disease_name: Mapped[str] = mapped_column(String(150))
    diagnosis_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    doctor_confirmed: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile = orm_relationship("Profile", back_populates="histories")


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), unique=True)
    registration_number: Mapped[str] = mapped_column(String(120), unique=True)
    specialization: Mapped[str] = mapped_column(String(150))
    qualification: Mapped[str | None] = mapped_column(String(200), nullable=True)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    account = orm_relationship("Account", back_populates="doctor_profile")


class GovernmentProfile(Base):
    __tablename__ = "government_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), unique=True)
    department: Mapped[str] = mapped_column(String(160))
    designation: Mapped[str] = mapped_column(String(160))
    organization: Mapped[str] = mapped_column(String(200))
    employee_id: Mapped[str] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    jurisdiction_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    account = orm_relationship("Account", back_populates="government_profile")


class CommunityReport(Base):
    __tablename__ = "community_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    concern_type: Mapped[str] = mapped_column(String(120), default="COMMUNITY_SIGNAL")
    summary: Mapped[str] = mapped_column(String(300))
    state: Mapped[str] = mapped_column(String(100))
    district: Mapped[str] = mapped_column(String(120))
    locality: Mapped[str | None] = mapped_column(String(150), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    water_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    people_affected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    reporter_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    reporter_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reporter_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="SUBMITTED")
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CaseReport(Base):
    __tablename__ = "case_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    disease: Mapped[str] = mapped_column(String(120), index=True)
    case_date: Mapped[date] = mapped_column(Date, index=True)
    state: Mapped[str] = mapped_column(String(100), index=True)
    district: Mapped[str] = mapped_column(String(120), index=True)
    confirmed_cases: Mapped[int] = mapped_column(Integer, default=0)
    suspected_cases: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="VERIFIED_DEMO")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Hospital(Base):
    __tablename__ = "hospitals"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    state: Mapped[str] = mapped_column(String(100))
    district: Mapped[str] = mapped_column(String(120))
    locality: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    emergency_available: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
