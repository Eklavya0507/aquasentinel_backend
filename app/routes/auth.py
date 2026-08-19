from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_account
from ..models import Account, AccountStatus, DoctorProfile, GovernmentProfile, Role
from ..schemas import LoginIn, RegisterDoctorIn, RegisterGovernmentIn, RegisterUserIn, TokenOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


def ensure_new_email(db: Session, email: str):
    if db.scalar(select(Account).where(Account.email == email.lower())):
        raise HTTPException(status_code=409, detail="Email already registered")


def token_for(account: Account) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(account.id, account.role),
        role=account.role,
        status=account.status,
        full_name=account.full_name,
    )


@router.post("/register", response_model=TokenOut)
def register(data: RegisterUserIn, db: Session = Depends(get_db)):
    ensure_new_email(db, data.email)
    account = Account(full_name=data.full_name, email=data.email.lower(), phone=data.phone,
                      password_hash=hash_password(data.password), role=Role.USER.value,
                      status=AccountStatus.APPROVED.value)
    db.add(account); db.commit(); db.refresh(account)
    return token_for(account)


@router.post("/register-doctor", response_model=TokenOut)
def register_doctor(data: RegisterDoctorIn, db: Session = Depends(get_db)):
    ensure_new_email(db, data.email)
    account = Account(full_name=data.full_name, email=data.email.lower(), phone=data.phone,
                      password_hash=hash_password(data.password), role=Role.DOCTOR.value,
                      status=AccountStatus.PENDING.value)
    db.add(account); db.flush()
    db.add(DoctorProfile(account_id=account.id, registration_number=data.registration_number,
                         specialization=data.specialization, qualification=data.qualification,
                         years_experience=data.years_experience, languages=data.languages))
    db.commit(); db.refresh(account)
    return token_for(account)


@router.post("/register-government", response_model=TokenOut)
def register_government(data: RegisterGovernmentIn, db: Session = Depends(get_db)):
    ensure_new_email(db, data.email)
    account = Account(full_name=data.full_name, email=data.email.lower(), phone=data.phone,
                      password_hash=hash_password(data.password), role=Role.GOVERNMENT.value,
                      status=AccountStatus.PENDING.value)
    db.add(account); db.flush()
    db.add(GovernmentProfile(account_id=account.id, department=data.department,
                             designation=data.designation, organization=data.organization,
                             employee_id=data.employee_id, state=data.state, district=data.district,
                             jurisdiction_level=data.jurisdiction_level))
    db.commit(); db.refresh(account)
    return token_for(account)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    account = db.scalar(select(Account).where(Account.email == data.email.lower()))
    if not account or not verify_password(data.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not account.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return token_for(account)


@router.get("/me")
def me(account: Account = Depends(get_current_account)):
    return {"id": account.id, "full_name": account.full_name, "email": account.email,
            "phone": account.phone, "role": account.role, "status": account.status}
