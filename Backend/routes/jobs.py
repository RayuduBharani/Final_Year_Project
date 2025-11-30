from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from bson import ObjectId
import os

from config.database import jobs_collection, applications_collection
from utils.helpers import serialize_doc, get_authenticated_user

jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')


@jobs_bp.route('', methods=['GET'])
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


@jobs_bp.route('/<job_id>', methods=['GET'])
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


@jobs_bp.route('', methods=['POST'])
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
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"jd_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
            jd_file.save(filepath)
            job['jd_file_path'] = filepath
    
    result = jobs_collection.insert_one(job)
    job['_id'] = result.inserted_id
    
    return jsonify({'success': True, 'message': 'Job created successfully', 'job': serialize_doc(job)}), 201


@jobs_bp.route('/<job_id>', methods=['PUT'])
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


@jobs_bp.route('/<job_id>', methods=['DELETE'])
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


@jobs_bp.route('/<job_id>/close', methods=['PUT'])
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
