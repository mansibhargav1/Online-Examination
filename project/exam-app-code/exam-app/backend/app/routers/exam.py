from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_candidate
from app.models import (
    Answer, Attempt, AttemptStatus, Exam, Option, Question, User, now_utc,
)
from app.schemas import (
    AnswerResult, AnswerReview, AnswerSubmit, ExamListItem,
    ExamSummary, OptionOut, QuestionOut, ResultOut, VerifyRequest,
)

router = APIRouter(prefix="/api/exam", tags=["exam"])

EXAM_COLS = (
    "id", "title", "description", "instructions", "seconds_per_question",
    "marks_correct", "marks_wrong", "marks_unattempted", "is_active",
)


def _aware(dt: datetime | None) -> datetime | None:
    """Postgres returns tz-aware datetimes, but guard anyway."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _get_attempt(db: Session, user: User, exam_id: str) -> Attempt:
    attempt = (
        db.query(Attempt)
        .filter(Attempt.user_id == user.id, Attempt.exam_id == exam_id)
        .first()
    )
    if not attempt:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Start the exam first.")
    return attempt


def _grade_expired_answers(db: Session, attempt: Attempt, exam: Exam) -> None:
    """Any served-but-unanswered question past its window is locked in at 0."""
    limit = exam.seconds_per_question
    now = now_utc()
    stale = (
        db.query(Answer)
        .filter(Answer.attempt_id == attempt.id, Answer.answered_at.is_(None))
        .all()
    )
    for ans in stale:
        elapsed = (now - _aware(ans.served_at)).total_seconds()
        if elapsed > limit:
            ans.answered_at = now
            ans.selected_option_id = None
            ans.is_correct = False
            ans.marks_awarded = exam.marks_unattempted
            ans.time_taken_seconds = limit
    db.commit()


@router.get("/available", response_model=list[ExamListItem])
def available_exams(user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    out = []
    for exam in db.query(Exam).filter(Exam.is_active.is_(True)).all():
        if not exam.questions:
            continue
        attempt = (
            db.query(Attempt)
            .filter(Attempt.user_id == user.id, Attempt.exam_id == exam.id)
            .first()
        )
        out.append(ExamListItem(
            **{c: getattr(exam, c) for c in EXAM_COLS},
            question_count=len(exam.questions),
            attempt_status=attempt.status.value if attempt else None,
        ))
    return out


@router.get("/{exam_id}/instructions", response_model=ExamSummary)
def instructions(exam_id: str, user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.is_active.is_(True)).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")
    return exam


@router.post("/{exam_id}/verify")
def verify(
    exam_id: str,
    payload: VerifyRequest,
    user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """Identity check + declaration. Must pass before any question is served."""
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.is_active.is_(True)).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")
    if not payload.declaration_accepted:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Accept the declaration to continue.")
    if not user.verification_code or payload.verification_code.strip() != user.verification_code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That verification code doesn't match. Check with your administrator.")

    attempt = (
        db.query(Attempt)
        .filter(Attempt.user_id == user.id, Attempt.exam_id == exam_id)
        .first()
    )
    if attempt and attempt.status == AttemptStatus.submitted:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You have already completed this exam.")

    if not attempt:
        attempt = Attempt(user_id=user.id, exam_id=exam_id)
        db.add(attempt)

    attempt.verified_at = now_utc()
    db.commit()
    return {"message": "Verified. You can begin.", "attempt_id": attempt.id}


@router.get("/{exam_id}/question", response_model=QuestionOut)
def current_question(
    exam_id: str,
    user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """Serves the question at current_index. Idempotent: re-fetching does not reset the clock."""
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.is_active.is_(True)).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")

    attempt = _get_attempt(db, user, exam_id)
    if not attempt.verified_at:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Complete verification first.")
    if attempt.status == AttemptStatus.submitted:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You have already completed this exam.")

    _grade_expired_answers(db, attempt, exam)

    questions = exam.questions
    total = len(questions)

    # Advance past any question already answered or auto-expired.
    while attempt.current_index < total:
        q = questions[attempt.current_index]
        ans = (
            db.query(Answer)
            .filter(Answer.attempt_id == attempt.id, Answer.question_id == q.id)
            .first()
        )
        if ans and ans.answered_at is not None:
            attempt.current_index += 1
            db.commit()
            continue
        break

    if attempt.current_index >= total:
        _finalise(db, attempt, exam)
        raise HTTPException(status.HTTP_409_CONFLICT, "All questions are done. Fetch your result.")

    question = questions[attempt.current_index]
    ans = (
        db.query(Answer)
        .filter(Answer.attempt_id == attempt.id, Answer.question_id == question.id)
        .first()
    )
    if not ans:
        ans = Answer(
            attempt_id=attempt.id,
            user_id=user.id,
            question_id=question.id,
            served_at=now_utc(),
            marks_awarded=exam.marks_unattempted,
        )
        db.add(ans)
        db.commit()
        db.refresh(ans)

    elapsed = (now_utc() - _aware(ans.served_at)).total_seconds()
    remaining = max(0, int(exam.seconds_per_question - elapsed))

    return QuestionOut(
        question_id=question.id,
        text=question.text,
        options=[OptionOut(id=o.id, text=o.text) for o in question.options],
        index=attempt.current_index + 1,
        total=total,
        seconds_remaining=remaining,
        seconds_per_question=exam.seconds_per_question,
    )


@router.post("/{exam_id}/answer", response_model=AnswerResult)
def submit_answer(
    exam_id: str,
    payload: AnswerSubmit,
    user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
):
    """Grades against the server clock. A late submission scores 0 regardless of correctness."""
    exam = db.query(Exam).filter(Exam.id == exam_id, Exam.is_active.is_(True)).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")

    attempt = _get_attempt(db, user, exam_id)
    if attempt.status == AttemptStatus.submitted:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You have already completed this exam.")

    ans = (
        db.query(Answer)
        .filter(Answer.attempt_id == attempt.id, Answer.question_id == payload.question_id)
        .first()
    )
    if not ans:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That question hasn't been served to you.")
    if ans.answered_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This question is already locked.")

    now = now_utc()
    elapsed = (now - _aware(ans.served_at)).total_seconds()
    expired = elapsed > exam.seconds_per_question

    ans.answered_at = now
    ans.time_taken_seconds = int(min(elapsed, exam.seconds_per_question))

    if expired or payload.selected_option_id is None:
        ans.selected_option_id = None
        ans.is_correct = False
        ans.marks_awarded = exam.marks_unattempted
        message = "Time ran out. Scored as unattempted." if expired else "Skipped. Scored as unattempted."
    else:
        option = (
            db.query(Option)
            .filter(Option.id == payload.selected_option_id, Option.question_id == payload.question_id)
            .first()
        )
        if not option:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "That option doesn't belong to this question.")
        ans.selected_option_id = option.id
        ans.is_correct = option.is_correct
        ans.marks_awarded = exam.marks_correct if option.is_correct else exam.marks_wrong
        message = "Answer recorded."

    attempt.current_index += 1
    db.commit()

    finished = attempt.current_index >= len(exam.questions)
    if finished:
        _finalise(db, attempt, exam)

    return AnswerResult(
        accepted=True,
        marks_awarded=ans.marks_awarded,
        expired=expired,
        message=message,
        finished=finished,
    )


def _finalise(db: Session, attempt: Attempt, exam: Exam) -> None:
    if attempt.status == AttemptStatus.submitted:
        return
    answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    attempt.total_score = sum(a.marks_awarded for a in answers)
    attempt.status = AttemptStatus.submitted
    attempt.finished_at = now_utc()
    db.commit()


@router.post("/{exam_id}/finish")
def finish(exam_id: str, user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    """Ends the attempt early. Every unserved question counts as unattempted."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")
    attempt = _get_attempt(db, user, exam_id)
    _grade_expired_answers(db, attempt, exam)
    _finalise(db, attempt, exam)
    return {"message": "Exam submitted."}


@router.get("/{exam_id}/result", response_model=ResultOut)
def result(exam_id: str, user: User = Depends(require_candidate), db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exam not found.")
    attempt = _get_attempt(db, user, exam_id)
    if attempt.status != AttemptStatus.submitted:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This attempt is still in progress.")

    answers_by_q = {
        a.question_id: a
        for a in db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    }

    review, correct, wrong, unattempted = [], 0, 0, 0
    for q in exam.questions:
        a = answers_by_q.get(q.id)
        correct_opt = next(o for o in q.options if o.is_correct)
        selected_text = None
        if a and a.selected_option_id:
            selected_text = next((o.text for o in q.options if o.id == a.selected_option_id), None)

        if a and a.is_correct:
            correct += 1
        elif a and a.selected_option_id:
            wrong += 1
        else:
            unattempted += 1

        review.append(AnswerReview(
            question_text=q.text,
            selected_option_text=selected_text,
            correct_option_text=correct_opt.text,
            is_correct=bool(a and a.is_correct),
            marks_awarded=a.marks_awarded if a else exam.marks_unattempted,
            time_taken_seconds=a.time_taken_seconds if a else None,
        ))

    return ResultOut(
        exam_title=exam.title,
        user_name=user.full_name,
        total_score=attempt.total_score,
        max_score=len(exam.questions) * exam.marks_correct,
        correct=correct,
        wrong=wrong,
        unattempted=unattempted,
        total_questions=len(exam.questions),
        finished_at=attempt.finished_at,
        review=review,
    )
