"""
Real ATS (Applicant Tracking System) Scoring Module
Implements industry-standard ATS scoring based on:
1. Keyword matching with JD (exact + semantic)
2. Skills alignment scoring
3. Experience level matching
4. Education relevance
5. Resume formatting & structure analysis
6. Keyword density and placement
7. Action verbs and achievements detection
"""

import re
import math
from collections import Counter
from difflib import SequenceMatcher


# ============== SKILL CATEGORIES ==============
TECHNICAL_SKILLS = {
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    "objective-c", "dart", "lua", "haskell", "elixir", "clojure", "groovy",
    
    # Frontend
    "react", "reactjs", "react.js", "angular", "angularjs", "vue", "vuejs", "vue.js",
    "next.js", "nextjs", "nuxt", "nuxt.js", "svelte", "ember", "backbone",
    "html", "html5", "css", "css3", "sass", "scss", "less", "tailwind", "tailwindcss",
    "bootstrap", "material-ui", "mui", "chakra", "styled-components", "webpack",
    "vite", "parcel", "rollup", "babel", "jquery",
    
    # Backend
    "node.js", "nodejs", "express", "express.js", "nestjs", "fastify", "koa",
    "django", "flask", "fastapi", "spring", "spring boot", "springboot",
    ".net", "asp.net", "rails", "ruby on rails", "laravel", "symfony",
    "gin", "echo", "fiber", "phoenix", "actix",
    
    # Databases
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "firebase", "firestore", "sqlite", "oracle",
    "mariadb", "couchdb", "neo4j", "graphql", "prisma", "sequelize", "mongoose",
    "typeorm", "sqlalchemy", "hibernate",
    
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud", "digitalocean",
    "heroku", "vercel", "netlify", "cloudflare", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "puppet", "chef", "jenkins", "gitlab ci", "github actions",
    "circleci", "travis ci", "argo", "helm", "istio", "prometheus", "grafana",
    "datadog", "splunk", "elk", "logstash", "kibana", "nginx", "apache",
    
    # AI/ML/Data
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
    "scikit-learn", "sklearn", "pandas", "numpy", "scipy", "matplotlib",
    "seaborn", "plotly", "jupyter", "nlp", "natural language processing",
    "computer vision", "opencv", "neural networks", "cnn", "rnn", "lstm",
    "transformer", "bert", "gpt", "llm", "langchain", "hugging face",
    "data science", "data analysis", "data engineering", "etl", "airflow",
    "spark", "hadoop", "kafka", "flink", "dbt", "snowflake", "databricks",
    "tableau", "power bi", "looker", "metabase",
    
    # Mobile
    "ios", "android", "react native", "flutter", "xamarin", "ionic",
    "swift ui", "swiftui", "jetpack compose", "kotlin multiplatform",
    
    # Tools & Version Control
    "git", "github", "gitlab", "bitbucket", "svn", "mercurial",
    "jira", "confluence", "trello", "asana", "notion", "slack",
    "figma", "sketch", "adobe xd", "invision", "zeplin",
    
    # Testing
    "jest", "mocha", "chai", "cypress", "selenium", "playwright", "puppeteer",
    "pytest", "unittest", "rspec", "junit", "testng", "postman", "insomnia",
    "tdd", "bdd", "unit testing", "integration testing", "e2e testing",
    
    # Architecture & Concepts
    "microservices", "rest", "rest api", "restful", "api", "graphql",
    "grpc", "websocket", "oauth", "jwt", "saml", "sso", "rbac",
    "ci/cd", "agile", "scrum", "kanban", "devops", "devsecops",
    "solid", "design patterns", "mvc", "mvvm", "clean architecture",
    "domain driven design", "ddd", "event sourcing", "cqrs",
    "serverless", "lambda", "cloud functions", "edge computing",
}

SOFT_SKILLS = {
    "leadership", "communication", "teamwork", "problem solving", "problem-solving",
    "critical thinking", "analytical", "creativity", "innovation", "adaptability",
    "time management", "project management", "stakeholder management",
    "presentation", "negotiation", "conflict resolution", "decision making",
    "mentoring", "coaching", "collaboration", "interpersonal", "attention to detail",
    "self-motivated", "proactive", "strategic thinking", "planning", "organization",
}

ACTION_VERBS = {
    "achieved", "accomplished", "administered", "analyzed", "architected", "automated",
    "built", "collaborated", "conceptualized", "conducted", "consolidated", "contributed",
    "created", "customized", "debugged", "delivered", "deployed", "designed", "developed",
    "directed", "documented", "drove", "enhanced", "established", "evaluated", "executed",
    "expanded", "facilitated", "founded", "generated", "grew", "headed", "identified",
    "implemented", "improved", "increased", "initiated", "innovated", "integrated",
    "launched", "led", "leveraged", "maintained", "managed", "mentored", "migrated",
    "modernized", "monitored", "negotiated", "optimized", "orchestrated", "organized",
    "oversaw", "partnered", "performed", "pioneered", "planned", "presented", "prioritized",
    "produced", "programmed", "proposed", "provided", "published", "reduced", "refactored",
    "refined", "resolved", "restructured", "reviewed", "revitalized", "scaled", "secured",
    "simplified", "spearheaded", "standardized", "streamlined", "strengthened", "supervised",
    "supported", "surpassed", "tested", "trained", "transformed", "troubleshot", "unified",
    "upgraded", "utilized", "validated", "visualized",
}

QUANTIFIABLE_PATTERNS = [
    r'\d+%', r'\$[\d,]+[KMB]?', r'[\d,]+\s*users?', r'[\d,]+\s*customers?',
    r'[\d,]+\s*clients?', r'[\d,]+\s*employees?', r'[\d,]+\s*team\s*members?',
    r'increased\s*by\s*\d+', r'reduced\s*by\s*\d+', r'improved\s*by\s*\d+',
    r'saved\s*\$?[\d,]+', r'\d+x\s*(?:faster|improvement|growth)',
    r'top\s*\d+%?', r'#\d+', r'rank(?:ed)?\s*\d+',
]


def preprocess_text(text):
    """Clean and normalize text for analysis"""
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove special characters but keep spaces and alphanumerics
    text = re.sub(r'[^\w\s\-\+\#\.]', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text):
    """Tokenize text into words and n-grams"""
    words = text.split()
    tokens = set(words)
    
    # Add bigrams for compound skills
    for i in range(len(words) - 1):
        tokens.add(f"{words[i]} {words[i+1]}")
    
    # Add trigrams
    for i in range(len(words) - 2):
        tokens.add(f"{words[i]} {words[i+1]} {words[i+2]}")
    
    return tokens


def extract_skills_from_text(text):
    """Extract technical and soft skills from text using comprehensive matching"""
    if not text:
        return []
    
    text_lower = preprocess_text(text)
    tokens = tokenize(text_lower)
    
    found_skills = set()
    
    # Check for technical skills
    for skill in TECHNICAL_SKILLS:
        if skill in text_lower or skill in tokens:
            found_skills.add(skill.title())
    
    # Check for soft skills
    for skill in SOFT_SKILLS:
        if skill in text_lower or skill in tokens:
            found_skills.add(skill.title())
    
    return list(found_skills)


def extract_keywords_from_jd(job):
    """Extract important keywords from job description"""
    keywords = set()
    
    # From requirements
    for req in job.get('requirements', []):
        req_processed = preprocess_text(req)
        keywords.update(tokenize(req_processed))
    
    # From responsibilities
    for resp in job.get('responsibilities', []):
        resp_processed = preprocess_text(resp)
        keywords.update(tokenize(resp_processed))
    
    # From description
    desc = preprocess_text(job.get('description', ''))
    keywords.update(tokenize(desc))
    
    # From title
    title = preprocess_text(job.get('title', ''))
    keywords.update(tokenize(title))
    
    return keywords


def calculate_keyword_match_score(resume_text, job):
    """
    Calculate ATS keyword match score
    - Exact keyword matching
    - Partial matching with similarity
    - Weighted by keyword importance
    """
    if not resume_text:
        return 0, [], []
    
    resume_processed = preprocess_text(resume_text)
    resume_tokens = tokenize(resume_processed)
    
    jd_keywords = extract_keywords_from_jd(job)
    
    # Filter to meaningful keywords (skills and important terms)
    important_keywords = set()
    for kw in jd_keywords:
        if kw in TECHNICAL_SKILLS or kw in SOFT_SKILLS:
            important_keywords.add(kw)
        elif len(kw) > 3:  # Filter out very short words
            # Check if it's a meaningful term
            if any(skill in kw or kw in skill for skill in TECHNICAL_SKILLS):
                important_keywords.add(kw)
    
    # Add explicit requirements as important
    for req in job.get('requirements', []):
        req_lower = req.lower().strip()
        if len(req_lower) > 2:
            important_keywords.add(req_lower)
    
    if not important_keywords:
        # Fallback to requirements list
        important_keywords = set(r.lower() for r in job.get('requirements', []))
    
    matched_keywords = []
    missing_keywords = []
    
    for keyword in important_keywords:
        # Exact match
        if keyword in resume_processed or keyword in resume_tokens:
            matched_keywords.append(keyword)
        # Fuzzy match for similar terms
        elif any(SequenceMatcher(None, keyword, token).ratio() > 0.85 for token in resume_tokens):
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)
    
    if not important_keywords:
        return 50, [], []  # Default score if no keywords to match
    
    score = int((len(matched_keywords) / len(important_keywords)) * 100)
    return min(100, score), matched_keywords[:20], missing_keywords[:10]


def calculate_skills_alignment_score(resume_skills, resume_text, job):
    """
    Calculate how well resume skills align with job requirements
    Uses both explicit skills and extracted skills from resume text
    """
    # Get all skills from resume
    all_resume_skills = set(s.lower() for s in resume_skills)
    extracted = extract_skills_from_text(resume_text)
    all_resume_skills.update(s.lower() for s in extracted)
    
    # Get required skills from job
    job_requirements = job.get('requirements', [])
    job_desc = job.get('description', '')
    job_title = job.get('title', '')
    
    # Extract skills from job
    job_text = ' '.join(job_requirements) + ' ' + job_desc + ' ' + job_title
    required_skills = set(s.lower() for s in extract_skills_from_text(job_text))
    
    # Also add explicit requirements
    for req in job_requirements:
        req_lower = req.lower()
        if req_lower in TECHNICAL_SKILLS or req_lower in SOFT_SKILLS:
            required_skills.add(req_lower)
    
    if not required_skills:
        return 70, [], []  # Default if no requirements specified
    
    matched_skills = []
    missing_skills = []
    
    for skill in required_skills:
        skill_matched = False
        for resume_skill in all_resume_skills:
            # Exact match or contains
            if skill == resume_skill or skill in resume_skill or resume_skill in skill:
                matched_skills.append(skill.title())
                skill_matched = True
                break
            # Fuzzy match
            if SequenceMatcher(None, skill, resume_skill).ratio() > 0.8:
                matched_skills.append(skill.title())
                skill_matched = True
                break
        
        if not skill_matched:
            missing_skills.append(skill.title())
    
    score = int((len(matched_skills) / len(required_skills)) * 100)
    return min(100, score), matched_skills, missing_skills


def calculate_experience_match_score(resume_text, experience_field, job):
    """
    Calculate experience matching score based on:
    - Years of experience mentioned
    - Relevance to job requirements
    - Quality of experience descriptions
    """
    combined_text = (resume_text + ' ' + experience_field).lower()
    
    # Extract years of experience
    years_patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)',
        r'(?:experience|exp)\s*(?:of)?\s*(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:in|of|working)',
        r'over\s*(\d+)\s*(?:years?|yrs?)',
    ]
    
    years_found = 0
    for pattern in years_patterns:
        matches = re.findall(pattern, combined_text)
        for match in matches:
            try:
                years_found = max(years_found, int(match))
            except:
                pass
    
    # Get job experience requirement
    job_exp = job.get('experience', '').lower()
    job_years_required = 0
    
    for pattern in years_patterns:
        matches = re.findall(pattern, job_exp)
        for match in matches:
            try:
                job_years_required = max(job_years_required, int(match))
            except:
                pass
    
    # Also check for simple patterns like "2-3 years"
    simple_pattern = re.findall(r'(\d+)', job_exp)
    if simple_pattern:
        job_years_required = max(job_years_required, int(simple_pattern[0]))
    
    # Calculate experience score
    if job_years_required == 0:
        # No specific requirement
        base_score = 75 if years_found > 0 else 60
    else:
        if years_found >= job_years_required:
            base_score = 90 + min(10, (years_found - job_years_required) * 2)
        elif years_found >= job_years_required * 0.7:
            base_score = 70 + int((years_found / job_years_required) * 20)
        else:
            base_score = 40 + int((years_found / max(1, job_years_required)) * 30)
    
    # Bonus for action verbs in experience
    action_verb_count = sum(1 for verb in ACTION_VERBS if verb in combined_text)
    action_bonus = min(5, action_verb_count // 2)
    
    # Bonus for quantifiable achievements
    quant_count = sum(1 for pattern in QUANTIFIABLE_PATTERNS if re.search(pattern, combined_text))
    quant_bonus = min(5, quant_count)
    
    final_score = min(100, base_score + action_bonus + quant_bonus)
    
    return final_score, years_found, job_years_required


def calculate_education_score(college, degree, resume_text, job):
    """
    Calculate education relevance score
    """
    combined_text = (college + ' ' + degree + ' ' + resume_text).lower()
    
    # Degree levels (higher = better)
    degree_scores = {
        'phd': 100, 'ph.d': 100, 'doctorate': 100,
        'master': 90, 'mba': 90, 'm.tech': 90, 'mtech': 90, 'ms': 90, 'msc': 88, 'm.sc': 88,
        'bachelor': 80, 'b.tech': 80, 'btech': 80, 'b.e': 80, 'be': 80, 'bsc': 78, 'b.sc': 78, 'ba': 75, 'b.a': 75,
        'diploma': 60, 'associate': 55, 'certificate': 50,
    }
    
    degree_score = 70  # Default
    for deg, score in degree_scores.items():
        if deg in combined_text:
            degree_score = max(degree_score, score)
            break
    
    # Premium institutions bonus
    premium_institutions = [
        'iit', 'iisc', 'bits', 'nit', 'iiit', 'isb', 'iim', 'nid',
        'mit', 'stanford', 'harvard', 'berkeley', 'cmu', 'carnegie mellon',
        'oxford', 'cambridge', 'caltech', 'eth zurich', 'georgia tech',
    ]
    
    institution_bonus = 0
    for inst in premium_institutions:
        if inst in combined_text:
            institution_bonus = 10
            break
    
    # Check relevance to job
    job_title = job.get('title', '').lower()
    job_dept = job.get('department', '').lower()
    
    relevance_bonus = 0
    tech_degrees = ['computer', 'software', 'engineering', 'technology', 'science', 'data', 'information']
    business_degrees = ['business', 'management', 'mba', 'commerce', 'economics', 'finance']
    design_degrees = ['design', 'art', 'creative', 'visual', 'ux', 'ui', 'graphic']
    
    if any(term in job_title or term in job_dept for term in ['software', 'developer', 'engineer', 'tech', 'data', 'ml', 'ai']):
        if any(deg in combined_text for deg in tech_degrees):
            relevance_bonus = 5
    elif any(term in job_title or term in job_dept for term in ['manager', 'business', 'analyst', 'product']):
        if any(deg in combined_text for deg in business_degrees):
            relevance_bonus = 5
    elif any(term in job_title or term in job_dept for term in ['design', 'ux', 'ui', 'creative']):
        if any(deg in combined_text for deg in design_degrees):
            relevance_bonus = 5
    
    final_score = min(100, degree_score + institution_bonus + relevance_bonus)
    return final_score


def calculate_formatting_score(resume_text):
    """
    Calculate resume formatting and structure score
    ATS systems prefer well-structured resumes
    """
    if not resume_text:
        return 50
    
    score = 60  # Base score
    
    # Check for section headers (indicates good structure)
    section_headers = ['experience', 'education', 'skills', 'projects', 'summary', 
                       'objective', 'work history', 'employment', 'qualifications',
                       'achievements', 'certifications', 'awards', 'languages']
    
    sections_found = sum(1 for header in section_headers if header in resume_text.lower())
    score += min(15, sections_found * 3)
    
    # Check for contact info patterns
    email_pattern = r'[\w\.-]+@[\w\.-]+'
    phone_pattern = r'[\+]?[\d\s\-\(\)]{10,}'
    
    if re.search(email_pattern, resume_text):
        score += 5
    if re.search(phone_pattern, resume_text):
        score += 5
    
    # Check for reasonable length
    word_count = len(resume_text.split())
    if 200 <= word_count <= 1500:
        score += 10
    elif word_count < 100:
        score -= 10
    
    # Check for bullet points or structured content
    if re.search(r'[•\-\*]\s', resume_text):
        score += 5
    
    return min(100, score)


def calculate_action_verbs_score(resume_text):
    """Score based on use of strong action verbs"""
    if not resume_text:
        return 50
    
    text_lower = resume_text.lower()
    words = text_lower.split()
    
    verb_count = sum(1 for word in words if word in ACTION_VERBS)
    
    # Score based on density of action verbs
    if verb_count >= 15:
        return 95
    elif verb_count >= 10:
        return 85
    elif verb_count >= 5:
        return 75
    elif verb_count >= 2:
        return 65
    else:
        return 50


def calculate_quantifiable_achievements_score(resume_text):
    """Score based on quantifiable achievements"""
    if not resume_text:
        return 50
    
    achievement_count = sum(1 for pattern in QUANTIFIABLE_PATTERNS if re.search(pattern, resume_text, re.IGNORECASE))
    
    if achievement_count >= 8:
        return 98
    elif achievement_count >= 5:
        return 88
    elif achievement_count >= 3:
        return 78
    elif achievement_count >= 1:
        return 65
    else:
        return 50


def generate_ai_analysis(scores, matched_keywords, missing_keywords, matched_skills, missing_skills, years_exp, years_required):
    """Generate detailed AI analysis based on all scores"""
    analysis_parts = []
    recommendations = []
    
    overall = scores['overall_score']
    
    # Overall assessment
    if overall >= 85:
        analysis_parts.append("🌟 Excellent match! This candidate strongly aligns with the job requirements.")
    elif overall >= 70:
        analysis_parts.append("✅ Good match. The candidate meets most of the key requirements.")
    elif overall >= 55:
        analysis_parts.append("⚡ Moderate match. The candidate has some relevant qualifications but gaps exist.")
    else:
        analysis_parts.append("⚠️ Low match. Significant gaps between candidate qualifications and requirements.")
    
    # Keyword analysis
    keyword_score = scores.get('keyword_match_score', 0)
    if keyword_score >= 80:
        analysis_parts.append(f"Keywords: Strong alignment with {len(matched_keywords)} key terms from the job description.")
    elif keyword_score >= 60:
        analysis_parts.append(f"Keywords: Moderate alignment. Found {len(matched_keywords)} matching keywords.")
    else:
        analysis_parts.append(f"Keywords: Consider adding more relevant keywords. Missing: {', '.join(missing_keywords[:5])}.")
        recommendations.append("Add more keywords from the job description to your resume")
    
    # Skills analysis
    skill_score = scores.get('skill_match_score', 0)
    if skill_score >= 80:
        analysis_parts.append(f"Skills: Excellent skill alignment with {len(matched_skills)} matching skills.")
    elif skill_score >= 60:
        analysis_parts.append(f"Skills: Good skill coverage. Consider highlighting: {', '.join(missing_skills[:3])}.")
    else:
        analysis_parts.append(f"Skills: Skills gap identified. Missing key skills: {', '.join(missing_skills[:5])}.")
        recommendations.append("Develop or highlight missing technical skills")
    
    # Experience analysis
    exp_score = scores.get('experience_score', 0)
    if years_required > 0:
        if years_exp >= years_required:
            analysis_parts.append(f"Experience: Meets requirement ({years_exp} years vs {years_required} required).")
        else:
            analysis_parts.append(f"Experience: Below requirement ({years_exp} years vs {years_required} required).")
            recommendations.append("Highlight relevant experience and transferable skills")
    else:
        if exp_score >= 70:
            analysis_parts.append("Experience: Relevant work experience demonstrated.")
        else:
            analysis_parts.append("Experience: Consider adding more details about work experience.")
    
    # Education analysis
    edu_score = scores.get('education_score', 0)
    if edu_score >= 85:
        analysis_parts.append("Education: Strong educational background relevant to the role.")
    elif edu_score >= 70:
        analysis_parts.append("Education: Adequate educational qualifications.")
    else:
        recommendations.append("Consider highlighting relevant coursework or certifications")
    
    # Formatting analysis
    format_score = scores.get('formatting_score', 0)
    if format_score < 70:
        recommendations.append("Improve resume structure with clear sections and bullet points")
    
    # Action verbs analysis
    action_score = scores.get('action_verbs_score', 0)
    if action_score < 70:
        recommendations.append("Use more action verbs (e.g., 'developed', 'implemented', 'led')")
    
    # Quantifiable achievements
    quant_score = scores.get('quantifiable_score', 0)
    if quant_score < 70:
        recommendations.append("Add quantifiable achievements (e.g., 'increased sales by 20%')")
    
    # Build final analysis
    full_analysis = " ".join(analysis_parts)
    
    if recommendations:
        full_analysis += "\n\n📋 Recommendations to improve ATS score:\n• " + "\n• ".join(recommendations[:5])
    
    return full_analysis


def score_resume(application, job, resume_text=None):
    """
    Main ATS scoring function
    Calculates comprehensive ATS score based on multiple factors
    Similar to real ATS systems like Taleo, Workday, Greenhouse
    """
    # Get resume text if available
    if resume_text is None:
        resume_text = application.get('resume_text', '')
    
    # Combine all available text from application
    experience_text = application.get('experience', '')
    cover_letter = application.get('cover_letter', '')
    combined_resume_text = f"{resume_text} {experience_text} {cover_letter}"
    
    resume_skills = application.get('skills', [])
    college = application.get('college', '')
    degree = application.get('degree', '')
    
    # Calculate individual scores
    
    # 1. Keyword Match Score (25% weight)
    keyword_score, matched_keywords, missing_keywords = calculate_keyword_match_score(combined_resume_text, job)
    
    # 2. Skills Alignment Score (25% weight)
    skill_score, matched_skills, missing_skills = calculate_skills_alignment_score(resume_skills, combined_resume_text, job)
    
    # 3. Experience Match Score (20% weight)
    experience_score, years_exp, years_required = calculate_experience_match_score(combined_resume_text, experience_text, job)
    
    # 4. Education Score (10% weight)
    education_score = calculate_education_score(college, degree, combined_resume_text, job)
    
    # 5. Resume Formatting Score (10% weight)
    formatting_score = calculate_formatting_score(resume_text)
    
    # 6. Action Verbs Score (5% weight)
    action_score = calculate_action_verbs_score(combined_resume_text)
    
    # 7. Quantifiable Achievements Score (5% weight)
    quantifiable_score = calculate_quantifiable_achievements_score(combined_resume_text)
    
    # Calculate weighted overall score
    overall_score = int(
        keyword_score * 0.25 +
        skill_score * 0.25 +
        experience_score * 0.20 +
        education_score * 0.10 +
        formatting_score * 0.10 +
        action_score * 0.05 +
        quantifiable_score * 0.05
    )
    
    scores = {
        'overall_score': overall_score,
        'keyword_match_score': keyword_score,
        'skill_match_score': skill_score,
        'experience_score': experience_score,
        'education_score': education_score,
        'formatting_score': formatting_score,
        'action_verbs_score': action_score,
        'quantifiable_score': quantifiable_score,
        'matched_keywords': matched_keywords[:15],
        'missing_keywords': missing_keywords[:10],
        'matched_skills': matched_skills[:15],
        'missing_skills': missing_skills[:10],
        'years_of_experience': years_exp,
        'years_required': years_required,
    }
    
    # Generate AI analysis
    scores['ai_analysis'] = generate_ai_analysis(
        scores, matched_keywords, missing_keywords,
        matched_skills, missing_skills, years_exp, years_required
    )
    
    return scores


def get_ats_breakdown(application, job, resume_text=None):
    """
    Get detailed ATS score breakdown for display
    Returns structured data for frontend visualization
    """
    scores = score_resume(application, job, resume_text)
    
    return {
        'overall': {
            'score': scores['overall_score'],
            'label': 'ATS Score',
            'description': 'Overall compatibility with job requirements'
        },
        'breakdown': [
            {
                'category': 'Keyword Match',
                'score': scores['keyword_match_score'],
                'weight': '25%',
                'description': 'How well resume keywords match job description',
                'matched': scores.get('matched_keywords', []),
                'missing': scores.get('missing_keywords', [])
            },
            {
                'category': 'Skills Alignment',
                'score': scores['skill_match_score'],
                'weight': '25%',
                'description': 'Technical and soft skills match',
                'matched': scores.get('matched_skills', []),
                'missing': scores.get('missing_skills', [])
            },
            {
                'category': 'Experience',
                'score': scores['experience_score'],
                'weight': '20%',
                'description': f"Experience level ({scores.get('years_of_experience', 0)} years found)"
            },
            {
                'category': 'Education',
                'score': scores['education_score'],
                'weight': '10%',
                'description': 'Educational background relevance'
            },
            {
                'category': 'Resume Format',
                'score': scores['formatting_score'],
                'weight': '10%',
                'description': 'Resume structure and readability'
            },
            {
                'category': 'Impact Language',
                'score': scores['action_verbs_score'],
                'weight': '5%',
                'description': 'Use of action verbs'
            },
            {
                'category': 'Achievements',
                'score': scores['quantifiable_score'],
                'weight': '5%',
                'description': 'Quantifiable accomplishments'
            }
        ],
        'analysis': scores['ai_analysis'],
        'recommendations': _extract_recommendations(scores)
    }


def _extract_recommendations(scores):
    """Extract improvement recommendations based on scores"""
    recommendations = []
    
    if scores['keyword_match_score'] < 70:
        recommendations.append({
            'priority': 'high',
            'area': 'Keywords',
            'suggestion': f"Add missing keywords: {', '.join(scores.get('missing_keywords', [])[:5])}"
        })
    
    if scores['skill_match_score'] < 70:
        recommendations.append({
            'priority': 'high',
            'area': 'Skills',
            'suggestion': f"Include these skills: {', '.join(scores.get('missing_skills', [])[:5])}"
        })
    
    if scores['experience_score'] < 70:
        recommendations.append({
            'priority': 'medium',
            'area': 'Experience',
            'suggestion': 'Highlight relevant work experience and quantify achievements'
        })
    
    if scores['formatting_score'] < 70:
        recommendations.append({
            'priority': 'medium',
            'area': 'Format',
            'suggestion': 'Use clear sections: Summary, Experience, Skills, Education'
        })
    
    if scores['action_verbs_score'] < 70:
        recommendations.append({
            'priority': 'low',
            'area': 'Language',
            'suggestion': 'Start bullet points with action verbs like "developed", "led", "improved"'
        })
    
    if scores['quantifiable_score'] < 70:
        recommendations.append({
            'priority': 'low',
            'area': 'Impact',
            'suggestion': 'Add metrics: percentages, dollar amounts, team sizes, user counts'
        })
    
    return recommendations
