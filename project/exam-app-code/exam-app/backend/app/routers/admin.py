from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.mail import send_credentials
from app.models import (
    Answer, Application, ApplicationStatus, Attempt, AttemptStatus,
    Exam, Option, Question, Role, User, now_utc,
)
from app.schemas import (
    ApplicationOut, ApproveApplication, CredentialsOut, ExamCreate,
    ExamListItem, LeaderRow, RejectApplication, UserOut,
)
from app.security import generate_password, generate_verification_code, hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------- Applications ----------
@router.get("/applications", response_model=list[ApplicationOut])
def list_applications(status_filter: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Application)
    if status_filter:
        q = q.filter(Application.status == status_filter)
    return q.order_by(Application.created_at.desc()).all()


@router.post("/applications/{app_id}/approve", response_model=CredentialsOut)
def approve_application(app_id: str, payload: ApproveApplication, db: Session = Depends(get_db)):
    """Creates the candidate account. This is the only path to an account."""
    app_row = db.query(Application).filter(Application.id == app_id).first()
    if not app_row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found.")
    if app_row.status == ApplicationStatus.approved:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This application is already approved.")
    if db.query(User).filter(User.email == app_row.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account already exists for this email.")

    raw_password = payload.password or generate_password()
    code = generate_verification_code()

    user = User(
        full_name=app_row.full_name,
        email=app_row.email,
        phone=app_row.phone,
        password_hash=hash_password(raw_password),
        role=Role.candidate,
        verification_code=code,
    )
    db.add(user)

    app_row.status = ApplicationStatus.approved
    app_row.admin_note = payload.admin_note
    db.commit()

    # Best-effort. A dead mail server must not undo an approval, so the
    # credentials are still returned either way.
    sent, detail = send_credentials(user.full_name, user.email, raw_password, code)

    return CredentialsOut(
        email=user.email,
        password=raw_password,
        verification_code=code,
        message="Account created. Share these credentials with the candidate — the password is shown only once.",
        email_sent=sent,
        email_detail=detail,
    )


@router.post("/applications/{app_id}/reject", response_model=ApplicationOut)
def reject_application(app_id: str, payload: RejectApplication, db: Session = Depends(get_db)):
    app_row = db.query(Application).filter(Application.id == app_id).first()
    if not app_row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found.")
    app_row.status = ApplicationStatus.rejected
    app_row.admin_note = payload.admin_note
    db.commit()
    db.refresh(app_row)
    return app_row


# ---------- Users ----------
@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users/{user_id}/toggle-active", response_model=UserOut)
def toggle_active(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    if user.role == Role.admin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Admin accounts cannot be deactivated here.")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-verification")
def reset_verification(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    user.verification_code = generate_verification_code()
    db.commit()
    return {"email": user.email, "verification_code": user.verification_code}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    raw = generate_password()
    user.password_hash = hash_password(raw)
    db.commit()

    sent, detail = send_credentials(user.full_name, user.email, raw, user.verification_code or "—")

    return {
        "email": user.email,
        "password": raw,
        "message": "Shown only once.",
        "email_sent": sent,
        "email_detail": detail,
    }


# ---------- Exams ----------
@router.post("/exams", response_model=ExamListItem, status_code=201)
def create_exam(payload: ExamCreate, db: Session = Depends(get_db)):
    for i, q in enumerate(payload.questions, start=1):
        if sum(1 for o in q.options if o.is_correct) != 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Question {i} must have exactly one correct option.",
            )

    exam = Exam(
        title=payload.title,
        description=payload.description,
        instructions=payload.instructions,
        seconds_per_question=payload.seconds_per_question,
        marks_correct=payload.marks_correct,
        marks_wrong=payload.marks_wrong,
        marks_unattempted=payload.marks_unattempted,
    )
    db.add(exam)
    db.flush()

    for qi, q in enumerate(payload.questions):
        question = Question(exam_id=exam.id, text=q.text, order_index=qi)
        db.add(question)
        db.flush()
        for oi, o in enumerate(q.options):
            db.add(Option(question_id=question.id, text=o.text, is_correct=o.is_correct, order_index=oi))

    db.commit()
    db.refresh(exam)
    return ExamListItem(
        **{c: getattr(exam, c) for c in (
            "id", "title", "description", "instructions", "seconds_per_question",
            "marks_correct", "marks_wrong", "marks_unattempted", "is_active",
        )},
        question_count=len(payload.questions),
    )


@router.get("/exams", response_model=list[ExamListItem])
def list_exams(db: Session = Depends(get_db)):
    out = []
    for exam in db.query(Exam).order_by(Exam.created_at.desc()).all():
        out.append(ExamListItem(
            **{c: getattr(exam, c) for c in (
                "id", "title", "description", "instructions", "seconds_per_question",
                "marks_correct", "marks_wrong", "marks_unattempted", "is_active",
            )},
            question_count=len(exam.questions),
        ))
    return out


@router.post("/exams/{exam_id}/questions", status_code=201)
def add_question(exam_id: str, payload: dict, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")

    options = payload.get("options", [])
    if sum(1 for o in options if o.get("is_correct")) != 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mark exactly one option as correct.")

    next_index = len(exam.questions)
    question = Question(exam_id=exam.id, text=payload["text"], order_index=next_index)
    db.add(question)
    db.flush()
    for oi, o in enumerate(options):
        db.add(Option(question_id=question.id, text=o["text"], is_correct=bool(o.get("is_correct")), order_index=oi))
    db.commit()
    return {"id": question.id, "message": "Question added."}


@router.delete("/exams/{exam_id}")
def delete_exam(exam_id: str, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")
    if db.query(Attempt).filter(Attempt.exam_id == exam_id).count():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Candidates have attempted this exam. Deactivate it instead.")
    db.delete(exam)
    db.commit()
    return {"message": "Exam deleted."}


@router.post("/exams/{exam_id}/toggle-active", response_model=ExamListItem)
def toggle_exam(exam_id: str, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")
    exam.is_active = not exam.is_active
    db.commit()
    db.refresh(exam)
    return ExamListItem(
        **{c: getattr(exam, c) for c in (
            "id", "title", "description", "instructions", "seconds_per_question",
            "marks_correct", "marks_wrong", "marks_unattempted", "is_active",
        )},
        question_count=len(exam.questions),
    )


# ---------- Results ----------
@router.get("/exams/{exam_id}/results", response_model=list[LeaderRow])
def exam_results(exam_id: str, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")

    rows = []
    attempts = (
        db.query(Attempt)
        .filter(Attempt.exam_id == exam_id, Attempt.status == AttemptStatus.submitted)
        .all()
    )
    for a in attempts:
        answers = db.query(Answer).filter(Answer.attempt_id == a.id).all()
        correct = sum(1 for x in answers if x.is_correct)
        wrong = sum(1 for x in answers if x.selected_option_id and not x.is_correct)
        unattempted = len(exam.questions) - correct - wrong
        rows.append(LeaderRow(
            user_name=a.user.full_name,
            email=a.user.email,
            total_score=a.total_score,
            correct=correct,
            wrong=wrong,
            unattempted=unattempted,
            finished_at=a.finished_at,
        ))
    rows.sort(key=lambda r: r.total_score, reverse=True)
    return rows


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return {
        "pending_applications": db.query(Application).filter(Application.status == ApplicationStatus.pending).count(),
        "candidates": db.query(User).filter(User.role == Role.candidate).count(),
        "exams": db.query(Exam).count(),
        "attempts_submitted": db.query(Attempt).filter(Attempt.status == AttemptStatus.submitted).count(),
        "attempts_in_progress": db.query(Attempt).filter(Attempt.status == AttemptStatus.in_progress).count(),
    }
