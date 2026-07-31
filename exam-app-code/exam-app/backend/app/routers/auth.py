from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Application, ApplicationStatus, User
from app.schemas import (
    ApplicationCreate, ApplicationOut, LoginRequest,
    PasswordChange, TokenResponse, UserOut,
)
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/apply", response_model=ApplicationOut, status_code=201)
def submit_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    """Public. Anyone may apply; only an admin can turn an application into an account."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account already exists for this email.")

    existing = (
        db.query(Application)
        .filter(Application.email == payload.email, Application.status == ApplicationStatus.pending)
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "An application for this email is already under review.")

    app_row = Application(**payload.model_dump())
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    return app_row


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect.")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated.")

    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        role=user.role.value,
        full_name=user.full_name,
        user_id=user.id,
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated."}
