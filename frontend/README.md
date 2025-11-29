# 🎓 HR Resume Review Portal

> **Final Year Project** - An AI-powered HR Resume Review System that helps recruiters efficiently manage job postings and evaluate candidate resumes with automated scoring.

![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green?logo=mongodb)
![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Data Flow](#-data-flow)
- [Scoring Algorithm](#-scoring-algorithm)
- [Installation](#-installation)
- [API Documentation](#-api-documentation)
- [Screenshots](#-screenshots)
- [Future Enhancements](#-future-enhancements)

---

## 🎯 Project Overview

The **HR Resume Review Portal** is a full-stack web application designed to streamline the recruitment process. It enables HR managers to:

1. **Post Job Openings** - Create detailed job descriptions with required skills
2. **Collect Applications** - Students/candidates submit resumes through the portal
3. **Automated Scoring** - AI-powered resume analysis and scoring based on job requirements
4. **Review & Shortlist** - View ranked candidates and manage application status

### Problem Statement

Traditional resume screening is:
- ⏱️ Time-consuming (average 7 seconds per resume)
- 🎯 Inconsistent (human bias in evaluation)
- 📊 Lacks quantifiable metrics

### Solution

Our system provides:
- ⚡ Instant automated resume parsing and scoring
- 📈 Objective scoring based on skill match, experience, and education
- 🏆 Ranked candidate list for efficient decision-making

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    (Next.js 14 + TypeScript)                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │  Home   │  │  Post   │  │  Apply  │  │ Review  │            │
│  │  Page   │  │  Job    │  │  Page   │  │  Page   │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
└───────┼────────────┼────────────┼────────────┼──────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      REST API (HTTP/JSON)                        │
│         GET /api/jobs    POST /api/jobs    POST /api/apply      │
└─────────────────────────────────────────────────────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│                     (Flask + Python)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Core Modules                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │    Auth     │  │   Resume    │  │   Scoring   │       │   │
│  │  │   Module    │  │   Parser    │  │   Engine    │       │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATABASE                                  │
│                   (MongoDB - Local)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Users   │  │   Jobs   │  │  Appli-  │  │ Sessions │        │
│  │Collection│  │Collection│  │ cations  │  │Collection│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### For HR Managers
| Feature | Description |
|---------|-------------|
| 🔐 Secure Login | JWT-based authentication system |
| 📝 Job Posting | Create jobs with title, description, requirements, and upload JD |
| 📊 Dashboard | View all jobs with applicant counts |
| 🏆 Resume Review | See ranked candidates with scores |
| ✅ Status Management | Shortlist, Interview, or Reject candidates |
| 📥 Resume Download | Download original resume files |

### For Candidates
| Feature | Description |
|---------|-------------|
| 🔍 Job Search | Browse and search available positions |
| 📄 Easy Apply | Submit applications with resume upload |
| 📋 Application Form | Enter personal, education, and experience details |
| 📎 File Upload | Support for PDF, DOC, DOCX formats |

---

## 🛠️ Technology Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 14** | React framework with App Router |
| **TypeScript** | Type-safe JavaScript |
| **Tailwind CSS** | Utility-first CSS framework |
| **shadcn/ui** | Modern UI component library |

### Backend
| Technology | Purpose |
|------------|---------|
| **Flask 3.0** | Python web framework |
| **Flask-CORS** | Cross-origin resource sharing |
| **PyMongo** | MongoDB driver for Python |
| **PyPDF2** | PDF text extraction |
| **python-docx** | DOCX text extraction |
| **Werkzeug** | Password hashing & file handling |

### Database
| Technology | Purpose |
|------------|---------|
| **MongoDB** | NoSQL document database |
| **Collections** | users, jobs, applications, sessions |

### Resume Parsing Libraries
| Library | Purpose |
|---------|---------|
| **PyPDF2** | Extract text from PDF resumes |
| **python-docx** | Extract text from Word documents |

---

## 🔄 Data Flow

### 1. Job Posting Flow
```
HR Login → Create Job Form → POST /api/jobs → MongoDB (jobs collection)
                ↓
         Upload JD File → Parse Requirements → Store in Database
```

### 2. Application Submission Flow
```
Candidate → View Job Details → Fill Application Form
                ↓
         Upload Resume (PDF/DOCX)
                ↓
         POST /api/jobs/{id}/apply
                ↓
    ┌─────────────────────────────────────┐
    │        Resume Processing            │
    │  1. Save file to server             │
    │  2. Extract text (PyPDF2/docx)      │
    │  3. Extract skills from text        │
    │  4. Calculate scores                │
    │  5. Generate AI analysis            │
    └─────────────────────────────────────┘
                ↓
         Store in MongoDB (applications collection)
```

### 3. Review Flow
```
HR Login → Select Job → GET /api/applications?job_id={id}
                ↓
         Display Ranked Candidates (sorted by score)
                ↓
         View Details → Update Status (shortlist/reject/interview)
                ↓
         PUT /api/applications/{id}/status → Update MongoDB
```

---

## 🧮 Scoring Algorithm

The system uses a **weighted scoring model** to evaluate resumes:

### Score Components

| Component | Weight | Description |
|-----------|--------|-------------|
| **Skill Match** | 40% | Match between resume skills and job requirements |
| **Experience** | 35% | Years of relevant experience |
| **Education** | 25% | College tier and degree level |

### Overall Score Formula
```
Overall Score = (Skill Score × 0.40) + (Experience Score × 0.35) + (Education Score × 0.25)
```

### Skill Matching Algorithm
```python
def calculate_skill_match(resume_skills, job_requirements):
    matched = count skills present in both lists
    base_score = (matched / total_requirements) × 100
    return min(100, base_score + random_variance)
```

**Skill Extraction** - Keywords are extracted from resume text using pattern matching against a predefined skill database:
- Programming: Python, JavaScript, React, Node.js, Java, etc.
- Databases: SQL, MongoDB, PostgreSQL, Redis
- Cloud: AWS, Azure, GCP, Docker, Kubernetes
- Tools: Git, Jira, Figma, etc.

### Experience Scoring
```python
Experience Score:
  - 3+ years → 85-98 points
  - 1-3 years → 70-85 points
  - 0-1 years → 55-70 points
```

### Education Scoring
```python
Education Score:
  - Premium colleges (IIT, IISC, BITS, NIT) → Base: 90
  - Other colleges → Base: 70
  - Advanced degree bonus (M.Tech, PhD, MBA) → +5 points
```

### AI Analysis Generation
Based on scores, the system generates natural language feedback:
- **Overall ≥ 90**: "Exceptional candidate with excellent qualifications"
- **Overall ≥ 80**: "Strong candidate with good potential"
- **Overall ≥ 70**: "Decent candidate worth considering"
- **Overall < 70**: "Candidate may need additional evaluation"

---

## 🚀 Installation

### Prerequisites
- Node.js 18+ 
- Python 3.10+
- MongoDB (local installation)

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/hr-resume-portal.git
cd hr-resume-portal
```

### 2. Backend Setup
```bash
cd Backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB (in separate terminal)
mongod

# Run the backend server
python app.py
```

Backend will run on: `http://localhost:5000`

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will run on: `http://localhost:3000`

### 4. Default Credentials
```
Email: hr@company.com
Password: hr123
```

---

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | HR login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/verify` | Verify token |

### Job Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | Get all jobs |
| GET | `/api/jobs/{id}` | Get job details |
| POST | `/api/jobs` | Create new job (HR only) |
| PUT | `/api/jobs/{id}` | Update job (HR only) |

### Application Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/applications` | Get applications |
| GET | `/api/applications/{id}` | Get application details |
| POST | `/api/jobs/{id}/apply` | Submit application |
| PUT | `/api/applications/{id}/status` | Update status (HR only) |

### Request/Response Examples

**Login Request:**
```json
POST /api/auth/login
{
  "email": "hr@company.com",
  "password": "hr123"
}
```

**Login Response:**
```json
{
  "success": true,
  "token": "uuid-token-here",
  "user": {
    "id": "...",
    "email": "hr@company.com",
    "name": "HR Admin",
    "role": "admin"
  }
}
```

**Submit Application:**
```
POST /api/jobs/{job_id}/apply
Content-Type: multipart/form-data

student_name: "John Doe"
email: "john@example.com"
phone: "+91 9876543210"
college: "IIT Delhi"
degree: "B.Tech CSE"
graduation_year: "2025"
experience: "2 years"
resume: [file]
```

---

## 📸 Screenshots

### Home Page - Job Listings
- Browse all available job openings
- Search and filter by department/status
- View applicant count per job

### Job Application Page
- View detailed job description
- Fill application form
- Upload resume (PDF/DOCX)

### HR Review Dashboard
- View all candidates ranked by score
- Score breakdown (skill, experience, education)
- One-click status updates
- Download resumes

---

## 🔮 Future Enhancements

1. **Advanced NLP** - Integrate BERT/GPT models for semantic skill matching
2. **Interview Scheduling** - Calendar integration for scheduling
3. **Email Notifications** - Automated status update emails
4. **Analytics Dashboard** - Hiring funnel visualization
5. **Multi-tenant Support** - Multiple company accounts
6. **Resume Parser API** - Integration with professional parsing services

---

## 👨‍💻 Author

**Final Year Project**  
Bachelor of Technology  
Year: 2025

---

## 📄 License

This project is for educational purposes as part of a final year project submission.

---

## 🙏 Acknowledgments

- Next.js Documentation
- Flask Documentation
- MongoDB University
- shadcn/ui Components
