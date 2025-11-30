from datetime import datetime
from bson import ObjectId
import uuid

from config.settings import ALLOWED_EXTENSIONS
from config.database import sessions_collection, users_collection


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
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_session_token():
    """Generate a unique session token"""
    return str(uuid.uuid4())


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
