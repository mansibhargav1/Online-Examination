import re
from datetime import date, datetime

from pydantic import (
    BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator,
)

# Per-document formats for Indian ID proofs. Each entry is (regex, error shown
# to the applicant). Aadhaar's first digit is 2-9 by spec; PAN's 4th character
# encodes holder type, and 'P' is an individual.
ID_PROOF_RULES: dict[str, tuple[str, str]] = {
    "Aadhaar": (r"[2-9]\d{11}", "Aadhaar must be 12 digits and cannot start with 0 or 1."),
    "PAN": (r"[A-Z]{5}\d{4}[A-Z]", "PAN must look like ABCDE1234F."),
    "Passport": (r"[A-PR-WY][1-9]\d\s?\d{4}[1-9]", "Enter a valid Indian passport number, e.g. A1234567."),
    "Driving Licence": (r"[A-Z]{2}\d{2}\s?\d{11}", "Driving licence must look like MP09 20230012345."),
    "Voter ID": (r"[A-Z]{3}\d{7}", "Voter ID must look like ABC1234567."),
}


# ---------- Auth ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalise(cls, v: EmailStr) -> str:
        # Applications store lowercase, so sign-in has to match.
        return str(v).strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    email: EmailStr
    phone: str | None = None
    role: str
    is_active: bool
    created_at: datetime | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


# ---------- Applications ----------
class ApplicationCreate(BaseModel):
    """Every field is required. An application is an identity claim an admin
    acts on, so half-filled forms are rejected at the door rather than chased
    down later."""

    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str
    dob: str
    address: str = Field(min_length=5, max_length=500)
    qualification: str = Field(min_length=2, max_length=120)
    id_proof_type: str
    id_proof_number: str

    @field_validator("full_name")
    @classmethod
    def check_name(cls, v: str) -> str:
        v = " ".join(v.split())  # collapse runs of whitespace
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", v):
            raise ValueError("Name can only contain letters, spaces, and . ' -")
        if not re.search(r"[A-Za-z]{2}", v):
            raise ValueError("Enter your full name.")
        return v

    @field_validator("email")
    @classmethod
    def check_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        # Accept what people actually type, then normalise.
        digits = re.sub(r"[\s\-()]", "", v.strip())
        digits = re.sub(r"^(\+91|0091|0)", "", digits)
        if not re.fullmatch(r"[6-9]\d{9}", digits):
            raise ValueError("Enter a 10-digit Indian mobile number starting with 6, 7, 8 or 9.")
        return digits

    @field_validator("dob")
    @classmethod
    def check_dob(cls, v: str) -> str:
        try:
            born = date.fromisoformat(v.strip())
        except ValueError:
            raise ValueError("Date of birth must be in YYYY-MM-DD format.")
        today = date.today()
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        if born > today:
            raise ValueError("Date of birth cannot be in the future.")
        if age < 15:
            raise ValueError("Candidates must be at least 15 years old.")
        if age > 100:
            raise ValueError("Check the date of birth — that age looks wrong.")
        return born.isoformat()

    @field_validator("id_proof_type")
    @classmethod
    def check_proof_type(cls, v: str) -> str:
        v = v.strip()
        if v not in ID_PROOF_RULES:
            allowed = ", ".join(ID_PROOF_RULES)
            raise ValueError(f"ID proof type must be one of: {allowed}")
        return v

    @model_validator(mode="after")
    def check_proof_number(self):
        """The number's format depends on which document it is, so this has to
        run after both fields are known."""
        rule = ID_PROOF_RULES.get(self.id_proof_type)
        if rule:
            pattern, message = rule
            cleaned = self.id_proof_number.strip().upper().replace(" ", "")
            if not re.fullmatch(pattern, cleaned):
                raise ValueError(message)
            self.id_proof_number = cleaned
        return self


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    email: EmailStr
    phone: str
    dob: str | None = None
    address: str | None = None
    qualification: str | None = None
    id_proof_type: str | None = None
    id_proof_number: str | None = None
    status: str
    admin_note: str | None = None
    created_at: datetime | None = None
    # Kept nullable: rows created before validation tightened may hold NULLs,
    # and the admin console should still render them rather than 500.


class ApproveApplication(BaseModel):
    password: str | None = Field(default=None, min_length=8)
    admin_note: str | None = None


class RejectApplication(BaseModel):
    admin_note: str | None = None


class CredentialsOut(BaseModel):
    email: EmailStr
    password: str
    verification_code: str
    message: str
    email_sent: bool = False
    email_detail: str | None = None


# ---------- Exam authoring ----------
class OptionIn(BaseModel):
    text: str
    is_correct: bool = False


class QuestionIn(BaseModel):
    text: str
    options: list[OptionIn] = Field(min_length=2, max_length=6)


class ExamCreate(BaseModel):
    title: str
    description: str | None = None
    instructions: str | None = None
    seconds_per_question: int = 120
    marks_correct: int = 4
    marks_wrong: int = -1
    marks_unattempted: int = 0
    questions: list[QuestionIn] = Field(default_factory=list)


class ExamSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str | None = None
    instructions: str | None = None
    seconds_per_question: int
    marks_correct: int
    marks_wrong: int
    marks_unattempted: int
    is_active: bool


class ExamListItem(ExamSummary):
    question_count: int = 0
    attempt_status: str | None = None


# ---------- Taking the exam ----------
class VerifyRequest(BaseModel):
    verification_code: str
    declaration_accepted: bool


class OptionOut(BaseModel):
    id: str
    text: str


class QuestionOut(BaseModel):
    question_id: str
    text: str
    options: list[OptionOut]
    index: int
    total: int
    seconds_remaining: int
    seconds_per_question: int


class AnswerSubmit(BaseModel):
    question_id: str
    selected_option_id: str | None = None


class AnswerResult(BaseModel):
    accepted: bool
    marks_awarded: int
    expired: bool
    message: str
    finished: bool


class AnswerReview(BaseModel):
    question_text: str
    selected_option_text: str | None
    correct_option_text: str
    is_correct: bool
    marks_awarded: int
    time_taken_seconds: int | None


class ResultOut(BaseModel):
    exam_title: str
    user_name: str
    total_score: int
    max_score: int
    correct: int
    wrong: int
    unattempted: int
    total_questions: int
    finished_at: datetime | None
    review: list[AnswerReview]


class LeaderRow(BaseModel):
    user_name: str
    email: str
    total_score: int
    correct: int
    wrong: int
    unattempted: int
    finished_at: datetime | None
