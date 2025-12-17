# 📝 Online Examination System

A **full‑stack Online Examination System** built using **Spring Boot, MySQL, HTML/CSS/JavaScript**, fully **Dockerized** using **Docker Compose**. This system allows users to take an exam **only once**, automatically manages exam timing, prevents multiple attempts, and stores all results securely in MySQL.

---

## 🚀 Features

### 👨‍🎓 Student
- User registration & login
- Start exam (only **one attempt allowed**)
- Timer‑based online exam
- Auto‑submit on:
  - Time expiry
  - Tab switch / page change (security)
- View score after submission

### 👨‍🏫 Admin
- Admin login
- Add / update / delete questions
- Secure admin passcode flow
- View user results

### 🔐 Security Rules
- One exam attempt per user
- Attempt stored using `results` table
- Tab switch / browser change auto‑submits exam

---

## 🏗️ Tech Stack

| Layer | Technology |
|------|------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Spring Boot (Java) |
| Database | MySQL 8 |
| Containerization | Docker, Docker Compose |

---

## 📂 Project Structure

```
online-exam/
├── backend/
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/main/java/com/examapp
│       ├── controller
│       ├── service
│       ├── repository
│       ├── model
│       └── config
│
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   ├── exam.html
│   ├── styles.css
│   ├── app.js
│   └── other html pages
│
├── docker-compose.yml
└── README.md
```

---

## 🐳 Docker Setup

### 🔧 Prerequisites
- Docker
- Docker Compose

Check installation:
```bash
docker --version
docker-compose --version
```

---

## ▶️ Run the Project (Step‑by‑Step)

### 1️⃣ Clone Repository
```bash
git clone <your-git-repo-url>
cd online-exam
```

### 2️⃣ Build & Start Containers
```bash
docker-compose up --build
```

### 3️⃣ Verify Running Containers
```bash
docker ps
```

Expected services:
- `exam-backend`
- `exam-frontend`
- `exam-mysql`

---

## 🌐 Access Application

| Service | URL |
|------|-----|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8081 |
| MySQL | localhost:3306 |

---

## 🛢️ MySQL Database Setup

### Enter MySQL Container
```bash
docker exec -it exam-mysql mysql -u examuser -pexampass
```

### Show Databases
```sql
SHOW DATABASES;
```

### Use Exam Database
```sql
USE examdb;
```

### Show Tables
```sql
SHOW TABLES;
```

Tables:
- `users`
- `admins`
- `questions`
- `results`
- `user_answers`

---

## 🧾 Important Tables Explanation

### 👤 users
Stores registered users.
```sql
SELECT * FROM users;
```

### ❓ questions
Stores exam questions.
```sql
SELECT * FROM questions;
```

### 🧮 results
Stores **one exam attempt per user**.
```sql
SELECT * FROM results;
```

Used to:
- Prevent multiple exam attempts
- Track start & end time
- Store score & result status

### ✍️ user_answers
Stores answers selected by users.
```sql
SELECT * FROM user_answers;
```

---

## 🔒 One‑Attempt Enforcement Logic

- When exam starts → entry inserted into `results`
- On re‑attempt → system checks `results` table
- If record exists → exam blocked

```sql
SELECT * FROM results WHERE user_id = ?;
```

---

## ⏱️ Exam Auto‑Submit Logic

- JavaScript tracks exam time
- `visibilitychange` event triggers auto‑submit
- Backend stores submission immediately

---

## 🔄 Reset Data (For Testing)

⚠️ **Use carefully**

```sql
DELETE FROM results;
DELETE FROM user_answers;
```

Reset auto‑increment:
```sql
ALTER TABLE results AUTO_INCREMENT = 1;
ALTER TABLE user_answers AUTO_INCREMENT = 1;
```

---

## 🛑 Stop & Remove Containers

```bash
docker-compose down
```

Remove volumes (fresh DB):
```bash
docker-compose down -v
```

---

## 🧪 Rebuild Only Backend / Frontend

```bash
docker-compose build backend
docker-compose build frontend
```

---

## 📌 Environment Configuration

Backend:
```
spring.datasource.url=jdbc:mysql://exam-mysql:3306/examdb
spring.datasource.username=examuser
spring.datasource.password=exampass
```

---

## 📈 Future Enhancements

- JWT authentication
- Result analytics dashboard
- Question randomization
- Proctoring (camera / mic)

---

## 👨‍💻 Author

Developed by **Ari Ji**  
Full‑Stack / DevOps Project

---

## ⭐ Final Notes

This project is:
- ✅ Fully Dockerized
- ✅ Interview‑ready
- ✅ College submission ready
- ✅ Production structured

Feel free to fork, modify, or enhance 🚀

