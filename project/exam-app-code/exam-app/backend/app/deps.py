from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue.")

    payload = decode_token(creds.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session has expired. Sign in again.")

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "This account is no longer active.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required.")
    return user


def require_candidate(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.candidate:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This area is for candidates.")
    return user
