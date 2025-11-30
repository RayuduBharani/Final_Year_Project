from flask import Blueprint, jsonify, request
from bson import ObjectId

from config.database import jobs_collection, applications_collection
from utils.helpers import serialize_doc, get_authenticated_user

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api')


@analytics_bp.route('/analytics/overview', methods=['GET'])
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


@analytics_bp.route('/analytics/job/<job_id>', methods=['GET'])
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
                'college': a.get('college', '')
            } for a in job_apps],
            key=lambda x: x['score'],
            reverse=True
        )[:10]
    }
    
    return jsonify({'success': True, 'analytics': analytics})


@analytics_bp.route('/departments', methods=['GET'])
def get_departments():
    """Get list of unique departments"""
    departments = jobs_collection.distinct('department')
    departments.sort()
    return jsonify({'success': True, 'departments': departments})
