import sys
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Account, Role, VerificationStatus


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/promote_admin.py email@example.com")
        raise SystemExit(1)

    email = sys.argv[1].lower()
    db = SessionLocal()
    try:
        account = db.scalar(select(Account).where(Account.email == email))
        if not account:
            print("Account not found")
            raise SystemExit(2)

        account.role = Role.ADMIN
        account.status = VerificationStatus.APPROVED
        db.commit()
        print(f"{email} promoted to ADMIN")
    finally:
        db.close()


if __name__ == "__main__":
    main()
