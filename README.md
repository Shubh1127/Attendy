# Attendy Backend

FastAPI backend for **Attendy**, a biometric attendance management system that uses facial recognition for secure classroom attendance.

---

## Features

- Teacher Authentication (JWT)
- Student Registration
- Face Embedding Registration
- Face Verification
- Subject Management
- Student Enrollment via PDF Upload
- Attendance Session Management
- Automatic Attendance Marking
- Automatic Session Expiry
- Attendance Analytics
- Supabase PostgreSQL Integration

---

## Tech Stack

- FastAPI
- Python 3.11+
- Supabase (PostgreSQL)
- JWT Authentication
- dlib
- face_recognition
- NumPy
- Pillow
- pdfplumber
- Pandas

---

## Project Structure

```
backend/
│
├── api/
│   ├── routes/
│   │   ├── attendance.py
│   │   ├── auth.py
│   │   ├── student.py
│   │   ├── subjects.py
│   │   └── teacher.py
│
├── core/
│   ├── auth.py
│   ├── config.py
│   └── schemas.py
│
├── database/
│   └── config.py
│
├── pipelines/
│   └── face_pipeline.py
│
├── app.py
├── requirements.txt
└── README.md
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/your-username/Attendy.git

cd Attendy/backend
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate

PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

CMD

```cmd
venv\Scripts\activate
```

Git Bash

```bash
source venv/Scripts/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file inside the backend folder.

```env
SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY

JWT_SECRET_KEY=YOUR_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
```

> **Note**
>
> Use the **Supabase Service Role Key** in the backend.
> Do **not** use the Anon/Public key.

---

## Run the Server

```bash
python -m uvicorn app:app --reload
```

Server

```
http://127.0.0.1:8000
```

Swagger Docs

```
http://127.0.0.1:8000/docs
```

ReDoc

```
http://127.0.0.1:8000/redoc
```

---

# Authentication

The backend uses JWT Bearer Authentication.

Include the access token in every protected request.

```
Authorization: Bearer YOUR_TOKEN
```

---

# Main Features

## Teacher

- Register
- Login
- Create Subjects
- Upload Student PDF
- Open Attendance Session
- Review Attendance
- Close Session

---

## Student

- Register Face
- Login
- View Subjects
- View Attendance Summary
- View Attendance Sessions
- Mark Attendance using Face Recognition

---

# Attendance Workflow

```
Teacher creates Subject
        │
        ▼
Teacher uploads Student PDF
        │
        ▼
Students register Face
        │
        ▼
Teacher opens Attendance Session
        │
        ▼
Students verify Face
        │
        ▼
Attendance marked automatically
        │
        ▼
Session closes automatically after 1 hour
        │
        ▼
Teacher reviews attendance
        │
        ▼
Attendance finalized
```

---

# Face Recognition

The backend uses **dlib** to generate 128-dimensional facial embeddings.

Workflow:

1. Student registers face.
2. Face embedding stored in PostgreSQL.
3. During attendance:
   - Face embedding generated.
   - Compared using Euclidean Distance.
   - Attendance marked if distance is below the threshold.

---

# PDF Upload

Teachers can upload a student list PDF.

The backend:

- Extracts tables
- Reads student names
- Reads enrollment numbers
- Inserts new students
- Enrolls students into the selected subject
- Updates subject student count automatically

---

# Database

Main Tables

- teacher
- student
- subjects
- subjects_student
- attendance_sessions
- attendance_logs

---

# API Documentation

Swagger UI

```
/docs
```

ReDoc

```
/redoc
```

---

# Future Improvements

- Voice Authentication
- Multi-face Detection Prevention
- Face Liveness Detection
- Attendance Reports
- Email Notifications
- Analytics Dashboard

---

# License

This project is developed for educational purposes.