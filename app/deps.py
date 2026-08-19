from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Account
from .security import decode_access_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_account(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> Account:
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = decode_access_token(token)
        account = db.get(Account, int(payload["sub"]))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not account or not account.is_active:
        raise HTTPException(status_code=401, detail="Account unavailable")
    return account


def require_roles(*roles: str):
    def checker(account: Account = Depends(get_current_account)):
        if account.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permission")
        return account
    return checker
