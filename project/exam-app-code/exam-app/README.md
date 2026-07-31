# Online Examination System

A complete examination portal: public application intake, admin-issued accounts, and a **server-timed** one-question-at-a-time MCQ engine.

- **Backend** — FastAPI, SQLAlchemy 2, PostgreSQL, JWT auth
- **Frontend** — React 18, Vite, React Router
- **Runs with** — Docker Compose (three containers: db, backend, frontend)

---

## Run it

You need Docker Desktop (or Docker Engine + Compose). Nothing else.

```bash
cd exam-app
docker compose up --build
```

First build takes a few minutes. When it settles:

| What | Where |
|---|---|
| The portal | http://localhost:8080 |
| API docs (Swagger) | http://localhost:8000/docs |
| Postgres | localhost:5432 |

**Admin sign-in:** `admin@exam.com` / `Admin@12345`

A demo exam ("Computer Science Fundamentals", 5 questions) is seeded automatically.

To stop: `Ctrl+C`. To wipe the database and start clean:

```bash
docker compose down -v
```

---

## The flow, end to end

1. **Apply** — anyone fills the form at `/apply`. This creates an *application*, not an account.
2. **Approve** — admin reviews it in the console and clicks Approve. Only now is the account created. The system returns a **password** and a **6-digit verification code**, shown once. Pass these to the candidate.
3. **Sign in** — candidate signs in at `/login`.
4. **Instructions** — the rules and marking scheme, shown before anything starts.
5. **Verify** — candidate enters the 6-digit code and accepts the declaration.
6. **Exam** — one question per screen, 2 minutes each, four options, one correct.
7. **Result** — score plus a question-by-question review. Admin sees a ranked leaderboard.

### Marking

| Outcome | Marks |
|---|---|
| Correct | **+4** |
| Wrong | **−1** |
| Blank or timed out | **0** |

All three values are configurable per exam.

---

## How the timer actually works

This is the part worth understanding, because it's where most exam apps are broken.

**The clock lives on the server, not in the browser.**

When a question is served, the server writes an `answers` row stamped with `served_at` from its own clock. On submit, it checks `now - served_at` against the limit. If the window has closed, the answer is recorded as unattempted and scored 0 — **even if the selected option was correct**.

What this buys you:

- **Refreshing does nothing.** The countdown you see is cosmetic; re-fetching returns the *remaining* time, not a fresh 2 minutes.
- **Closing the tab doesn't pause anything.** Walk away, and the question auto-grades to 0 the next time the attempt is touched.
- **Editing the JS timer doesn't help.** The client never reports elapsed time; the server never asks.
- **One attempt per exam**, enforced by a unique constraint on `(user_id, exam_id)`.
- **Answers are final** — a second submit for the same question is rejected.

Verified by tests: a *correct* answer submitted after the window scored 0, an abandoned question auto-graded and advanced, and a refresh reduced the remaining time rather than resetting it.

---

## Answers are stored per candidate

Every `answers` row carries `user_id` alongside `attempt_id`, so results are one query per person:

```sql
SELECT * FROM answers WHERE user_id = '<uuid>';
```

Each row records the selected option, whether it was correct, the marks awarded, and the seconds taken.

---

## Application form rules

Every field is required — an application is an identity claim an admin acts on,
so half-filled forms are rejected rather than chased down later.

| Field | Rule |
|---|---|
| Full name | Letters, spaces, and `.` `'` `-` only. Whitespace collapsed. |
| Email | Standard format. Stored lowercase; sign-in matches case-insensitively. |
| Mobile | 10 digits starting 6–9. `+91`, `0091`, `0`, spaces, dashes and brackets are stripped before storing. |
| Date of birth | `YYYY-MM-DD`, not in the future, age 15–100. |
| Address | At least 5 characters. |
| Qualification | At least 2 characters. |
| ID proof type | One of Aadhaar, PAN, Passport, Driving Licence, Voter ID. |
| ID proof number | Format depends on the type (see below). Stored uppercase, spaces removed. |

**ID proof formats**

| Type | Rule | Example |
|---|---|---|
| Aadhaar | 12 digits, first digit 2–9 | `234567890123` |
| PAN | 5 letters, 4 digits, 1 letter | `ABCDE1234F` |
| Passport | Letter (not Q/X/Z) + 7 digits | `A1234567` |
| Driving Licence | State + RTO code + 11 digits | `MP09 20230012345` |
| Voter ID | 3 letters + 7 digits | `ABC1234567` |

Rules live in `backend/app/schemas.py` and are mirrored in `frontend/src/pages/Apply.jsx`
so applicants see errors inline before submitting. **The server re-validates
everything** — the client copy is courtesy, not security. A test asserts the two
stay in agreement; if you change one, change both.

These are format checks, not identity checks. A well-formed Aadhaar number isn't
a real one — verifying that needs UIDAI integration and is out of scope here.
The admin reviewing the application is still the actual gate.

---

## Email (optional)

When an admin approves an application, the app can email the candidate their
password and verification code. **This is off by default** — the app runs fine
without it, and credentials still appear in the admin console.

### Turning it on

```bash
cp .env.example .env
```

Edit `.env` with your SMTP details, then `docker compose up --build`.

**Gmail** — free, quick, fine for testing:

1. Turn on 2-Step Verification on your Google account
2. Generate an App Password at https://myaccount.google.com/apppasswords
3. Use the 16-character string as `SMTP_PASSWORD` — *not* your Gmail password
4. Set `MAIL_FROM` to the same address as `SMTP_USER` (Gmail rewrites the sender anyway)

**Resend / Brevo** — better deliverability, needs a verified domain. See the
commented blocks in `.env.example`.

### What to expect

- **Sending never blocks approval.** If the mail server is down or misconfigured,
  the account is still created, the credentials still come back, and the console
  shows why the email failed. Verified by test.
- **Deliverability is the hard part, not the code.** Without a verified domain
  carrying SPF and DKIM records, credential emails often land in spam — which is
  the worst outcome, since candidates can't sit the exam and you won't know why.
  Budget time for domain verification if this goes to real users.
- **The console fallback stays.** Even with email working, credentials are shown
  on screen. That panel is how you unblock someone when mail silently fails.
- **Passwords are sent in plaintext.** Mail sits unencrypted on servers and in
  inboxes indefinitely. Acceptable for throwaway exam accounts; not acceptable if
  these accounts ever hold anything sensitive. The stronger pattern is emailing a
  one-time setup link and letting candidates choose their own password.

`.env` is gitignored. Don't commit real credentials, and rotate any password
that's been pasted into a screenshot or chat.

---

## Configuration

Set in `docker-compose.yml` under `backend.environment`:

| Variable | Default | Meaning |
|---|---|---|
| `ADMIN_EMAIL` | `admin@exam.com` | Seeded admin account |
| `ADMIN_PASSWORD` | `Admin@12345` | Seeded admin password |
| `QUESTION_TIME_SECONDS` | `120` | Default per-question window |
| `JWT_SECRET` | *(dev value)* | **Change this before deploying** |
| `SEED_DEMO_EXAM` | `true` | Set `false` for an empty install |
| `MAIL_ENABLED` | `false` | Turn credential emails on |
| `SMTP_HOST` / `SMTP_PORT` | — | e.g. `smtp.gmail.com` / `587` |
| `SMTP_USER` / `SMTP_PASSWORD` | — | Gmail: an **App Password**, not your login |
| `MAIL_FROM` | — | Must equal `SMTP_USER` on Gmail |
| `PORTAL_URL` | `http://localhost:8080` | Sign-in link used inside the email |

> Do not use `.local` in `ADMIN_EMAIL` — it's a reserved TLD and email validation rejects it.

---

## Project layout

```
exam-app/
├── docker-compose.yml
├── .env.example             # copy to .env for email config
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # app startup, table creation, seeding
│       ├── config.py        # env-driven settings
│       ├── database.py      # engine + session
│       ├── models.py        # User, Application, Exam, Question, Option, Attempt, Answer
│       ├── schemas.py       # request/response shapes
│       ├── security.py      # bcrypt hashing, JWT, code generation
│       ├── deps.py          # auth guards (admin / candidate)
│       ├── mail.py          # SMTP send, best-effort
│       ├── seed.py          # admin account + demo exam
│       └── routers/
│           ├── auth.py      # apply, login, me, change-password
│           ├── admin.py     # approvals, users, exams, results
│           └── exam.py      # the timed engine
└── frontend/
    ├── Dockerfile
    ├── nginx.conf           # serves the SPA, proxies /api -> backend
    └── src/
        ├── App.jsx          # routes
        ├── styles.css       # design system
        ├── lib/api.js       # fetch wrapper, token handling
        ├── components/      # Layout, Protected
        └── pages/           # Home, Apply, Login, Dashboard,
                             # Instructions, Verify, Exam, Result, Admin
```

---

## API reference

**Public**
- `POST /api/auth/apply` — submit an application
- `POST /api/auth/login` — sign in

**Candidate**
- `GET  /api/exam/available`
- `GET  /api/exam/{id}/instructions`
- `POST /api/exam/{id}/verify`
- `GET  /api/exam/{id}/question` — serves current question; starts the clock
- `POST /api/exam/{id}/answer` — graded against the server clock
- `POST /api/exam/{id}/finish`
- `GET  /api/exam/{id}/result`

**Admin**
- `GET  /api/admin/applications`
- `POST /api/admin/applications/{id}/approve` — creates the account
- `POST /api/admin/applications/{id}/reject`
- `GET  /api/admin/users`, `POST .../reset-password`, `.../reset-verification`, `.../toggle-active`
- `POST /api/admin/exams`, `GET /api/admin/exams`, `POST .../toggle-active`, `DELETE .../{id}`
- `GET  /api/admin/exams/{id}/results` — leaderboard
- `GET  /api/admin/stats`

Full interactive docs at http://localhost:8000/docs

---

## Developing without Docker

**Backend**

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL="sqlite:///./dev.db"   # or point at Postgres
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173, proxies /api to :8000
```

---

## Before you deploy

- Replace `JWT_SECRET` with a long random string.
- Change `ADMIN_PASSWORD`.
- Put it behind HTTPS.
- Swap `create_all()` for Alembic migrations once the schema starts moving.
- Restrict `CORS_ORIGINS` to your real domain.
