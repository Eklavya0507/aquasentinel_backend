from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Account,
    DoctorLanguage,
    DoctorProfile,
    GovernmentOfficial,
    Role,
    VerificationStatus,
)
from ..schemas import (
    LoginIn,
    RegisterDoctorIn,
    RegisterGovernmentIn,
    RegisterUserIn,
    TokenOut,
)
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


def ensure_new_email(db: Session, email: str):
    if db.scalar(select(Account).where(Account.email == email.lower())):
        raise HTTPException(status_code=409, detail="Email already registered")


@router.post("/register", response_model=TokenOut)
def register_user(data: RegisterUserIn, db: Session = Depends(get_db)):
    ensure_new_email(db, data.email)
    account = Account(
        full_name=data.full_name,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=Role.USER,
        status=VerificationStatus.APPROVED,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return TokenOut(
        access_token=create_access_token(str(account.id), account.role.value),
        role=account.role.value,
        status=account.status.value,
    )


@router.post("/register-doctor", response_model=TokenOut)
def register_doctor(data: RegisterDoctorIn, db: Session = Depends(get_db)):
    ensure_new_email(db, data.email)
    account = Account(
        full_name=data.full_name,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=Role.DOCTOR,
        status=VerificationStatus.PENDING,
    )
    db.add(account)
    db.flush()

    doctor = DoctorProfile(
        account_id=account.id,
        registration_number=data.registration_number,
        specialization=data.specialization,
        qualification=data.qualification,
        years_experience=data.years_experience,
        verification_status=VerificationStatus.PENDING,
    )
    db.add(doctor)
    db.flush()

    for language in data.languages:
        db.add(DoctorLanguage(doctor_id=doctor.id, language_code=language))

    db.commit()
    return TokenOut(
        access_token=create_access_token(str(account.id), account.role.value),
        role=account.role.value,
        status=account.status.value,
    )


@router.post("/register-government", response_model=TokenOut)
def register_government(data: RegisterGovernmentIn, db: Session = Depends(get_db)):
    ensure_new_email(db, data.email)
    account = Account(
        full_name=data.full_name,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=Role.GOVERNMENT,
        status=VerificationStatus.PENDING,
    )
    db.add(account)
    db.flush()

    profile = GovernmentOfficial(
        account_id=account.id,
        department=data.department,
        designation=data.designation,
        organization=data.organization,
        employee_id=data.employee_id,
        state=data.state,
        district=data.district,
        jurisdiction_level=data.jurisdiction_level,
        verification_status=VerificationStatus.PENDING,
    )
    db.add(profile)
    db.commit()

    return TokenOut(
        access_token=create_access_token(str(account.id), account.role.value),
        role=account.role.value,
        status=account.status.value,
    )


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    account = db.scalar(select(Account).where(Account.email == data.email.lower()))
    if not account or not verify_password(data.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not account.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    return TokenOut(
        access_token=create_access_token(str(account.id), account.role.value),
        role=account.role.value,
        status=account.status.value,
    )
