# 📝 Online Examination System (Cloud Deployment)

A **full-stack Online Examination System** built using **Spring Boot, MySQL, HTML/CSS/JavaScript**, deployed on a **GCP Virtual Machine using Docker Compose**.

---

## 🚀 Live Application

🌐 **Access URL:**
http://onlinexam:8080

---

## 📸 Application Screenshot

<img width="1436" height="852" alt="image" src="https://github.com/user-attachments/assets/2ef88029-df30-48ba-854d-c4b092dc5140" />




---

## 🏗️ Architecture

```
GCP VM (Ubuntu)
   ├── Frontend (Nginx - Docker)
   ├── Backend (Spring Boot - Docker)
   └── MySQL (Docker)
```

---

## 🧰 Tech Stack

| Layer            | Technology                             |
| ---------------- | -------------------------------------- |
| Frontend         | HTML, CSS, JavaScript                  |
| Backend          | Spring Boot (Java)                     |
| Database         | MySQL 8                                |
| Containerization | Docker, Docker Compose, Harbor (Private Registry) |
| Cloud            | Google Cloud Platform (Compute Engine) |

---

## ⚙️ Setup on GCP VM

### 🔹 1. Create VM

* Machine Type: `e2-medium`
* OS: Ubuntu 22.04
* Enable HTTP/HTTPS traffic

---

### 🔹 2. Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl unzip vim

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Enable Docker for user
sudo usermod -aG docker $USER
newgrp docker
```

---

### 🔹 3. Clone Repository

```bash
git clone <your-repo-url>
cd online-exam
```

---

### 🔹 4. Run Application

```bash
docker compose up --build -d
```

## 🐳 Harbor (Private Docker Registry)

A private container registry (Harbor) is used to store Docker images securely with HTTPS enabled.

- URL: https://harbor.local  
- Used for managing application images  
- Secured using TLS certificates  

<img width="1430" height="672" alt="image" src="https://github.com/user-attachments/assets/c358c948-8a2d-499f-b335-f03bb4a87241" />


---

## 📦 Image Push Example

```bash
docker tag exam-backend harbor.local/online-exam/backend:v1
docker push harbor.local/online-exam/backend:v1
---

### 🔹 5. Verify Containers

```bash
docker ps
```

Expected containers:

* exam-frontend
* exam-backend
* exam-mysql

---

## 🌐 Access Application

| Service     | URL                 |
| ----------- | ------------------- |
| Frontend    | http://<VM_IP>:8080 |
| Backend API | http://<VM_IP>:8081 |

---

## 🔓 Firewall Configuration

Allow ports:

* 8080 (Frontend)
* 8081 (Backend)

---

## 🛢️ Database Details

| Field    | Value    |
| -------- | -------- |
| DB Name  | examdb   |
| Username | examuser |
| Password | exampass |
| Port     | 3306     |

---

## ⚠️ Limitations (Current Setup)

* MySQL runs inside container ❌
* No automated backup ❌
* Not production-grade yet ❌

---

## 🚀 Future Enhancements

* Move DB to **Cloud SQL**
* Enable **automatic backups (24 hrs)**
* Use **Secret Manager**
* Deploy on **GKE (Kubernetes)**
* Add CI/CD (GitHub Actions / Jenkins)

---

## 👨‍💻 Author

Developed by **Mansi**
Full Stack + DevOps Project

---

## ⭐ Final Note

This project demonstrates:

* Containerization using Docker
* Cloud deployment on GCP VM
* Full-stack integration

Ready for further scaling to Kubernetes 🚀
