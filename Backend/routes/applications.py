from flask import Blueprint, jsonify, request, send_file, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from bson import ObjectId
import os
import uuid
import random

from config.database import jobs_collection, applications_collection
from config.settings import ALLOWED_EXTENSIONS
from utils.helpers import serialize_doc, get_authenticated_user, allowed_file
from utils.text_extraction import extract_text_from_pdf, extract_text_from_docx
from utils.scoring import extract_skills_from_text, score_resume, get_ats_breakdown

applications_bp = Blueprint('applications', __name__, url_prefix='/api')


@applications_bp.route('/applications', methods=['GET'])
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


@applications_bp.route('/applications/<app_id>', methods=['GET'])
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


@applications_bp.route('/jobs/<job_id>/apply', methods=['POST'])
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
        print(f"📥 Application received: {data.get('student_name')} - {data.get('email')}")
    else:
        data = request.get_json() or {}
        resume_file = None
        print(f"📥 JSON Application received: {data}")
    
    # Validate - make college and degree optional
    if not data.get('student_name'):
        print("❌ Validation failed: Name is required")
        return jsonify({'success': False, 'message': 'Name is required'}), 400
    
    if not data.get('email'):
        print("❌ Validation failed: Email is required")
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    
    if '@' not in data['email']:
        print("❌ Validation failed: Invalid email format")
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    # Check duplicate
    existing = applications_collection.find_one({
        'job_id': job_id,
        'email': {'$regex': f'^{data["email"]}$', '$options': 'i'}
    })
    if existing:
        print(f"❌ Duplicate application: {data['email']} already applied")
        return jsonify({'success': False, 'message': 'You have already applied for this job'}), 400
    
    # Handle file upload
    resume_filename = None
    extracted_skills = []
    resume_text = ""
    
    if resume_file and allowed_file(resume_file.filename):
        original_filename = secure_filename(resume_file.filename)
        filename = f"{data['student_name'].replace(' ', '_')}_{job_id}_{uuid.uuid4().hex[:8]}_{original_filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes', filename)
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
        'college': data.get('college', '').strip(),
        'degree': data.get('degree', '').strip(),
        'graduation_year': data.get('graduation_year', '').strip(),
        'experience': data.get('experience', '').strip(),
        'cover_letter': data.get('cover_letter', '').strip(),
        'skills': skills,
        'resume_file': resume_filename,
        'resume_text': resume_text,  # Store extracted resume text for future rescoring
        'submitted_at': datetime.now(),
        'status': 'pending'
    }
    
    # Calculate ATS scores using the new comprehensive scoring system
    scores = score_resume(application, serialize_doc(job), resume_text)
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


@applications_bp.route('/applications/<app_id>/status', methods=['PUT'])
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


@applications_bp.route('/applications/<app_id>/rescore', methods=['POST'])
def rescore_application(app_id):
    """Recalculate ATS scores for an application"""
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
    
    # Get resume text - either from stored text or re-extract from file
    resume_text = application.get('resume_text', '')
    
    if not resume_text and application.get('resume_file'):
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes', application['resume_file'])
        if os.path.exists(file_path):
            file_ext = application['resume_file'].rsplit('.', 1)[1].lower()
            if file_ext == 'pdf':
                from utils.text_extraction import extract_text_from_pdf
                resume_text = extract_text_from_pdf(file_path)
            elif file_ext in ['doc', 'docx']:
                from utils.text_extraction import extract_text_from_docx
                resume_text = extract_text_from_docx(file_path)
    
    scores = score_resume(serialize_doc(application), serialize_doc(job), resume_text)
    
    # Update application with new scores and resume text
    update_data = scores.copy()
    if resume_text:
        update_data['resume_text'] = resume_text
    
    applications_collection.update_one({'_id': ObjectId(app_id)}, {'$set': update_data})
    
    updated_app = applications_collection.find_one({'_id': ObjectId(app_id)})
    return jsonify({
        'success': True,
        'message': 'ATS scores recalculated successfully',
        'application': serialize_doc(updated_app)
    })


@applications_bp.route('/applications/<app_id>/ats-breakdown', methods=['GET'])
def get_ats_score_breakdown(app_id):
    """Get detailed ATS score breakdown for an application"""
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
    
    if not job:
        return jsonify({'success': False, 'message': 'Associated job not found'}), 404
    
    # Get resume text
    resume_text = application.get('resume_text', '')
    
    if not resume_text and application.get('resume_file'):
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes', application['resume_file'])
        if os.path.exists(file_path):
            file_ext = application['resume_file'].rsplit('.', 1)[1].lower()
            if file_ext == 'pdf':
                from utils.text_extraction import extract_text_from_pdf
                resume_text = extract_text_from_pdf(file_path)
            elif file_ext in ['doc', 'docx']:
                from utils.text_extraction import extract_text_from_docx
                resume_text = extract_text_from_docx(file_path)
    
    # Get detailed breakdown
    breakdown = get_ats_breakdown(serialize_doc(application), serialize_doc(job), resume_text)
    
    return jsonify({
        'success': True,
        'application_id': app_id,
        'candidate_name': application.get('student_name', ''),
        'job_title': job.get('title', ''),
        'ats_breakdown': breakdown
    })


@applications_bp.route('/jobs/<job_id>/rescore-all', methods=['POST'])
def rescore_all_applications(job_id):
    """Recalculate ATS scores for all applications of a job"""
    user = get_authenticated_user(request)
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid job ID'}), 400
    
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    
    # Get all applications for this job
    applications = list(applications_collection.find({'job_id': job_id}))
    
    rescored_count = 0
    errors = []
    
    for application in applications:
        try:
            # Get resume text
            resume_text = application.get('resume_text', '')
            
            if not resume_text and application.get('resume_file'):
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes', application['resume_file'])
                if os.path.exists(file_path):
                    file_ext = application['resume_file'].rsplit('.', 1)[1].lower()
                    if file_ext == 'pdf':
                        resume_text = extract_text_from_pdf(file_path)
                    elif file_ext in ['doc', 'docx']:
                        resume_text = extract_text_from_docx(file_path)
            
            # Calculate new scores
            scores = score_resume(serialize_doc(application), serialize_doc(job), resume_text)
            
            # Update application
            update_data = scores.copy()
            if resume_text:
                update_data['resume_text'] = resume_text
            
            applications_collection.update_one(
                {'_id': application['_id']},
                {'$set': update_data}
            )
            rescored_count += 1
            
        except Exception as e:
            errors.append({
                'application_id': str(application['_id']),
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'message': f'Rescored {rescored_count} applications',
        'total': len(applications),
        'rescored': rescored_count,
        'errors': errors
    })


@applications_bp.route('/applications/<app_id>/resume', methods=['GET'])
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
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes', application['resume_file'])
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Resume file not found on server'}), 404
    
    return send_file(file_path, as_attachment=True)


@applications_bp.route('/applications/<app_id>', methods=['DELETE'])
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
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes', application['resume_file'])
        if os.path.exists(file_path):
            os.remove(file_path)
    
    applications_collection.delete_one({'_id': ObjectId(app_id)})
    return jsonify({'success': True, 'message': 'Application deleted successfully'})
