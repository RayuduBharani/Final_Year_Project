from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient
import os
import uuid
import random

# Optional: For PDF text extraction
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("PyPDF2 not installed. PDF text extraction disabled.")

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    print("python-docx not installed. DOCX text extraction disabled.")

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'resumes'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'job_descriptions'), exist_ok=True)

# ============== MongoDB Connection ==============
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.environ.get('DB_NAME', 'hr_resume_portal')

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Collections
    users_collection = db['users']
    jobs_collection = db['jobs']
    applications_collection = db['applications']
    sessions_collection = db['sessions']
    
    # Create indexes for better performance
    users_collection.create_index('email', unique=True)
    jobs_collection.create_index('status')
    jobs_collection.create_index('department')
    applications_collection.create_index('job_id')
    applications_collection.create_index('email')
    sessions_collection.create_index('token', unique=True)
    sessions_collection.create_index('expires_at', expireAfterSeconds=0)
    
    # Test connection
    client.admin.command('ping')
    MONGO_CONNECTED = True
    print(f"✅ Connected to MongoDB: {MONGO_URI}")
    print(f"📁 Database: {DB_NAME}")
except Exception as e:
    MONGO_CONNECTED = False
    print(f"❌ MongoDB connection failed: {e}")
    print("⚠️  Make sure MongoDB is running on localhost:27017")


# ============== Helper Functions ==============

def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable dict"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == '_id':
                result['id'] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    return doc


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_session_token():
    return str(uuid.uuid4())


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    if not PDF_SUPPORT:
        return ""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    if not DOCX_SUPPORT:
        return ""
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
        return ""


def extract_skills_from_text(text):
    """Extract skills from resume text using keyword matching"""
    common_skills = [
        "python", "javascript", "typescript", "react", "angular", "vue", "node.js",
        "java", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
        "git", "github", "gitlab", "bitbucket", "jira", "confluence",
        "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
        "pandas", "numpy", "scikit-learn", "data analysis", "statistics",
        "html", "css", "sass", "tailwind", "bootstrap", "figma", "sketch",
        "agile", "scrum", "kanban", "ci/cd", "devops", "rest api", "graphql"
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return found_skills[:10]


def calculate_skill_match(resume_skills, job_requirements):
    """Calculate skill match percentage"""
    if not job_requirements:
        return 70
    
    resume_skills_lower = [s.lower() for s in resume_skills]
    job_req_lower = [r.lower() for r in job_requirements]
    
    matched = sum(1 for req in job_req_lower if any(req in skill or skill in req for skill in resume_skills_lower))
    base_score = int((matched / len(job_requirements)) * 100)
    return min(100, base_score + random.randint(5, 15))


def calculate_experience_score(experience_text, job_experience_req):
    """Calculate experience score based on years mentioned"""
    years_mentioned = 0
    words = experience_text.lower().replace('-', ' ').split()
    for i, word in enumerate(words):
        if word.isdigit():
            years_mentioned = max(years_mentioned, int(word))
        elif 'year' in word and i > 0 and words[i-1].isdigit():
            years_mentioned = max(years_mentioned, int(words[i-1]))
    
    if years_mentioned >= 3:
        return random.randint(85, 98)
    elif years_mentioned >= 1:
        return random.randint(70, 85)
    else:
        return random.randint(55, 70)


def calculate_education_score(college, degree):
    """Calculate education score"""
    premium_colleges = ["iit", "iisc", "bits", "nit", "iiit", "isb", "iim", "nid"]
    college_lower = college.lower()
    
    base_score = 70
    if any(pc in college_lower for pc in premium_colleges):
        base_score = 90
    
    degree_lower = degree.lower()
    if "m.tech" in degree_lower or "msc" in degree_lower or "phd" in degree_lower or "mba" in degree_lower:
        base_score += 5
    elif "mdes" in degree_lower or "m.des" in degree_lower:
        base_score += 5
    
    return min(100, base_score + random.randint(0, 8))


def score_resume(application, job):
    """Calculate all scores for a resume"""
    skill_score = calculate_skill_match(application.get('skills', []), job.get('requirements', []))
    experience_score = calculate_experience_score(application.get('experience', ''), job.get('experience', ''))
    education_score = calculate_education_score(application.get('college', ''), application.get('degree', ''))
    
    overall = int(skill_score * 0.4 + experience_score * 0.35 + education_score * 0.25)
    
    return {
        'overall_score': overall,
        'skill_match_score': skill_score,
        'experience_score': experience_score,
        'education_score': education_score,
        'ai_analysis': generate_ai_analysis(overall, skill_score, experience_score, education_score)
    }


def generate_ai_analysis(overall, skill, exp, edu):
    """Generate AI analysis text"""
    analyses = []
    
    if overall >= 90:
        analyses.append("Exceptional candidate with excellent qualifications.")
    elif overall >= 80:
        analyses.append("Strong candidate with good potential.")
    elif overall >= 70:
        analyses.append("Decent candidate worth considering.")
    else:
        analyses.append("Candidate may need additional evaluation.")
    
    if skill >= 85:
        analyses.append("Skills align well with job requirements.")
    elif skill >= 70:
        analyses.append("Most required skills are present.")
    else:
        analyses.append("Some skill gaps identified.")
    
    if exp >= 85:
        analyses.append("Relevant experience demonstrated.")
    elif exp >= 70:
        analyses.append("Adequate experience for the role.")
    else:
        analyses.append("Limited relevant experience.")
    
    if edu >= 90:
        analyses.append("Strong educational background from top institution.")
    elif edu >= 80:
        analyses.append("Good educational credentials.")
    
    return " ".join(analyses)


def get_authenticated_user(request):
    """Get authenticated user from request header"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None
    
    session = sessions_collection.find_one({'token': token})
    if not session:
        return None
    
    if datetime.now() > session['expires_at']:
        sessions_collection.delete_one({'token': token})
        return None
    
    user = users_collection.find_one({'email': session['email']})
    return serialize_doc(user)


def init_default_data():
    """Initialize database with default data if empty"""
    # Create default HR user if not exists
    if users_collection.count_documents({}) == 0:
        users_collection.insert_one({
            'email': 'hr@company.com',
            'password': generate_password_hash('hr123'),
            'name': 'HR Admin',
            'role': 'admin',
            'created_at': datetime.now()
        })
        print("✅ Created default HR user: hr@company.com / hr123")
    
    # Create sample jobs if not exists
    if jobs_collection.count_documents({}) == 0:
        sample_jobs = [
            {
                "title": "Frontend Developer",
                "department": "Engineering",
                "description": "We are looking for a skilled frontend developer with experience in React and TypeScript to build modern web applications.",
                "requirements": ["React", "TypeScript", "CSS", "JavaScript", "Git"],
                "responsibilities": [
                    "Develop and maintain web applications using React and TypeScript",
                    "Collaborate with designers to implement UI/UX designs",
                    "Write clean, maintainable, and efficient code"
                ],
                "location": "Bangalore, India",
                "type": "Full-time",
                "experience": "3-5 years",
                "salary": "₹15-25 LPA",
                "created_at": datetime.now() - timedelta(days=4),
                "deadline": (datetime.now() + timedelta(days=16)).strftime('%Y-%m-%d'),
                "status": "active",
                "created_by": "hr1"
            },
            {
                "title": "Data Scientist",
                "department": "Analytics",
                "description": "Seeking an experienced data scientist to work on machine learning models and data analysis.",
                "requirements": ["Python", "Machine Learning", "SQL", "TensorFlow", "Statistics"],
                "responsibilities": [
                    "Build and deploy machine learning models",
                    "Analyze large datasets to extract insights",
                    "Collaborate with engineering teams"
                ],
                "location": "Hyderabad, India",
                "type": "Full-time",
                "experience": "2-4 years",
                "salary": "₹18-30 LPA",
                "created_at": datetime.now() - timedelta(days=9),
                "deadline": (datetime.now() + timedelta(days=11)).strftime('%Y-%m-%d'),
                "status": "active",
                "created_by": "hr1"
            },
            {
                "title": "Product Manager",
                "department": "Product",
                "description": "Looking for a product manager to lead product development and roadmap planning.",
                "requirements": ["Agile", "Roadmapping", "Stakeholder Management", "Analytics"],
                "responsibilities": [
                    "Define and communicate product vision and strategy",
                    "Create and maintain product roadmap",
                    "Work with cross-functional teams"
                ],
                "location": "Mumbai, India",
                "type": "Full-time",
                "experience": "5-8 years",
                "salary": "₹25-40 LPA",
                "created_at": datetime.now() - timedelta(days=14),
                "deadline": (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                "status": "closed",
                "created_by": "hr1"
            },
            {
                "title": "Backend Developer",
                "department": "Engineering",
                "description": "Experienced backend developer needed for building scalable APIs and microservices.",
                "requirements": ["Node.js", "Python", "PostgreSQL", "Docker", "AWS"],
                "responsibilities": [
                    "Design and implement RESTful APIs",
                    "Build and maintain microservices architecture",
                    "Optimize database queries and performance"
                ],
                "location": "Pune, India",
                "type": "Full-time",
                "experience": "3-6 years",
                "salary": "₹18-28 LPA",
                "created_at": datetime.now() - timedelta(days=7),
                "deadline": (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
                "status": "active",
                "created_by": "hr1"
            },
            {
                "title": "UX Designer",
                "department": "Design",
                "description": "Creative UX designer to create intuitive user experiences and design systems.",
                "requirements": ["Figma", "User Research", "Prototyping", "Design Systems"],
                "responsibilities": [
                    "Conduct user research and usability testing",
                    "Create wireframes, prototypes, and designs",
                    "Develop and maintain design systems"
                ],
                "location": "Delhi, India",
                "type": "Full-time",
                "experience": "2-4 years",
                "salary": "₹12-20 LPA",
                "created_at": datetime.now() - timedelta(days=11),
                "deadline": (datetime.now() + timedelta(days=13)).strftime('%Y-%m-%d'),
                "status": "active",
                "created_by": "hr1"
            }
        ]
        jobs_collection.insert_many(sample_jobs)
        print(f"✅ Created {len(sample_jobs)} sample jobs")
    
    # Create sample applications if not exists
    if applications_collection.count_documents({}) == 0:
        jobs = list(jobs_collection.find())
        if jobs:
            sample_applications = [
                {
                    "job_id": str(jobs[0]['_id']),
                    "student_name": "Rahul Sharma",
                    "email": "rahul.sharma@email.com",
                    "phone": "+91 98765 43210",
                    "college": "IIT Delhi",
                    "degree": "B.Tech Computer Science",
                    "graduation_year": "2025",
                    "experience": "2 years at TechCorp as Frontend Developer",
                    "cover_letter": "I am excited to apply for this position...",
                    "skills": ["React", "TypeScript", "Node.js", "CSS", "Git", "JavaScript"],
                    "resume_file": None,
                    "submitted_at": datetime.now() - timedelta(days=1),
                    "status": "shortlisted",
                    "overall_score": 92,
                    "skill_match_score": 95,
                    "experience_score": 88,
                    "education_score": 94,
                    "ai_analysis": "Strong candidate with excellent skill match."
                },
                {
                    "job_id": str(jobs[0]['_id']),
                    "student_name": "Priya Patel",
                    "email": "priya.patel@email.com",
                    "phone": "+91 87654 32109",
                    "college": "NIT Trichy",
                    "degree": "B.Tech IT",
                    "graduation_year": "2025",
                    "experience": "1 year internship at StartupXYZ",
                    "cover_letter": "As a passionate frontend developer...",
                    "skills": ["React", "JavaScript", "HTML", "CSS", "Bootstrap"],
                    "resume_file": None,
                    "submitted_at": datetime.now() - timedelta(days=2),
                    "status": "pending",
                    "overall_score": 78,
                    "skill_match_score": 72,
                    "experience_score": 75,
                    "education_score": 88,
                    "ai_analysis": "Good foundational skills. Could benefit from more TypeScript experience."
                },
                {
                    "job_id": str(jobs[0]['_id']),
                    "student_name": "Vikram Singh",
                    "email": "vikram.singh@email.com",
                    "phone": "+91 54321 09876",
                    "college": "IIT Bombay",
                    "degree": "M.Tech Computer Science",
                    "graduation_year": "2025",
                    "experience": "4 years at Google as Software Engineer",
                    "cover_letter": "With my experience at Google...",
                    "skills": ["React", "TypeScript", "Next.js", "GraphQL", "Git", "Docker"],
                    "resume_file": None,
                    "submitted_at": datetime.now() - timedelta(days=5),
                    "status": "shortlisted",
                    "overall_score": 96,
                    "skill_match_score": 98,
                    "experience_score": 95,
                    "education_score": 96,
                    "ai_analysis": "Exceptional candidate with top-tier experience."
                },
                {
                    "job_id": str(jobs[1]['_id']) if len(jobs) > 1 else str(jobs[0]['_id']),
                    "student_name": "Ananya Gupta",
                    "email": "ananya.gupta@email.com",
                    "phone": "+91 98761 23456",
                    "college": "IISc Bangalore",
                    "degree": "M.Sc Data Science",
                    "graduation_year": "2025",
                    "experience": "2 years at Analytics Corp",
                    "cover_letter": "I am passionate about data science...",
                    "skills": ["Python", "TensorFlow", "SQL", "Machine Learning", "Deep Learning"],
                    "resume_file": None,
                    "submitted_at": datetime.now() - timedelta(days=2),
                    "status": "shortlisted",
                    "overall_score": 94,
                    "skill_match_score": 96,
                    "experience_score": 90,
                    "education_score": 95,
                    "ai_analysis": "Outstanding data science background."
                },
                {
                    "job_id": str(jobs[3]['_id']) if len(jobs) > 3 else str(jobs[0]['_id']),
                    "student_name": "Arjun Nair",
                    "email": "arjun.nair@email.com",
                    "phone": "+91 65431 23456",
                    "college": "NIT Karnataka",
                    "degree": "B.Tech Computer Science",
                    "graduation_year": "2024",
                    "experience": "3 years at Flipkart as Backend Engineer",
                    "cover_letter": "I specialize in building scalable backend systems...",
                    "skills": ["Node.js", "Python", "PostgreSQL", "Docker", "AWS", "Redis"],
                    "resume_file": None,
                    "submitted_at": datetime.now() - timedelta(days=4),
                    "status": "pending",
                    "overall_score": 91,
                    "skill_match_score": 95,
                    "experience_score": 90,
                    "education_score": 88,
                    "ai_analysis": "Strong backend skills with relevant experience."
                }
            ]
            applications_collection.insert_many(sample_applications)
            print(f"✅ Created {len(sample_applications)} sample applications")


# ============== Authentication Routes ==============

@app.route('/api/auth/login', methods=['POST'])
def login():
    """HR Login endpoint"""
    data = request.get_json()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    
    user = users_collection.find_one({'email': email})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    
    # Create session token
    token = generate_session_token()
    sessions_collection.insert_one({
        'token': token,
        'user_id': str(user['_id']),
        'email': email,
        'expires_at': datetime.now() + timedelta(hours=24)
    })
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'name': user['name'],
            'role': user['role']
        }
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """HR Logout endpoint"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        sessions_collection.delete_one({'token': token})
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """Verify if session token is valid"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = sessions_collection.find_one({'token': token})
    
    if not session:
        return jsonify({'valid': False}), 401
    
    if datetime.now() > session['expires_at']:
        sessions_collection.delete_one({'token': token})
        return jsonify({'valid': False, 'message': 'Session expired'}), 401
    
    user = users_collection.find_one({'email': session['email']})
    return jsonify({
        'valid': True,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'name': user['name'],
            'role': user['role']
        }
    })


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new HR user"""
    data = request.get_json()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    
    if not email or not password or not name:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    
    if users_collection.find_one({'email': email}):
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    result = users_collection.insert_one({
        'email': email,
        'password': generate_password_hash(password),
        'name': name,
        'role': 'hr',
        'created_at': datetime.now()
    })
    
    return jsonify({'success': True, 'message': 'Registration successful', 'user_id': str(result.inserted_id)})


# ============== Jobs Routes ==============

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs with optional filters"""
    status = request.args.get('status')
    department = request.args.get('department')
    search = request.args.get('search', '').lower()
    
    # Build query
    query = {}
    if status and status != 'all':
        query['status'] = status
    if department and department != 'all':
        query['department'] = {'$regex': department, '$options': 'i'}
    if search:
        query['$or'] = [
            {'title': {'$regex': search, '$options': 'i'}},
            {'description': {'$regex': search, '$options': 'i'}}
        ]
    
    jobs = list(jobs_collection.find(query).sort('created_at', -1))
    jobs_list = []
    
    for job in jobs:
        job_data = serialize_doc(job)
        # Add applicant count
        job_data['applicants'] = applications_collection.count_documents({'job_id': str(job['_id'])})
        jobs_list.append(job_data)
    
    return jsonify({'success': True, 'jobs': jobs_list, 'total': len(jobs_list)})


@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get single job by ID"""
    try:
        job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid job ID'}), 400
    
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    
    job_data = serialize_doc(job)
    job_data['applicants'] = applications_collection.count_documents({'job_id': job_id})
    
    return jsonify({'success': True, 'job': job_data})


@app.route('/api/jobs', methods=['POST'])
def create_job():
    """Create a new job posting"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Handle both JSON and FormData
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json() or {}
    
    if not data.get('title') or not data.get('department'):
        return jsonify({'success': False, 'error': 'Title and department are required'}), 400
    
    requirements = data.get('requirements', [])
    if isinstance(requirements, str):
        requirements = [r.strip() for r in requirements.split(',') if r.strip()]
    
    responsibilities = data.get('responsibilities', [])
    if isinstance(responsibilities, str):
        responsibilities = [r.strip() for r in responsibilities.split('\n') if r.strip()]
    
    job = {
        'title': data['title'].strip(),
        'department': data['department'].strip(),
        'description': data.get('description', '').strip(),
        'requirements': requirements,
        'responsibilities': responsibilities,
        'location': data.get('location', 'Remote').strip(),
        'type': data.get('type', 'Full-time'),
        'experience': data.get('experience', 'Not specified'),
        'salary': data.get('salary', 'Competitive'),
        'created_at': datetime.now(),
        'deadline': data.get('deadline', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')),
        'status': data.get('status', 'active'),
        'created_by': user['id']
    }
    
    # Handle JD file upload if provided
    if 'jd_file' in request.files:
        jd_file = request.files['jd_file']
        if jd_file and jd_file.filename:
            filename = secure_filename(jd_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"jd_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
            jd_file.save(filepath)
            job['jd_file_path'] = filepath
    
    result = jobs_collection.insert_one(job)
    job['_id'] = result.inserted_id
    
    return jsonify({'success': True, 'message': 'Job created successfully', 'job': serialize_doc(job)}), 201


@app.route('/api/jobs/<job_id>', methods=['PUT'])
def update_job(job_id):
    """Update an existing job"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid job ID'}), 400
    
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    
    data = request.get_json()
    update_data = {}
    
    updatable_fields = ['title', 'department', 'description', 'requirements', 'responsibilities',
                        'location', 'type', 'experience', 'salary', 'deadline', 'status']
    
    for field in updatable_fields:
        if field in data:
            if field == 'requirements' and isinstance(data[field], str):
                update_data[field] = [r.strip() for r in data[field].split(',') if r.strip()]
            elif field == 'responsibilities' and isinstance(data[field], str):
                update_data[field] = [r.strip() for r in data[field].split('\n') if r.strip()]
            else:
                update_data[field] = data[field]
    
    if update_data:
        jobs_collection.update_one({'_id': ObjectId(job_id)}, {'$set': update_data})
    
    updated_job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    return jsonify({'success': True, 'message': 'Job updated successfully', 'job': serialize_doc(updated_job)})


@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        result = jobs_collection.delete_one({'_id': ObjectId(job_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid job ID'}), 400
    
    if result.deleted_count == 0:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    
    # Delete related applications
    applications_collection.delete_many({'job_id': job_id})
    
    return jsonify({'success': True, 'message': 'Job deleted successfully'})


@app.route('/api/jobs/<job_id>/close', methods=['PUT'])
def close_job(job_id):
    """Close a job posting"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        result = jobs_collection.update_one({'_id': ObjectId(job_id)}, {'$set': {'status': 'closed'}})
    except:
        return jsonify({'success': False, 'message': 'Invalid job ID'}), 400
    
    if result.matched_count == 0:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    
    job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    return jsonify({'success': True, 'message': 'Job closed successfully', 'job': serialize_doc(job)})


# ============== Applications Routes ==============

@app.route('/api/applications', methods=['GET'])
def get_applications():
    """Get applications with optional filters"""
    job_id = request.args.get('job_id')
    status = request.args.get('status')
    sort_by = request.args.get('sort_by', 'score')
    
    query = {}
    if job_id:
        query['job_id'] = job_id
    if status and status != 'all':
        query['status'] = status
    
    # Determine sort order
    sort_field = 'overall_score'
    sort_order = -1
    if sort_by == 'date':
        sort_field = 'submitted_at'
    elif sort_by == 'name':
        sort_field = 'student_name'
        sort_order = 1
    
    applications = list(applications_collection.find(query).sort(sort_field, sort_order))
    apps_list = serialize_doc(applications)
    
    # Calculate stats
    all_apps = list(applications_collection.find(query))
    stats = {
        'total': len(all_apps),
        'shortlisted': len([a for a in all_apps if a.get('status') == 'shortlisted']),
        'pending': len([a for a in all_apps if a.get('status') == 'pending']),
        'interviewed': len([a for a in all_apps if a.get('status') == 'interviewed']),
        'rejected': len([a for a in all_apps if a.get('status') == 'rejected'])
    }
    
    return jsonify({'success': True, 'applications': apps_list, 'stats': stats})


@app.route('/api/applications/<app_id>', methods=['GET'])
def get_application(app_id):
    """Get single application by ID"""
    try:
        application = applications_collection.find_one({'_id': ObjectId(app_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid application ID'}), 400
    
    if not application:
        return jsonify({'success': False, 'message': 'Application not found'}), 404
    
    # Get job details
    job = None
    if application.get('job_id'):
        try:
            job = jobs_collection.find_one({'_id': ObjectId(application['job_id'])})
            job = serialize_doc(job)
        except:
            pass
    
    return jsonify({'success': True, 'application': serialize_doc(application), 'job': job})


@app.route('/api/jobs/<job_id>/apply', methods=['POST'])
def submit_application(job_id):
    """Submit a job application"""
    try:
        job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid job ID'}), 400
    
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    
    if job['status'] != 'active':
        return jsonify({'success': False, 'message': 'This job is no longer accepting applications'}), 400
    
    # Handle form data
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = {
            'student_name': request.form.get('student_name', '') or request.form.get('fullName', ''),
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', ''),
            'college': request.form.get('college', ''),
            'degree': request.form.get('degree', ''),
            'graduation_year': request.form.get('graduation_year', '') or request.form.get('graduationYear', ''),
            'experience': request.form.get('experience', ''),
            'cover_letter': request.form.get('cover_letter', '') or request.form.get('coverLetter', ''),
            'skills': [s.strip() for s in request.form.get('skills', '').split(',') if s.strip()] if request.form.get('skills') else []
        }
        resume_file = request.files.get('resume')
    else:
        data = request.get_json() or {}
        resume_file = None
    
    # Validate - make college and degree optional
    if not data.get('student_name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    
    if not data.get('email'):
        return jsonify({'success': False, 'error': 'Email is required'}), 400
    
    if '@' not in data['email']:
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    # Check duplicate
    existing = applications_collection.find_one({
        'job_id': job_id,
        'email': {'$regex': f'^{data["email"]}$', '$options': 'i'}
    })
    if existing:
        return jsonify({'success': False, 'message': 'You have already applied for this job'}), 400
    
    # Handle file upload
    resume_filename = None
    extracted_skills = []
    
    if resume_file and allowed_file(resume_file.filename):
        original_filename = secure_filename(resume_file.filename)
        filename = f"{data['student_name'].replace(' ', '_')}_{job_id}_{uuid.uuid4().hex[:8]}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', filename)
        resume_file.save(file_path)
        resume_filename = filename
        
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        if file_ext == 'pdf':
            resume_text = extract_text_from_pdf(file_path)
        elif file_ext in ['doc', 'docx']:
            resume_text = extract_text_from_docx(file_path)
        else:
            resume_text = ""
        
        if resume_text:
            extracted_skills = extract_skills_from_text(resume_text)
    
    skills = data.get('skills', [])
    if not skills and extracted_skills:
        skills = extracted_skills
    if not skills:
        skills = random.sample(job.get('requirements', []), min(3, len(job.get('requirements', []))))
    
    application = {
        'job_id': job_id,
        'student_name': data['student_name'].strip(),
        'email': data['email'].lower().strip(),
        'phone': data.get('phone', '').strip(),
        'college': data['college'].strip(),
        'degree': data['degree'].strip(),
        'graduation_year': data.get('graduation_year', '').strip(),
        'experience': data.get('experience', '').strip(),
        'cover_letter': data.get('cover_letter', '').strip(),
        'skills': skills,
        'resume_file': resume_filename,
        'submitted_at': datetime.now(),
        'status': 'pending'
    }
    
    # Calculate scores
    scores = score_resume(application, serialize_doc(job))
    application.update(scores)
    
    result = applications_collection.insert_one(application)
    
    return jsonify({
        'success': True,
        'message': 'Application submitted successfully!',
        'application_id': str(result.inserted_id),
        'scores': {
            'overall': application['overall_score'],
            'skill_match': application['skill_match_score'],
            'experience': application['experience_score'],
            'education': application['education_score']
        }
    }), 201


@app.route('/api/applications/<app_id>/status', methods=['PUT'])
def update_application_status(app_id):
    """Update application status"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    new_status = data.get('status')
    
    valid_statuses = ['pending', 'shortlisted', 'rejected', 'interviewed']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': f'Invalid status. Must be: {", ".join(valid_statuses)}'}), 400
    
    try:
        result = applications_collection.update_one(
            {'_id': ObjectId(app_id)},
            {'$set': {'status': new_status}}
        )
    except:
        return jsonify({'success': False, 'message': 'Invalid application ID'}), 400
    
    if result.matched_count == 0:
        return jsonify({'success': False, 'message': 'Application not found'}), 404
    
    application = applications_collection.find_one({'_id': ObjectId(app_id)})
    return jsonify({
        'success': True,
        'message': f'Application status updated to {new_status}',
        'application': serialize_doc(application)
    })


@app.route('/api/applications/<app_id>/rescore', methods=['POST'])
def rescore_application(app_id):
    """Recalculate scores for an application"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        application = applications_collection.find_one({'_id': ObjectId(app_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid application ID'}), 400
    
    if not application:
        return jsonify({'success': False, 'message': 'Application not found'}), 404
    
    try:
        job = jobs_collection.find_one({'_id': ObjectId(application['job_id'])})
    except:
        return jsonify({'success': False, 'message': 'Associated job not found'}), 404
    
    scores = score_resume(serialize_doc(application), serialize_doc(job))
    applications_collection.update_one({'_id': ObjectId(app_id)}, {'$set': scores})
    
    updated_app = applications_collection.find_one({'_id': ObjectId(app_id)})
    return jsonify({
        'success': True,
        'message': 'Scores recalculated successfully',
        'application': serialize_doc(updated_app)
    })


@app.route('/api/applications/<app_id>/resume', methods=['GET'])
def download_resume(app_id):
    """Download resume file"""
    try:
        application = applications_collection.find_one({'_id': ObjectId(app_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid application ID'}), 400
    
    if not application:
        return jsonify({'success': False, 'message': 'Application not found'}), 404
    
    if not application.get('resume_file'):
        return jsonify({'success': False, 'message': 'No resume file attached'}), 404
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', application['resume_file'])
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Resume file not found on server'}), 404
    
    return send_file(file_path, as_attachment=True)


@app.route('/api/applications/<app_id>', methods=['DELETE'])
def delete_application(app_id):
    """Delete an application"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        application = applications_collection.find_one({'_id': ObjectId(app_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid application ID'}), 400
    
    if not application:
        return jsonify({'success': False, 'message': 'Application not found'}), 404
    
    # Delete resume file
    if application.get('resume_file'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', application['resume_file'])
        if os.path.exists(file_path):
            os.remove(file_path)
    
    applications_collection.delete_one({'_id': ObjectId(app_id)})
    return jsonify({'success': True, 'message': 'Application deleted successfully'})


# ============== Analytics Routes ==============

@app.route('/api/analytics/overview', methods=['GET'])
def get_analytics_overview():
    """Get dashboard analytics overview"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    total_jobs = jobs_collection.count_documents({})
    active_jobs = jobs_collection.count_documents({'status': 'active'})
    total_applications = applications_collection.count_documents({})
    shortlisted = applications_collection.count_documents({'status': 'shortlisted'})
    pending = applications_collection.count_documents({'status': 'pending'})
    interviewed = applications_collection.count_documents({'status': 'interviewed'})
    rejected = applications_collection.count_documents({'status': 'rejected'})
    
    # Applications by department
    pipeline = [
        {'$lookup': {
            'from': 'jobs',
            'let': {'job_id': {'$toObjectId': '$job_id'}},
            'pipeline': [{'$match': {'$expr': {'$eq': ['$_id', '$$job_id']}}}],
            'as': 'job'
        }},
        {'$unwind': {'path': '$job', 'preserveNullAndEmptyArrays': True}},
        {'$group': {'_id': '$job.department', 'count': {'$sum': 1}}},
        {'$match': {'_id': {'$ne': None}}}
    ]
    dept_stats = {doc['_id']: doc['count'] for doc in applications_collection.aggregate(pipeline)}
    
    # Average score
    avg_pipeline = [
        {'$match': {'overall_score': {'$exists': True}}},
        {'$group': {'_id': None, 'avg_score': {'$avg': '$overall_score'}}}
    ]
    avg_result = list(applications_collection.aggregate(avg_pipeline))
    avg_score = round(avg_result[0]['avg_score'], 1) if avg_result else 0
    
    # Top candidates
    top_candidates = list(applications_collection.find({'overall_score': {'$exists': True}}).sort('overall_score', -1).limit(5))
    
    return jsonify({
        'success': True,
        'analytics': {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'closed_jobs': total_jobs - active_jobs,
            'total_applications': total_applications,
            'shortlisted': shortlisted,
            'pending': pending,
            'interviewed': interviewed,
            'rejected': rejected,
            'average_score': avg_score,
            'applications_by_department': dept_stats,
            'top_candidates': [{
                'id': str(c['_id']),
                'name': c['student_name'],
                'job_id': c['job_id'],
                'score': c['overall_score'],
                'status': c['status']
            } for c in top_candidates]
        }
    })


@app.route('/api/analytics/job/<job_id>', methods=['GET'])
def get_job_analytics(job_id):
    """Get analytics for a specific job"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid job ID'}), 400
    
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    
    job_apps = list(applications_collection.find({'job_id': job_id}))
    
    # Score distribution
    score_ranges = {
        '90-100': len([a for a in job_apps if a.get('overall_score', 0) >= 90]),
        '80-89': len([a for a in job_apps if 80 <= a.get('overall_score', 0) < 90]),
        '70-79': len([a for a in job_apps if 70 <= a.get('overall_score', 0) < 80]),
        '60-69': len([a for a in job_apps if 60 <= a.get('overall_score', 0) < 70]),
        'Below 60': len([a for a in job_apps if a.get('overall_score', 0) < 60])
    }
    
    avg_score = round(sum(a.get('overall_score', 0) for a in job_apps) / len(job_apps), 1) if job_apps else 0
    
    analytics = {
        'job': serialize_doc(job),
        'total_applicants': len(job_apps),
        'shortlisted': len([a for a in job_apps if a['status'] == 'shortlisted']),
        'pending': len([a for a in job_apps if a['status'] == 'pending']),
        'interviewed': len([a for a in job_apps if a['status'] == 'interviewed']),
        'rejected': len([a for a in job_apps if a['status'] == 'rejected']),
        'average_score': avg_score,
        'score_distribution': score_ranges,
        'top_candidates': sorted(
            [{
                'id': str(a['_id']),
                'name': a['student_name'],
                'score': a.get('overall_score', 0),
                'status': a['status'],
                'college': a['college']
            } for a in job_apps],
            key=lambda x: x['score'],
            reverse=True
        )[:10]
    }
    
    return jsonify({'success': True, 'analytics': analytics})


# ============== Departments Route ==============

@app.route('/api/departments', methods=['GET'])
def get_departments():
    """Get list of unique departments"""
    departments = jobs_collection.distinct('department')
    departments.sort()
    return jsonify({'success': True, 'departments': departments})


# ============== Health Check ==============

@app.route('/', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'HR Resume Review Backend API is running!',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'database': 'MongoDB',
        'mongo_connected': MONGO_CONNECTED,
        'pdf_support': PDF_SUPPORT,
        'docx_support': DOCX_SUPPORT,
        'stats': {
            'total_jobs': jobs_collection.count_documents({}) if MONGO_CONNECTED else 0,
            'total_applications': applications_collection.count_documents({}) if MONGO_CONNECTED else 0
        }
    })


# ============== Error Handlers ==============

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500


@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'success': False, 'message': 'File too large. Maximum size is 16MB'}), 413


# ============== Run Server ==============

if __name__ == '__main__':
    print("\n" + "="*65)
    print("🚀  HR Resume Review Backend Server (MongoDB)")
    print("="*65)
    print(f"\n📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"🗄️  MongoDB URI: {MONGO_URI}")
    print(f"📦 Database: {DB_NAME}")
    print(f"🔌 MongoDB Connected: {'✅ Yes' if MONGO_CONNECTED else '❌ No'}")
    print(f"📄 PDF Support: {'✅ Enabled' if PDF_SUPPORT else '❌ Disabled'}")
    print(f"📝 DOCX Support: {'✅ Enabled' if DOCX_SUPPORT else '❌ Disabled'}")
    
    if MONGO_CONNECTED:
        # Initialize default data
        init_default_data()
    
    print("\n" + "-"*65)
    print("📌 API Endpoints:")
    print("-"*65)
    print("\n🔐 Authentication:")
    print("   POST   /api/auth/login     - Login with email/password")
    print("   POST   /api/auth/logout    - Logout and invalidate session")
    print("   POST   /api/auth/register  - Register new HR user")
    print("   GET    /api/auth/verify    - Verify session token")
    print("\n💼 Jobs:")
    print("   GET    /api/jobs           - List all jobs")
    print("   POST   /api/jobs           - Create new job [Auth]")
    print("   GET    /api/jobs/<id>      - Get job details")
    print("   PUT    /api/jobs/<id>      - Update job [Auth]")
    print("   DELETE /api/jobs/<id>      - Delete job [Auth]")
    print("\n📝 Applications:")
    print("   GET    /api/applications         - List applications")
    print("   POST   /api/jobs/<id>/apply      - Submit application")
    print("   PUT    /api/applications/<id>/status - Update status [Auth]")
    print("\n📊 Analytics:")
    print("   GET    /api/analytics/overview   - Dashboard overview [Auth]")
    print("   GET    /api/analytics/job/<id>   - Job analytics [Auth]")
    print("\n" + "-"*65)
    print("🔑 Default HR Login Credentials:")
    print("   Email:    hr@company.com")
    print("   Password: hr123")
    print("="*65 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
